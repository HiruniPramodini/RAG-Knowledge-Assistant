"""Evaluation Metrics for the Enterprise RAG Knowledge Assistant.

Calculates Context Precision, Context Recall, and Faithfulness (LLM-as-a-Judge)
with transient error retries and lazy client initialization.
"""

import time
from typing import List, Optional, Tuple
from google import genai
from google.genai.errors import ServerError, ClientError
from src.config import GEMINI_API_KEY, GENERATION_MODEL, validate_config

_client: Optional[genai.Client] = None


def get_eval_client() -> genai.Client:
    """Returns or lazily creates the GenAI client."""
    global _client
    if _client is None:
        validation = validate_config(require_api_key=True)
        if not validation["valid"]:
            raise ValueError("\n".join(validation["errors"]))
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def compute_precision(retrieved_chunks, expected_sources) -> Optional[float]:
    """Calculates what fraction of retrieved chunks originated from an expected document.

    Returns None for out-of-scope questions where expected_sources is empty.
    """
    if not expected_sources:
        return None

    if not retrieved_chunks:
        return 0.0

    relevant_count = sum(
        1 for chunk in retrieved_chunks
        if any(source in chunk.metadata.get("source", "") for source in expected_sources)
    )
    return round(relevant_count / len(retrieved_chunks), 3)


def compute_recall(retrieved_chunks, expected_sources) -> Optional[float]:
    """Calculates what fraction of expected source documents were captured in top-k chunks.

    Returns None for out-of-scope questions.
    """
    if not expected_sources:
        return None

    retrieved_sources = set(chunk.metadata.get("source", "") for chunk in retrieved_chunks)

    found_count = sum(
        1 for expected in expected_sources
        if any(expected in source for source in retrieved_sources)
    )
    return round(found_count / len(expected_sources), 3)


def compute_faithfulness(answer: str, retrieved_chunks) -> Tuple[float, str]:
    """Uses LLM-as-a-Judge to verify whether every factual assertion is supported by context.

    Returns:
        (score, reason) where score is 1.0 (fully grounded) or 0.0 (contains unsupported claims).
    """
    if not retrieved_chunks:
        return 0.0, "No context chunks retrieved to verify faithfulness."

    context = "\n\n".join(
        f"[Document: {chunk.metadata.get('title', chunk.metadata.get('source', ''))}]\n{chunk.page_content}"
        for chunk in retrieved_chunks
    )

    judge_prompt = f"""You are an expert AI evaluator assessing factual groundedness.
Verify whether EVERY factual claim in the generated answer is directly supported by the context below.

Context:
{context}

Answer to evaluate:
{answer}

Respond in EXACTLY this format:
SCORE: [1 if fully supported with zero hallucinations, 0 if it contains unsupported claims]
REASON: [one concise sentence explaining the judgment]"""

    client = get_eval_client()

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GENERATION_MODEL,
                contents=judge_prompt,
            )
            result_text = response.text.strip()
            break
        except ServerError:
            time.sleep(4)
        except ClientError as e:
            if "429" in str(e):
                time.sleep(15)
            else:
                raise e
    else:
        return 0.0, "Judge request failed after retries."

    score = 0.0
    reason = "Could not parse judge response"
    for line in result_text.split("\n"):
        if line.startswith("SCORE:"):
            try:
                score = float(line.replace("SCORE:", "").strip())
            except ValueError:
                score = 0.0
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    return score, reason