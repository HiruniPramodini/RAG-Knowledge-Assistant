# Ground-truth test questions for evaluating the RAG pipeline.
# Each case includes the expected source document(s), based on the
# actual content of our reference docs (we wrote them, so we know
# exactly where each answer should come from).

TEST_CASES = [
    # --- Docker questions ---
    {
        "question": "How do I stop my container from losing data on restart?",
        "expected_sources": ["docker_basics.md"],
    },
    {
        "question": "What is the difference between a Docker image and a container?",
        "expected_sources": ["docker_basics.md"],
    },
    {
        "question": "What command do I use to build a Docker image from a Dockerfile?",
        "expected_sources": ["docker_basics.md"],
    },

    # --- Kubernetes questions ---
    {
        "question": "What is a Kubernetes pod?",
        "expected_sources": ["kubernetes_basics.md"],
    },
    {
        "question": "How does Kubernetes automatically recover from a crashed pod?",
        "expected_sources": ["kubernetes_basics.md"],
    },
    {
        "question": "What is Horizontal Pod Autoscaling?",
        "expected_sources": ["kubernetes_basics.md"],
    },

    # --- FastAPI questions ---
    {
        "question": "How does FastAPI validate incoming request data?",
        "expected_sources": ["fastapi_basics.md"],
    },
    {
        "question": "How do I load a trained model only once instead of on every request?",
        "expected_sources": ["fastapi_basics.md"],
    },

    # --- Cross-document question (tests multi-source retrieval) ---
    {
        "question": "What's the difference between how Docker and Kubernetes handle scaling?",
        "expected_sources": ["docker_basics.md", "kubernetes_basics.md"],
    },

    # --- Out-of-scope question (tests honest "I don't know" behavior) ---
    {
        "question": "What is the capital of France?",
        "expected_sources": [],  # nothing in our docs should match this
    },
]