from google import genai

from config import GEMINI_API_KEY
from retrieve import retrieve_relevant_chunks

client = genai.Client(api_key=GEMINI_API_KEY)


def build_prompt(query, chunks):
    """Combine retrieved chunks and the user's question into a single prompt."""
    context = "\n\n".join(
        f"[Source: {chunk.metadata.get('source', 'unknown')}]\n{chunk.page_content}"
        for chunk in chunks
    )

    prompt = f"""You are a helpful engineering assistant. Answer the question using ONLY the context provided below. If the context doesn't contain enough information to answer, say so honestly instead of guessing.

Context:
{context}

Question: {query}

Answer:"""
    return prompt


def generate_answer(query, k=3):
    """Retrieve relevant chunks and generate a grounded answer."""
    chunks = retrieve_relevant_chunks(query, k=k)
    prompt = build_prompt(query, chunks)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    sources = sorted(set(chunk.metadata.get("source", "unknown") for chunk in chunks))

    return {
        "answer": response.text,
        "sources": sources,
    }


if __name__ == "__main__":
    query = "how do I stop my container from losing data on restart?"
    result = generate_answer(query)

    print(f"Question: {query}\n")
    print(f"Answer:\n{result['answer']}\n")
    print(f"Sources: {', '.join(result['sources'])}")