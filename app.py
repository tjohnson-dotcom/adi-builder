# app.py — ADI Builder (Streamlit, Branded, with ADI Bloom Policy Auto-Picker)

from __future__ import annotations
import streamlit as st
from io import BytesIO
from datetime import datetime
import os, random

try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")

# ---- ADI COLORS ----
ADI_GREEN = "#006C35"
ADI_BEIGE = "#C8B697"
ADI_SAND  = "#D9CFC2"
ADI_BROWN = "#6B4E3D"
ADI_GRAY  = "#F5F5F5"

# ---- BLOOM VERBS (from ADI policy doc) ----
ADI_LOW  = ["define","identify","list","recall"]
ADI_MED  = ["apply","demonstrate","interpret","compare"]
ADI_HIGH = ["analyze","evaluate","justify","design"]

# ---- CSS Styling ----
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%); }}
html,body,[class*="css"] {{ font-family: 'Segoe UI', Inter, Roboto, system-ui, sans-serif; }}
h1,h2,h3 {{ color:{ADI_GREEN}; font-weight: 750; }}

.banner {{ background:{ADI_GREEN}; color:#fff; padding:18px 28px; border-radius:12px; margin:12px 0 18px; }}
.badge  {{ display:inline-block; background:{ADI_BEIGE}; color:#222; padding:3px 9px; border-radius:9px; font-size:.8rem; margin-left:8px; }}

/* Inputs */
textarea,
.stTextInput > div > div > input,
.stNumberInput input,
.stSelectbox > div > div > div,
.stFileUploader label {{
  border: 2px solid #2e7d57 !important;
  border-radius: 10px !important;
  background: #fff !important;
}}
textarea:focus,
.stTextInput > div > div > input:focus,
.stNumberInput input:focus,
.stSelectbox > div > div > div:focus-within,
.stFileUploader label:focus-within {{
  border-color: {ADI_GREEN} !important;
  box-shadow: 0 0 0 3px rgba(0,108,53,.18) !important;
}}

/* Verb chips */
.chips {{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0; }}
.chip {{ padding:6px 12px; border-radius:999px; font-size:.85rem; font-weight:600; cursor:default; transition: all .2s ease; }}
.chip.low  {{ background:{ADI_SAND}; color:#333; }}
.chip.med  {{ background:{ADI_GREEN}; color:#fff; }}
.chip.high {{ background:{ADI_BROWN}; color:#fff; }}
.chip.more {{ background:#eee; color:#555; font-weight:500; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
  border-bottom: 2px solid #ddd;
  gap: 8px;
}}
.stTabs [data-baseweb="tab-list"] button {{
  font-weight: 600;
  padding: 6px 16px;
  border-radius: 8px 8px 0 0;
  background: #f7f7f7;
  color: #333;
  border: 1px solid #ccc;
  border-bottom: none;
}}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  background: {ADI_GREEN} !important;
  color: #fff !important;
  border: 1px solid {ADI_GREEN} !important;
}}
.stTabs [data-baseweb="tab-list"] button:hover {{
  background: #eaeaea;
}}
</style>
""", unsafe_allow_html=True)

# ---- Banner ----
st.markdown(f"""
<div class='banner'>
<h1>🎓 ADI Builder — Lesson Activities & Questions <span class='badge'>Branded</span></h1>
</div>
""", unsafe_allow_html=True)

# ---- Sidebar ----
if os.path.exists("assets/adi-logo.png"):
    st.sidebar.image("assets/adi-logo.png", width=180)
else:
    st.sidebar.markdown(f"<div style='font-weight:700;color:{ADI_GREEN};'>Academy of Defense Industries</div>", unsafe_allow_html=True)

st.sidebar.caption("ADI Bloom tiers used for MCQs:")

st.sidebar.markdown(
    "<div class='chips'>" + "".join(f"<span class='chip low'>{v}</span>" for v in ADI_LOW) +
    "<span class='chip more'>+low</span></div>", unsafe_allow_html=True)

st.sidebar.markdown(
    "<div class='chips'>" + "".join(f"<span class='chip med'>{v}</span>" for v in ADI_MED) +
    "<span class='chip more'>+med</span></div>", unsafe_allow_html=True)

st.sidebar.markdown(
    "<div class='chips'>" + "".join(f"<span class='chip high'>{v}</span>" for v in ADI_HIGH) +
    "<span class='chip more'>+high</span></div>", unsafe_allow_html=True)

# ---- Helper: RTF Export ----
def to_rtf(title: str, body: str) -> bytes:
    def esc(s: str) -> str:
        return s.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\line ")
    rtf = [r"{\rtf1\ansi\deff0", r"{\fonttbl{\f0 Calibri;}}", r"\fs22", r"\pard\f0 "]
    if title: rtf.append(r"\b " + esc(title) + r"\b0\line\line ")
    rtf.append(esc(body)); rtf.append("}")
    return "\n".join(rtf).encode("utf-8")

# ---- Tabs ----
kn_tab, skills_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# ---- Knowledge MCQs ----
with kn_tab:
    st.subheader("Generate MCQs (auto-aligned to ADI Bloom Policy)")
    topic = st.text_input("Topic", "Module/Outcome")
    n_sets = st.number_input("How many MCQ sets? (3 Qs each)",1,10,2)

    if st.button("Generate MCQs"):
        mcqs=[]
        for s in range(n_sets):
            low  = random.choice(ADI_LOW)
            med  = random.choice(ADI_MED)
            high = random.choice(ADI_HIGH)
            stems=[
              (f"Define: What does **{topic}** mean?", low, "A) vague\nB) precise\nC) anecdotal\nD) unrelated","B"),
              (f"Apply: How would you **{med}** {topic} in practice?", med, "A) ignore\nB) relevant\nC) random\nD) generic","B"),
              (f"Evaluate: Why is it important to **{high}** {topic}?", high, "A) unrelated\nB) assumptions noted\nC) formatting only\nD) outcomes no criteria","B")
            ]
            mcqs.extend(stems)

        blocks=[]
        for i,(stem,verb,opts,ans) in enumerate(mcqs,1):
            q_text=f"Q{i}. {stem}\n{opts}\nAnswer: {ans} ({verb})"
            st.text_area(f"Q{i}",q_text,height=120)
            blocks.append(q_text)

        txt_out="\n\n".join(blocks)
        rtf=to_rtf("ADI Builder — Knowledge MCQs", txt_out)

        st.download_button("Download MCQs (.rtf)", rtf, file_name="adi_mcqs.rtf")
        if DOCX_AVAILABLE:
            doc=Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Knowledge MCQs',level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for i,blk in enumerate(blocks,1):
                doc.add_heading(f'Question {i}',level=2)
                for line in blk.split('\n'):
                    if line.startswith(("A)","B)","C)","D)")):
                        doc.add_paragraph(line,style='List Bullet')
                    else:
                        doc.add_paragraph(line)
            bio=BytesIO(); doc.save(bio); bio.seek(0)
            st.download_button("Download MCQs (.docx)",bio.getvalue(),file_name="adi_mcqs.docx")

# ---- Skills Activities ----
with skills_tab:
    st.subheader("Generate Skills Activities")
    n_act=st.number_input("Activities",1,10,2)
    duration=st.number_input("Duration (mins)",5,120,30)
    if st.button("Generate Activities"):
        acts=[]
        for i in range(1,n_act+1):
            step1=f"Introduce the activity and explain relevance to {topic}."
            step2=f"In pairs or groups, work to apply {random.choice(ADI_MED)} in context."
            step3="Share outputs with peers or upload to LMS."
            text=f"Activity {i} — {duration} mins\n1) {step1}\n2) {step2}\n3) {step3}"
            st.text_area(f"Activity {i}",text,height=120)
            acts.append(text)
        edited_out="\n\n".join(acts)
        rtf=to_rtf("ADI Builder — Skills Activities", edited_out)
        st.download_button("Download Activities (.rtf)",rtf,file_name="adi_activities.rtf")
        if DOCX_AVAILABLE:
            doc=Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Skills Activities',level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for a in acts: doc.add_paragraph(a)
            bio=BytesIO(); doc.save(bio); bio.seek(0)
            st.download_button("Download Activities (.docx)",bio.getvalue(),file_name="adi_activities.docx")
