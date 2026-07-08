import time
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
    needs_retrieval: Optional[bool]
    answer: Optional[str]
    sources: Optional[list]
    history: list  # list of {"question": ..., "answer": ...} from previous turns


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


def router_node(state: GraphState) -> GraphState:
    """
    Decide whether this question needs document retrieval, or can be
    answered directly without touching the vector database at all.
    """
    question = state["question"]
    history_text = format_history(state.get("history", []))

