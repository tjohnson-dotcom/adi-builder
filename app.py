# app.py — ADI Builder v5 – Professional Layout

import io
import random
from datetime import datetime
from typing import List, Dict

import streamlit as st

# ---------- Page ----------
st.set_page_config(page_title="ADI Builder v5 – Professional Layout", page_icon="🧰", layout="wide")

# ---------- Optional deps (fail-soft) ----------
try:
    from pptx import Presentation           # python-pptx
except Exception:
    Presentation = None

try:
    from docx import Document               # python-docx
    from docx.shared import Pt
except Exception:
    Document = None

# ---------- Static data (from your screenshots) ----------
COURSES = [
    {"code": "GE4-EPM", "name": "Defense Technology Practices: Experimentation, Quality Management and Inspection", "color": "#bfe6c7"},
    {"code": "GE4-IPM", "name": "Integrated Project and Materials Management in Defense Technology", "color": "#bfe6c7"},
    {"code": "GE4-MRO", "name": "Military Vehicle and Aircraft MRO: Principles & Applications", "color": "#bfe6c7"},
    {"code": "CT4-COM", "name": "Computation for Chemical Technologists", "color": "#f5e5b3"},
    {"code": "CT4-EMG", "name": "Explosives Manufacturing", "color": "#f5e5b3"},
    {"code": "CT4-TFL", "name": "Thermofluids", "color": "#f5e5b3"},
]

COHORTS = [
    "D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
    "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"
]

INSTRUCTORS = [
    "Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen","Dari","Ghamza",
    "Michail","Meshari","Mohammed Alwuthaylah","Myra","Meshal","Ibrahim","Khalil","Salem",
    "Rana","Daniel","Ahmed Albader"
]

# Auto mapping Cohort → Instructor
COHORT_TO_INSTRUCTOR = {
    "D1-C01": "Daniel",
    "D1-E01": "Ben",
    "D1-E02": "Gerhard",
    "D1-M01": "Faiz Lazam",
    "D1-M02": "Nerdeen",
    "D1-M03": "Dari",
    "D1-M04": "Ghamza",
    "D1-M05": "Michail",
    "D2-C01": "Meshari",
    "D2-M01": "Mohammed Alwuthaylah",
    "D2-M02": "Myra",
    "D2-M03": "Meshal",
    "D2-M04": "Ibrahim",
    "D2-M05": "Rana",
    "D2-M06": "Ahmed Albader",
}

# Course quick templates (topics + default verbs)
COURSE_TEMPLATES = {
    "GE4-EPM": {"topics": ["Quality management plans","Inspection methods","Experiment design basics"],
                 "verbs": {"Low": "identify", "Medium": "apply", "High": "evaluate"}},
    "GE4-IPM": {"topics": ["Materials lifecycle","Inventory strategies","Procurement workflow"],
                 "verbs": {"Low": "define", "Medium": "analyze", "High": "design"}},
    "GE4-MRO": {"topics": ["Aircraft MRO phases","Maintenance records","Reliability metrics"],
                 "verbs": {"Low": "list", "Medium": "classify", "High": "evaluate"}},
    "CT4-COM": {"topics": ["Numerical methods","Error analysis","Units & conversions"],
                 "verbs": {"Low": "recognize", "Medium": "apply", "High": "critique"}},
    "CT4-EMG": {"topics": ["Safety protocols","Process flow","Material sensitivity"],
                 "verbs": {"Low": "identify", "Medium": "compare", "High": "evaluate"}},
    "CT4-TFL": {"topics": ["Fluid properties","Continuity & momentum","Heat transfer modes"],
                 "verbs": {"Low": "define", "Medium": "apply", "High": "design"}},
}

# ---------- Bloom policy ----------
LOW_VERBS  = ["remember", "list", "define", "identify", "state", "recognize"]
MED_VERBS  = ["apply", "analyze", "explain", "compare", "classify", "illustrate"]
HIGH_VERBS = ["evaluate", "create", "design", "critique", "synthesize", "hypothesize"]

def bloom_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    if 10 <= week <= 14: return "High"
    return "Medium"

def verbs(level: str) -> List[str]:
    return {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}.get(level, MED_VERBS)

