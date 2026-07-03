from src.generate import generate_answer


def main():
    print("=" * 60)
    print("RAG Knowledge Assistant")
    print("Ask questions about Docker, Kubernetes, and FastAPI.")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    while True:
        query = input("\nYour question: ").strip()

        if query.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not query:
            continue

        result = generate_answer(query)

        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources: {', '.join(result['sources'])}")


if __name__ == "__main__":
    main()