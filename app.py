# app.py — ADI Builder (Streamlit)
# Branded UI • Upload PDF/DOCX/PPTX • Lesson/Week extractor • Bloom + verbs • Difficulty scaler
# MCQs with per-question Passage/Image • Activities with steps • Exports: DOCX + RTF • Full Pack DOCX

from __future__ import annotations
import os, re
from io import BytesIO
from datetime import datetime
import streamlit as st

# ---------- Optional libs (graceful fallbacks) ----------
try:
    from docx import Document
    from docx.shared import Pt, Inches
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except Exception:
    PPTX_AVAILABLE = False

# ---------- Page + Brand ----------
st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")
ADI_GREEN = "#006C35"; ADI_BEIGE = "#C8B697"; ADI_SAND = "#D9CFC2"; ADI_BROWN = "#6B4E3D"; ADI_GRAY = "#F5F5F5"

st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%); }}
html,body,[class*="css"] {{ font-family: 'Segoe UI', Inter, Roboto, system-ui, -apple-system, sans-serif; }}
h1,h2,h3 {{ color:{ADI_GREEN}; font-weight: 750; }}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  border-bottom: 4px solid {ADI_GREEN}; color:{ADI_GREEN}; font-weight: 650;
}}
.banner {{ background:{ADI_GREEN}; color:#fff; padding:18px 28px; border-radius:12px; margin: 12px 0 18px; }}
.badge {{ display:inline-block; background:{ADI_BEIGE}; color:#222; padding:3px 9px; border-radius:9px; font-size:.8rem; margin-left:8px; }}
.card {{ background:#fff; border-radius:16px; box-shadow:0 6px 18px rgba(0,0,0,.06); padding:18px; border-left:6px solid {ADI_GREEN}; margin:14px 0; }}
.card h4 {{ margin:0 0 8px 0; color:{ADI_GREEN}; }}
.card .meta {{ color:#666; font-size:.9rem; margin-bottom:8px; }}
.card .label {{ font-weight:650; color:{ADI_BROWN}; }}
.stButton>button {{ background:{ADI_GREEN}; color:#fff; border:none; border-radius:10px; padding:8px 14px; font-weight:600; }}
.stButton>button:hover {{ background:#0c5a2f; }}
textarea {{ border:1.4px solid #c7c7c7 !important; border-radius:10px !important; padding:10px !important; background:#fff !important; }}
textarea:focus {{ outline:none !important; border-color:{ADI_GREEN} !important; box-shadow:0 0 0 2px rgba(0,108,53,.15); }}
.chips {{ display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 0; }}
.chip {{ background:{ADI_SAND}; color:{ADI_BROWN}; border:1px solid #e9e0d6; padding:4px 8px; border-radius:999px; font-size:.8rem; }}
.chip.more {{ background:#eee; color:#555; }}
.answer-badge {{ background:{ADI_GREEN}; color:#fff; border-radius:999px; padding:2px 8px; font-size:.8rem; }}
.btnrow {{ display:flex; gap:8px; flex-wrap:wrap; margin:6px 0 8px; }}

/* Difficulty slider */
.stSlider label p {{
  text-align: center !important;
  font-weight: 700 !important;
  color: {ADI_GREEN} !important;
}}
.stSlider > div[data-baseweb="slider"] > div {{
  background: {ADI_GREEN} !important;
}}
.stSlider [role="slider"] {{
  background: white !important;
  border: 2px solid {ADI_GREEN} !important;
}}

/* Verb chips in sidebar */
.stMultiSelect div[role="option"] {{
  background: {ADI_BEIGE} !important;
  color: {ADI_GREEN} !important;
  border-radius: 12px !important;
  padding: 4px 8px !important;
  font-weight: 600 !important;
}}
.stMultiSelect div[role="option"]:hover {{
  background: {ADI_GREEN} !important;
  color: white !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="banner">
  <h1>🎓 ADI Builder — Lesson Activities & Questions <span class="badge">Branded</span></h1>
</div>
""", unsafe_allow_html=True)
st.caption("Professional, branded, editable and export-ready.")

# ---- The rest of your code remains the same as in the previous full version ----
"""
