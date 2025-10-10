
import io
import random
from datetime import datetime
from typing import List, Dict

import streamlit as st

# ------- COLORS -------
ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
STONE_BG = "#F3F3F0"

st.set_page_config(page_title="ADI Builder", page_icon="🧰", layout="wide")

# ------- OPTIONAL DEPS (fail-soft) -------
try:
    from pptx import Presentation  # python-pptx
except Exception:
    Presentation = None
try:
    from docx import Document      # python-docx
    from docx.shared import Pt
except Exception:
    Document = None

# ------- STYLE: MATCH THE MINIMAL MOCK -------
st.markdown(f"""
<style>
:root {{ --adi-green:{ADI_GREEN}; --adi-gold:{ADI_GOLD}; --stone:{STONE_BG}; }}
.block-container {{ padding-top: 1.25rem; max-width: 1400px; }}

h1, h2, h3, h4 {{ color: var(--adi-green) !important; }}
small.badge {{
  display:inline-block; padding:.15rem .5rem; border:1px solid var(--adi-green);
  border-radius:.5rem; color:var(--adi-green); background:#fff; font-weight:600;
}}
.hr {{ border:0; height:1px; background:#ececec; margin:1rem 0; }}

/* Buttons: light outline style by default, strong for primary */
.stButton>button {{
  border-radius: .6rem; padding:.55rem 1rem; border:1px solid #cfd3cf;
  background:#fff; color:#111; font-weight:600;
}}
.stButton>button[kind="primary"] {{
  background: var(--adi-green); color:#fff; border-color: var(--adi-green);
}}

/* Sidebar nav */
.sidebar-title {{ font-weight:800; color:#111; }}
.nav-section {{ font-size:.9rem; color:#6a6a6a; margin:.25rem 0 .35rem; }}
.week-btn button {{ width:100%; margin-bottom:.4rem; border-radius:999px; }}
.add-btn button {{ width:100%; border-radius:.6rem; }}

/* Inputs rounded */
input, textarea, .stSelectbox, .stMultiSelect {{ border-radius:.6rem !important; }}
</style>
""", unsafe_allow_html=True)

# ------- BLOOM MAP -------
LOW_VERBS = ["define", "identify", "list", "state", "recognize"]
MED_VERBS = ["explain", "compare", "apply", "classify", "illustrate"]
HIGH_VERBS = ["analyze", "evaluate", "design", "critique", "hypothesize"]

def bloom_for_week(week:int)->str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    if 10 <= week <= 14: return "High"
    return "Medium"

def verbs(level:str):
    return {"Low":LOW_VERBS, "Medium":MED_VERBS, "High":HIGH_VERBS}.get(level, MED_VERBS)

# ------- PPTX -> topics (titles + bullets) -------

def extract_topics(file) -> List[str]:
    if not file or Presentation is None: return []
    prs = Presentation(file)
    seen = []
    for s in prs.slides:
        if s.shapes.title and s.shapes.title.text:
            t = s.shapes.title.text.strip()
            if t and t not in seen: seen.append(t)
        for sh in s.shapes:
            if hasattr(sh, "text_frame") and sh.text_frame:
                for p in sh.text_frame.paragraphs:
                    txt = (p.text or "").strip()
                    if 3 <= len(txt) <= 80 and txt not in seen:
                        seen.append(txt)
        if len(seen) > 40: break
    # light clean
    out = []
    for s in seen:
        s = " ".join(s.split()).strip("•-–—: ")
        if s and s not in out: out.append(s)
    return out[:25]

# ------- MCQ -------

def make_mcq(topic:str, level:str)->Dict:
    stem = f"{random.choice(verbs(level)).cap
