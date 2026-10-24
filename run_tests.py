"""Run the AI tests from the terminal:  python run_tests.py"""
from dotenv import load_dotenv

load_dotenv(override=True)

import evals  # noqa: E402


def main():
    print("Running the test set twice (this takes about a minute)...")
    r = evals.run_evals(on_progress=lambda d, t: print(f"\r  {d}/{t} calls", end="", flush=True))
    print("\n")
    print(f"Model:        {r['model']}")
    print(f"Test cases:   {r['cases']}")
    print(f"Accuracy:     {r['correct']}/{r['cases']} ({r['correct'] / r['cases']:.0%})")
    print(f"Consistency:  {r['consistent']}/{r['cases']} ({r['consistent'] / r['cases']:.0%}) same label both runs")
    if r["errors"]:
        print(f"API errors:   {r['errors']}")
    print("\nBy type:")
    for t, (ok, n) in evals.per_type(r).items():
        print(f"  {t:42s} {ok}/{n}")
    misses = [c for c in r["results"] if not c["correct"]]
    if misses:
        print("\nMissed:")
        for c in misses:
            print(f"  #{c['id']}: {c['user_answer']} -> {c['correct_answer']}  expected {c['expected']}, got {c['run1']}")
    print("\nSaved to eval_results.json (the Testing page shows it).")


if __name__ == "__main__":
    main()
