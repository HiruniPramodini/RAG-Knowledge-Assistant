# RAG Knowledge Assistant

A retrieval-augmented generation (RAG) system that answers engineering questions grounded in real documentation — with source citations, so answers are verifiable rather than trusted blindly.

Built as a knowledge assistant over Docker, Kubernetes, and FastAPI reference documentation, but the pipeline generalizes to any document set (internal wikis, policy docs, API references).

## Why RAG instead of calling an LLM directly?

A general-purpose LLM only knows what it learned during training. It can't answer questions about documents it's never seen, and when it doesn't know something, it tends to guess rather than admit uncertainty — a problem known as hallucination.

This system solves that by retrieving the most relevant passages from a document set *before* generating an answer, and explicitly instructing the model to answer only from that retrieved context. The result is an answer grounded in real, verifiable text, with the source document cited alongside it.

## How it works

1. **Ingestion** (`src/ingest.py`) — Documents are loaded, split into overlapping chunks (500 characters, 50-character overlap), converted into vector embeddings via Gemini's embedding model, and stored in a local ChromaDB vector database.
2. **Retrieval** (`src/retrieve.py`) — An incoming question is embedded the same way, and ChromaDB returns the most semantically similar chunks via cosine similarity — regardless of whether the question shares exact words with the source text.
3. **Generation** (`src/generate.py`) — The retrieved chunks are combined with the question into a single prompt, explicitly instructing Gemini to answer only from the provided context. The response is returned along with the source document(s) it was grounded in.

## Tech stack

- **LangChain** — document loading and chunking
- **ChromaDB** — local vector database
- **Google Gemini API** — embeddings (`gemini-embedding-001`) and generation (`gemini-2.5-flash`)
- **Python** — `python-dotenv` for secrets management, `pytest` for testing

## Project structure

```
rag-knowledge-assistant/
├── data/raw_docs/       # source documents
├── src/
│   ├── config.py         # centralized settings
│   ├── ingest.py          # load, chunk, embed, store
│   ├── retrieve.py        # semantic search
│   └── generate.py        # grounded answer generation
├── tests/
│   └── test_retrieve.py   # automated retrieval tests
├── app.py                 # interactive CLI entry point
└── vectorstore/           # generated ChromaDB files (not committed)
```

## Setup

1. Clone the repo and create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Add Gemini API key to a `.env` file:
   ```
   GEMINI_API_KEY=API_key_here
   ```
   Get a free key at [aistudio.google.com](https://aistudio.google.com).

3. Run ingestion once to build the vector database:
   ```
   python -m src.ingest
   ```

4. Ask questions interactively:
   ```
   python app.py
   ```

## Running tests

```
pytest tests/ -v
```

Tests verify that retrieval returns relevant, non-empty results from the correct source documents across all three document domains.

## Design decisions worth noting

- **Chunk size (500 chars) with overlap (50 chars):** balances retrieval precision against losing context at chunk boundaries.
- **Top-k = 3:** enough context for the model to work with, without diluting the prompt with irrelevant chunks or inflating token cost.
- **Explicit "answer only from context" instruction:** a deliberate prompt-engineering choice to reduce hallucination, rather than leaving grounding implicit.
- **Source citation on every answer:** every response includes which document(s) it was generated from, so correctness is verifiable rather than assumed.

## Possible extensions

- Retrieval evaluation layer (faithfulness, context precision/recall)
- Agentic workflow (LangGraph) for multi-step questions requiring more than one retrieval pass
- Docker + CI/CD deployment, following the same MLOps practices as a companion project
- Azure Hosting
## Demo

**Asking a question — cross-document retrieval:**

![CLI demo](screenshots/demo-qa.png)

**Automated tests passing:**

![Tests passing](screenshots/tests-passing.png)
