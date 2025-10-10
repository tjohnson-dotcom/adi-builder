# -------------------------------
# ADI Builder — Lesson Activities & Questions
# Clean / safe build: palette-chips + sticky-tab + hover + dashed-uploader
# Streamlit 1.36+ compatible
# -------------------------------

import io
import datetime as dt
from typing import List, Dict

import streamlit as st

# ---------- ONE-TIME PAGE CONFIG (must be first) ----------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="🧭",
    layout="wide",
)

# ---------- SHORTCUTS ----------
ss = st.session_state

# ---------- DATA (replace with your real sources as needed) ----------
COURSES = [
    "GE4-IPM — Integrated Project & Materials Management in Defense Technology",
    "GE4-EPM — Defense Technology Practices: Experimentation, QM & Inspection",
    "GE4-MRO — Military Vehicle & Aircraft MRO: Principles & Applications",
    "CT4-COM — Computation for Chemical Technologists",
    "CT4-EMG — Explosives Manufacturing",
    "CT4-TFL — Thermofluids",
    "MT4-CMG — Composite Manufacturing",
    "MT4-CAD — Computer Aided Design",
    "MT4-MAE — Machine Elements",
    "EE4-MFC — Electrical Materials",
    "EE4-PMG — PCB Manufacturing",
    "EE4-PCT — Power Circuits & Transmission",
]
COHORTS = [f"D{i}-C0{j}" for i in (1, 2) for j in range(1, 7)]  # D1-C01 ... D2-C06
INSTRUCTORS = [
    "Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen Tariq",
    "Dari","Ghamza Labeeb","Michail","Meshari","Mohammed Alwuthaylah","Myra",
    "Meshal Algurabi","Ibrahim Alrawaili","Khalil","Salem","Chetan","Yasser",
    "Ahmed Albader","Muath","Sultan","Dr. Mashael","Noura Aldossari","Daniel"
]

LOW_VERBS    = ["define", "identify", "list", "recall", "describe", "label"]
MEDIUM_VERBS = ["apply", "demonstrate", "solve", "classify", "compare", "illustrate"]
HIGH_VERBS   = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

# Palette (stay within Streamlit chip look, but color surroundings)
PAL = {
    "green_dark":  "#153a27",  # header/bars
    "green":       "#245a34",
    "green_soft":  "#cfe8d9",
    "amber_soft":  "#f8e6c9",
    "blue_soft":   "#dfe6ff",
    "chip_text":   "#ffffff",
}

# ---------- DEFAULT SESSION STATE ----------
def set_default(key, value):
    if key not in ss:
        ss[key] = value

set_default("course", COURSES[0])
set_default("cohort", COHORTS[0])
set_default("instructor", INSTRUCTORS[-1])  # Daniel
set_default("date", dt.date.today().isoformat())
set_default("lesson", 1)
set_default("week", 1)

# verbs selected
set_default("verbs_low",    ["define", "identify", "list"])
set_default("verbs_med",    ["apply", "demonstrate", "solve"])
set_default("verbs_high",   ["evaluate", "synthesize", "design"])

# MCQ state
set_default("how_many", 10)
set_default("include_answer_key", True)
set_default("topic", "")
set_default("mcqs", [])  # list of dicts

# Tabs sticky via query param
def get_active_tab() -> str:
    qp = st.query_params
    return qp.get("tab", "mcq")

def set_active_tab(tab_name: str):
    qp = st.query_params
    qp["tab"] = tab_name
    st.query_params.update(qp)

set_default("active_tab", get_active_tab())  # initialize once

