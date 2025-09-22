import io
import re
import random
from datetime import date

import streamlit as st

# File parsers
import fitz  # PyMuPDF
from pptx import Presentation
from docx import Document
from docx.shared import Pt

# --------------------------
# PAGE & THEME
# --------------------------
st.set_page_config(page_title="ADI Builder", page_icon="🧩", layout="wide")

ADI_GREEN = "#15563d"
ADI_BEIGE = "#b79e82"
ADI_SAND = "#efeae3"
ADI_BORDER = "#ccbca9"

CUSTOM_CSS = f"""
<style>
/* Page background */
html, body, [data-testid="stAppViewContainer"] {{
  background: linear-gradient(180deg, #fcfcfb 0%, {ADI_SAND} 100%) !important;
}}

/* Headings */
h1, h2, h3 {{ letter-spacing: .2px; }}
h1 {{
  font-size: 2.1rem !important;
  font-weight: 800 !important;
  color: {ADI_GREEN} !important;
}}
h2 {{
  font-size: 1.25rem !important;
  font-weight: 700 !important;
  color: #1f2725 !important;
  border-left: 6px solid {ADI_GREEN};
  padding-left: .5rem;
}}

/* Divider line */
.adi-line {{
  height: 3px;
  width: 100%;
  background: {ADI_GREEN};
  border-radius: 2px;
  margin: 8px 0 14px 0;
}}

/* Tabs underline -> ADI green */
[data-baseweb="tab-list"] > div[aria-selected="true"]::after {{
  background-color: {ADI_GREEN} !important;
  height: 3px !important;
}}

/* Inputs and selects */
[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea, input[type="text"] {{
  border: 1px solid {ADI_BORDER} !important;
  border-radius: 12px !important;
}}
[data-baseweb="select"]:focus-within > div,
div[data-baseweb="input"]:focus-within > div,
textarea:focus, input[type="text"]:focus {{
  box-shadow: 0 0 0 3px rgba(21, 86, 61, .15) !important;
  border-color: {ADI_GREEN} !important;
}}

/* Buttons */
.stButton > button {{
  background: {ADI_GREEN} !important;
  color: #fff !important;
  border: 1px solid {ADI_GREEN} !important;
  border-radius: 12px !important;
  padding: .6rem 1.05rem !important;
  font-weight: 600 !important;
}}
.stButton > button:hover {{ filter: brightness(.95); }}

/* File uploader */
div[data-testid="stFileUploadDropzone"] {{
  border: 2px dashed {ADI_GREEN} !important;
  border-radius: 12px !important;
  background: #fff !important;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------
# TEXT EXTRACTION
# --------------------------
def extract_text_from_pdf(file):
    text = []
    with fitz.open(stream=file.read(), filetype="pdf") as pdf:
        for page in pdf:
            text.append(page.get_text("text"))
    return "\n".join(text)

def extract_text_from_docx(file):
    data = file.read()
    bio = io.BytesIO(data)
    doc = Document(bio)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_pptx(file):
    data = file.read()
    prs = Presentation(io.BytesIO(data))
    slides = []
    for idx, slide in enumerate(prs.slides, start=1):
        bits = []
        for shp in slide.shapes:
            if hasattr(shp, "text"):
                bits.append(shp.text)
        if bits:
            slides.append(f"Slide {idx}: " + " ".join(bits))
    return "\n".join(slides)

def extract_text_from_upload(uploaded):
    if uploaded is None:
        return ""
    name = uploaded.name.lower()
    if name.endswith(".pdf"):
        uploaded.seek(0); return extract_text_from_pdf(uploaded)
    if name.endswith(".docx"):
        uploaded.seek(0); return extract_text_from_docx(uploaded)
    if name.endswith(".pptx"):
        uploaded.seek(0); return extract_text_from_pptx(uploaded)
    return ""

# --------------------------
# QUESTION GENERATION
# --------------------------
BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
DEFAULT_VERBS = {
    "Remember": ["define", "list", "recall"],
    "Understand": ["explain", "summarise", "describe"],
    "Apply": ["demonstrate", "use", "illustrate"],
    "Analyze": ["differentiate", "compare", "contrast"],
    "Evaluate": ["justify", "critique", "assess"],
    "Create": ["design", "develop", "compose"]
}

def guess_topics(raw_text, max_topics=10):
    sentences = re.split(r"[.!?\n]", raw_text)
    return [s.strip() for s in sentences if len(s.split()) > 4][:max_topics]

def make_mcq(topic, level, verb):
    stem = f"{verb.capitalize()} the key ideas of: {topic}"
    options = [
        f"Defines criteria for {topic}",
        f"Summarises {topic}",
        f"Compares {topic} with another concept",
        f"Unrelated statement"
    ]
    random.shuffle(options)
    return {"stem": stem, "level": level, "verb": verb,
            "options": options, "answer": options[0]}

def generate_mcqs(raw_text, levels, verbs_map, total, auto_verbs, level_mix):
    topics = guess_topics(raw_text, max_topics=20)
    if not topics:
        return []
    mcqs = []
    for i in range(total):
        level = random.choice(levels) if level_mix else levels[0]
        verb = random.choice(DEFAULT_VERBS[level]) if auto_verbs else random.choice(verbs_map.get(level, DEFAULT_VERBS[level]))
        topic = topics[i % len(topics)]
        mcqs.append(make_mcq(topic, level, verb))
    return mcqs

# --------------------------
# UI
# --------------------------
st.markdown("## ADI Builder")
st.caption("Upload eBooks/lessons, pick Bloom’s levels, and generate MCQs or activities.")

# Upload & schedule
col1, col2 = st.columns([1,1])
with col1:
    uploaded = st.file_uploader("Upload PDF / DOCX / PPTX", type=["pdf","docx","pptx"])
with col2:
    week = st.selectbox("Week", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson", list(range(1,5)), index=0)

pasted = st.text_area("Or paste content here", height=150)

st.markdown('<div class="adi-line"></div>', unsafe_allow_html=True)

tab_mcq, tab_act = st.tabs(["Knowledge MCQs", "Skills Activities"])

with tab_mcq:
    st.markdown("### Knowledge MCQs")
    st.markdown('<div class="adi-line"></div>', unsafe_allow_html=True)

    colA, colB, colC = st.columns([2,2,2])
    with colA:
        levels = st.multiselect("Bloom’s levels", BLOOM_LEVELS, default=["Understand","Apply"])
    with colB:
        auto_verbs = st.checkbox("Auto-select verbs", value=True)
    with colC:
        level_mix = st.checkbox("Mix levels", value=False)

    total_q = st.slider("Number of MCQs", 5, 10, 6)

    user_verbs = {}
    if not auto_verbs:
        for lev in levels:
            user_verbs[lev] = st.multiselect(
                f"Verbs for {lev}", DEFAULT_VERBS[lev], default=DEFAULT_VERBS[lev][:2]
            )

    if st.button("Generate MCQs"):
        raw_text = extract_text_from_upload(uploaded) if uploaded else pasted
        mcqs = generate_mcqs(raw_text, levels or ["Apply"], user_verbs, total_q, auto_verbs, level_mix)
        for i, q in enumerate(mcqs, start=1):
            st.markdown(f"**Q{i}. {q['stem']}**")
            for opt in q['options']:
                st.markdown(f"- {opt}")
            st.caption(f"Answer: {q['answer']}")
            st.markdown("---")

with tab_act:
    st.markdown("### Skills Activities")
    st.markdown('<div class="adi-line"></div>', unsafe_allow_html=True)

    count = st.slider("Number of activities", 1, 4, 2)
    duration = st.selectbox("Duration (mins)", list(range(10,65,5)), index=2)

    if st.button("Generate Activities"):
        raw_text = extract_text_from_upload(uploaded) if uploaded else pasted
        topics = guess_topics(raw_text, max_topics=count)
        for i, t in enumerate(topics, start=1):
            st.markdown(f"**{i}. ({duration} mins)** Practice activity on: {t}")
