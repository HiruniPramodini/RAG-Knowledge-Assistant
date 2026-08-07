import time
import ast
import operator
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END
from google import genai
from google.genai.errors import ServerError

from src.config import GEMINI_API_KEY
from src.generate import generate_answer

client = genai.Client(api_key=GEMINI_API_KEY)


class GraphState(TypedDict):
    """The shared 'clipboard' that travels through every node in the graph."""
    question: str
    route: Optional[str]  # "rag", "direct", "clarify", or "tool_calculator"
    answer: Optional[str]
    sources: Optional[list]
    history: list  # list of {"question": ..., "answer": ..., "route": ...} from previous turns


def call_gemini_with_retry(model, contents, max_retries=3, delay_seconds=10):
    """
    Calls Gemini, retrying a few times if the server is temporarily
    overloaded (503), instead of crashing immediately.
    """
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model, contents=contents)
        except ServerError as e:
            if attempt < max_retries - 1:
                print(f"  [Retry] Server busy, waiting {delay_seconds}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay_seconds)
            else:
                raise e


def format_history(history, limit=3):
    """
    Turn the last few conversation turns into readable text for a prompt.
    Capped at `limit` turns so the prompt doesn't grow unbounded as a
    conversation gets longer (a simple 'sliding window' memory).
    """
    if not history:
        return ""

    recent_turns = history[-limit:]
    formatted = "\n".join(
        f"Q: {turn['question']}\nA: {turn['answer']}" for turn in recent_turns
    )
    return f"Previous conversation:\n{formatted}\n\n"


# --- Tool: calculator -------------------------------------------------
# A real "tool" in the agentic sense: precise, deterministic code the
# LLM cannot do reliably itself. We use Python's `ast` module to safely
# evaluate only arithmetic expressions -- never raw eval(), which would
# be a security risk (it could execute arbitrary code).

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}



def router_node(state: GraphState) -> GraphState:
    """
    Decide how to handle this question: retrieve documents (RAG), answer
    directly, ask a clarifying question, or hand off to the calculator
    tool for precise arithmetic.

    If the immediately previous turn was a clarifying question, we
    deterministically force the RAG path rather than asking the LLM to
    judge that again -- relying on the model to infer "this is a reply
    to my own clarification" from history text alone proved unreliable.
    """
    question = state["question"]
    history = state.get("history", [])

    if history and history[-1].get("route") == "clarify":
        print("[Router] Decision: rag (forced — this is a reply to a clarifying question)")
        return {**state, "route": "rag"}

    history_text = format_history(history)

    routing_prompt = f"""{history_text}You are routing a user's message to one of four paths. Respond with 
exactly one word: RAG, DIRECT, CLARIFY, or CALCULATOR.

- RAG: the question is about Docker, Kubernetes, or FastAPI, even generally, and there is 
  enough information to search documentation and answer it.
- DIRECT: the question is unrelated to those topics (greetings, small talk, general 
  knowledge, personal info sharing) and needs no document lookup.
- CLARIFY: the question is about Docker, Kubernetes, or FastAPI, BUT it is too vague or 
  ambiguous to answer usefully as-is.
- CALCULATOR: the question requires precise arithmetic (addition, subtraction, 
  multiplication, division, exponents) on specific numbers, e.g. "what is 15% of 200" or 
  "if I run 3 replicas at 512MB each, how much total memory is that?".

Current question: {question}

Respond with exactly one word: RAG, DIRECT, CLARIFY, or CALCULATOR."""

    response = call_gemini_with_retry(
        model="gemini-2.5-flash-lite",
        contents=routing_prompt,
    )

    decision = response.text.strip().upper()

    if "CALCULATOR" in decision:
        route = "tool_calculator"
    elif "CLARIFY" in decision:
        route = "clarify"
    elif "RAG" in decision:
        route = "rag"
    else:
        route = "direct"

    print(f"[Router] Decision: {route}")

    return {**state, "route": route}


def rag_node(state: GraphState) -> GraphState:
    """Run the existing retrieve + generate pipeline, passing conversation history through."""
    result = generate_answer(state["question"], history=state.get("history", []))
    return {**state, "answer": result["answer"], "sources": result["sources"]}


def direct_answer_node(state: GraphState) -> GraphState:
    """Answer directly, without any document retrieval, but still aware of prior turns."""
    history_text = format_history(state.get("history", []))

    prompt = f"""You are a helpful assistant having an ongoing conversation. 
Use the conversation history below to remember facts the user has already told you 
(like their name), and answer naturally as a continuation of the conversation.

{history_text}Current question: {state['question']}

Answer:"""

    response = call_gemini_with_retry(
        model="gemini-2.5-flash-lite",
        contents=prompt,
    )
    return {**state, "answer": response.text, "sources": []}


def clarify_node(state: GraphState) -> GraphState:
    """
    The question is too ambiguous to answer well. Ask the user a specific
    clarifying question instead of guessing, and stop here for this turn.
    """
    history_text = format_history(state.get("history", []))

    prompt = f"""{history_text}The user's question below is too vague or ambiguous to answer 
usefully as-is, in the context of a Docker/Kubernetes/FastAPI assistant. Ask ONE short, 
specific clarifying question to understand what they actually need. Do not answer the 
question yet — only ask for clarification.

Question: {state['question']}

Clarifying question:"""

    response = call_gemini_with_retry(
        model="gemini-2.5-flash-lite",
        contents=prompt,
    )
    return {**state, "answer": response.text, "sources": []}


def calculator_node(state: GraphState) -> GraphState:
    """
    Tool-calling node: extract a plain arithmetic expression from the
    question using the LLM, then compute the exact answer with real code
    instead of letting the LLM guess at arithmetic (which it is prone to
    get wrong, especially with larger numbers or multiple steps).
    """
    extraction_prompt = f"""Extract ONLY the arithmetic expression from this question, using 
plain math symbols (+, -, *, /, **) and numbers. Do not solve it. Do not explain. 
Respond with ONLY the expression, nothing else.

Question: {state['question']}

Expression:"""

    response = call_gemini_with_retry(
        model="gemini-2.5-flash-lite",
        contents=extraction_prompt,
    )
    expression = response.text.strip()

    try:
        result = calculator_tool(expression)
        answer = f"{expression} = {result}"
        print(f"[Tool: Calculator] Evaluated '{expression}' = {result}")
    except Exception:
        answer = (
            f"I identified this as a math question, but couldn't safely parse the "
            f"expression ('{expression}'). Could you rephrase it as a plain calculation?"
        )
        print(f"[Tool: Calculator] Failed to parse '{expression}'")

    return {**state, "answer": answer, "sources": []}


def route_decision(state: GraphState) -> str:
    """Tells the graph which node to go to next, based on the router's decision."""
    mapping = {
        "rag": "rag_node",
        "direct": "direct_answer_node",
        "clarify": "clarify_node",
        "tool_calculator": "calculator_node",
    }
    return mapping[state["route"]]


def build_graph():
    """Assemble the graph: nodes, edges, and the conditional routing logic."""
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
    graph = build_graph()
    history = []

    test_questions = [
        "If I run 3 replicas at 512 megabytes each, what's the total memory in megabytes?",
        "Hello, how are you today?",
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        result = graph.invoke({
            "question": question,
            "route": None,
            "answer": None,
            "sources": None,
            "history": history,
        })
        print(f"Answer: {result['answer']}")
        print(f"Sources: {result['sources']}")

        history.append({
            "question": question,
            "answer": result["answer"],
            "route": result["route"],
        })