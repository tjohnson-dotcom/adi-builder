import streamlit as st
from pathlib import Path
import random

# ---------------------------------
# Page setup
# ---------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="🧩", layout="wide")

# Brand colors
BRAND  = "#15563d"   # ADI green
ACCENT = "#b79e82"   # beige
BG     = "#f7f8f7"   # light background

# ---------------------------------
# CSS Styling
# ---------------------------------
CUSTOM_CSS = f"""
<style>
:root {{
  --brand: {BRAND};
  --accent: {ACCENT};
  --bg: {BG};
  --ink: #1d252d;
}}

html, body, .stApp {{ background: var(--bg); color: var(--ink); }}

h1, h2, h3, h4 {{ color: var(--brand); font-weight: 800; letter-spacing: .2px; }}
h1 {{ font-size: 2.2rem; }}
h2 {{ font-size: 1.55rem; }}
h3 {{ font-size: 1.2rem; }}

.brandband {{
  margin: -1rem -1rem 1rem -1rem;
  padding: 22px 28px;
  background: linear-gradient(90deg, var(--brand), #0e3d2a 60%, var(--accent));
  color: #fff;
  border-bottom: 3px solid rgba(0,0,0,.06);
}}
.brandtitle {{ font-weight: 900; font-size: 1.8rem; line-height: 1.15; }}
.brandsub   {{ opacity:.95; font-weight:600; margin-top:.15rem; }}

.card {{
  background: #fff;
  border-radius: 16px;
  padding: 18px;
  border: 1px solid rgba(13,32,23,.06);
  box-shadow: 0 10px 24px rgba(0,0,0,.04);
  transition: transform .12s ease, box-shadow .12s ease;
}}
.card:hover {{ transform: translateY(-2px); box-shadow: 0 16px 32px rgba(0,0,0,.06); }}

.stButton>button {{
  background: var(--brand);
  color: #fff !important;
  font-weight: 700; letter-spacing: .3px;
  border-radius: 12px; border: 0;
  padding: .62rem 1.15rem;
  box-shadow: 0 6px 14px rgba(21,86,61,.18);
}}
.stButton>button:hover {{ filter: brightness(.96); transform: translateY(-1px); }}
.stButton>button:active {{ transform: translateY(0); }}

.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea textarea {{
  border-radius: 12px !important;
  border-color: rgba(13,32,23,.18) !important;
}}
.stSlider [data-baseweb="slider"]>div>div {{ background: var(--brand); }}
.stSlider [role="slider"] {{ box-shadow: 0 0 0 4px rgba(21,86,61,.15) !important; }}

.stTabs [data-baseweb="tab-list"] {{ gap:.25rem; }}
.stTabs [data-baseweb="tab"] {{
  font-weight: 700;
  border-radius: 10px 10px 0 0;
  padding: .6rem 1rem;
  background: #eef2ef;
  color: #14382a;
}}
.stTabs [aria-selected="true"] {{
  background: #fff !important; color: var(--brand) !important;
  border-bottom: 3px solid var(--accent);
}}

.small  {{ color:#5d6a6b; font-size:.86rem }}
.badge  {{
  display:inline-block; background: var(--accent); color:#fff;
  padding:.12rem .55rem; border-radius: 10px; font-size:.78rem; margin-left:.4rem;
}}
.divider {{ height: 1px; background: rgba(13,32,23,.08); margin: 12px 0; }}
</style>
"""

# Inject CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------
# Header with branding
# ---------------------------------
st.markdown(
    """
    <div class="brandband">
      <div class="brandtitle">ADI Builder <span class="badge">v1.0</span></div>
      <div class="brandsub">A clean, staff-friendly tool to generate questions and skills activities</div>
    </div>
    """,
    unsafe_allow_html=True,
)

logo_path = Path(__file__).with_name("logo.png")
if logo_path.exists():
    cols = st.columns([1,3])
    with cols[0]:
        st.image(str(logo_path), width=120)
    with cols[1]:
        st.markdown(
            "<div class='card'><b>Status:</b> Ready · Upload lesson (PDF/DOCX/PPTX), pick week & lesson, then generate.</div>",
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        "<div class='card'><b>Status:</b> Ready · Upload lesson (PDF/DOCX/PPTX), pick week & lesson, then generate.</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------------------------------
# UI: Upload + Schedule
# ---------------------------------
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("1) Upload lesson / eBook (drag & drop)")
    upload = st.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"])

with col2:
    st.subheader("2) Schedule")
    week = st.selectbox("Week (1–14)", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson (1–4)", list(range(1,5)), index=0)
    st.write(f"📅 Selected: Week {week}, Lesson {lesson}")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------------------------------
# Bloom’s taxonomy
# ---------------------------------
st.subheader("Generate crisp, staff-ready MCQs")
blooms = {
    "Remember": ["define", "list", "recall", "state"],
    "Understand": ["explain", "summarise", "describe", "classify"],
    "Apply": ["demonstrate", "use", "illustrate", "solve"],
    "Analyse": ["differentiate", "compare", "contrast", "categorise"],
    "Evaluate": ["judge", "critique", "assess", "recommend"],
    "Create": ["design", "develop", "construct", "propose"],
}
level = st.selectbox("Bloom’s level:", list(blooms.keys()), index=2)
verb = st.selectbox("Choose a Bloom’s verb:", blooms[level])

count = st.slider("Total MCQs", 5, 10, 6)
extra_verbs = st.text_input("Extra verbs (optional, comma-separated)")

# ---------------------------------
# Generate MCQs (dummy example)
# ---------------------------------
if st.button("Generate MCQs"):
    verbs = blooms[level] + [v.strip() for v in extra_verbs.split(",") if v.strip()]
    questions = []
    for i in range(count):
        q = f"Q{i+1}: {random.choice(verbs).capitalize()} the main idea of Week {week}, Lesson {lesson}."
        questions.append(q)

    st.success(f"Generated {len(questions)} questions:")
    for q in questions:
        st.markdown(f"- {q}")
