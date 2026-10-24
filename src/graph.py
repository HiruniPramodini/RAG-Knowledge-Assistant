"""Agentic StateGraph Orchestrator for the Enterprise Company Knowledge Assistant.

Orchestrates multi-turn intent routing, document-grounded RAG, safe conversational
direct responses, focused ambiguity clarification, and deterministic AST-based arithmetic calculation.
"""

import ast
import operator
import re
import time
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, START, END
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

from src.config import (
    GEMINI_API_KEY,
    ROUTING_MODEL,
    GENERATION_MODEL,
    validate_config,
)
from src.generate import generate_answer, format_history

# Initialized lazily
_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    """Returns or creates the GenAI client instance."""
    global _client
    if _client is None:
        validation = validate_config(require_api_key=True)
        if not validation["valid"]:
            raise ValueError("\n".join(validation["errors"]))
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class GraphState(TypedDict):
    """The shared state dictionary carried through all graph nodes."""
    question: str
    route: Optional[str]             # "rag", "direct", "clarify", "tool_calculator"
    answer: Optional[str]
    sources: Optional[List[str]]
    source_details: Optional[List[Dict[str, Any]]]
    history: List[Dict[str, Any]]   # [{"question": ..., "answer": ..., "route": ...}]
    is_grounded: Optional[bool]


# -----------------------------------------------------------------------------
# SAFE AST CALCULATOR TOOL
# -----------------------------------------------------------------------------

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

MAX_EXPRESSION_LENGTH = 120
MAX_POWER_EXPONENT = 10
MAX_RESULT_MAGNITUDE = 10**14


