

# app.py — ADI Builder (interactive course picker)

import io
import random
from datetime import datetime
from typing import List, Dict
import streamlit as st

# ---------- Page ----------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🧰", layout="wide")

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

# ---------- Styling ----------
def inject_css():
    css = """
    <style>
    :root { --adi: #245a34; --gold: #C8A85A; --stone: #F3F3F0; }
    .block-container { padding-top: .8rem; max-width: 1480px; }
    h1,h2,h3,h4 { color: var(--adi) !important; }
    .course-card { border:2px dashed #999; border-radius:.5rem; padding:.6rem; margin:.3rem 0; cursor:pointer; }
    .course-card:hover { background:#f0f0f0; }
    .course-card.selected { border-color: var(--adi); background: #e6f2e6; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_css()

# ---------- State ----------
if "selected_course_ix" not in st.session_state:
    st.session_state.selected_course_ix = 0

# ---------- Sidebar ----------
with st.sidebar:
    st.subheader("Upload (optional)")
    uploaded = st.file_uploader("Drag and drop file here", type=["txt", "docx", "pptx", "pdf"], help="We can scan titles & bullets from PPTX.")
    if uploaded:
        st.success(f"File uploaded: {uploaded.name} ({uploaded.size//1024} KB)")

    st.subheader("Course details")
    course_ix = st.session_state.selected_course_ix
    course_display = f"{COURSES[course_ix]['code']} — {COURSES[course_ix]['name']}"
    st.markdown(f"**Selected Course:** {course_display}")
    cohort = st.selectbox("Class / Cohort", COHORTS, index=0)
    instructor = st.selectbox("Instructor name", INSTRUCTORS, index=INSTRUCTORS.index("Daniel") if "Daniel" in INSTRUCTORS else 0)
    date = st.date_input("Date", value=datetime.now())
    lesson = st.number_input("Lesson", min_value=1, max_value=5, value=1, step=1)
    week = st.number_input("Week", min_value=1, max_value=14, value=1, step=1)

# ---------- Main ----------
st.markdown("## ADI Builder — Lesson Activities & Questions")
st.markdown("<hr>", unsafe_allow_html=True)

st.subheader("Course quick-pick")
for i, c in enumerate(COURSES):
    selected = "selected" if i == st.session_state.selected_course_ix else ""
    if st.button(f"{c['code']} — {c['name']}", key=f"course_{i}"):
        st.session_state.selected_course_ix = i
    st.markdown(f"<div class='course-card {selected}' style='background:{c['color']}'>{c['name']}<br><b>{c['code']}</b></div>", unsafe_allow_html=True)
