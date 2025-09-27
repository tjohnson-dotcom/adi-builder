# app.py — ADI Learning Tracker Question Generator (simple 4-step flow with style)

import io, os, re, base64, random
from io import BytesIO
from typing import List
import pandas as pd
import streamlit as st

# ---------- Optional parsers ----------
try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None
try:
    from pptx import Presentation
except Exception:
    Presentation = None

# ---------- Word export ----------
try:
    from docx import Document
    from docx.shared import Pt, Inches
except Exception:
    Document = None
    Pt = Inches = None

# ---------- Page config ----------
st.set_page_config(page_title="Learning Tracker Question Generator", page_icon="🧭", layout="centered")

# ---------- CSS theme ----------
CSS = '''
<style>
:root{
  --adi:#245a34;        /* ADI green */
  --gold:#C8A85A;       /* ADI gold */
  --ink:#0f172a;
  --muted:#667085;
  --bg:#f6f8f7;
  --card:#ffffff;
  --border:#e7ecea;
  --shadow:0 6px 28px rgba(36,90,52,0.08);
}
*{font-family: ui-sans-serif, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif;}
html, body { background:var(--bg); }
main .block-container { padding-top:.75rem; max-width: 980px; }

.h1{ font-size:28px; font-weight:900; color:var(--ink); margin:0 0 2px 0; }
.small{ color:var(--muted); }
hr{ border:none; height:1px; background:linear-gradient(90deg, rgba(36,90,52,0.25), rgba(36,90,52,0.06)); margin:.9rem 0 1.1rem; }

.card{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:18px; box-shadow: var(--shadow); }
.h2{ font-size:19px; font-weight:800; color:var(--ink); margin:2px 0 10px 0; }

.notice{ padding:14px; border-radius:14px; border:1px dashed #dae4de; background:#fff; }
.callout{ padding:14px; border-radius:14px; background:#eef6ff; border:1px solid #dbeafe; margin:10px 0; }
.next-tip{ margin-top:14px; padding:12px 14px; border-radius:12px; background:linear-gradient(180deg,#f4faf6,#f7fbf8); border:1px solid #dfece6; color:#0b3d22; }

.stTabs [role="tablist"] { gap:.5rem; }
.stTabs [role="tab"] { font-weight:800; padding:.6rem .8rem; border-radius:10px 10px 0 0; }
.stTabs [data-baseweb="tab-highlight"]{ height:3px; background:linear-gradient(90deg,var(--adi),var(--gold)) !important; }
.stTabs [aria-selected="true"] { color: var(--adi) !important; }

.stButton>button{
  background: linear-gradient(180deg, #2a6a3f, var(--adi));
  color:#fff; border:1px solid #1e4e2e; font-weight:800;
  border-radius:12px; padding:.6rem 1rem; box-shadow:0 6px 18px rgba(36,90,52,0.20);
}
.stButton>button:hover{ filter: brightness(1.05); }
.stButton>button:focus{ outline:3px solid rgba(36,90,52,0.25); }

.stNumberInput > div > div, .stTextInput > div > div, .stTextArea > div > div{
  border-radius:12px !important; border-color:#e4e9e6 !important;
}
.stNumberInput input, .stTextInput input, .stTextArea textarea{ border-radius:10px !important; }
.stTextArea textarea::placeholder{ color:#9aa6a0; }

[data-testid="stFileUploaderDropzone"]{
  border:2px dashed #dfe7e3 !important; border-radius:14px !important; background:#fff !important;
}
[data-testid="stFileUploaderDropzone"]:hover{
  border-color:#cfe1d7 !important; background:#fbfdfc !important;
}

.badge{ display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border-radius:999px; color:#fff; font-weight:800; font-size:12px; margin-right:10px; }
.badge.g{ background:#245a34; } .badge.a{ background:#d97706; } .badge.r{ background:#b91c1c; }
.qcard{ border:1px solid var(--border); border-radius:12px; padding:10px 12px; background:#fff; }
.qitem{ display:flex; gap:10px; align-items:flex-start; padding:6px 0; }

.stDownloadButton>button{
  background:linear-gradient(180deg,#fafafa,#f1f5f2); color:#1b1b1b; border:1px solid #e1e7e3;
  border-radius:12px; font-weight:800;
}
.stDownloadButton>button:hover{ filter:brightness(0.98); }
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)
