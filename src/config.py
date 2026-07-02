import os
from dotenv import load_dotenv

# Load environment variables from .env file into the program
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Paths
RAW_DOCS_DIR = "data/raw_docs"
VECTORSTORE_DIR = "vectorstore"

# Chunking settings
CHUNK_SIZE = 500        # characters per chunk
CHUNK_OVERLAP = 50      # characters shared between consecutive chunks

# Embedding model
EMBEDDING_MODEL = "models/gemini-embedding-001"