# app.py — ADI Builder (Streamlit, Branded, with Difficulty + Attachments)
# Fixed exports: DOCX (native Word) and RTF (opens instantly in Word, no encoding dialog).

from __future__ import annotations
import streamlit as st
from io import BytesIO
from datetime import datetime
import os

try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")

ADI_GREEN = "#006C35"
ADI_BEIGE = "#C8B697"
ADI_SAND  = "#D9CFC2"
ADI_BROWN = "#6B4E3D"
ADI_GRAY  = "#F5F5F5"

st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%); }}
h1,h2,h3 {{ color:{ADI_GREEN}; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='background:#006C35;color:white;padding:15px;border-radius:0 0 12px 12px;'>
<h1>🎓 ADI Builder — Lesson Activities & Questions <span style='background:#C8B697;color:#000;padding:2px 6px;border-radius:6px;font-size:0.8rem;'>Branded</span></h1>
</div>
""", unsafe_allow_html=True)

# Sidebar logo
if os.path.exists("assets/adi-logo.png"):
    st.sidebar.image("assets/adi-logo.png", width=180)
else:
    st.sidebar.markdown(f"<div style='font-weight:700;color:{ADI_GREEN};'>Academy of Defense Industries</div>", unsafe_allow_html=True)

# Helper: generate RTF so it opens instantly in Word
def to_rtf(title: str, body: str) -> bytes:
    def esc(s: str) -> str:
        s = s.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
        return s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", r"\line ")
    rtf = [
        r"{\rtf1\ansi\deff0",
        r"{\fonttbl{\f0 Calibri;}}",
        r"\fs22",  # 11pt
        r"\pard\f0 "
    ]
    if title:
        rtf.append(r"\b " + esc(title) + r"\b0\line\line ")
    rtf.append(esc(body))
    rtf.append("}")
    return "\n".join(rtf).encode("utf-8")

# Difficulty toggle
difficulty = st.sidebar.select_slider("Difficulty", ["Easy","Medium","Hard"], value="Medium")

# Tabs
kn_tab, skills_tab = st.tabs(["Knowledge MCQs","Skills Activities"])

with kn_tab:
    st.subheader("Generate MCQs")
    topic = st.text_input("Topic", "Module/Outcome")
    n_mcq = st.number_input("How many MCQs?",1,20,3)

    if st.button("Generate MCQs"):
        import random
        BASE = [
            lambda t:(f"Which is the best definition of {t}?",["A) vague","B) precise","C) anecdotal","D) unrelated"],"B"),
            lambda t:(f"Which example best illustrates {t}?",["A) contradicts","B) realistic","C) random","D) generic"],"B")
        ]
        HARD=[lambda t:(f"In a scenario applying {t}, which option justifies the choice?",["A) unrelated","B) assumptions noted","C) formatting only","D) outcomes no criteria"],"B")]
        pool = BASE if difficulty=="Medium" else (BASE[:1] if difficulty=="Easy" else BASE+HARD)
        mcqs=[random.choice(pool)(topic) for _ in range(n_mcq)]

        blocks=[]
        for i,(stem,opts,ans) in enumerate(mcqs,1):
            q_text=stem+"\n"+"\n".join(opts)+f"\nAnswer: {ans}"
            st.text_area(f"Q{i}",q_text,height=120)
            blocks.append(q_text)

        txt_out="\n\n".join(blocks)
        # Word-friendly formats only
        mcq_rtf=to_rtf("ADI Builder — Knowledge MCQs", txt_out)
        st.download_button("Download MCQs (.rtf)", mcq_rtf, file_name="adi_mcqs.rtf")
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
            bio=BytesIO();doc.save(bio);bio.seek(0)
            st.download_button("Download MCQs (.docx)",bio.getvalue(),file_name="adi_mcqs.docx")

with skills_tab:
    st.subheader("Generate Activities")
    n_act=st.number_input("Activities",1,10,2)
    duration=st.number_input("Duration (mins)",5,120,30)
    verb=st.selectbox("Verb",["apply","analyze","create"])
    if st.button("Generate Activities"):
        acts=[]
        for i in range(1,n_act+1):
            if difficulty=="Easy": step2=f"In pairs, {verb} a simple example."
            elif difficulty=="Hard": step2=f"In teams, {verb} under constraints and justify."
            else: step2=f"{verb} the concept in context."
            text=f"Activity {i} — {duration} mins\n1) Intro\n2) {step2}\n3) Share"
            st.text_area(f"Activity {i}",text,height=120)
            acts.append(text)
        edited_out="\n\n".join(acts)
        # Word-friendly formats only
        act_rtf=to_rtf("ADI Builder — Skills Activities", edited_out)
        st.download_button("Download Activities (.rtf)", act_rtf, file_name="adi_activities.rtf")
        if DOCX_AVAILABLE:
            doc=Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Skills Activities',level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for a in acts:
                doc.add_paragraph(a)
            bio=BytesIO();doc.save(bio);bio.seek(0)
            st.download_button("Download Activities (.docx)",bio.getvalue(),file_name="adi_activities.docx")

# Full Pack
def build_full_pack_docx(mcqs,acts):
    doc=Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
    doc.add_heading('ADI Builder — Lesson Pack',0)
    doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
    if mcqs:
        doc.add_heading('Section A — MCQs',level=1)
        for i,blk in enumerate(mcqs,1):
            doc.add_heading(f'Question {i}',level=2)
            for line in blk.split('\n'):
                if line.startswith(("A)","B)","C)","D)")):
                    doc.add_paragraph(line,style='List Bullet')
                else:
                    doc.add_paragraph(line)
    if acts:
        doc.add_page_break()
        doc.add_heading('Section B — Activities',level=1)
        for a in acts:
            doc.add_paragraph(a)
    bio=BytesIO();doc.save(bio);bio.seek(0)
    return bio.getvalue()

if DOCX_AVAILABLE and st.button("Build Full Pack"):
    mcqs = []
    acts = []
    # You could pull from session state if needed
    docx_bytes = build_full_pack_docx(mcqs,acts)
    st.download_button("Download Full Pack (.docx)",docx_bytes,file_name="adi_full_pack.docx")