# ---------- CSS (plain string; no f-strings) ----------
def inject_css():
    css = """
    <style>
    :root { --adi: #245a34; --gold: #C8A85A; --stone: #F6F6F4; }
    .block-container { padding-top: 0.6rem; max-width: 1280px; }
    h1,h2,h3,h4 { color: var(--adi) !important; }

    /* layout cards */
    .card { background:#fff; border:1px solid #e9e9e9; border-radius:14px; padding:14px; box-shadow:0 1px 2px rgba(0,0,0,.04); }
    .note { background:#f7faf7; border:1px dashed #d9e6d9; border-radius:10px; padding:8px 10px; font-size:0.9rem; }
    .thin-hr { border:0; height:1px; background:#ececec; margin:.8rem 0; }

    /* sidebar */
    section[data-testid="stSidebar"] > div { background: var(--stone); }

    /* tabs */
    .stTabs [data-baseweb=tab-list] { gap: .35rem; }
    .stTabs [data-baseweb=tab] { border:1px solid var(--adi); border-radius:999px; padding:.35rem .9rem; }
    .stTabs [aria-selected=true] { background: var(--adi); color:#fff; }

    /* buttons */
    .stButton>button { border-radius:.7rem; font-weight:700; }
    .stButton>button[kind=primary] { background: var(--adi); color:#fff; border-color: var(--adi); }

    /* chips */
    .chip { border:1px solid #b9b9b9; border-radius:10px; padding:9px 12px; font-weight:700; text-align:center; }
    .badge { display:inline-block; padding:.15rem .55rem; border:1px solid var(--adi); color:var(--adi); border-radius:8px; font-weight:700; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_css()

# ---------- PPTX topic extraction ----------
def extract_topics(upload) -> List[str]:
    if not upload or Presentation is None:
        return []
    prs = Presentation(upload)
    rough = []
    for slide in prs.slides:
        if slide.shapes.title and slide.shapes.title.text:
            t = slide.shapes.title.text.strip()
            if t and t not in rough: rough.append(t)
        for shp in slide.shapes:
            if hasattr(shp, "text_frame") and shp.text_frame:
                for p in shp.text_frame.paragraphs:
                    txt = (p.text or "").strip()
                    if 3 <= len(txt) <= 80 and txt not in rough:
                        rough.append(txt)
        if len(rough) > 50:
            break
    cleaned = []
    for s in rough:
        s = " ".join(s.split()).strip("•-–—: ")
        if s and s not in cleaned:
            cleaned.append(s)
    return cleaned[:30]

# ---------- MCQ generation ----------
def make_mcq(topic: str, level: str) -> Dict:
    verb = random.choice(verbs(level)).capitalize()
    stem = f"{verb} the key idea related to: {topic}"
    correct = f"{topic} — core concept"
    distractors = [
        f"{topic} — unrelated detail",
        f"{topic} — misconception",
        f"{topic} — peripheral fact",
    ]
    options = [correct] + distractors
    random.shuffle(options)
    return {"stem": stem, "options": options, "answer": correct}

# ---------- Export (Word if available; else TXT) ----------
def export_word(mcqs: List[Dict], meta: Dict) -> bytes:
    if not mcqs:
        return b""

    if Document is None:
        buf = io.StringIO()
        course = meta.get("course", ""); cohort = meta.get("cohort", ""); week_s = meta.get("week", "")
        buf.write(f"ADI Lesson — {course} — {cohort} — Week {week_s}\n\n")
        for i, q in enumerate(mcqs, 1):
            buf.write(f"Q{i}. {q['stem']}\n")
            for j, o in enumerate(q["options"], 1):
                buf.write(f"   {chr(64+j)}. {o}\n")
            if meta.get("answer_key", True):
                buf.write(f"Answer: {q['answer']}\n")
            buf.write("\n")
        return buf.getvalue().encode("utf-8")

    doc = Document(); doc.styles["Normal"].font.name = "Arial"; doc.styles["Normal"].font.size = Pt(11)
    doc.add_heading("ADI Lesson Activities & Questions", level=1)
    doc.add_paragraph(f"Course: {meta.get('course','')}  |  Cohort: {meta.get('cohort','')}  |  Instructor: {meta.get('instructor','')}")
    doc.add_paragraph(f"Date: {meta.get('date','')}  |  Lesson: {meta.get('lesson','')}  |  Week: {meta.get('week','')}")
    doc.add_paragraph("")
    doc.add_heading("Knowledge MCQs", level=2)
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        for j, o in enumerate(q["options"], 1):
            doc.add_paragraph(f"{chr(64+j)}. {o}", style="List Bullet")
        if meta.get("answer_key", True):
            doc.add_paragraph(f"Answer: {q['answer']}")
        doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

# Summary export (1-pager)

def export_summary(meta: Dict, topics: List[str]) -> bytes:
    if Document is None:
        buf = io.StringIO()
        buf.write("ADI Lesson Summary\n\n")
        for k in ["course","cohort","instructor","date"]:
            buf.write(f"{k.capitalize()}: {meta.get(k,'')}\n")
        buf.write(f"Lesson: {meta.get('lesson','')}  Week: {meta.get('week','')}\n\n")
        if topics:
            buf.write("Topics:\n");
            for t in topics: buf.write(f" - {t}\n")
        return buf.getvalue().encode("utf-8")
    doc = Document(); doc.styles["Normal"].font.name = "Arial"; doc.styles["Normal"].font.size = Pt(11)
    doc.add_heading("ADI Lesson Summary", level=1)
    doc.add_paragraph(f"Course: {meta.get('course','')}")
    doc.add_paragraph(f"Cohort: {meta.get('cohort','')}")
    doc.add_paragraph(f"Instructor: {meta.get('instructor','')}")
    doc.add_paragraph(f"Date: {meta.get('date','')}  |  Lesson: {meta.get('lesson','')}  |  Week: {meta.get('week','')}")
    if topics:
        doc.add_heading("Topics", level=2)
        for t in topics: doc.add_paragraph(f"• {t}")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

# ---------- State ----------
if "topics" not in st.session_state: st.session_state.topics = []
if "mcqs" not in st.session_state: st.session_state.mcqs = []

# ---------- Sidebar (compact, stone background) ----------
with st.sidebar:
    st.markdown("### Setup")
    uploaded = st.file_uploader("Upload (optional)", type=["txt","docx","pptx","pdf"], help="PPTX titles & bullets are extracted.")

    st.markdown("<div class='thin-hr'></div>", unsafe_allow_html=True)
    course_ix = st.selectbox("Course", list(range(len(COURSES))), format_func=lambda i: f"{COURSES[i]['code']} — {COURSES[i]['name']}")
    cohort = st.selectbox("Cohort", COHORTS, index=0)

    # Auto-assign instructor
    auto = st.checkbox("Auto-assign instructor from cohort", value=True)
    instr_default = INSTRUCTORS.index("Daniel") if "Daniel" in INSTRUCTORS else 0
    if auto and cohort in COHORT_TO_INSTRUCTOR:
        name = COHORT_TO_INSTRUCTOR[cohort]
        if name in INSTRUCTORS:
            instr_default = INSTRUCTORS.index(name)
    instructor = st.selectbox("Instructor", INSTRUCTORS, index=instr_default)

    date = st.date_input("Date", value=datetime.now())
    c1, c2 = st.columns(2)
    with c1: lesson = st.number_input("Lesson", 1, 5, 1)
    with c2: week = st.number_input("Week", 1, 14, 1)

# ---------- Main header ----------
st.markdown("# ADI Builder — Lesson Activities & Questions")
st.markdown("<div class='thin-hr'></div>", unsafe_allow_html=True)

# Two-column: main editor (narrow) + helper panel
main, side = st.columns([1.05, 0.95])

with main:
    st.markdown("#### Lesson builder")
    with st.container():
        topic = st.text_area("Topic / Outcome (optional)", placeholder="e.g., Integrated Project and …")

    st.markdown("<div class='thin-hr'></div>", unsafe_allow_html=True)

    # Flow: quick-load + extract inline
    cA, cB = st.columns([1,1])
    with cA:
        if st.button("Quick‑load template"):
            code = COURSES[course_ix]["code"]
            t = COURSE_TEMPLATES.get(code)
            if t:
                st.session_state.topics = t.get("topics", [])
                st.toast(f"Loaded {len(st.session_state.topics)} topics from {code}")
    with cB:
        if uploaded and Presentation is not None and st.button("Extract topics from PPTX"):
            st.session_state.topics = extract_topics(uploaded)
            st.toast(f"Extracted {len(st.session_state.topics)} topics" if st.session_state.topics else "No topics found")

    # Recommended Bloom
    recommended = bloom_for_week(int(week))
    badge_bg = {"Low": "#e7f3ea", "Medium": "#f7efd9", "High": "#e8f0fb"}.get(recommended, "#eef2f1")
    st.markdown(f"<div class='note'>ADI policy: 1–4 Low • 5–9 Medium • 10–14 High — Recommended for Week {int(week)}: <span class='badge' style='background:{badge_bg}'>{recommended}</span></div>", unsafe_allow_html=True)

    # Topics area (always visible)
    topics = st.session_state.get("topics", [])
    if topics:
        picked = st.multiselect("Pick topics (5–10)", topics, default=topics[:8], max_selections=10)
    else:
        manual = st.text_area("Enter topics (one per line)", placeholder="Topic A\nTopic B\nTopic C")
        picked = [t.strip() for t in manual.splitlines() if t.strip()]

    # Count + generate
    n_q = st.selectbox("How many MCQs?", [5,10,12,15,20], index=1)
    include_key = st.checkbox("Include answer key", value=True)

    # Suggested verb from template (small hint)
    code = COURSES[course_ix]["code"]
    sugg = COURSE_TEMPLATES.get(code, {}).get("verbs", {}).get(recommended)
    if sugg:
        st.caption(f"Suggested verb for {code} at {recommended}: **{sugg}**")

    if st.button("Generate MCQs", type="primary"):
        base = picked if picked else ([topic] if topic.strip() else [])
        if not base:
            st.error("Provide at least one topic (or extract from upload).")
        else:
            pool = []
            while len(pool) < n_q:
                for t in base:
                    pool.append(t)
                    if len(pool) >= n_q: break
            random.shuffle(pool)
            st.session_state.mcqs = [make_mcq(t, recommended) for t in pool]
            st.success(f"Generated {len(st.session_state.mcqs)} MCQs at {recommended} level.")

    # Preview & inline edit
    if st.session_state.mcqs:
        with st.expander("Preview / quick edit"):
            for i, q in enumerate(st.session_state.mcqs, 1):
                q["stem"] = st.text_input(f"Q{i}", value=q["stem"], key=f"stem_{i}")
                for j, o in enumerate(q["options"], 1):
                    q["options"][j-1] = st.text_input(f"Option {chr(64+j)}", value=o, key=f"opt_{i}_{j}")
                q["answer"] = st.selectbox("Correct answer", q["options"], index=q["options"].index(q["answer"]), key=f"ans_{i}")
                st.divider()

    # Export dropdown (Word MCQs / Summary / Both)
    meta = {
        "course": f"{COURSES[course_ix]['code']} — {COURSES[course_ix]['name']}",
        "cohort": cohort,
        "instructor": instructor,
        "date": date.strftime("%Y/%m/%d"),
        "lesson": int(lesson),
        "week": int(week),
        "answer_key": include_key,
    }
    export_choice = st.selectbox("Export", ["Word: MCQs", "Word: Summary", "Both (MCQs + Summary)"])
    if st.button("Download"):
        if export_choice.startswith("Word: MCQs") and st.session_state.mcqs:
            data = export_word(st.session_state.mcqs, meta)
            st.download_button("Download MCQs", data, file_name=f"ADI_Lesson_{COURSES[course_ix]['code']}_W{int(week)}_{datetime.now().strftime('%Y%m%d_%H%M')}.{('docx' if Document else 'txt')}", mime=("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if Document else "text/plain"), key="dl_mcq")
        elif export_choice.endswith("Summary"):
            summ = export_summary(meta, st.session_state.get("topics", []))
            st.download_button("Download Summary", summ, file_name=f"ADI_Summary_{COURSES[course_ix]['code']}_W{int(week)}_{datetime.now().strftime('%Y%m%d_%H%M')}.{('docx' if Document else 'txt')}", mime=("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if Document else "text/plain"), key="dl_sum")
        else:
            if st.session_state.mcqs:
                data = export_word(st.session_state.mcqs, meta)
                st.download_button("Download MCQs", data, file_name=f"ADI_Lesson_{COURSES[course_ix]['code']}_W{int(week)}_{datetime.now().strftime('%Y%m%d_%H%M')}.{('docx' if Document else 'txt')}", mime=("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if Document else "text/plain"), key="dl_both_mcq")
            summ = export_summary(meta, st.session_state.get("topics", []))
            st.download_button("Download Summary", summ, file_name=f"ADI_Summary_{COURSES[course_ix]['code']}_W{int(week)}_{datetime.now().strftime('%Y%m%d_%H%M')}.{('docx' if Document else 'txt')}", mime=("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if Document else "text/plain"), key="dl_both_sum")

with side:
    st.markdown("#### Course quick‑pick")
    cols = st.columns(3)
    for i, c in enumerate(COURSES):
        with cols[i % 3]:
            st.markdown(f"<div class='chip' style='background:{c['color']}'>{c['name']}<br><b>{c['code']}</b></div>", unsafe_allow_html=True)
    st.markdown("<div class='thin-hr'></div>", unsafe_allow_html=True)

    if st.session_state.mcqs:
        st.success(f"{len(st.session_state.mcqs)} MCQs ready to export.")
    else:
        st.info("No questions yet — add a topic or extract from upload, then Generate.")

# ---------- Requirements ----------
# requirements.txt:
# streamlit
# python-pptx
# python-docx