# ---------- STYLES ----------
st.markdown(
    f"""
<style>
/* Top bar */
.adi-header {{
  width: 100%;
  padding: 10px 14px;
  border-radius: 8px;
  background: {PAL["green_dark"]};
  color: #fff;
  font-weight: 600;
}}

/* Uploader dashed box + hover */
div[data-testid="stFileUploaderDropzone"] {{
  border: 2px dashed {PAL["green"]} !important;
  border-radius: 10px !important;
  background: #f8faf9;
}}
div[data-testid="stFileUploaderDropzone"]:hover {{
  box-shadow: 0 0 0 3px {PAL["green_soft"]} inset !important;
}}

/* Pointer + hover rings on interactive widgets */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button {{
  cursor: pointer !important;
}}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {{
  box-shadow: 0 0 0 2px {PAL["green"]} inset !important;
}}
:focus-visible {{
  outline: 2px solid {PAL["green"]} !important;
  outline-offset: 2px;
}}

/* Verb bands */
.band {{ 
  padding: 6px 10px; 
  border: 2px solid {PAL["green"]}; 
  border-radius: 8px;
  margin: 8px 0 0 0;
  color: #111827;
}}
.band.low    {{ background: {PAL["green_soft"]}; }}
.band.medium {{ background: {PAL["amber_soft"]}; }}
.band.high   {{ background: {PAL["blue_soft"]}; }}
.band.active {{ border-width: 3px; }}

/* Tabs underline color match green */
.css-1r6slb0 a, .stTabs [data-baseweb="tab"] {{
  color: #111827;
}}
.stTabs [aria-selected="true"] {{
  border-color: {PAL["green"]} !important;
}}

/* Generate button style */
button.adi {{
  background: {PAL["green"]} !important;
  color: #fff !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- HEADER ----------
col_logo, col_title, _ = st.columns([0.14, 0.66, 0.2])
with col_logo:
    # Avoid use_container_width for older versions
    st.image("adi_logo.png", width=120)
with col_title:
    st.markdown('<div class="adi-header">ADI Builder — Lesson Activities & Questions</div>',
                unsafe_allow_html=True)

st.write("")  # spacer

# ---------- LAYOUT ----------
left, right = st.columns([0.22, 0.78])

# ---------- LEFT SIDEBAR (controls) ----------
with left:
    st.subheader("Upload (optional)")
    st.file_uploader(
        "Drag and drop file here",
        type=["txt", "docx", "pptx", "pdf"],
        accept_multiple_files=False,
        key="uploader",
        label_visibility="collapsed",
    )
    st.checkbox("Deep scan source (slower, better coverage)", value=False, key="deep_scan")

    st.subheader("Course details")

    st.selectbox("Course name", COURSES, index=COURSES.index(ss.course), key="course")
    st.selectbox("Class / Cohort", COHORTS, index=COHORTS.index(ss.cohort), key="cohort")
    st.selectbox("Instructor name", INSTRUCTORS, index=INSTRUCTORS.index(ss.instructor), key="instructor")

    st.text_input("Date", ss.date, key="date")

    colL, colW = st.columns(2)
    with colL:
        st.number_input("Lesson", min_value=1, max_value=14, step=1, value=int(ss.lesson), key="lesson")
    with colW:
        st.number_input("Week", min_value=1, max_value=14, step=1, value=int(ss.week), key="week")

# ---------- RIGHT MAIN ----------
with right:
    # Topic
    st.text_area("Topic / Outcome (optional)",
                 value=ss.topic,
                 key="topic",
                 placeholder="e.g., Integrated Project and …")

    # Verb bands (function that safely renders and sets keys only once)
    def band(title: str, verbs: List[str], key: str, level: str):
        selected = ss.get(key, [])
        # Mark band active visually if any selections are present
        active_class = "active" if selected else ""
        st.markdown(f'<div class="band {level} {active_class}"><strong>{title}</strong></div>',
                    unsafe_allow_html=True)
        st.multiselect(
            " ",  # no extra label; rely on band heading above
            options=verbs,
            default=selected,
            key=key,
            label_visibility="collapsed",
        )

    band("Low (Weeks 1–4) — Remember / Understand", LOW_VERBS, "verbs_low", "low")
    band("Medium (Weeks 5–9) — Apply / Analyse",    MEDIUM_VERBS, "verbs_med", "medium")
    band("High (Weeks 10–14) — Evaluate / Create",  HIGH_VERBS, "verbs_high", "high")

    # Tabs with sticky behavior
    tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])
    tab_names = ["mcq", "skills", "revision", "print"]

    # ensure our desired active tab shows first (informational, not strictly required)
    # we won't re-run to force position; we just store query param when clicked.
    def on_tab_click(which: str):
        ss.active_tab = which
        set_active_tab(which)

    # ---- MCQ TAB ----
    with tabs[0]:
        if ss.active_tab != "mcq":
            on_tab_click("mcq")

        st.caption("ADI policy: 1–3 per lesson • 5–9 Medium • 10–14 High")
        st.selectbox(
            "How many MCQs?",
            [5, 10, 12, 15, 20],
            index=[5, 10, 12, 15, 20].index(ss.how_many) if ss.how_many in [5, 10, 12, 15, 20] else 1,
            key="how_many",
        )
        st.checkbox("Answer key", value=ss.include_answer_key, key="include_answer_key")

        st.write("")
        if st.button("Generate from verbs/topic", key="gen_mcq", type="primary"):
            ss.mcqs = generate_mcqs_stub(
                topic=ss.topic,
                low=ss.verbs_low, med=ss.verbs_med, high=ss.verbs_high,
                n=ss.how_many
            )

        # Render editable MCQs
        if not ss.mcqs:
            st.info("No questions yet. Click **Generate from verbs/topic**.")
        else:
            for i, q in enumerate(ss.mcqs, start=1):
                with st.expander(f"Q{i}", expanded=True):
                    st.text_area("Question", value=q["question"], key=f"q_{i}_text")
                    colA, colB = st.columns(2)
                    with colA:
                        st.text_input("A", value=q["A"], key=f"q_{i}_A")
                        st.text_input("B", value=q["B"], key=f"q_{i}_B")
                    with colB:
                        st.text_input("C", value=q["C"], key=f"q_{i}_C")
                        st.text_input("D", value=q["D"], key=f"q_{i}_D")
                    st.radio("Correct answer", ["A", "B", "C", "D"],
                             index=["A","B","C","D"].index(q["answer"]),
                             key=f"q_{i}_ans")

            # Update state back from widget values (safe; different keys)
            for i, q in enumerate(ss.mcqs, start=1):
                q["question"] = ss.get(f"q_{i}_text", q["question"])
                for opt in ["A","B","C","D"]:
                    q[opt] = ss.get(f"q_{i}_{opt}", q[opt])
                q["answer"] = ss.get(f"q_{i}_ans", q["answer"])

            st.write("")
            dl_col1, dl_col2, dl_col3 = st.columns([0.25,0.25,0.5])
            with dl_col1:
                st.download_button("⬇️ Download DOCX (All MCQs)",
                                   data=export_docx(ss.mcqs, ss.include_answer_key),
                                   file_name=f"ADI_MCQ__{slug(ss.course)}__{slug(ss.topic or 'Topic')}__{ss.cohort}__W{ss.week}__Q{len(ss.mcqs)}.docx")
            with dl_col2:
                st.download_button("⬇️ Download TXT (All MCQs)",
                                   data=export_txt(ss.mcqs, ss.include_answer_key),
                                   file_name=f"ADI_MCQ__{slug(ss.course)}__{slug(ss.topic or 'Topic')}__{ss.cohort}__W{ss.week}__Q{len(ss.mcqs)}.txt")

    # ---- SKILLS TAB ----
    with tabs[1]:
        if ss.active_tab != "skills":
            on_tab_click("skills")

        st.caption("Pick **1, 2 or 3** per lesson. Time per activity **5–60 mins**. Group size: **Solo / Pairs / Triads / 4**.")
        colN, colT, colG = st.columns([0.25, 0.25, 0.5])
        with colN:
            n_acts = st.selectbox("How many activities?", [1,2,3], index=0, key="skills_n")
        with colT:
            mins = st.selectbox("Minutes per activity", list(range(5,65,5)), index=1, key="skills_mins")
        with colG:
            group = st.selectbox("Group size", ["Solo (1)","Pairs (2)","Triads (3)","4"], index=0, key="skills_group")

        if st.button("Generate Activities", key="gen_skills", help="Draft activities from verbs & topic", use_container_width=False):
            st.session_state["skills"] = generate_skills_stub(
                ss.topic, ss.verbs_low, ss.verbs_med, ss.verbs_high, n_acts, mins, group
            )

        skills = ss.get("skills", [])
        if not skills:
            st.info("No activities yet. Click **Generate Activities**.")
        else:
            for i, act in enumerate(skills, start=1):
                with st.expander(f"Activity {i}", expanded=True):
                    st.markdown(f"**Goal:** {act['goal']}")
                    st.markdown(f"**Instructions:** {act['steps']}")
                    st.markdown(f"**Time:** {act['minutes']} min &nbsp;&nbsp; **Group:** {act['group']}")

    # ---- REVISION TAB ----
    with tabs[2]:
        if ss.active_tab != "revision":
            on_tab_click("revision")
        st.info("Revision section — coming next.")

    # ---- PRINT SUMMARY TAB ----
    with tabs[3]:
        if ss.active_tab != "print":
            on_tab_click("print")
        st.write("### Print Summary")
        st.write(f"**Course:** {ss.course}")
        st.write(f"**Cohort:** {ss.cohort}")
        st.write(f"**Instructor:** {ss.instructor}")
        st.write(f"**Date:** {ss.date} &nbsp;&nbsp; **Lesson:** {ss.lesson} &nbsp;&nbsp; **Week:** {ss.week}")
        st.write(f"**Topic:** {ss.topic or '—'}")
        st.write("**Verbs**")
        st.write(f"- Low: {', '.join(ss.verbs_low) or '—'}")
        st.write(f"- Medium: {', '.join(ss.verbs_med) or '—'}")
        st.write(f"- High: {', '.join(ss.verbs_high) or '—'}")

# ---------- HELPERS ----------
def slug(s: str) -> str:
    return "-".join("".join(ch for ch in s if ch.isalnum() or ch in " -_")\
                    .strip().split())

def generate_mcq_from_verb(verb: str, topic: str, idx: int) -> Dict:
    """Tiny starter: makes simple, sensible question stems without LLM."""
    base = topic.strip() or "the lesson"
    q = {
        "question": f"{idx}. Using **{verb}**, what is the correct statement about {base}?",
        "A": f"A statement related to {base} ({verb}).",
        "B": f"Another statement related to {base}.",
        "C": f"A distractor about {base}.",
        "D": f"Another distractor about {base}.",
        "answer": "A",
    }
    return q

def generate_mcqs_stub(topic: str, low: List[str], med: List[str], high: List[str], n: int) -> List[Dict]:
    pool = (high or []) + (med or []) + (low or [])
    if not pool:
        pool = ["understand"]
    out = []
    for i in range(1, n+1):
        v = pool[(i-1) % len(pool)]
        out.append(generate_mcq_from_verb(v, topic, i))
    return out

def generate_skills_stub(topic: str, low: List[str], med: List[str], high: List[str],
                         n: int, minutes: int, group: str) -> List[Dict]:
    verbs = (med or []) + (high or []) + (low or [])
    if not verbs:
        verbs = ["apply"]
    acts = []
    for i in range(n):
        v = verbs[i % len(verbs)]
        acts.append({
            "goal": f"Students will **{v}** key ideas from {topic or 'the lesson'}.",
            "steps": f"1) In {group}, brainstorm examples.\n2) Share briefly.\n3) Capture a one-minute reflection.",
            "minutes": minutes,
            "group": group,
        })
    return acts

def export_txt(mcqs: List[Dict], include_key: bool) -> bytes:
    buf = io.StringIO()
    for i, q in enumerate(mcqs, start=1):
        buf.write(f"Q{i}. {q['question']}\n")
        buf.write(f"A) {q['A']}\nB) {q['B']}\nC) {q['C']}\nD) {q['D']}\n")
        if include_key:
            buf.write(f"Answer: {q['answer']}\n")
        buf.write("\n")
    return buf.getvalue().encode("utf-8")

def export_docx(mcqs: List[Dict], include_key: bool) -> bytes:
    """Lightweight DOCX export using python-docx if available; fallback to TXT."""
    try:
        from docx import Document
    except Exception:
        return export_txt(mcqs, include_key)

    doc = Document()
    doc.add_heading("ADI — Knowledge MCQs", level=1)
    for i, q in enumerate(mcqs, start=1):
        doc.add_paragraph(f"Q{i}. {q['question']}")
        doc.add_paragraph(f"A) {q['A']}")
        doc.add_paragraph(f"B) {q['B']}")
        doc.add_paragraph(f"C) {q['C']}")
        doc.add_paragraph(f"D) {q['D']}")
        if include_key:
            doc.add_paragraph(f"Answer: {q['answer']}")
        doc.add_paragraph("")
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()
