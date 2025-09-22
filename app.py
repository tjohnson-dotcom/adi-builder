# app.py — ADI Builder (Streamlit, Branded + Upload + Lesson/Week Extractor + Bloom Verbs + Full Exports)
# Sleek, professional, and staff-friendly. Upload eBook/Plan/PPT → pick Lesson/Week → edit in white box → export.

from __future__ import annotations
import streamlit as st
from io import BytesIO
from datetime import datetime
import re

# === Optional libraries and graceful fallbacks ===
try:
    from docx import Document
    from docx.shared import Pt
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

st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")

# === ADI Brand Colors ===
ADI_GREEN = "#006C35"
ADI_BEIGE = "#C8B697"
ADI_SAND  = "#D9CFC2"
ADI_BROWN = "#6B4E3D"
ADI_GRAY  = "#F5F5F5"

CUSTOM_CSS = f"""
<style>
.stApp {{ background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%); }}
html, body, [class*="css"] {{ font-family: 'Segoe UI', Roboto, Inter, sans-serif; }}
h1, h2, h3 {{ font-weight: 700; color: {ADI_GREEN}; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  border-bottom: 4px solid {ADI_GREEN};
  font-weight: 600; color: {ADI_GREEN};
}}

/* Banner */
.banner {{ background: {ADI_GREEN}; color: white; padding: 18px 28px; border-radius: 0 0 12px 12px; display: flex; align-items: center; justify-content: flex-start; gap:12px; margin-bottom: 18px; }}
.banner h1 {{ color: white !important; font-size: 1.6rem; margin: 0; }}

/* Cards */
.card {{ background:#fff; border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,0.08); padding:20px; margin:14px 0; border-left:6px solid {ADI_GREEN}; }}
.card h4 {{ margin:0 0 10px 0; color:{ADI_GREEN}; }}
.card .meta {{ color:#666; font-size:0.9rem; margin-bottom:8px; }}
.card .label {{ font-weight:600; color:{ADI_BROWN}; }}

/* Toolbar */
.toolbar {{ display:flex; justify-content:flex-end; gap:12px; margin:16px 0; flex-wrap: wrap; }}

/* Buttons */
.stButton>button {{ background:{ADI_GREEN}; color:#fff; border:none; border-radius:10px; padding:8px 14px; font-weight:600; font-size:0.9rem; white-space:nowrap; transition:background .2s; }}
.stButton>button:hover {{ background:{ADI_BROWN}; }}

/* White editable areas */
textarea {{ border:1.5px solid #bbb !important; border-radius:10px !important; padding:10px !important; background:#fff !important; }}
textarea:focus {{ outline:none !important; border-color:{ADI_GREEN} !important; box-shadow:0 0 0 2px rgba(0,108,53,0.15); }}

/* Badges + Chips */
.badge {{ display:inline-block; padding:4px 8px; background:{ADI_BEIGE}; border-radius:8px; font-size:.8rem; color:#333; }}
.chips {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }}
.chip {{ background:{ADI_SAND}; color:{ADI_BROWN}; border:1px solid #e7ddd2; padding:4px 8px; border-radius:999px; font-size:.8rem; }}
.chip.more {{ background:#f0ebe4; color:#555; }}

/* Multiselect chips */
.stMultiSelect [data-baseweb="tag"] {{
  background: {ADI_GREEN};
  color: #fff;
  border-radius: 999px;
}}
.stMultiSelect [data-baseweb="tag"] svg {{ display:none; }}

/* Inline pill buttons */
.btn-row {{ display:flex; gap:10px; }}
.btn-row .stButton>button {{ border-radius:999px; }}

/* Answer badge */
.answer-badge {{ display:inline-block; background:{ADI_GREEN}; color:#fff; padding:2px 8px; border-radius:999px; font-size:0.8rem; }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# === Banner with ADI logo (sidebar only) ===
st.sidebar.image("https://i.ibb.co/7y6h3F2/adi-logo.png", width=180)
st.markdown(
    f"""
    <div class='banner'>
        <h1>🎓 ADI Builder — Lesson Activities & Questions <span class='badge'>Branded</span></h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Professional, branded, editable and export-ready.")

