
# app.py — ADI Builder (polished)

import io
import random
from datetime import datetime
from typing import List, Dict
import streamlit as st

# ---------- Page ----------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🧠", layout="wide")

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

# ---------- Hard data ----------
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

def inject_css():
    css = """
    <style>
    :root { --adi: #245a34; --gold: #C8A85A; --stone: #F3F3F0; }
    .block-container { padding-top: .8rem; max-width: 1480px; }
    h1,h2,h3,h4 { color: var(--adi) !important; }
    .stTabs [data-baseweb=tab-list] { gap:.35rem; }
    .stTabs [data-baseweb=tab] { border:1px solid var(--adi); border-radius:999px; padding:.35rem .9rem; }
    .stTabs [aria-selected=true] { background:var(--adi); color:#fff; }
    .badge { display:inline-block; padding:.2rem .55rem; border:1px solid var(--adi); color:var(--adi);
    border-radius:.5rem; font-weight:700; }
    .course-chip { border:1px solid #999; border-radius:.4rem; padding:.4rem; font-size:.85rem;
    font-weight:700; text-align:center; margin-bottom:.5rem; }
    .thin-hr { border:0; height:1px; background:#ececec; margin:.8rem 0; }
    .stButton>button { border-radius:.6rem; font-weight:700; }
    .stButton>button[kind=primary] { background:var(--adi); color:#fff; border-color:var(--adi); }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_css()

# ---------- Sidebar ----------
with st.sidebar:
    with st.expander("📁 Upload Lesson File", expanded=True):
        uploaded = st.file_uploader("Drag and drop file here", type=["txt", "docx", "pptx", "pdf"], help="We can scan titles & bullets from PPTX.")
    with st.expander("📘 Course Details", expanded=True):
        course_ix = st.selectbox("Course name", list(range(len(COURSES))),
            format_func=lambda i: f"{COURSES[i]['code']} — {COURSES[i]['name']}")
        cohort = st.selectbox("Class / Cohort", COHORTS, index=0)
        instructor = st.selectbox("Instructor name", INSTRUCTORS, index=INSTRUCTORS.index("Daniel") if "Daniel" in INSTRUCTORS else 0)
        date = st.date_input("Date", value=datetime.now())
        c1, c2 = st.columns(2)
        with c1:
            lesson = st.number_input("Lesson", min_value=1, max_value=5, value=1, step=1)
        with c2:
            week = st.number_input("Week", min_value=1, max_value=14, value=1, step=1)

# ---------- Main ----------
st.markdown("## ADI Builder — Lesson Activities & Questions")
st.markdown("<div class='thin-hr'></div>", unsafe_allow_html=True)

recommended = bloom_for_week(int(week))
st.write(f"**Recommended Bloom for Week {int(week)}:**  "
         f"<span class='badge'>{recommended}</span>", unsafe_allow_html=True)
st.caption(f"Bloom’s Verbs: {', '.join(verbs(recommended))}")

tab1, tab2, tab3, tab4 = st.tabs(["Knowledge MCQs", "Skills Activities", "Revision Pack", "Print Summary"])

with tab1:
    st.subheader("Generate MCQs")
    st.text_input("Topic", placeholder="e.g., Integrated Project Management")
    st.selectbox("Number of MCQs", [5, 10, 15, 20], index=1)
    st.checkbox("Include answer key", value=True)
    st.button("Generate MCQs", type="primary")
    st.caption("Download will appear after generation.")
    st.download_button("⬇️ Download Word", data=b"", file_name="ADI_Lesson.docx", disabled=True)

with tab2:
    st.subheader("Skills Activities")
    st.markdown("### Sample Activity")
    st.markdown("- **Scenario**: You are tasked with evaluating a defense project timeline.")
    st.markdown("- **Task**: Create a Gantt chart and identify critical path.")
    st.markdown("- **Bloom Level**: Evaluate, Design")

with tab3:
    st.subheader("Revision Pack")
    st.markdown("### Summary Points")
    st.markdown("- Key concepts from lesson")
    st.markdown("- Definitions and diagrams")
    st.markdown("- Practice questions")

with tab4:
    st.subheader("Print Summary")
    st.markdown("### Lesson Overview")
    st.markdown(f"- Course: {COURSES[course_ix]['code']} — {COURSES[course_ix]['name']}")
    st.markdown(f"- Cohort: {cohort}")
    st.markdown(f"- Instructor: {instructor}")
    st.markdown(f"- Date: {date.strftime('%Y-%m-%d')}")
    st.markdown(f"- Lesson: {lesson} | Week: {week}")
