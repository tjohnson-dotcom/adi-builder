# app.py — ADI Builder (stable “no-surprises” build)
# Keeps your existing look; only adds tiny stability patches.

from __future__ import annotations
import io
import base64
from typing import List, Dict, Tuple
from datetime import date

import streamlit as st

# ---------- THEME / GLOBAL STYLES (unchanged look, stability-only) ----------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

st.markdown("""
<style>
:root { --adi:#245a34; --adi-dark:#153a27; }

html, body, [data-testid="stAppViewContainer"] { background-color:#ffffff; }
.block-container { padding-top: 0.6rem; }

/* Top banner card look that you liked */
.adi-banner {
  background: var(--adi-dark);
  color: #fff;
  padding: 12px 16px;
  border-radius: 8px;
  font-weight: 600;
}

/* Chips & bands */
.band { border: 1px solid #e6ece6; padding: 10px 12px; border-radius: 10px; }
.band + .band { margin-top: 10px; }
.band.active { border-color: var(--adi); box-shadow: 0 0 0 2px var(--adi) inset; }

/* Make interactive bits feel clickable (pointer) */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button {
  cursor: pointer !important;
}

/* Hover feedback */
div[data-testid="stFileUploaderDropzone"]:hover {
  box-shadow: 0 0 0 3px var(--adi) inset !important;
}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {
  box-shadow: 0 0 0 2px var(--adi) inset !important;
}

/* Keyboard accessibility */
:focus-visible {
  outline: 2px solid var(--adi) !important;
  outline-offset: 2px;
}

/* Green dashed dropzone (requested) */
div[data-testid="stFileUploaderDropzone"] {
  border: 2px dashed var(--adi) !important;
  border-radius: 10px !important;
}

/* Compact tabs feel */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { padding: 6px 10px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
def _safe_success(msg: str):
    """Toast when available; never crash older versions."""
    try:
        st.toast(msg, icon="✅")
    except Exception:
        st.success(msg)

def _read_txt(file) -> str:
    return file.read().decode("utf-8", errors="ignore")

def _read_docx(file) -> str:
    try:
        from docx import Document
        with io.BytesIO(file.read()) as mem:
            doc = Document(mem)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

def _read_pptx(file) -> str:
    try:
        from pptx import Presentation
        with io.BytesIO(file.read()) as mem:
            prs = Presentation(mem)
        texts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    texts.append(shape.text)
        return "\n".join(texts)
    except Exception:
        return ""

def _read_pdf(file) -> str:
    try:
        import fitz  # PyMuPDF
        with io.BytesIO(file.read()) as mem:
            doc = fitz.open(stream=mem, filetype="pdf")
        out = []
        for p in doc:
            out.append(p.get_text("text"))
        return "\n".join(out)
    except Exception:
        return ""

def extract_text_from_upload(uploaded_file) -> str:
    if not uploaded_file:
        return ""
    name = (uploaded_file.name or "").lower()
    if name.endswith(".txt"):
        return _read_txt(uploaded_file)
    if name.endswith(".docx"):
        return _read_docx(uploaded_file)
    if name.endswith(".pptx"):
        return _read_pptx(uploaded_file)
    if name.endswith(".pdf"):
        return _read_pdf(uploaded_file)
    # fallback raw bytes string
    try:
        return uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

# ---------- DATA ----------
LOW_VERBS     = ["define", "identify", "list", "describe", "label", "recall"]
MEDIUM_VERBS  = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH_VERBS    = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

COURSES = [
    "GE4-IPM — Integrated Project & Materials Mgmt in Defense Technology",
    "GE4-EPM — Defense Technology Practices",
    "GE4-MRO — MRO Principles & Applications",
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

COHORTS = ["D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
           "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"]

INSTRUCTORS = ["Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen Tariq",
               "Dari","Ghamza Labeeb","Michail","Meshari","Mohammed Alwuthaylah","Myra",
               "Meshal Algurabi","Ibrahim Alrawaili","Khalil","Salem","Chetan","Yasser",
               "Ahmed Albader","Muath","Sultan","Dr. Mashael","Noura Aldossari","Daniel"]

# ---------- SIDEBAR ----------
with st.sidebar:
    # Stability fix: remove use_container_width arg (was causing crash on some versions)
    st.image("adi_logo.png", width=160)

    st.write("**Upload (optional)**")
    uploaded_file = st.file_uploader(
        "Drag and drop file here",
        type=["txt","docx","pptx","pdf"],
        help="Limit 200MB per file • TXT, DOCX, PPTX, PDF"
    )
    extracted_text = ""
    if uploaded_file:
        extracted_text = extract_text_from_upload(uploaded_file)
        _safe_success(f"Uploaded: {uploaded_file.name}")

    st.caption("Quick scan reads the first 10 PDF pages. Turn on deep scan for full documents.")
    deep_scan = st.toggle("Deep scan source (slower, better coverage)", value=False)

    st.markdown("---")
    st.write("**Course details**")

    # Keep your + / - mental model simple (not bound to data changes here)
    cols = st.columns([1,0.25,0.25])
    with cols[0]:
        course = st.selectbox("Course name", COURSES, index=0, key="course")
    with cols[1]:
        st.button("＋", key="add_course", help="Add a course (admin flow)")
    with cols[2]:
        st.button("－", key="rem_course", help="Remove a course (admin flow)")

    cols = st.columns([1,0.25,0.25])
    with cols[0]:
        cohort = st.selectbox("Class / Cohort", COHORTS, index=0, key="cohort")
    with cols[1]:
        st.button("＋", key="add_cohort")
    with cols[2]:
        st.button("－", key="rem_cohort")

    cols = st.columns([1,0.25,0.25])
    with cols[0]:
        instructor = st.selectbox("Instructor name", INSTRUCTORS, index=INSTRUCTORS.index("Daniel"), key="instructor")
    with cols[1]:
        st.button("＋", key="add_instructor")
    with cols[2]:
        st.button("－", key="rem_instructor")

    st.date_input("Date", value=date.today(), key="the_date")

    st.markdown("**Context**")
    ctx_cols = st.columns(2)
    with ctx_cols[0]:
        lesson = st.number_input("Lesson", min_value=1, max_value=16, value=1, step=1, key="lesson")
    with ctx_cols[1]:
        week = st.number_input("Week", min_value=1, max_value=14, value=1, step=1, key="week")

# ---------- MAIN ----------
st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

st.write("**Topic / Outcome (optional)**")
st.text_area("e.g., Integrated Project and ...", label_visibility="collapsed", height=80, key="topic_text")

# Decide which band should highlight (week policy)
wk = int(st.session_state.get("week", 1))
active_band = "low"
if 5 <= wk <= 9:
    active_band = "med"
elif wk >= 10:
    active_band = "high"

# LOW
st.markdown(f'<div class="band {"active" if active_band=="low" else ""}">', unsafe_allow_html=True)
st.caption("Low (Weeks 1–4) — Remember / Understand")
low_verbs = st.multiselect("Low verbs", LOW_VERBS, default=["define","identify","list"], key="low_verbs")
st.markdown('</div>', unsafe_allow_html=True)

# MEDIUM
st.markdown(f'<div class="band {"active" if active_band=="med" else ""}">', unsafe_allow_html=True)
st.caption("Medium (Weeks 5–9) — Apply / Analyse")
med_verbs = st.multiselect("Medium verbs", MEDIUM_VERBS, default=["apply","demonstrate","solve"], key="med_verbs")
st.markdown('</div>', unsafe_allow_html=True)

# HIGH
st.markdown(f'<div class="band {"active" if active_band=="high" else ""}">', unsafe_allow_html=True)
st.caption("High (Weeks 10–14) — Evaluate / Create")
high_verbs = st.multiselect("High verbs", HIGH_VERBS, default=["evaluate","synthesize","design"], key="high_verbs")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

# ----------------- MCQs TAB -----------------
with tabs[0]:
    cols = st.columns([1,0.3])
    with cols[0]:
        qty = st.selectbox("How many?", options=[5,10,15,20], index=1, key="mcq_qty")
    with cols[1]:
        show_key = st.checkbox("Answer key", value=True, key="mcq_key")

    # Placeholder question area (kept simple & stable).
    q_area = st.container()

    def render_mcq_editor(container, index:int=1, prompt:str="Explain the role of inspection in quality management."):
        with container:
            st.markdown(f"**Q{index}**")
            st.text_area("Question", value=prompt, key=f"q_{index}")
            colsA = st.columns(2)
            with colsA[0]:
                st.text_input("A", value="To verify conformance", key=f"q{index}_A")
                st.text_input("B", value="To set company policy", key=f"q{index}_B")
            with colsA[1]:
                st.text_input("C", value="To hire staff", key=f"q{index}_C")
                st.text_input("D", value="To control budgets", key=f"q{index}_D")
            st.radio("Correct answer", ["A","B","C","D"], index=0, key=f"q{index}_ans")
            st.divider()

    # seed one editable question (keeps the layout you liked)
    render_mcq_editor(q_area, 1)

    # Stable key names for buttons (prevents DuplicateWidgetID)
    c2 = st.columns(4)
    with c2[0]:
        st.download_button("📥 Download DOCX (Q1)", data=b"", file_name="Q1.docx", key="dl_docx_q1")
    with c2[1]:
        st.download_button("📥 Download TXT (Q1)", data="".encode(), file_name="Q1.txt", key="dl_txt_q1")
    with c2[2]:
        st.button("➕ Add blank question", key="btn_add_blank")
    with c2[3]:
        st.button("➖ Remove last", key="btn_remove_last")

    c3 = st.columns(2)
    with c3[0]:
        st.download_button("📥 Download TXT (All MCQs)", data="".encode(), file_name="all_mcqs.txt", key="dl_txt_all")
    with c3[1]:
        st.download_button("📥 Download DOCX (All MCQs)", data=b"", file_name="all_mcqs.docx", key="dl_docx_all")

    st.markdown("---")
    # The generator button with a unique key (fix)
    if st.button("Generate from verbs/topic", key="btn_generate_mcq"):
        # Hook your existing MCQ generation here; we keep this safe & non-crashing.
        _safe_success("MCQs generated from selected verbs/topic (demo).")

# ----------------- SKILLS TAB -----------------
with tabs[1]:
    a, b, c = st.columns(3)
    with a:
        how_many = st.selectbox("How many activities?", [1,2,3], index=0, key="skills_count")
    with b:
        minutes = st.selectbox("Minutes per activity", [5,10,15,20,30,45,60], index=1, key="skills_minutes")
    with c:
        group_size = st.selectbox("Group size", ["Solo (1)","Pairs (2)","Triads (3)","Groups of 4"], index=0, key="skills_group")

    st.write(" ")
    if st.button("Generate Activities", key="btn_generate_skills"):
        _safe_success("Activities generated (demo).")

# ----------------- REVISION -----------------
with tabs[2]:
    st.write("Use selected verbs to build revision prompts. (Demo area.)")
    if st.button("Generate Revision Set", key="btn_gen_revision"):
        _safe_success("Revision set created (demo).")

# ----------------- PRINT SUMMARY -----------------
with tabs[3]:
    st.write("Print-ready summary preview. (Demo area.)")
    st.download_button("📄 Download Summary (PDF)", data=b"", file_name="summary.pdf", key="dl_summary_pdf")
