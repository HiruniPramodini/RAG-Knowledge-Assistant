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


def build_prompt(query, chunks, history=None):
    """Combine retrieved chunks, conversation history, and the question into one prompt."""
    context = "\n\n".join(
        f"[Source: {chunk.metadata.get('source', 'unknown')}]\n{chunk.page_content}"
        for chunk in chunks
    )

    history_text = format_history(history or [])

    prompt = f"""You are a helpful engineering assistant. Answer the question using ONLY the context provided below. If the context doesn't contain enough information to answer, say so honestly instead of guessing.

{history_text}Context:
{context}

Question: {query}

Answer:"""
    return prompt


def generate_answer(query, k=3, history=None):
    """Retrieve relevant chunks and generate a grounded answer, aware of prior conversation turns."""
    chunks = retrieve_relevant_chunks(query, k=k)
    prompt = build_prompt(query, chunks, history=history)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    sources = sorted(set(chunk.metadata.get("source", "unknown") for chunk in chunks))

    return {
        "answer": response.text,
        "sources": sources,
    }

