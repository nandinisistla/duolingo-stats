"""Duolingo Stats - a dashboard of the French mistakes you keep making.
Run with:  streamlit run app.py
"""
import html
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)  # .env always wins over old keys set elsewhere

import ai  # noqa: E402  (needs the .env loaded first)
import db  # noqa: E402
import evals  # noqa: E402
from sample_data import TESTERS, load_data  # noqa: E402

GREEN, DARK_GREEN, LIME, LIGHT_GREEN = "#58CC02", "#58A700", "#89E219", "#D7FFB8"
RED, LIGHT_RED, TEXT, MUTED, BORDER, BG = "#FF4B4B", "#FFDFE0", "#3C3C3C", "#777777", "#E5E5E5", "#F7F7F7"
GREENS = [GREEN, DARK_GREEN, LIME, "#B8F28B", LIGHT_GREEN]
CHART_FONT = "Nunito, Helvetica, Arial, sans-serif"
PAGES = ["Dashboard", "Add mistakes", "Practice", "Review", "Testing"]

st.set_page_config(page_title="Duolingo Stats", page_icon="🟢", layout="wide", initial_sidebar_state="collapsed")
db.init_db()

# ---------- Styles ----------
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&display=swap');
html, body, .stApp, .stMarkdown, button, input, textarea, label, p, [data-testid="stWidgetLabel"] {{
    font-family: 'Nunito', sans-serif !important;
}}
.stApp {{ background: {BG}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], #MainMenu, footer {{ display: none; }}
.block-container, .stMainBlockContainer {{ padding-top: 0 !important; max-width: 1180px; }}
button p, button div {{ font-family: 'Nunito', sans-serif !important; font-weight: 800 !important; }}
h1, h2, h3, h4 {{ font-family: 'Nunito', sans-serif !important; color: {TEXT}; }}

/* Top bar */
.st-key-navbar {{ background: white; padding: 10px 0; margin-bottom: 26px;
    box-shadow: 0 0 0 100vmax white, 0 2px 0 100vmax {BORDER}; clip-path: inset(0 -100vmax -2px); }}
.logo {{ font-size: 1.55rem; font-weight: 900; color: {GREEN}; letter-spacing: -.5px; white-space: nowrap; padding-top: 2px; }}
.logo span {{ color: {TEXT}; }}
.st-key-navbar [data-testid="stButtonGroup"] button {{ border: none !important; background: transparent !important;
    font-weight: 800; color: {MUTED}; box-shadow: none !important; }}
.st-key-navbar [data-testid="stButtonGroup"] button p {{ font-size: 1rem; font-weight: 800; }}
.st-key-navbar [data-testid="stBaseButton-segmented_controlActive"] {{ color: {GREEN} !important;
    background: {LIGHT_GREEN} !important; border-radius: 12px !important; }}
.st-key-navbar [data-testid="stPopover"] {{ display: flex; justify-content: flex-end; }}
[data-testid="stPopover"] button {{ border: 2px solid {BORDER}; border-radius: 12px; font-weight: 800; background: white; }}

/* Buttons: green primary, white secondary, both chunky */
.stButton > button, .stFormSubmitButton > button {{ border-radius: 14px; font-weight: 800; text-transform: uppercase;
    letter-spacing: .4px; transition: transform .05s; }}
[data-testid="stBaseButton-primary"], .stFormSubmitButton > button {{ background: {GREEN} !important; color: white !important;
    border: none !important; box-shadow: 0 4px 0 {DARK_GREEN}; padding: .6rem 1.3rem; }}
[data-testid="stBaseButton-primary"]:hover {{ background: #61E002 !important; }}
[data-testid="stBaseButton-secondary"] {{ background: white !important; color: {GREEN} !important;
    border: 2px solid {BORDER} !important; box-shadow: 0 3px 0 {BORDER}; text-transform: none !important;
    padding: .3rem .7rem; }}
.stButton > button:active, .stFormSubmitButton > button:active {{ transform: translateY(3px); box-shadow: none; }}

/* Cards */
[class*="st-key-card"] {{ background: white; border: 2px solid {BORDER}; border-bottom-width: 4px; border-radius: 18px;
    padding: 20px 22px; }}
.card-title {{ font-size: 1.25rem; font-weight: 900; color: {TEXT}; margin-bottom: 2px; }}
.card-sub {{ color: {MUTED}; font-weight: 700; font-size: .9rem; margin-bottom: 8px; }}
.page-title {{ font-size: 2.3rem; font-weight: 900; color: {GREEN}; margin: 0 0 14px; }}

.row {{ display: flex; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid #F0F0F0;
    font-weight: 700; color: {TEXT}; }}
.row b {{ font-weight: 900; }}
.pname {{ font-weight: 800; color: {TEXT}; line-height: 1.25; }}
.pmeta {{ font-size: .82rem; font-weight: 700; color: {MUTED}; }}
.chip {{ display: inline-block; font-size: .75rem; font-weight: 800; border-radius: 99px; padding: 1px 9px; margin-left: 4px; }}
.up {{ background: {LIGHT_RED}; color: {RED}; }}
.down {{ background: {LIGHT_GREEN}; color: {DARK_GREEN}; }}
.flat {{ background: #F1F1F1; color: {MUTED}; }}
.qp {{ text-align: center; color: {MUTED}; font-weight: 700; font-size: .85rem; margin-top: 6px; }}
.ex {{ font-size: .95rem; color: {TEXT}; margin: 2px 0; }}
.wrong {{ color: {RED}; font-weight: 800; text-decoration: line-through; }}
.right {{ color: {DARK_GREEN}; font-weight: 800; }}
.note {{ color: {MUTED}; font-size: .85rem; font-weight: 700; }}
.mistake {{ border: 2px solid {BORDER}; border-radius: 14px; padding: 10px 14px; margin-bottom: 10px; background: white; }}
.result-good {{ background: {LIGHT_GREEN}; border-color: {GREEN}; }}
.result-bad {{ background: {LIGHT_RED}; border-color: {RED}; }}
.badge {{ display: inline-block; font-size: .72rem; font-weight: 800; border-radius: 99px; padding: 2px 9px;
    text-transform: uppercase; letter-spacing: .3px; }}
.b-real {{ background: {LIGHT_GREEN}; color: {DARK_GREEN}; }}
.b-sim {{ background: #EEF2FF; color: #4F46E5; }}
.b-sample {{ background: #F1F1F1; color: {MUTED}; }}
.tile {{ border: 2px solid {BORDER}; border-radius: 16px; padding: 14px 10px; text-align: center; background: white; }}
.tile .num {{ font-size: 2rem; font-weight: 900; color: {GREEN}; line-height: 1.1; }}
.tile .lbl {{ font-size: .8rem; font-weight: 800; color: {MUTED}; text-transform: uppercase; }}
.tile .sub {{ font-size: .8rem; font-weight: 700; color: #AFAFAF; }}
.tbl {{ width: 100%; border-collapse: collapse; font-weight: 700; color: {TEXT}; font-size: .92rem; }}
.tbl th {{ text-align: left; color: {MUTED}; font-size: .78rem; text-transform: uppercase; padding: 6px 8px;
    border-bottom: 2px solid {BORDER}; }}
.tbl td {{ padding: 8px; border-bottom: 1px solid #F0F0F0; }}
</style>
""",
    unsafe_allow_html=True,
)


def esc(s):
    return html.escape(str(s or ""))


def clear_keys(*prefixes):
    """Forget old widget answers so a new review or quiz starts fresh."""
    for k in list(st.session_state):
        if k.startswith(prefixes):
            del st.session_state[k]


def go(page, mtype=None):
    st.session_state["page"] = page
    if mtype:
        st.session_state["practice_type"] = mtype


def short(t):
    return t.split(" (")[0]


st.session_state.setdefault("page", "Dashboard")
st.session_state.setdefault("user", "Ramya")
user = (st.session_state["user"] or "Ramya").strip()

# ---------- Top bar ----------
with st.container(key="navbar"):
    logo_col, nav_col, acct_col = st.columns([2.2, 5, 1.6], vertical_alignment="center")
    logo_col.markdown('<div class="logo">duolingo<span>stats</span></div>', unsafe_allow_html=True)
    with nav_col:
        st.segmented_control("Menu", PAGES, key="page", label_visibility="collapsed")
    with acct_col:
        with st.popover(f"👤 {user}"):
            known = sorted(set(db.list_users()) | {"Ramya", *TESTERS} | {user})
            st.selectbox("Learner", known, key="user", accept_new_options=True,
                         help="Pick a learner, or type a new name to add one.")
            st.caption("Data")
            if st.button("Load data", width="stretch"):
                load_data("Ramya")
                st.rerun()
            if st.button("Remove Ramya's demo data", width="stretch"):
                db.clear_demo_data()
                st.rerun()
            if st.button("Clear this learner", width="stretch"):
                db.clear_user(user)
                clear_keys("pending", "quiz")
                st.rerun()
            st.caption("AI")
            if st.button("Test AI connection", width="stretch"):
                ok, msg = ai.test_connection()
                (st.success if ok else st.error)(msg)
            elif not ai.has_key():
                st.caption("⚠️ No API key (add it to .env)")

page = st.session_state["page"] or "Dashboard"

# ---------- Data ----------
df = pd.DataFrame(db.get_mistakes(user))
if not df.empty:
    df["created_at"] = pd.to_datetime(df["created_at"])
prac = pd.DataFrame(db.get_practice(user))
now = datetime.now()
week_ago, two_weeks_ago = now - timedelta(days=7), now - timedelta(days=14)


def pattern_summary():
    if df.empty:
        return []
    rows = []
    for mtype, g in df.groupby("mistake_type"):
        rows.append({
            "type": mtype, "total": len(g),
            "this": int((g["created_at"] >= week_ago).sum()),
            "last": int(((g["created_at"] >= two_weeks_ago) & (g["created_at"] < week_ago)).sum()),
            "examples": g.sort_values("created_at", ascending=False).to_dict("records"),
        })
    return sorted(rows, key=lambda r: r["total"], reverse=True)


patterns = pattern_summary()
types = [p["type"] for p in patterns]


def trend_chip(p):
    d = p["this"] - p["last"]
    if d < 0:
        return f'<span class="chip down">↓ {abs(d)}</span>'
    if d > 0:
        return f'<span class="chip up">↑ {d}</span>'
    return '<span class="chip flat">–</span>'


def donut(data, colors, center, sub):
    base = alt.Chart(data).encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color("label:N", scale=alt.Scale(domain=list(data["label"]), range=colors),
                        legend=alt.Legend(orient="bottom", title=None, labelFont=CHART_FONT, labelFontSize=12,
                                          labelLimit=200, columns=2)),
        tooltip=["label", "value"],
    )
    arc = base.mark_arc(innerRadius=62, outerRadius=98, cornerRadius=4, padAngle=0.015)
    mid = pd.DataFrame({"t": [center], "s": [sub]})
    big = alt.Chart(mid).mark_text(fontSize=28, fontWeight=900, color=TEXT, font=CHART_FONT, dy=-6).encode(text="t:N")
    small = alt.Chart(mid).mark_text(fontSize=12, fontWeight=700, color=MUTED, font=CHART_FONT, dy=16).encode(text="s:N")
    return (arc + big + small).properties(height=280).configure_view(stroke=None)


def empty_state():
    with st.container(key="card_empty"):
        st.markdown('<div class="card-title">No mistakes yet</div>'
                    '<div class="card-sub">Add your first mistakes, or load data from the account menu.</div>',
                    unsafe_allow_html=True)
        st.button("Add mistakes", type="primary", on_click=go, args=("Add mistakes",))


# ---------- Dashboard ----------
if page == "Dashboard":
    st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)
    if not patterns:
        empty_state()
    else:
        left, right = st.columns([1.1, 2], gap="medium")

        with left, st.container(key="card_suggested"):
            st.markdown('<div class="card-title">Suggested practice</div>'
                        '<div class="card-sub">Your mistake patterns, most common first</div>', unsafe_allow_html=True)
            for i, p in enumerate(patterns):
                a, b = st.columns([3, 1], vertical_alignment="center")
                a.markdown(f'<div class="pname">{esc(p["type"])}</div>'
                           f'<div class="pmeta">{p["total"]} mistakes · this week {p["this"]} {trend_chip(p)}</div>',
                           unsafe_allow_html=True)
                b.button("Go →", key=f"sug_{i}", on_click=go, args=("Practice", p["type"]), width="stretch")

        with right:
            with st.container(key="card_quick"):
                st.markdown('<div class="card-title">Quick practice</div>'
                            '<div class="card-sub">Built from your real mistakes</div>', unsafe_allow_html=True)
                qcols = st.columns(2)
                for col, p in zip(qcols, patterns[:2]):
                    with col:
                        st.button(f"Practice {short(p['type'])}", key=f"qp_{p['type']}", type="primary",
                                  on_click=go, args=("Practice", p["type"]), width="stretch")
                        st.markdown(f'<div class="qp">{p["total"]} mistakes saved</div>', unsafe_allow_html=True)

            st.write("")
            with st.container(key="card_results"):
                st.markdown('<div class="card-title">Results summary</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div class="card-sub" style="text-align:center">Mistakes by type</div>', unsafe_allow_html=True)
                    top = patterns[:4]
                    rest = sum(p["total"] for p in patterns[4:])
                    d = pd.DataFrame({"label": [short(p["type"]) for p in top] + (["Other"] if rest else []),
                                      "value": [p["total"] for p in top] + ([rest] if rest else [])})
                    st.altair_chart(donut(d, GREENS[: len(d)], str(len(df)), "mistakes"), use_container_width=True)
                with c2:
                    st.markdown('<div class="card-sub" style="text-align:center">Practice accuracy</div>', unsafe_allow_html=True)
                    if prac.empty:
                        st.markdown('<p class="note" style="text-align:center;margin-top:90px">No practice yet</p>',
                                    unsafe_allow_html=True)
                    else:
                        right_n, total_n = int(prac["score"].sum()), int(prac["total"].sum())
                        d = pd.DataFrame({"label": ["Correct", "Incorrect"], "value": [right_n, total_n - right_n]})
                        st.altair_chart(donut(d, [GREEN, LIGHT_GREEN], f"{right_n / total_n:.0%}", "correct"),
                                        use_container_width=True)

                this_wk = int((df["created_at"] >= week_ago).sum())
                last_wk = int(((df["created_at"] >= two_weeks_ago) & (df["created_at"] < week_ago)).sum())
                avg = f'{prac["score"].sum() / prac["total"].sum():.0%}' if not prac.empty else "–"
                st.markdown(
                    f"""<div class="row"><span>Mistakes saved</span><b>{len(df)}</b></div>
                    <div class="row"><span>Mistakes this week</span><b>{this_wk}</b></div>
                    <div class="row"><span>Mistakes last week</span><b>{last_wk}</b></div>
                    <div class="row"><span>Top pattern</span><b>{esc(short(patterns[0]["type"]))}</b></div>
                    <div class="row"><span>Practice sets done</span><b>{len(prac)}</b></div>
                    <div class="row" style="border:none"><span>Average practice score</span><b>{avg}</b></div>""",
                    unsafe_allow_html=True,
                )

        st.write("")
        with st.container(key="card_time"):
            st.markdown('<div class="card-title">Your top 3 patterns over time</div>'
                        '<div class="card-sub">Mistakes per week. Going down means practice is working.</div>',
                        unsafe_allow_html=True)
            order = ["2 weeks ago", "Last week", "This week"]
            recent = df[df["mistake_type"].isin(types[:3])].copy()
            recent["wk"] = ((now - recent["created_at"]).dt.days // 7).clip(upper=2)
            counts = recent.groupby(["wk", "mistake_type"]).size().unstack(fill_value=0).reindex([2, 1, 0], fill_value=0)
            counts.index = order
            long = counts.reset_index(names="week").melt("week", var_name="pattern", value_name="mistakes")
            long["pattern"] = long["pattern"].map(short)
            line = alt.Chart(long).mark_line(point=alt.OverlayMarkDef(size=80, filled=True), strokeWidth=4).encode(
                x=alt.X("week:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelFont=CHART_FONT, labelFontSize=13)),
                y=alt.Y("mistakes:Q", title=None, axis=alt.Axis(tickMinStep=1, labelFont=CHART_FONT, gridColor="#F0F0F0")),
                color=alt.Color("pattern:N", scale=alt.Scale(range=[GREEN, "#1CB0F6", "#FF9600"]),
                                legend=alt.Legend(orient="top", title=None, labelFont=CHART_FONT, labelFontSize=13)),
                tooltip=["pattern", "week", "mistakes"],
            ).properties(height=260).configure_view(stroke=None)
            st.altair_chart(line, use_container_width=True)

# ---------- Add mistakes ----------
elif page == "Add mistakes":
    st.markdown('<div class="page-title">Add mistakes</div>', unsafe_allow_html=True)
    with st.container(key="card_add"):
        method = st.radio("How?", ["📸 Screenshot", "⌨️ Quick type (faster)"], horizontal=True)
        if method == "📸 Screenshot":
            files = st.file_uploader("Upload screenshots of wrong answers", type=["png", "jpg", "jpeg", "webp"],
                                     accept_multiple_files=True)
            if files and st.button("Find my mistakes", type="primary"):
                found, failed = [], False
                with st.spinner("Reading your screenshots..."):
                    for f in files:
                        mt = f.type if f.type in ("image/png", "image/jpeg", "image/webp") else "image/png"
                        try:
                            found += ai.read_screenshot(f.getvalue(), mt)
                        except Exception as e:  # show the problem instead of crashing the demo
                            failed = True
                            msg = ai.friendly_error(e)
                            st.error(f"{f.name}: {msg}")
                            if "key" in msg or "credit" in msg or "model" in msg:
                                break
                clear_keys("type_", "keep_")
                st.session_state["pending"] = [dict(m, _src="screenshot") for m in found]
                if not found and not failed:
                    st.warning("No mistakes found in those screenshots.")
        else:
            with st.form("typed", clear_on_submit=True, border=False):
                q = st.text_input("Exercise (optional)", placeholder="Translate: the apple")
                wrong = st.text_input("What you wrote", placeholder="le pomme")
                right = st.text_input("Correct answer", placeholder="la pomme")
                if st.form_submit_button("Check it") and wrong and right:
                    with st.spinner("Labeling..."):
                        try:
                            clear_keys("type_", "keep_")
                            st.session_state["pending"] = [dict(ai.label_typed(q, wrong, right), _src="typed")]
                        except Exception as e:
                            st.error(ai.friendly_error(e))

    pending = st.session_state.get("pending", [])
    if pending:
        st.write("")
        with st.container(key="card_review_ai"):
            st.markdown('<div class="card-title">Check what the AI found</div>'
                        '<div class="card-sub">The AI can be wrong. Fix the type or untick anything that isn\'t a real mistake.</div>',
                        unsafe_allow_html=True)
            for i, m in enumerate(pending):
                st.markdown(
                    f"""<div class="mistake"><p class="ex">{esc(m.get("question"))}<br>
                    <span class="wrong">{esc(m.get("user_answer"))}</span> → <span class="right">{esc(m.get("correct_answer"))}</span><br>
                    <span class="note">{esc(m.get("explanation"))}</span></p></div>""",
                    unsafe_allow_html=True,
                )
                a, b = st.columns([3, 1], vertical_alignment="center")
                idx = ai.MISTAKE_TYPES.index(m["mistake_type"]) if m.get("mistake_type") in ai.MISTAKE_TYPES else len(ai.MISTAKE_TYPES) - 1
                a.selectbox("Type", ai.MISTAKE_TYPES, index=idx, key=f"type_{i}", label_visibility="collapsed")
                b.checkbox("Keep", value=True, key=f"keep_{i}")
            if st.button("Save to my history", type="primary"):
                saved = 0
                for i, m in enumerate(pending):
                    if st.session_state.get(f"keep_{i}"):
                        ai_type = m["mistake_type"]  # what the AI suggested
                        m["mistake_type"] = st.session_state[f"type_{i}"]  # what the learner kept
                        db.add_mistake(user, m, source=m["_src"], ai_type=ai_type)
                        saved += 1
                st.session_state.pop("pending")
                st.toast(f"Saved {saved} mistake(s)")
                st.rerun()

# ---------- Practice ----------
elif page == "Practice":
    st.markdown('<div class="page-title">Practice</div>', unsafe_allow_html=True)
    if not patterns:
        empty_state()
    else:
        if st.session_state.get("practice_type") not in types:
            st.session_state["practice_type"] = types[0]
        with st.container(key="card_practice"):
            totals = {p["type"]: p["total"] for p in patterns}
            mtype = st.selectbox("Pattern to practice", types, key="practice_type",
                                 format_func=lambda t: f"{t}  ({totals[t]} mistakes)")
            if st.button("Make 5 questions", type="primary"):
                examples = next(p["examples"] for p in patterns if p["type"] == mtype)
                with st.spinner("Writing questions from your real mistakes..."):
                    try:
                        clear_keys("ans_")
                        st.session_state["quiz"] = ai.make_practice(mtype, examples)
                        st.session_state["quiz_type"] = mtype
                        st.session_state["quiz_done"] = False
                    except Exception as e:
                        st.error(ai.friendly_error(e))

        quiz = st.session_state.get("quiz")
        if quiz and st.session_state.get("quiz_type") == mtype:
            done = st.session_state.get("quiz_done", False)
            st.write("")
            with st.container(key="card_quiz"):
                for i, q in enumerate(quiz):
                    st.markdown(f'<div class="pname" style="margin-top:8px">{i + 1}. {esc(q["question"])}</div>',
                                unsafe_allow_html=True)
                    choice = st.radio(f"q{i}", q["options"], index=None, key=f"ans_{i}", horizontal=True,
                                      label_visibility="collapsed", disabled=done)
                    if done:
                        ok = choice == q["answer"]
                        css = "result-good" if ok else "result-bad"
                        head = "✅ Correct!" if ok else f'❌ Answer: {esc(q["answer"])}'
                        st.markdown(f'<div class="mistake {css}"><b>{head}</b><br><span class="note">{esc(q["why"])}</span></div>',
                                    unsafe_allow_html=True)
                if not done and st.button("Check answers", type="primary"):
                    score = sum(st.session_state.get(f"ans_{i}") == q["answer"] for i, q in enumerate(quiz))
                    db.add_practice(user, mtype, score, len(quiz))
                    st.session_state["quiz_done"] = True
                    st.session_state["last_score"] = score
                    st.rerun()
                if done:
                    st.success(f'You got {st.session_state["last_score"]} / {len(quiz)}. Saved to your dashboard.')

# ---------- Review ----------
elif page == "Review":
    st.markdown('<div class="page-title">Review</div>', unsafe_allow_html=True)
    if not patterns:
        empty_state()
    else:
        with st.container(key="card_reviewall"):
            pick = st.selectbox("Show", ["All patterns"] + types)
            shown = df if pick == "All patterns" else df[df["mistake_type"] == pick]
            st.markdown(f'<div class="card-sub">{len(shown)} mistakes, newest first</div>', unsafe_allow_html=True)
            for _, e in shown.sort_values("created_at", ascending=False).head(60).iterrows():
                st.markdown(
                    f"""<div class="mistake"><div class="pmeta">{e["created_at"]:%b %d} · {esc(e["mistake_type"])}</div>
                    <p class="ex">{esc(e["question"])}<br>
                    <span class="wrong">{esc(e["user_answer"])}</span> → <span class="right">{esc(e["correct_answer"])}</span><br>
                    <span class="note">{esc(e["explanation"])}</span></p></div>""",
                    unsafe_allow_html=True,
                )


# ---------- Testing ----------
else:
    st.markdown('<div class="page-title">Testing</div>', unsafe_allow_html=True)

    def tile(col, num, lbl, sub=""):
        col.markdown(f'<div class="tile"><div class="num">{num}</div><div class="lbl">{lbl}</div>'
                     f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)

    # 1. AI test set: real Claude runs on test cases with answers written in advance
    with st.container(key="card_evals"):
        st.markdown('<div class="card-title">AI test set</div>'
                    '<div class="card-sub">40 French mistakes with the correct type written in advance. '
                    'Claude labels each one twice: accuracy = right type, consistency = same type both times.</div>',
                    unsafe_allow_html=True)
        res = evals.load_results()
        if st.button("Run tests" if not res else "Run tests again", type="primary"):
            bar = st.progress(0.0, text="Labeling test mistakes...")
            try:
                res = evals.run_evals(on_progress=lambda d, t: bar.progress(d / t, text=f"Labeling test mistakes... {d}/{t}"))
                bar.empty()
            except Exception as e:
                bar.empty()
                st.error(ai.friendly_error(e))
        if not res:
            st.info("No test run yet. Click Run tests (needs your API key, takes about a minute).")
        else:
            n = res["cases"]
            t1, t2, t3 = st.columns(3)
            tile(t1, n, "Test cases", f"{len(evals.per_type(res))} mistake types")
            tile(t2, f'{res["correct"] / n:.0%}', "Accuracy", f'{res["correct"]}/{n} right type')
            tile(t3, f'{res["consistent"] / n:.0%}', "Consistency", f'{res["consistent"]}/{n} same label twice')
            st.caption(f'Last run {res["run_at"].replace("T", " ")} · model {res["model"]}'
                       + (f' · ⚠️ {res["errors"]} API errors' if res["errors"] else ""))
            a, b = st.columns(2, gap="medium")
            with a:
                rows = "".join(f"<tr><td>{esc(short(t))}</td><td>{ok}/{tot}</td></tr>"
                               for t, (ok, tot) in evals.per_type(res).items())
                st.markdown(f'<table class="tbl"><tr><th>Mistake type</th><th>Right</th></tr>{rows}</table>',
                            unsafe_allow_html=True)
            with b:
                misses = [c for c in res["results"] if not c["correct"] or not c["consistent"]]
                st.markdown(f'<div class="pname" style="margin:4px 0 8px">What broke ({len(misses)})</div>',
                            unsafe_allow_html=True)
                if not misses:
                    st.markdown('<p class="note">Every test case was labeled right, both times.</p>', unsafe_allow_html=True)
                for c in misses[:8]:
                    why = "wrong type" if not c["correct"] else "changed between runs"
                    st.markdown(
                        f"""<div class="mistake"><span class="wrong">{esc(c["user_answer"])}</span> →
                        <span class="right">{esc(c["correct_answer"])}</span><br>
                        <span class="note">Expected {esc(short(c["expected"]))} · got {esc(short(c["run1"]))}
                        {"/ " + esc(short(c["run2"])) if not c["consistent"] else ""} · {why}</span></div>""",
                        unsafe_allow_html=True)

    # 2. Testers: who used it, and how often they kept the AI's label
    st.write("")
    with st.container(key="card_testers"):
        st.markdown('<div class="card-title">Testers</div>'
                    '<div class="card-sub">"AI label kept" = how often the learner saved the type the AI suggested '
                    'without changing it.</div>',
                    unsafe_allow_html=True)
        allm = pd.DataFrame(db.get_mistakes())
        allp = pd.DataFrame(db.get_practice())
        if allm.empty:
            st.info("No testers yet. Add mistakes, or load data from the account menu.")
        else:
            body = ""
            for u, g in allm.groupby("user"):
                rated = g[g["ai_type"].notna()]
                kept = f'{(rated["ai_type"] == rated["mistake_type"]).mean():.0%} <span class="note">({len(rated)})</span>' \
                    if len(rated) else '<span class="note">–</span>'
                pu = allp[allp["user"] == u] if not allp.empty else allp
                avg = f'{pu["score"].sum() / pu["total"].sum():.0%}' if len(pu) else "–"
                body += (f"<tr><td>{esc(u)}</td><td>{len(g)}</td>"
                         f"<td>{kept}</td><td>{len(pu)}</td><td>{avg}</td></tr>")
            st.markdown('<table class="tbl"><tr><th>Learner</th><th>Mistakes</th><th>AI label kept</th>'
                        f'<th>Practice sets</th><th>Avg score</th></tr>{body}</table>', unsafe_allow_html=True)

            fixed = allm[allm["ai_type"].notna() & (allm["ai_type"] != allm["mistake_type"])]
            if len(fixed):
                st.markdown(f'<div class="pname" style="margin:18px 0 8px">Labels learners fixed ({len(fixed)})</div>',
                            unsafe_allow_html=True)
                for _, e in fixed.head(6).iterrows():
                    st.markdown(
                        f"""<div class="mistake"><b>{esc(e["user"])}</b> · <span class="wrong">{esc(e["user_answer"])}</span> →
                        <span class="right">{esc(e["correct_answer"])}</span><br>
                        <span class="note">AI said {esc(short(e["ai_type"]))} · learner changed it to {esc(short(e["mistake_type"]))}</span></div>""",
                        unsafe_allow_html=True)
