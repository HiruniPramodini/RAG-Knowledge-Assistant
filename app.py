from src.graph import build_graph


def main():
    print("=" * 60)
    print("RAG Knowledge Assistant")
    print("Ask questions about Docker, Kubernetes, and FastAPI.")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    graph = build_graph()
    history = []

    while True:
        query = input("\nYour question: ").strip()

        if query.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not query:
            continue

        result = graph.invoke({
            "question": query,
            "needs_retrieval": None,
            "answer": None,
            "sources": None,
            "history": history,
        })

        print(f"\nAnswer:\n{result['answer']}")
        if result["sources"]:
            print(f"\nSources: {', '.join(result['sources'])}")

        # Add this turn to history for future questions
        history.append({"question": query, "answer": result["answer"]})


if __name__ == "__main__":
    main()