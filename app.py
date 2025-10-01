
# app_v1_4.py — ADI Builder (broad action bar)
import os
import io
import time
import tempfile
from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF
from pptx import Presentation
from docx import Document
from docx.shared import Pt, Inches
import streamlit as st

st.set_page_config(page_title="ADI Builder", layout="wide", page_icon="📘")

PRIMARY_GREEN = "#245a34"
ACCENT_GOLD = "#C8A85A"
STONE_BG = "#f4f1ec"

CUSTOM_CSS = f"""
<style>
header {{ height: 0px; }}
.block-container {{ padding-top: 0.75rem; }}
:root {{
  --adi-green: {PRIMARY_GREEN};
  --adi-gold: {ACCENT_GOLD};
  --adi-stone: {STONE_BG};
}}
section[data-testid="stSidebar"] {{ background: var(--adi-stone); }}
.stButton > button {{
  border-radius: 14px; padding: .5rem .9rem;
  border: 1px solid var(--adi-green);
  background: white; color: var(--adi-green);
  box-shadow: 0 1px 0 rgba(0,0,0,.04);
}}
.stButton > button:hover {{ background: var(--adi-green); color: white; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
.stTabs [data-baseweb="tab"] {{ border: 1px solid #ddd; border-radius: 999px; padding: .35rem .9rem; }}
.stTextInput > div > div > input, .stTextArea textarea {{
  background: #faf8f5; border-radius: 12px; border: 1px solid #ddd;
}}
.action-bar {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: .25rem 0 1rem; }}
.action-bar .stButton>button {{ border: 1px solid var(--adi-gold); }}
small.hint {{ color: #666; }}
</style>
"""
st.write(CUSTOM_CSS, unsafe_allow_html=True)

with st.sidebar:
    logo_path = Path("Logo.png")
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    st.markdown("### ADI Builder")
    lesson = st.radio("Lesson", [1,2,3,4,5], index=0, horizontal=True)
    week = st.radio("Week", list(range(1,15)), index=0, horizontal=True)
    st.caption("Bloom policy: Weeks 1-4 Low, 5-9 Medium, 10-14 High")

TMP_DIR = Path("/tmp/adi_builder"); TMP_DIR.mkdir(exist_ok=True)

def save_to_tmp(name: str, data: bytes) -> Path:
    path = TMP_DIR / name; path.write_bytes(data); return path

def extract_text_from_pdf(fbytes: bytes) -> str:
    text = []
    with fitz.open(stream=io.BytesIO(fbytes), filetype="pdf") as doc:
        for page in doc:
            text.append(page.get_text())
    return "\n".join(text)

def extract_text_from_pptx(fbytes: bytes) -> str:
    bio = io.BytesIO(fbytes); prs = Presentation(bio)
    chunks = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                chunks.append(shape.text)
    return "\n".join(chunks)

def extract_text_from_docx(fbytes: bytes) -> str:
    bio = io.BytesIO(fbytes); doc = Document(bio)
    return "\n".join(p.text for p in doc.paragraphs)

def guess_extract(name: str, fbytes: bytes) -> str:
    lower = name.lower()
    if lower.endswith(".pdf"): return extract_text_from_pdf(fbytes)
    if lower.endswith(".pptx"): return extract_text_from_pptx(fbytes)
    if lower.endswith(".docx"): return extract_text_from_docx(fbytes)
    try: return fbytes.decode("utf-8", errors="ignore")
    except Exception: return ""

def bloom_level_for_week(w:int) -> str:
    if 1 <= w <= 4: return "Low"
    if 5 <= w <= 9: return "Medium"
    return "High"

LOW_VERBS = ["list", "define", "identify", "recall", "label"]
MED_VERBS = ["explain", "summarize", "classify", "compare", "apply"]
HIGH_VERBS = ["analyze", "evaluate", "design", "hypothesize", "create"]

def verbs_for_week(w:int) -> List[str]:
    lvl = bloom_level_for_week(w)
    if lvl == "Low": return LOW_VERBS
    if lvl == "Medium": return MED_VERBS
    return HIGH_VERBS

def generate_mcqs(source_text: str, n:int=10, week:int=1) -> List[Tuple[str, List[str], int]]:
    import random
    lines = [ln.strip() for ln in source_text.splitlines() if ln.strip()]
    chosen = lines[: max(5, min(60, len(lines)))]
    v = verbs_for_week(week)
    out = []
    if not chosen: chosen = [f"Sample fact about the topic to {v[0]}"]
    for i in range(n):
        base = chosen[i % len(chosen)]
        prompt = f"{v[i % len(v)].capitalize()} the correct statement: {base}"
        correct = base
        wrongs = [
            base[::-1][: max(8, min(40, len(base)))],
            base.upper()[: max(8, min(40, len(base)))],
            "None of the above" if i % 3 == 0 else base.replace(" the ", " a "),
        ]
        options = [correct] + wrongs
        random.shuffle(options)
        answer_idx = options.index(correct)
        out.append((prompt, options, answer_idx))
    return out