# === Bloom's Taxonomy (verbs catalog) ===
VERBS_CATALOG = {
    "Remember": ["define","duplicate","label","list","match","memorize","name","omit","recall","recognize","record","repeat","reproduce","state"],
    "Understand": ["classify","convert","defend","describe","discuss","distinguish","estimate","explain","express","identify","indicate","locate","report","restate","review","select","translate","summarize"],
    "Apply": ["apply","change","choose","compute","demonstrate","discover","dramatize","employ","illustrate","interpret","manipulate","modify","operate","practice","schedule","sketch","solve","use"],
    "Analyze": ["analyze","appraise","break down","calculate","categorize","compare","contrast","criticize","debate","deduce","diagram","differentiate","discriminate","examine","experiment","infer","inspect","inventory","question","test"],
    "Evaluate": ["appraise","argue","assess","attach value","choose","compare","conclude","contrast","criticize","decide","defend","estimate","evaluate","explain","grade","judge","justify","measure","predict","rate","revise","score","select","support","value"],
    "Create": ["arrange","assemble","categorize","collect","combine","compose","construct","create","design","develop","explain solution","formulate","generate","manage","organize","plan","prepare","propose","rearrange","reconstruct","relate","rewrite","set up","summarize","write"],
}

# === Export: Full Pack (MCQs + Activities) ===
if DOCX_AVAILABLE:
    if st.session_state.get("mcq_blocks") or st.session_state.get("activities_list"):
        st.markdown("<hr>")
        st.subheader("Export — Full Pack")
        st.caption("One Word document containing MCQs and Activities, ready to use or upload to Moodle.")

        def build_full_pack_docx(mcq_blocks, activities_list):
            doc = Document()
            s = doc.styles['Normal']; s.font.name='Calibri'; s.font.size = Pt(11)
            doc.add_heading('ADI Builder — Lesson Pack', level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))

            # MCQs section
            if mcq_blocks:
                doc.add_heading('Section A — Knowledge MCQs', level=1)
                for idx, blk in enumerate(mcq_blocks, 1):
                    lines = [l.rstrip() for l in blk.splitlines() if l.strip()]
                    if not lines:
                        continue
                    stem = lines[0]
                    options = [l for l in lines[1:] if re.match(r'^[A-D]\)', l)]
                    ans_line = next((l for l in lines if l.lower().startswith('answer:')), '')
                    doc.add_heading(f'Question {idx}', level=2)
                    doc.add_paragraph(stem)
                    for opt in options:
                        doc.add_paragraph(opt, style='List Bullet')
                    if ans_line:
                        p = doc.add_paragraph(ans_line)
                        if p.runs:
                            p.runs[0].italic = True
                    doc.add_paragraph('')

            # Activities section
            if activities_list:
                doc.add_heading('Section B — Skills Activities', level=1)
                for block in activities_list:
                    lines = [l.rstrip() for l in block.split('\n')]
                    title = next((l for l in lines if l.startswith('Activity ')), 'Activity')
                    doc.add_heading(title, level=2)
                    def add_sec(label):
                        try:
                            idx = next(i for i,l in enumerate(lines) if l.lower().startswith(label))
                        except StopIteration:
                            return
                        doc.add_heading(label[:-1].title(), level=3)
                        i = idx+1
                        while i < len(lines) and lines[i].strip():
                            txt = lines[i].strip()
                            if re.match(r'^(\d+\)|- )', txt):
                                style = 'List Number' if txt[0].isdigit() else 'List Bullet'
                                doc.add_paragraph(re.sub(r'^(\d+\)|- )\s*','',txt), style=style)
                            else:
                                doc.add_paragraph(txt)
                            i += 1
                    for sec in ['context:','steps:','output:','evidence:','success criteria:']:
                        add_sec(sec)
                    doc.add_paragraph('')
            bio = BytesIO(); doc.save(bio); bio.seek(0)
            return bio.getvalue()

        full_docx = build_full_pack_docx(st.session_state.get('mcq_blocks', []), st.session_state.get('activities_list', []))
        if full_docx:
            st.download_button("🧾 Full Pack (.docx)", full_docx, file_name="adi_lesson_pack.docx")
