# app.py — ADI Learning Tracker (polished rebuild)

import io, os, re, base64, random
from io import BytesIO
from typing import List
import pandas as pd
import streamlit as st

# ---------- Page config ----------
st.set_page_config(page_title="ADI Learning Tracker", page_icon="🧭", layout="centered")

# ---------- ADI Theme / CSS ----------
CSS = r'''
<style>
:root{
  --adi:#245a34;  /* ADI green */
  --gold:#C8A85A; /* ADI gold  */
  --stone:#f6f8f7;
  --ink:#0f172a;
  --muted:#667085;
  --border:#e7ecea;
  --shadow:0 10px 30px rgba(36,90,52,0.10);
}
*{font-family: ui-sans-serif, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif;}
html, body { background:var(--stone); }
main .block-container { padding-top:.75rem; max-width: 980px; }

.h1{ font-size:30px; font-weight:900; color:var(--ink); margin:0 0 2px 0; letter-spacing:.2px; }
.small{ color:var(--muted); font-size:14px; }
hr{ border:none; height:1px; background:linear-gradient(90deg, rgba(36,90,52,0.25), rgba(36,90,52,0.06)); margin:.8rem 0 1rem; }

.card{ background:#fff; border:1px solid var(--border); border-radius:18px; padding:18px; box-shadow:var(--shadow); margin-bottom:1rem; }
.h2{ font-size:19px; font-weight:800; color:var(--ink); margin:0 0 10px 0; }

.stTabs [role="tablist"] { gap:.5rem; }
.stTabs [role="tab"] { font-weight:800; padding:.6rem .9rem; border-radius:12px 12px 0 0; }
.stTabs [data-baseweb="tab-highlight"] { height:3px; background:linear-gradient(90deg,var(--adi),var(--gold)) !important; }
.stTabs [aria-selected="true"] { color:var(--adi) !important; }

.stButton>button{
  background: linear-gradient(180deg, #2b6c40, var(--adi));
  color:#fff; border:1px solid #1f4e31; font-weight:800; border-radius:12px;
  padding:.62rem 1rem; box-shadow:0 8px 20px rgba(36,90,52,0.25);
}
.stButton>button:hover{ filter:brightness(1.06); }
.stButton>button:focus{ outline:3px solid rgba(36,90,52,0.28); }

.stNumberInput > div > div, .stTextInput > div > div, .stTextArea > div > div{
  border-radius:12px !important; border-color:#e4e9e6 !important;
}
.stTextArea textarea::placeholder{ color:#9aa6a0; }
[data-testid="stFileUploaderDropzone"]{
  border:2px dashed #dfe7e3 !important; border-radius:16px !important; background:#fff !important;
}
[data-testid="stFileUploaderDropzone"]:hover{ border-color:#cfe1d7 !important; background:#fbfdfc !important; }

/* Bloom chips */
.bloom-row{ display:flex; flex-wrap:wrap; gap:.5rem .6rem; margin:.35rem 0 1rem; }
.chip{
  display:inline-flex; align-items:center; justify-content:center; padding:6px 14px;
  border-radius:999px; font-size:13px; font-weight:800; letter-spacing:.2px; position:relative;
  box-shadow: 0 6px 16px rgba(0,0,0,0.08), inset 0 -2px 0 rgba(255,255,255,0.25);
  border:1px solid rgba(0,0,0,0.10);
}
.chip.low   { background:#245a34; color:#fff; border-color:#1a4628; }
.chip.med   { background:#C8A85A; color:#111; border-color:#9c874b; }
.chip.high  { background:#333;    color:#fff; border-color:#222; }
.chip.hl { outline:3px solid
