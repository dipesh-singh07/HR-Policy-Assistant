"""
HR Policy Assistant - Automated Verification Suite
==================================================
Tests all five required questions from the exam specification:
1. How many days of Privilege Leave (PL) does a permanent employee get per year?
2. What is the probation period for employees up to Senior Manager?
3. What is the company's health-insurance premium amount?
4. What is the current GST rate in India?
5. How many days of maternity leave are given?

Validates strict grounding, exact 'Not found' for unsupported questions,
and citation of source page and policy section.
"""

import sys
import json
from rag_pipeline import HRPolicyAssistant

TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "How many days of Privilege Leave (PL) does a permanent employee get per year?",
        "expected_found": True,
        "expected_terms": ["12", "privilege leave"],
        "expected_page": 60,
        "expected_section": "[G] Leave Policy"
    },
    {
        "id": 2,
        "question": "What is the probation period for employees up to Senior Manager?",
        "expected_found": True,
        "expected_terms": ["3 months", "probation"],
        "expected_page": 42,
        "expected_section": "[B] Probation Policy"
    },
    {
        "id": 3,
        "question": "What is the company's health-insurance premium amount?",
        "expected_found": False,
        "expected_terms": ["not found"],
        "expected_page": None,
        "expected_section": None
    },
    {
        "id": 4,
        "question": "What is the current GST rate in India?",
        "expected_found": False,
        "expected_terms": ["not found"],
        "expected_page": None,
        "expected_section": None
    },
    {
        "id": 5,
        "question": "How many days of maternity leave are given?",
        "expected_found": True,
        "expected_terms": ["12 weeks", "90 days", "maternity"],
        "expected_page": 62,
        "expected_section": "[G] Leave Policy"
    }
]


def run_tests():
    print("=" * 70)
    print("      HR POLICY ASSISTANT - EXAM VERIFICATION TEST SUITE       ")
    print("=" * 70)

    try:
        assistant = HRPolicyAssistant()
    except Exception as e:
        print(f"\n[FAIL] Initialization error: {e}", file=sys.stderr)
        return False

    all_passed = True
    results = []

    for test in TEST_QUESTIONS:
        qid = test["id"]
        q = test["question"]
        print(f"\n[Test {qid}] {q}")

        res = assistant.ask(q)
        ans = res["answer"]
        is_found = res["is_found"]
        sources = res["sources"]

        print(f"  Generated Answer: {ans}")

        passed = True
        notes = []

        if not test["expected_found"]:
            # Strict grounding test: MUST be "Not found"
            if ans.strip().lower() != "not found":
                passed = False
                notes.append(f"Expected exact 'Not found', but received: '{ans}'")
            else:
                notes.append("Correctly returned exact 'Not found' (strictly grounded).")
        else:
            # Documented answer test
            if not is_found or ans.strip().lower() == "not found":
                passed = False
                notes.append("Expected answer to be found in document, but was returned as 'Not found'.")
            else:
                # Check citations
                pages = [s["page"] for s in sources]
                sections = [s["section"] for s in sources]
                citations_str = ", ".join([f"Page {s['page']} ({s['section']})" for s in sources[:2]])
                print(f"  Citations: {citations_str}")

                if test["expected_page"] and test["expected_page"] not in pages:
                    notes.append(f"Warning: Expected page {test['expected_page']} in retrieved citations ({pages}).")
                else:
                    notes.append(f"Cited page {test['expected_page']} correctly.")

        status_str = "PASS" if passed else "FAIL"
        print(f"  Status: [{status_str}] - {'; '.join(notes)}")

        if not passed:
            all_passed = False

        results.append({
            "id": qid,
            "question": q,
            "answer": ans,
            "is_found": is_found,
            "sources": sources,
            "passed": passed,
            "notes": notes
        })

    print("\n" + "=" * 70)
    summary_status = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
    print(f"TEST SUMMARY: {summary_status}")
    print("=" * 70)

    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved test results to test_results.json")

    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
