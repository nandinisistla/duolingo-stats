"""The model step: Claude reads mistakes, labels their type, and writes practice."""
import base64
import io
import json
import os
import re

from anthropic import Anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

# A fixed list keeps labels consistent, so mistakes can be counted over time.
MISTAKE_TYPES = [
    "Gender (le/la, un/une)",
    "Verb conjugation",
    "Adjective agreement",
    "Articles & partitives (du, de la, des)",
    "Prepositions",
    "Word order",
    "Spelling & accents",
    "Vocabulary (wrong word)",
    "Other",
]

TYPE_LIST = "\n".join(f"- {t}" for t in MISTAKE_TYPES)

# Short definitions help the model pick the same type every time.
TYPE_GUIDE = """How to choose:
- Gender: wrong le/la/un/une/l' because the noun's gender is wrong.
- Verb conjugation: wrong verb ending or verb form for the subject (je/tu/il/nous/vous/ils).
- Adjective agreement: adjective or past participle doesn't match the noun's gender or number.
- Articles & partitives: missing or wrong du/de la/des/de/le when talking about "some" or after a negative.
- Prepositions: wrong à/en/au/dans/sur/de, including before cities and countries.
- Word order: right words, wrong order (adjective position, ne...pas, pronoun position).
- Spelling & accents: right word, but missing or wrong accent or letter (e/é/è, c/ç).
- Vocabulary: a completely different word with a different meaning."""


def has_key():
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _client():
    if not has_key():
        raise RuntimeError("No ANTHROPIC_API_KEY found. Add it to your .env file.")
    # Retries cover short API hiccups during a live demo.
    return Anthropic(max_retries=3, timeout=60)


def _ask(content, max_tokens=1500):
    # Current Claude models reject sampling settings like temperature, so none are sent.
    msg = _client().messages.create(model=MODEL, max_tokens=max_tokens,
                                    messages=[{"role": "user", "content": content}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def friendly_error(e):
    """Turn API errors into one clear sentence for the screen."""
    s = str(e)
    if "401" in s or "authentication" in s.lower():
        return "Your Claude API key isn't working. Check the key in your .env file, then restart the app."
    if "404" in s or "not_found" in s:
        return f"The model '{MODEL}' wasn't found. Set CLAUDE_MODEL in your .env to a model your account has."
    if "429" in s or "rate" in s.lower():
        return "Too many requests at once. Wait a few seconds and try again."
    if "credit" in s.lower() or "billing" in s.lower():
        return "Your Anthropic account is out of credit. Add credit in the console."
    if "overloaded" in s.lower() or "529" in s:
        return "Claude is busy right now. Try again in a few seconds."
    return s


def test_connection():
    """Tiny call to check the key and model before a demo. Returns (ok, message)."""
    try:
        _ask("Reply with OK.", max_tokens=5)
        return True, f"Connected to {MODEL}"
    except Exception as e:
        return False, friendly_error(e)


def _parse_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = min([i for i in (text.find("["), text.find("{")) if i != -1], default=-1)
    if start == -1:
        return None
    end = max(text.rfind("]"), text.rfind("}"))
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _clean_type(t):
    return t if t in MISTAKE_TYPES else "Other"


def _prepare_image(image_bytes, media_type):
    """Shrink big phone screenshots so they upload fast and stay under the API's size limit."""
    try:
        from PIL import Image
    except ImportError:
        return image_bytes, media_type
    try:
        im = Image.open(io.BytesIO(image_bytes))
        if max(im.size) <= 1568 and len(image_bytes) < 3_500_000:
            return image_bytes, media_type
        im.thumbnail((1568, 1568))
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        out = io.BytesIO()
        im.save(out, format="JPEG", quality=90)
        return out.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, media_type


def read_screenshot(image_bytes, media_type="image/png"):
    """Find the wrong answers in one Duolingo screenshot and label each one."""
    prompt = f"""This is a screenshot from a Duolingo French course.
Find every exercise the learner got WRONG. Only use what is visible in the image.
Do not invent mistakes. If there is no visible mistake, return [].
If the learner's own answer is not visible, set "user_answer" to "not visible".

For each mistake, return:
- "question": the exercise prompt
- "user_answer": what the learner wrote or picked
- "correct_answer": the correct answer shown
- "mistake_type": exactly one of these:
{TYPE_LIST}
- "explanation": one short, simple sentence a beginner understands

{TYPE_GUIDE}

Return only a JSON array, nothing else."""
    image_bytes, media_type = _prepare_image(image_bytes, media_type)
    b64 = base64.standard_b64encode(image_bytes).decode()
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
        {"type": "text", "text": prompt},
    ]
    data = _parse_json(_ask(content)) or []
    if isinstance(data, dict):
        data = [data]
    out = []
    for m in data:
        if isinstance(m, dict) and m.get("correct_answer"):
            m["mistake_type"] = _clean_type(m.get("mistake_type", ""))
            out.append(m)
    return out


def label_typed(question, user_answer, correct_answer):
    """The lighter input: the learner just types what they wrote and the right answer."""
    prompt = f"""A French learner made this mistake on Duolingo.
Exercise: {question or "(not given)"}
They wrote: {user_answer}
Correct answer: {correct_answer}

Return a JSON object with:
- "mistake_type": exactly one of these:
{TYPE_LIST}
- "explanation": one short, simple sentence a beginner understands

{TYPE_GUIDE}

Return only JSON."""
    data = _parse_json(_ask(prompt, 400)) or {}
    if isinstance(data, list):
        data = data[0] if data and isinstance(data[0], dict) else {}
    return {
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "mistake_type": _clean_type(data.get("mistake_type", "")),
        "explanation": data.get("explanation", ""),
    }


def make_practice(mistake_type, examples, n=5):
    """Write practice questions aimed at one pattern, based on the learner's real mistakes."""
    ex = "\n".join(
        f'- Wrote "{e["user_answer"]}", correct was "{e["correct_answer"]}"' for e in examples[:8]
    )
    prompt = f"""A French learner keeps making "{mistake_type}" mistakes. Here are their real past mistakes:
{ex}

Write {n} short multiple-choice practice questions that target this exact weakness.
Use similar words and sentences to their real mistakes, but do not just repeat them.

Each question is a JSON object with:
- "question": short instruction plus the French sentence with a blank, e.g. "Fill in: ___ pomme est rouge."
- "options": 4 short answer options
- "answer": the correct option, copied exactly from "options"
- "why": one short, simple sentence explaining the answer

Return only a JSON array."""
    data = _parse_json(_ask(prompt, 2000)) or []
    good = []
    for q in data if isinstance(data, list) else []:
        if isinstance(q, dict) and q.get("answer") in q.get("options", []):
            good.append(q)
    return good[:n]
