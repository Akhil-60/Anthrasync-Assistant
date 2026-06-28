"""
evaluate.py  -  a small evaluation harness.

Runs every question in test_cases.json through the pipeline and checks three things:
  1. Accuracy    - does the answer contain the expected fact (keyword)?
  2. Citation    - is the expected source document among the returned sources?
  3. Not-found   - for out-of-scope questions, did the system correctly refuse?

Prints a per-question table and overall scores. This is intentionally simple and
keyword-based; a heavier setup could use an LLM judge or semantic similarity.

Run with:
    python -m eval.evaluate
"""

import json
from pathlib import Path

from src.pipeline import RAGPipeline
from src.generator import NOT_FOUND

CASES_FILE = Path(__file__).resolve().parent / "test_cases.json"


def answer_has_keywords(answer: str, keywords: list) -> bool:
    text = answer.lower()
    return all(kw.lower() in text for kw in keywords)


def source_matches(sources: list, expected_doc: str) -> bool:
    return any(s["document"] == expected_doc for s in sources)


def main():
    cases = json.loads(CASES_FILE.read_text())
    pipeline = RAGPipeline()

    correct_answer = 0
    correct_source = 0
    source_total = 0
    notfound_correct = 0
    notfound_total = 0

    print(f"{'Q':<55} {'ans':<5} {'src':<5}")
    print("-" * 70)

    for case in cases:
        result = pipeline.ask(case["question"])
        answer = result["answer"]
        q_short = case["question"][:52]

        if case.get("expect_not_found"):
            notfound_total += 1
            ok = NOT_FOUND.lower() in answer.lower()
            notfound_correct += int(ok)
            print(f"{q_short:<55} {'--':<5} {'OK' if ok else 'MISS':<5}")
            continue

        ans_ok = answer_has_keywords(answer, case.get("expect_keywords", []))
        correct_answer += int(ans_ok)

        src_ok = True
        if "expect_source" in case:
            source_total += 1
            src_ok = source_matches(result["sources"], case["expect_source"])
            correct_source += int(src_ok)

        print(f"{q_short:<55} {'OK' if ans_ok else 'MISS':<5} {'OK' if src_ok else 'MISS':<5}")

    in_scope = len(cases) - notfound_total
    print("-" * 70)
    print(f"Answer accuracy : {correct_answer}/{in_scope}")
    print(f"Citation accuracy: {correct_source}/{source_total}")
    print(f"Not-found handling: {notfound_correct}/{notfound_total}")


if __name__ == "__main__":
    main()
