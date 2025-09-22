import io
import re
import random
from datetime import date

import streamlit as st

# ---- File parsers ----
import fitz  # PyMuPDF
from pptx import Presentation
from docx import Document

# ======================
# PAGE & GLOBAL THEME
# ======================
st.set_page_config(page_title="ADI Builder", page_icon="🧩", layout="wide")

ADI_GREEN = "#15563d"     # deep green
ADI_BEIGE = "#b79e82"     # warm beige / brown tint
ADI_SAND  = "#efeae3"     # soft sandy background
ADI_TEXT  = "#1f2725"
ADI_BORDER= "#ccbca9"

CSS = f"""
<style>
/* ----- page background with gentle gradient ----- */
html, body, [data-testid="stAppViewContainer"] {{
  background: linear-gradient(180deg, #fcfcfb 0%, {ADI_SAND} 100%) !important;
  color: {ADI_TEXT};
}}

/* ----- headings ----- */
h1, h2, h3, h4 {{
  letter-spacing: .2px;
}}
h1 {{
  font-size: 2.0rem !important;
  font-weight: 800 !important;
  color: {ADI_GREEN} !important;
  margin-bottom: .3rem !important;
}}
h2 {{
  font-size: 1.15rem !important;
  font-weight: 700 !important;
  color: {ADI_TEXT} !important;
}}
/* section title row */
.adi-section-title {{
  display: flex; align-items:center; gap:.5rem; margin: .2rem 0 .6rem 0;
}}
.adi-line {{
  height: 3px; width: 100%; background: {ADI_GREEN}; border-radius: 2px; margin: 6px 0 12px 0;
}}

/* ----- cards / surface boxes ----- */
.adi-card {{
  background: #ffffff;
  border: 1px solid {ADI_BORDER};
  border-radius: 14px;
  padding: 14px 16px;
}}
.adi-tight {{
  padding-top: 8px; padding-bottom: 8px;
}}

/* ----- inputs/selects ----- */
[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea, input[type="text"] {{
  border: 1px solid {ADI_BORDER} !important;
  border-radius: 12px !important;
  background: #fff !important;
}}
[data-baseweb="select"]:focus-within > div,
div[data-baseweb="input"]:focus-within > div,
textarea:focus, input[type="text"]:focus {{
  box-shadow: 0 0 0 3px rgba(21,86,61,.15) !important;
  border-color: {ADI_GREEN} !important;
}}

/* ----- tags / chips (remove Streamlit red) ----- */
[data-baseweb="tag"] {{
  background: #f4efe9 !important;   /* soft beige chip */
  color: {ADI_TEXT} !important;
  border: 1px solid {ADI_BORDER} !important;
}}
[data-baseweb="tag"] svg {{ color: {ADI_BEIGE} !important; }}

/* ----- tabs: selected underline = ADI green ----- */
[data-baseweb="tab-list"] > div[aria-selected="true"]::after {{
  background-color: {ADI_GREEN} !important;
  height: 3px !important;
}}

/* ----- buttons ----- */
.stButton > button {{
  background: {ADI_GREEN} !important;
  color: #fff !important;
  border: 1px solid {ADI_GREEN} !important;
  border-radius: 12px !important;
  padding: .58rem 1.05rem !important;
  font-weight: 650 !important;
}}
.stButton > button:hover {{ filter: brightness(.96); }}

/* ----- file uploader with dashed green outline ----- */
div[data-testid="stFileUploadDropzone"] {{
  border: 2px dashed {ADI_GREEN} !important;
  border-radius: 14px !important;
  background: #fff !important;
}}
div[data-testid="stFileUploader"] label p {{
  color: {ADI_TEXT} !important;
}}

/* ----- slider accents to ADI green ----- */
[data-baseweb="slider"] div[role="slider"] {{
  background: {ADI_GREEN} !important;
}}
[data-baseweb="slider"] > div > div > div {{
  background: rgba(21,86,61,.25) !important;   /* track */
}}

/* compact radio/checkbox spacing */
.css-1pcexqc, .stMultiSelect, .stSelectbox {{
  margin-bottom: 0rem !important;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ======================
# TEXT EXTRACTION
# ======================
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
    if uploaded is None: return ""
    name = uploaded.name.lower()
    uploaded.seek(0)
    if name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded)
    if name.endswith(".docx"):
        return extract_text_from_docx(uploaded)
    if name.endswith(".pptx"):
        return extract_text_from_pptx(uploaded)
    return ""

# ======================
# GENERATION LOGIC
# ======================
BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
DEFAULT_VERBS = {
    "Remember":   ["define", "list", "recall"],
    "Understand": ["explain", "summarise", "describe"],
    "Apply":      ["demonstrate", "use", "illustrate"],
    "Analyze":    ["differentiate", "compare", "contrast"],
    "Evaluate":   ["justify", "critique", "assess"],
    "Create":     ["design", "develop", "compose"]
}

def guess_topics(raw_text, max_topics=12):
    # simple sentence split → keep 5+ word lines
    sentences = re.split(r"[.!?\n]", raw_text or "")
    picks = [s.strip() for s in sentences if len(s.split()) >= 5]
    return picks[:max_topics]

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
    if not topics: return []
    if not levels: levels = ["Apply"]

    mcqs = []
    for i in range(total):
        level = random.choice(levels) if level_mix else levels[0]
        if auto_verbs:
            verb = random.choice(DEFAULT_VERBS[level])
        else:
            pool = verbs_map.get(level, DEFAULT_VERBS[level])
            verb = random.choice(pool) if pool else random.choice(DEFAULT_VERBS[level])
        topic = topics[i % len(topics)]
        mcqs.append(make_mcq(topic, level, verb))
    return mcqs

# ======================
# UI LAYOUT
# ======================
st.markdown("<h1>ADI Builder</h1>", unsafe_allow_html=True)
st.caption("Create crisp knowledge questions and simple skills activities from your lesson materials.")

# ---- Upload + Schedule Row ----
with st.container():
    up_col, wk_col, ls_col = st.columns([2.2, .9, .9])
    with up_col:
        st.markdown('<div class="adi-card adi-tight">', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload PDF / DOCX / PPTX", type=["pdf","docx","pptx"])
        st.markdown('</div>', unsafe_allow_html=True)
    with wk_col:
        st.markdown('<div class="adi-card adi-tight">', unsafe_allow_html=True)
        week = st.selectbox("Week", list(range(1, 15)), index=0)
        st.markdown('</div>', unsafe_allow_html=True)
    with ls_col:
        st.markdown('<div class="adi-card adi-tight">', unsafe_allow_html=True)
        lesson = st.selectbox("Lesson", list(range(1, 5)), index=0)
        st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    pasted = st.text_area("Or paste content here", height=140, placeholder="Paste lesson notes or text from your eBook…")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="adi-line"></div>', unsafe_allow_html=True)

# ---- Tabs ----
tab_mcq, tab_act = st.tabs(["Knowledge MCQs", "Skills Activities"])

# ---------------- MCQs ----------------
with tab_mcq:
    st.markdown('<div class="adi-section-title"><h2>Knowledge MCQs</h2></div>', unsafe_allow_html=True)

    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.8, 1.2, 1.2])

    with c1:
        levels = st.multiselect("Bloom’s levels", BLOOM_LEVELS, default=["Understand", "Apply"])
    with c2:
        auto_verbs = st.checkbox("Auto-select verbs (balanced)", value=True)
    with c3:
        level_mix = st.checkbox("Mix levels", value=False)

    total_q = st.slider("Number of MCQs", 5, 10, 6)

    # Per-level verbs when auto-select is off
    user_verbs = {}
    if not auto_verbs:
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        st.markdown("**Choose verbs for selected levels**")
        for lev in levels:
            user_verbs[lev] = st.multiselect(
                f"Verbs for {lev}",
                DEFAULT_VERBS[lev],
                default=DEFAULT_VERBS[lev][:2],
                key=f"verbs_{lev}"
            )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="adi-card adi-tight">', unsafe_allow_html=True)
    if st.button("Generate MCQs"):
        raw_text = extract_text_from_upload(uploaded) if uploaded else pasted
        mcqs = generate_mcqs(raw_text, levels, user_verbs, total_q, auto_verbs, level_mix)

        if not mcqs:
            st.info("No content found. Upload a file or paste some lesson text above.")
        else:
            for i, q in enumerate(mcqs, start=1):
                st.markdown(f"**Q{i}. {q['stem']}**")
                for opt in q["options"]:
                    st.markdown(f"- {opt}")
                st.caption(f"Answer: {q['answer']}  •  Level: {q['level']}  •  Verb: {q['verb']}")
                st.markdown("---")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Activities ----------------
with tab_act:
    st.markdown('<div class="adi-section-title"><h2>Skills Activities</h2></div>', unsafe_allow_html=True)

    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    ac1, ac2 = st.columns([1.2, 1.2])
    with ac1:
        act_count = st.slider("Number of activities", 1, 4, 2)
    with ac2:
        act_duration = st.selectbox("Duration (mins)", list(range(10, 65, 5)), index=2)

    if st.button("Generate Activities"):
        raw_text = extract_text_from_upload(uploaded) if uploaded else pasted
        topics = guess_topics(raw_text, max_topics=act_count)
        if not topics:
            st.info("No content found. Upload a file or paste some lesson text above.")
        else:
            for i, t in enumerate(topics, start=1):
                st.markdown(f"**{i}. ({act_duration} mins)**  {t}")
                st.markdown("- Task: Work in pairs or small groups.")
                st.markdown("- Output: Short presentation or annotated diagram.")
                st.markdown("- Evidence: Photo or upload to LMS.")
                st.markdown("---")
    st.markdown('</div>', unsafe_allow_html=True)