def _safe_eval_node(node: ast.AST) -> float:
    """Recursively evaluates AST nodes against an explicit whitelist of safe operations."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Only numeric constants are supported.")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

        left_val = _safe_eval_node(node.left)
        right_val = _safe_eval_node(node.right)

        # Safety bounds on exponentiation to prevent CPU denial of service
        if op_type is ast.Pow:
            if abs(right_val) > MAX_POWER_EXPONENT or abs(left_val) > 10000:
                raise ValueError(
                    f"Exponentiation too large. Maximum supported exponent is {MAX_POWER_EXPONENT}."
                )

        # Handle division by zero safely
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right_val == 0:
            raise ZeroDivisionError("Division by zero is undefined.")

        result = _ALLOWED_OPERATORS[op_type](left_val, right_val)

        if abs(result) > MAX_RESULT_MAGNITUDE:
            raise ValueError("Calculation result exceeds maximum supported magnitude.")

        return float(result)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand_val = _safe_eval_node(node.operand)
        return float(_ALLOWED_OPERATORS[op_type](operand_val))

    else:
        # Explicitly reject all other AST types: ast.Call, ast.Name, ast.Attribute, ast.Import, etc.
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def calculator_tool(expression: str) -> float:
    """Safely evaluates an arithmetic expression using AST parsing without raw eval().

    Args:
        expression: String containing math expression (e.g., '20 - 12', '1500 * 0.10').

    Returns:
        Evaluated numeric float or int result.
    """
    clean_expr = expression.strip()
    if not clean_expr:
        raise ValueError("Empty calculation expression.")

    if len(clean_expr) > MAX_EXPRESSION_LENGTH:
        raise ValueError("Expression is too long to evaluate safely.")

    # Parse into an AST tree in eval mode
    tree = ast.parse(clean_expr, mode="eval")
    result = _safe_eval_node(tree.body)

    # Return clean integer if result has no fractional part
    if result.is_integer():
        return int(result)
    return round(result, 4)


# -----------------------------------------------------------------------------
# GRAPH NODES
# -----------------------------------------------------------------------------

def call_gemini_with_retry(model: str, contents: str, max_retries: int = 2) -> str:
    """Helper to query Gemini with retry on transient server or rate limit errors, and fallback models."""
    client = get_client()
    candidates = [model, "gemma-4-26b-a4b-it", "gemini-3.5-flash", "gemini-3.6-flash", "gemma-4-31b-it"]
    seen = set()
    models = [m for m in candidates if not (m in seen or seen.add(m))]

    for m in models:
        try:
            if "gemma" in m.lower():
                config = None
            else:
                config = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            resp = client.models.generate_content(model=m, contents=contents, config=config)
            text = resp.text.strip()
            if text:
                return text
        except Exception as e:
            # Try next model if quota or server error
            continue

    return ""


def router_node(state: GraphState) -> GraphState:
    """Classifies user intent into one of 4 deterministic paths:

    - RAG: Questions asking about company policies, IT, projects, standards, culture.
    - DIRECT: Pure greetings, polite small talk, general bot capability inquiries.
    - CLARIFY: Genuinely ambiguous internal questions needing follow-up details.
    - TOOL_CALCULATOR: Questions requiring arithmetic computation on numbers.
    """
    question = state["question"]
    history = state.get("history", [])

    # Deterministic Rule 1: If the immediately previous turn was a clarification,
    # the user's current response is an answer to that clarification -> force RAG!
    if history and history[-1].get("route") == "clarify":
        return {**state, "route": "rag"}

    # Deterministic Rule 2: Pure greetings without company queries
    clean_lower = question.strip().lower()
    clean_no_punct = re.sub(r"[^\w\s]", "", clean_lower).strip()
    greetings = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you", "how are you doing today", "how are you doing"}
    if clean_no_punct in greetings or any(clean_no_punct.startswith(g) for g in ["hello", "hi ", "hey "]):
        # Check if they also asked a company question in the same message
        company_keywords = ["leave", "policy", "aurelia", "vpn", "laptop", "project", "sick", "holiday", "salary", "hours", "review", "mfa"]
        if not any(k in clean_no_punct for k in company_keywords):
            return {**state, "route": "direct"}

    # Deterministic Rule 3: Fast keyword routing for unambiguous company queries
    company_rag_keywords = [
        "policy", "leave", "vacation", "sick", "benefits", "insurance", "carry over", "carryover",
        "vpn", "laptop", "macbook", "okta", "1password", "hardware", "wifi",
        "engineering", "tech stack", "git", "branch", "pull request", "code review", " pr ",
        "project atlas", "project horizon", "project beacon", "architecture", "microservice",
        "code of conduct", "harassment", "whistleblower", "pto", "holiday", "onboarding"
    ]
    math_clues = ["how many are left", "how many left", "calculate", "compute", "remaining"]
    if any(kw in clean_lower for kw in company_rag_keywords) and not any(clue in clean_lower for clue in math_clues):
        return {**state, "route": "rag"}

    # Deterministic Rule 4: Conversational follow-ups when prior turn was RAG
    followup_clues = [
        "what about", "how about", "and what", "can you summarize", "summarize",
        "summarise", "tell me more", "explain that", "what does that mean",
        "in simple terms", "who owns that", "is that allowed", "elaborate"
    ]
    if history and history[-1].get("route") == "rag" and any(fc in clean_lower for fc in followup_clues):
        return {**state, "route": "rag"}

    # Prompt LLM for intent classification
    history_context = format_history(history, limit=2)

    prompt = f"""{history_context}You are an intent router for Aurelia Tech' Internal Knowledge Assistant.
Analyze the user's current message and classify it into EXACTLY ONE route: RAG, DIRECT, CLARIFY, or CALCULATOR.

RULES:
- RAG: Question is about the company (policies, HR, leave, IT onboarding, hardware, VPN, passwords, engineering standards, tech stack, current projects, code of conduct, acronyms, contacts, or documentation).
- DIRECT: Conversational greetings, pleasantries, small talk, or asking what the assistant can do.
- CLARIFY: The user is asking about an internal company process, BUT the question is too vague or ambiguous to look up usefully as-is (e.g. "Can I do that?", "What is the policy for it?").
- CALCULATOR: The question asks to compute an exact numeric calculation (e.g., "If I have 20 days and take 8, how many are left?", "What is 1500 * 0.10?"). Note: Questions simply asking what a number is in policy (e.g., "How many leave days do I get?") are RAG, NOT calculator.

