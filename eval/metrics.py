from google import genai
from src.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


def compute_precision(retrieved_chunks, expected_sources):
    """
    Of the chunks we retrieved, what fraction came from an expected source?

    Returns a float between 0 and 1. If expected_sources is empty
    (out-of-scope question), precision is undefined for this metric,
    so we return None and handle it separately.
    """
    if not expected_sources:
        return None

    if not retrieved_chunks:
        return 0.0

    relevant_count = sum(
        1 for chunk in retrieved_chunks
        if any(source in chunk.metadata.get("source", "") for source in expected_sources)
    )
    return relevant_count / len(retrieved_chunks)


def compute_recall(retrieved_chunks, expected_sources):
    """
    Did we retrieve at least one chunk from EACH expected source?

    Returns a float between 0 and 1 representing the fraction of
    expected sources that were found by at least one retrieved chunk.
    """
    if not expected_sources:
        return None

    retrieved_sources = set(chunk.metadata.get("source", "") for chunk in retrieved_chunks)

    found_count = sum(
        1 for expected in expected_sources
        if any(expected in source for source in retrieved_sources)
    )
    return found_count / len(expected_sources)


def compute_faithfulness(answer, retrieved_chunks):
    """
    Uses an LLM as a judge: is every claim in the answer actually
    supported by the retrieved context, or did the model add
    unsupported information?

    Returns a float: 1.0 if fully supported, 0.0 if not, with the
    judge's reasoning also returned for inspection.
    """
    context = "\n\n".join(chunk.page_content for chunk in retrieved_chunks)

    judge_prompt = f"""You are evaluating whether an AI-generated answer is fully supported by given context.

Context:
{context}

Answer to evaluate:
{answer}

Is every claim in the answer directly supported by the context above? 
Respond in exactly this format:
SCORE: [1 if fully supported, 0 if it contains unsupported claims]
REASON: [one sentence explanation]"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=judge_prompt,
    )

    result_text = response.text.strip()

    # Parse the judge's structured response
    score = 0.0
    reason = "Could not parse judge response"
    for line in result_text.split("\n"):
        if line.startswith("SCORE:"):
            score = float(line.replace("SCORE:", "").strip())
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    return score, reason