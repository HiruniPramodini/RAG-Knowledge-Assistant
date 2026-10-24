"""Command Line Interface (CLI) for the Enterprise Company Knowledge Assistant.

Provides an interactive terminal session with multi-turn memory and route inspection.
"""

import sys
from src.graph import build_graph
from src.config import validate_config


def main():
    validation = validate_config(require_api_key=True)
    if not validation["valid"]:
        print("\n[Configuration Error]")
        for err in validation["errors"]:
            print(f"  - {err}")
        print("\nPlease configure your .env file or environment variables before running.")
        sys.exit(1)

    print("=" * 65)
    print("  Aurelia Tech — Enterprise Knowledge Assistant (CLI)")
    print("  Ask questions about HR policies, IT onboarding, engineering,")
    print("  tech stack, current projects, code of conduct, or do math.")
    print("  Type 'exit' or 'quit' to end your session.")
    print("=" * 65)

    graph = build_graph()
    history = []

    while True:
        try:
            query = input("\nEmployee Question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended. Goodbye!")
            break

        if query.lower() in ("exit", "quit", "q"):
            print("\nThank you for using the Aurelia Knowledge Assistant. Goodbye!")
            break

        if not query:
            continue

        try:
            result = graph.invoke({
                "question": query,
                "route": None,
                "answer": None,
                "sources": None,
                "source_details": None,
                "history": history,
                "is_grounded": None,
            })

            route = result.get("route", "unknown")
            print(f"\n[Route: {route.upper()}]")
            print(f"Assistant:\n{result.get('answer', '')}")

            sources = result.get("sources", [])
            if sources:
                print(f"\nVerified Sources: {', '.join(sources)}")

            # Append turn to history
            history.append({
                "question": query,
                "answer": result.get("answer", ""),
                "route": route,
            })

        except Exception as e:
            print(f"\n[Error processing question]: {e}")


if __name__ == "__main__":
    main()