Current Question: {question}

Respond with EXACTLY ONE word: RAG, DIRECT, CLARIFY, or CALCULATOR."""

    try:
        decision_raw = call_gemini_with_retry(ROUTING_MODEL, prompt)
        decision = decision_raw.strip().upper()
    except Exception as e:
        print(f"[Router Warning] Model routing failed ({e}), falling back to safe heuristic.")
        # Fallback heuristic: check if message has numbers and arithmetic intent
        has_digits = any(c.isdigit() for c in question)
        math_clues = ["how many are left", "how many left", "remaining", "minus", "plus", "calculate", "compute", "take ", "used "]
        if has_digits and any(clue in clean_lower for clue in math_clues):
            decision = "CALCULATOR"
        else:
            decision = "RAG"

    if "CALCULATOR" in decision:
        route = "tool_calculator"
    elif "CLARIFY" in decision:
        route = "clarify"
    elif "DIRECT" in decision:
        route = "direct"
    else:
        # Default fallback favors RAG to avoid missing internal company documentation
        route = "rag"

    return {**state, "route": route}


def rag_node(state: GraphState) -> GraphState:
    """Executes document retrieval and grounded answer synthesis with source validation."""
    result = generate_answer(
        query=state["question"],
        history=state.get("history", []),
    )
    return {
        **state,
        "answer": result["answer"],
        "sources": result["sources"],
        "source_details": result.get("source_details", []),
        "is_grounded": result.get("is_grounded", False),
    }


def direct_answer_node(state: GraphState) -> GraphState:
    """Answers conversational pleasantries directly without searching documentation."""
    history_text = format_history(state.get("history", []), limit=2)

    prompt = f"""You are the friendly, professional internal Knowledge Assistant for Aurelia Tech.
Respond to the employee's conversational message politely.

CRITICAL RULE: Do NOT invent or state factual company policies, benefits numbers, or project statuses here. If the user appears to be asking for company information, invite them to ask the specific question so you can search the verified internal documentation.

{history_text}Employee message: {state['question']}

Response:"""

    try:
        answer_text = call_gemini_with_retry(ROUTING_MODEL, prompt)
    except Exception:
        answer_text = (
            "Hello! I am the Aurelia Knowledge Assistant. I can help answer questions "
            "about company policies, HR benefits, IT setup, engineering standards, "
            "and active projects. How can I help you today?"
        )

    return {
        **state,
        "answer": answer_text,
        "sources": [],
        "source_details": [],
        "is_grounded": False,
    }


def clarify_node(state: GraphState) -> GraphState:
    """Prompts the user for one specific clarifying detail when the query is ambiguous."""
    history_text = format_history(state.get("history", []), limit=2)

    prompt = f"""{history_text}The employee's question below is too vague or ambiguous to search internal company documentation effectively.
Ask ONE clear, polite, and specific clarifying question to determine what they need (e.g. which department, policy, or project they are referring to). Do NOT answer the question yet.

Question: {state['question']}

Clarifying question:"""

    try:
        clarifying_q = call_gemini_with_retry(ROUTING_MODEL, prompt)
    except Exception:
        clarifying_q = (
            "Could you please specify which company policy, department, or project you would like to know about?"
        )

    return {
        **state,
        "answer": clarifying_q,
        "sources": [],
        "source_details": [],
        "is_grounded": False,
    }


def calculator_node(state: GraphState) -> GraphState:
    """Extracts arithmetic expression from the question and evaluates it deterministically via AST."""
    extraction_prompt = f"""Extract ONLY the plain arithmetic expression from this question using numbers and math operators (+, -, *, /, **, %).
Do NOT solve it. Do NOT explain. Respond with ONLY the expression (e.g. '20 - 12' or '1500 * 0.15').

