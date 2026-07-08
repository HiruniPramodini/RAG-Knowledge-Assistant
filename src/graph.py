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