def mcqs_to_gift(mcqs: List[Tuple[str, List[str], int]]) -> str:
    lines = []
    for i, (q, opts, correct_index) in enumerate(mcqs, 1):
        lines.append(f"::Q{i}:: {q} {{")
        for j, opt in enumerate(opts):
            prefix = "=" if j == correct_index else "~"
            lines.append(f"  {prefix}{opt}")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)

def export_mcqs_docx(mcqs) -> bytes:
    doc = Document(); doc.add_heading("MCQs", 0)
    for i, (q, opts, correct_idx) in enumerate(mcqs, 1):
        doc.add_paragraph(f"{i}. {q}")
        for j, opt in enumerate(opts):
            letter = "ABCD"[j] if j < 4 else f"({j+1})"
            p = doc.add_paragraph(f"{letter}. {opt}")
            p.paragraph_format.left_indent = Inches(0.25)
        doc.add_paragraph(f"Answer: {'ABCD'[correct_idx]}"); doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def generate_activities(source_text: str, count:int=5, week:int=1) -> List[str]:
    verbs = verbs_for_week(week)
    acts = [f"{i+1}. Students will {verbs[i % len(verbs)]} using the provided topic excerpt." for i in range(count)]
    return acts

def export_lesson_plan_docx(activities: List[str]) -> bytes:
    doc = Document(); doc.add_heading("Lesson Plan (Activities)", 0)
    for line in activities: doc.add_paragraph(line)
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_ebook_docx(source_text: str) -> bytes:
    doc = Document(); doc.add_heading("E-Book", 0)
    for para in source_text.split("\n\n"): doc.add_paragraph(para.strip())
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

st.title("ADI Builder")
st.caption("Green UI - MCQs - Activities - Revision - .docx & Moodle GIFT exports")

uploaded = st.file_uploader("Upload your source (PDF, PPTX, DOCX, or TXT)", type=["pdf","pptx","docx","txt"])
colL, colR = st.columns([1,2])
with colL:
    use_text_clicked = st.button("Use uploaded text")
with colR:
    default_count = st.number_input("Default MCQ count", 5, 50, 10)

if "source_text" not in st.session_state: st.session_state.source_text = ""

if uploaded is not None:
    tmp_path = save_to_tmp(uploaded.name, uploaded.getvalue())
    st.info(f"Saved upload to {tmp_path}")
    if use_text_clicked:
        with st.spinner("Extracting text..."):
            st.session_state.source_text = guess_extract(uploaded.name, uploaded.getvalue())
            st.success("Text ready.")

source_text = st.session_state.source_text
if not source_text:
    st.warning("No source text yet. Upload a file and click Use uploaded text.")
else:
    st.text_area("Source preview", source_text[:5000], height=220)

# Action bar (broad)
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Export Lesson Plan (.docx)"):
        acts = generate_activities(source_text, 8, week)
        st.download_button("Download Lesson Plan (.docx)", export_lesson_plan_docx(acts), file_name="lesson_plan.docx")
with col2:
    if st.button("Export E-Book (.docx)"):
        st.download_button("Download E-Book (.docx)", export_ebook_docx(source_text), file_name="ebook.docx")
with col3:
    if st.button("Export Moodle (.gift)"):
        mcqs = generate_mcqs(source_text, default_count, week)
        gift = mcqs_to_gift(mcqs)
        st.download_button("Download Moodle (.gift)", gift, file_name="mcqs.gift")

tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

with tabs[0]:
    st.subheader("Generate MCQs")
    n = st.slider("How many MCQs?", 5, 40, default_count)
    if st.button("Generate MCQs"):
        mcqs = generate_mcqs(source_text, n, week)
        for i, (q, opts, ans) in enumerate(mcqs, 1):
            st.markdown(f"**{i}. {q}**")
            for j, opt in enumerate(opts):
                st.write(f"- {opt}")
            st.caption(f"Answer: {chr(65+ans)}")
            st.divider()
        docx_bytes = export_mcqs_docx(mcqs)
        gift_text = mcqs_to_gift(mcqs)
        st.download_button("Download .docx", data=docx_bytes, file_name="mcqs.docx")
        st.download_button("Download Moodle (.gift)", data=gift_text, file_name="mcqs.gift")

with tabs[1]:
    st.subheader("Generate Activities")
    c = st.slider("How many activities?", 3, 15, 6)
    if st.button("Generate Activities"):
        acts = generate_activities(source_text, c, week)
        for line in acts: st.write(line)
        st.download_button("Download Lesson Plan (.docx)", export_lesson_plan_docx(acts), file_name="lesson_plan.docx")

with tabs[2]:
    st.subheader("Revision / Notes")
    notes = st.text_area("Draft quick revision notes here:", "", height=200, placeholder="Key concepts, reminders, examples...")
    if st.button("Export Revision Notes (.docx)"):
        doc = Document(); doc.add_heading("Revision Notes", 0)
        for para in notes.split("\n"): doc.add_paragraph(para)
        bio = io.BytesIO(); doc.save(bio)
        st.download_button("Download Revision (.docx)", bio.getvalue(), file_name="revision.docx")