Question: {state['question']}

Expression:"""

    q_lower = state["question"].lower()
    expr_clean = ""
    try:
        expr_text = call_gemini_with_retry(ROUTING_MODEL, extraction_prompt)
        expr_clean = expr_text.strip().replace("`", "").split("\n")[0].strip()
        expr_clean = re.sub(r"[^0-9+\-*/().%* ]", "", expr_clean)
    except Exception:
        expr_clean = ""

    # Fallback heuristic extraction if model extraction fails or is rate-limited
    if not expr_clean:
        nums = re.findall(r"\b\d+(?:\.\d+)?\b", state["question"])
        if len(nums) >= 2:
            if any(w in q_lower for w in ["take", "minus", "left", "used", "remaining", "subtract"]):
                expr_clean = f"{nums[0]} - {nums[1]}"
            elif any(w in q_lower for w in ["plus", "add", "total", "sum"]):
                expr_clean = f"{nums[0]} + {nums[1]}"
            elif any(w in q_lower for w in ["times", "multiply", "*"]):
                expr_clean = f"{nums[0]} * {nums[1]}"
            elif any(w in q_lower for w in ["divide", "split"]):
                expr_clean = f"{nums[0]} / {nums[1]}"

    try:
        computed_result = calculator_tool(expr_clean)
        answer = f"**Calculation:** `{expr_clean}` = **{computed_result}**"
    except ZeroDivisionError:
        answer = "I identified this as a math question, but cannot divide by zero."
    except Exception as e:
        answer = (
            f"I recognized this as a calculation request, but could not safely evaluate the expression. "
            f"Please enter standard numbers and operators (e.g. `20 - 8`)."
        )

    return {
        **state,
        "answer": answer,
        "sources": [],
        "source_details": [],
        "is_grounded": False,
    }


def route_decision(state: GraphState) -> str:
    """Conditional edge dispatcher mapping the state's route to the next graph node."""
    mapping = {
        "rag": "rag_node",
        "direct": "direct_answer_node",
        "clarify": "clarify_node",
        "tool_calculator": "calculator_node",
    }
    return mapping.get(state.get("route", "rag"), "rag_node")


# -----------------------------------------------------------------------------
# GRAPH COMPILER
# -----------------------------------------------------------------------------

def build_graph():
    """Assembles and compiles the StateGraph workflow."""
    workflow = StateGraph(GraphState)

    workflow.add_node("router_node", router_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("direct_answer_node", direct_answer_node)
    workflow.add_node("clarify_node", clarify_node)
    workflow.add_node("calculator_node", calculator_node)

    workflow.add_edge(START, "router_node")

    workflow.add_conditional_edges(
        "router_node",
        route_decision,
        {
            "rag_node": "rag_node",
            "direct_answer_node": "direct_answer_node",
            "clarify_node": "clarify_node",
            "calculator_node": "calculator_node",
        },
    )

    workflow.add_edge("rag_node", END)
    workflow.add_edge("direct_answer_node", END)
    workflow.add_edge("clarify_node", END)
    workflow.add_edge("calculator_node", END)

    return workflow.compile()


if __name__ == "__main__":
    app_graph = build_graph()
    test_queries = [
        "Hello there!",
        "What is the annual leave carryover rule?",
        "If I accrue 20 days and take 14, how many days remain?",
    ]
    test_history: List[Dict[str, Any]] = []

    for q in test_queries:
        print(f"\n{'='*60}\nUser: {q}")
        res = app_graph.invoke({
            "question": q,
            "route": None,
            "answer": None,
            "sources": None,
            "source_details": None,
            "history": test_history,
            "is_grounded": None,
        })
        print(f"Route: {res['route']}")
        print(f"Assistant:\n{res['answer']}")
        if res.get("sources"):
            print(f"Sources: {res['sources']}")
        test_history.append({
            "question": q,
            "answer": res["answer"],
            "route": res["route"],
        })