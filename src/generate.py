from google import genai

from src.config import GEMINI_API_KEY
from src.retrieve import retrieve_relevant_chunks

client = genai.Client(api_key=GEMINI_API_KEY)


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
    return f"Previous conversation (use this to resolve references like 'that' or 'it'):\n{formatted}\n\n"

