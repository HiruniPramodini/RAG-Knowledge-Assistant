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


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator_tool(expression: str):
    """
    Safely evaluates a plain arithmetic expression (+, -, *, /, **)
    and returns a numeric result, without using Python's raw eval().
    """
    tree = ast.parse(expression, mode="eval")
    return _safe_eval(tree.body)

