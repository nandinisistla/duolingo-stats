# Duolingo Stats

See the French mistakes you keep making, and fix them.

## Run it

1. Open this folder in VS Code and the terminal (View → Terminal).
2. Install (Windows):
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Put your Claude API key in `.env` (copy `.env.example`).
4. Start the app:
   ```
   streamlit run app.py
   ```

## Pages

- **Dashboard** – patterns, trends vs last week, practice accuracy.
- **Add mistakes** – screenshot or quick-type. You check the AI's label before saving.
- **Practice** – 5 questions written from your past mistakes.
- **Review** – every mistake, with a real / sample / simulated badge.
- **Testing** – runs the AI test set, and shows each tester's stats.
- **Account menu** – switch learner, load/remove demo data, **Test AI connection**.

## Testing

- `test_set.csv` – 40 French mistakes (5 per type) with the correct type written in advance.
- Click **Run tests** on the Testing page, or run `python run_tests.py`.
  Each case is labeled twice: **accuracy** = right type, **consistency** = same type both times.
  Results are saved to `eval_results.json`.
- Every mistake a learner saves records the AI's suggested type next to the type they kept,
  so real use shows how often the AI's label was right ("AI label kept").

## Data sources

| Source | Meaning |
|---|---|
| `screenshot`, `typed` | Real mistakes entered in the app |
| `sample` | Made-up 3-week history for Ramya |
| `simulated` | Made-up testers: Alekhya, Sanjana, Chandana |

**Remove demo data** deletes sample and simulated rows only. Real mistakes stay.
