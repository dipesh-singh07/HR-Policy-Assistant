"""
HR Policy Assistant - CLI Query Tool
====================================
Interactive command-line interface to query the HR Policy Manual.
Matches and extends the reference repository's ask.py.

Usage:
    python ask.py
    or
    python ask.py "How many days of Privilege Leave (PL) does a permanent employee get per year?"
"""

import sys
from rag_pipeline import HRPolicyAssistant


def print_result(result: dict):
    print("\n" + "=" * 60)
    print(f"QUESTION: {result['question']}")
    print("-" * 60)
    print(f"ANSWER:\n{result['answer']}")
    print("-" * 60)

    if result["is_found"] and result["sources"]:
        print("SOURCE CITATIONS:")
        seen = set()
        for s in result["sources"]:
            key = (s["source"], s["page"], s["section"])
            if key not in seen:
                seen.add(key)
                print(f" • File: {s['source']} | Page: {s['page']} | Section: {s['section']}")
    elif not result["is_found"]:
        print("STATUS: Answer is not established in the HR Policy Manual (Returned 'Not found').")
    print("=" * 60 + "\n")


def main():
    try:
        assistant = HRPolicyAssistant()
    except Exception as e:
        print(f"\n[ERROR] Initialization failed: {e}\n", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        result = assistant.ask(query)
        print_result(result)
    else:
        # Interactive loop
        print("\n=======================================================")
        print("  HR Policy Assistant - Interactive Question & Answer  ")
        print("  Type your question below, or type 'quit' to exit.    ")
        print("=======================================================")
        while True:
            try:
                question = input("\nAsk an HR policy question > ").strip()
                if question.lower() in {"quit", "exit", "q"}:
                    print("Exiting HR Policy Assistant. Goodbye!")
                    break
                if not question:
                    continue
                result = assistant.ask(question)
                print_result(result)
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break


if __name__ == "__main__":
    main()
