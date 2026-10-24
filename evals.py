"""Tests the AI step: does Claude label each test mistake correctly, and the same way twice?

The test set (test_set.csv) has 40 French mistakes with the correct type written in advance.
Each one is labeled by Claude twice:
- Accuracy    = run 1 label matches the expected type
- Consistency = run 1 and run 2 give the same label
Results are saved to eval_results.json so the Testing page can show them instantly.
"""
import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import ai

HERE = os.path.dirname(os.path.abspath(__file__))
TEST_SET = os.path.join(HERE, "test_set.csv")
RESULTS = os.getenv("DUO_EVAL_RESULTS") or os.path.join(HERE, "eval_results.json")
RUNS = 2


def load_test_set():
    with open(TEST_SET, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _label(row):
    try:
        return ai.label_typed(row["question"], row["user_answer"], row["correct_answer"])["mistake_type"]
    except Exception as e:  # one failed call shouldn't stop the whole test
        return "ERROR: " + ai.friendly_error(e)


def run_evals(on_progress=None, workers=5):
    """Label every test case RUNS times. on_progress(done, total) is called as calls finish."""
    rows = load_test_set()
    jobs = [(i, r) for r in rows for i in range(RUNS)]
    labels = {}
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_label, r): (i, r["id"]) for i, r in jobs}
        for fut in as_completed(futures):
            labels[futures[fut]] = fut.result()
            done += 1
            if on_progress:
                on_progress(done, len(jobs))

    cases = []
    for r in rows:
        got = [labels[(i, r["id"])] for i in range(RUNS)]
        cases.append({
            "id": r["id"], "question": r["question"], "user_answer": r["user_answer"],
            "correct_answer": r["correct_answer"], "expected": r["expected_type"],
            "run1": got[0], "run2": got[1],
            "correct": got[0] == r["expected_type"],
            "consistent": got[0] == got[1],
        })
    n = len(cases)
    result = {
        "run_at": datetime.now().isoformat(timespec="minutes"),
        "model": ai.MODEL,
        "cases": n,
        "correct": sum(c["correct"] for c in cases),
        "consistent": sum(c["consistent"] for c in cases),
        "errors": sum(c["run1"].startswith("ERROR") or c["run2"].startswith("ERROR") for c in cases),
        "results": cases,
    }
    with open(RESULTS, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def load_results():
    if not os.path.exists(RESULTS):
        return None
    with open(RESULTS, encoding="utf-8") as f:
        return json.load(f)


def per_type(result):
    """Accuracy for each expected mistake type."""
    out = {}
    for c in result["results"]:
        t = out.setdefault(c["expected"], [0, 0])
        t[0] += c["correct"]
        t[1] += 1
    return out
