import base64, io, os, random
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

# Optional parsers
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None
try:
    from docx import Document
    from pptx import Presentation
except Exception:
    Document = None
    Presentation = None

# ----------------------------- Page setup -----------------------------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide", initial_sidebar_state="expanded")
LOGO_PATH = "logo.png"

def _read_logo_data_uri(path: str):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass
    return None
logo_uri = _read_logo_data_uri(LOGO_PATH)

# ----------------------------- CSS -----------------------------
st.markdown("""
<style>
:root{--adi-green:#245a34; --adi-gold:#C8A85A; --bg:#F7F7F4; --border:#E3E8E3}
html,body{background:var(--bg);} main .block-container{max-width:1180px; padding-top:0.6rem}
.adi-hero{display:flex; align-items:center; gap:14px; padding:18px 20px; border-radius:22px; color:#fff;
  background:linear-gradient(95deg,var(--adi-green),#1f4c2c); margin-bottom:14px}
.logo{width:48px;height:48px;border-radius:12px;background:rgba(0,0,0,.12);display:flex;align-items:center;justify-content:center;overflow:hidden}
.logo img{width:100%;height:100%;object-fit:contain}
.h-title{font-size:22px;font-weight:800;margin:0}
.side-card{background:#fff; border:1px solid var(--border); border-radius:16px; padding:12px; margin:12px 6px}
.rule{height:2px; background:linear-gradient(90deg,var(--adi-gold),transparent); border:0; margin:6px 0 12px}
.badge{display:inline-block; padding:4px 8px; border-radius:999px; font-size:12px; font-weight:600}
.low{background:#eaf5ec; color:#245a34}
.med{background:#f8f3e8; color:#6a4b2d}
.high{background:#f3f1ee; color:#4a4a45}
</style>
<div class='adi-badge' style="position:fixed;top:10px;right:12px;background:#245a34;color:#fff;
padding:6px 10px;border-radius:999px;font-size:12px;">ADI style v15</div>
""", unsafe_allow_html=True)

# ----------------------------- State -----------------------------
def ensure_state():
    ss = st.session_state
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("mcq_blocks", 5)
    ss.setdefault("mcq_df", None)
    ss.setdefault("act_df", None)
    ss.setdefault("upload_text", "")
ensure_state()

LOW_VERBS = ["define","identify","list","recall","describe","label"]
MED_VERBS = ["apply","demonstrate","interpret","compare"]
HIGH_VERBS = ["analyze","evaluate","design","formulate"]

def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# ----------------------------- Upload Parser -----------------------------
def extract_text_from_upload(up_file) -> str:
    if up_file is None: return ""
    name = up_file.name.lower(); text=""
    try:
        if name.endswith(".pdf") and PdfReader:
            reader=PdfReader(up_file)
            for page in reader.pages[:10]:
                txt=page.extract_text() or ""; text+=txt+"\n"
        elif name.endswith(".docx") and Document:
            doc=Document(up_file)
            for p in doc.paragraphs[:150]:
                text+=(p.text or "")+"\n"
        elif name.endswith(".pptx") and Presentation:
            prs=Presentation(up_file)
            for slide in prs.slides[:30]:
                for shp in slide.shapes:
                    if hasattr(shp,"text") and shp.text:
                        text+=shp.text+"\n"
        lines=[ln.strip() for ln in text.split("\n") if ln.strip()]
        return "\n".join(lines)[:2000]
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ----------------------------- Tiny NLP -----------------------------
def _sentences(text:str)->list[str]:
    rough=[]
    for chunk in text.split("\n"):
        parts=[p.strip() for p in chunk.replace("•",". ").split(".")]
        for p in parts:
            if p: rough.append(p)
    return [s for s in rough if len(s)>=30][:80]

def _distractors(correct:str,pool:list[str],n:int)->list[str]:
    rand=random.Random(42); cands=[p for p in pool if p.strip()!=correct.strip()]
    rand.shuffle(cands); out=[]
    for s in cands:
        if 25<=len(s)<=130 and s not in out: out.append(s)
        if len(out)==n: break
    while len(out)<n:
        out.append("Alternative statement not matching the context.")
    return out

# ----------------------------- Generators -----------------------------
def generate_mcq_blocks(topic:str,source:str,num_blocks:int,lesson:int,week:int)->pd.DataFrame:
    bloom=bloom_focus_for_week(week)
    sents=_sentences(source) or [f"{topic} covers essential ideas."]
    rows=[]
    for b in range(1,num_blocks+1):
        # Low
        v=random.choice(LOW_VERBS); s=random.choice(sents)
        q=f"{v.capitalize()} the key concept: what does this statement mean in *{topic}*?"
        correct=s if len(s)<=130 else s[:127]+"…"; opts=_distractors(correct,sents,3)+[correct]; random.shuffle(opts)
        rows.append({"Block":b,"Lesson":lesson,"Week":week,"Tier":"Low","Question":q,
                     "Option A":opts[0],"Option B":opts[1],"Option C":opts[2],"Option D":opts[3],
                     "Answer":["A","B","C","D"][opts.index(correct)]})
        # Medium
        v=random.choice(MED_VERBS); s=random.choice(sents)
        q=f"In applying {v}, which option fits best in the context of *{topic}*?"
        correct=s if len(s)<=130 else s[:127]+"…"; opts=_distractors(correct,sents,3)+[correct]; random.shuffle(opts)
        rows.append({"Block":b,"Lesson":lesson,"Week":week,"Tier":"Medium","Question":q,
                     "Option A":opts[0],"Option B":opts[1],"Option C":opts[2],"Option D":opts[3],
                     "Answer":["A","B","C","D"][opts.index(correct)]})
        # High
        v=random.choice(HIGH_VERBS); s=random.choice(sents)
        q=f"Critically {v} this aspect of *{topic}*: which choice is most valid?"
        correct=s if len(s)<=130 else s[:127]+"…"; opts=_distractors(correct,sents,3)+[correct]; random.shuffle(opts)
        rows.append({"Block":b,"Lesson":lesson,"Week":week,"Tier":"High","Question":q,
                     "Option A":opts[0],"Option B":opts[1],"Option C":opts[2],"Option D":opts[3],
                     "Answer":["A","B","C","D"][opts.index(correct)]})
    return pd.DataFrame(rows)

def generate_activities(count:int,duration:int,tier:str,topic:str,lesson:int,week:int)->pd.DataFrame:
    verbs={"Low":LOW_VERBS,"Medium":MED_VERBS,"High":HIGH_VERBS}[tier]
    rows=[]
    for i in range(1,count+1):
        v=verbs[(i-1)%len(verbs)]
        steps=[f"Starter: {v.capitalize()} prior knowledge.",
               f"Main: {v} a task related to {topic}.",
               f"Plenary: Reflect and refine answers."]
        rows.append({"Lesson":lesson,"Week":week,"Tier":tier,"Title":f"{tier} Activity {i}",
                     "Objective":f"Students will {v} key ideas from {topic}.",
                     "Steps":" ".join(steps),"Duration (mins)":duration})
    return pd.DataFrame(rows)

# ----------------------------- Export -----------------------------
def df_to_docx_mcqs(df:pd.DataFrame,topic:str)->bytes:
    if DocxDocument is None: raise RuntimeError("python-docx not installed")
    doc=DocxDocument(); doc.add_heading(f"ADI MCQs — {topic}",1)
    for b in sorted(df["Block"].unique()):
        doc.add_heading(f"Block {b}",2)
        for j,(_,r) in enumerate(df[df["Block"]==b].iterrows(),1):
            doc.add_paragraph(f"Q{j}. [{r['Tier']}] {r['Question']}")
            doc.add_paragraph(f"A. {r['Option A']}"); doc.add_paragraph(f"B. {r['Option B']}")
            doc.add_paragraph(f"C. {r['Option C']}"); doc.add_paragraph(f"D. {r['Option D']}")
            doc.add_paragraph(f"Answer: {r['Answer']}"); doc.add_paragraph("")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def df_to_docx_activities(df:pd.DataFrame,topic:str)->bytes:
    if DocxDocument is None: raise RuntimeError("python-docx not installed")
    doc=DocxDocument(); doc.add_heading(f"ADI Activities — {topic}",1)
    for _,r in df.iterrows():
        doc.add_heading(r["Title"],2)
        doc.add_paragraph(f"Lesson {r['Lesson']}, Week {r['Week']}")
        doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph(f"Steps: {r['Steps']}"); doc.add_paragraph(f"Duration: {r['Duration (mins)']} mins")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

# ----------------------------- Header -----------------------------
st.markdown(f"<div class='adi-hero'><div class='logo'>{('<img src=\"'+logo_uri+'\"/>') if logo_uri else 'ADI'}</div><div><div class='h-title'>ADI Builder — Lesson Activities & Questions</div></div></div>", unsafe_allow_html=True)

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    with st.container():
        st.markdown("<div class='side-card'><div>UPLOAD (OPTIONAL)</div><hr class='rule'/>", unsafe_allow_html=True)
        up_file=st.file_uploader("Choose a file",type=["pdf","docx","pptx"],label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='side-card'><div>COURSE CONTEXT</div><hr class='rule'/>", unsafe_allow_html=True)
        bloom=bloom_focus_for_week(st.session_state.week)
        st.markdown(f"<div><strong>Lesson:</strong> {st.session_state.lesson}</div><div><strong>Week:</strong> {st.session_state.week}</div><div class='badge {bloom.lower()}'>{bloom} focus</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='side-card'><div>KNOWLEDGE MCQs</div><hr class='rule'/>", unsafe_allow_html=True)
        pick=st.radio("Quick pick blocks",[5,10,20,30],horizontal=True,index=[5,10,20,30].index(st.session_state.mcq_blocks))
        st.session_state.mcq_blocks=pick
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='side-card'><div>SKILLS ACTIVITIES</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.setdefault("ref_act_n",3); st.session_state.setdefault("ref_act_d",45)
        st.session_state.ref_act_n=st.number_input("Activities count",min_value=1,value=st.session_state.ref_act_n)
        st.session_state.ref_act_d=st.number_input("Duration (mins)",min_value=5,value=st.session_state.ref_act_d)
        st.markdown("</div>", unsafe_allow_html=True)

    if up_file: st.session_state.upload_text=extract_text_from_upload(up_file)

# ----------------------------- Tabs -----------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)","Skills Activities"])

with mcq_tab:
    lesson=st.selectbox("Lesson",list(range(1,7)),index=st.session_state.lesson-1)
    week=st.selectbox("Week",list(range(1,15)),index=st.session_state.week-1)
    st.session_state.lesson, st.session_state.week = lesson, week
    topic=st.text_input("Topic / Outcome (optional)")
    with st.expander("Source (from upload) — optional",expanded=False):
        source=st.text_area("",value=st.session_state.upload_text,height=160,label_visibility="collapsed",key="source_mcq")
    if st.button("Generate MCQ Blocks"):
        st.session_state.mcq_df=generate_mcq_blocks(topic,source,int(st.session_state.mcq_blocks),lesson,week)
    if st.session_state.mcq_df is not None:
        df=st.data_editor(st.session_state.mcq_df,use_container_width=True,num_rows="dynamic")
        st.download_button("Download Word (.docx)",df_to_docx_mcqs(df,topic or "Module"),file_name="adi_mcqs.docx")
    else:
        st.info("No MCQs yet.")

with act_tab:
    lesson=st.selectbox("Lesson",list(range(1,7)),index=st.session_state.lesson-1,key="lesson_act")
    week=st.selectbox("Week",list(range(1,15)),index=st.session_state.week-1,key="week_act")
    tier=st.radio("Emphasis",["Low","Medium","High"],horizontal=True)
    topic2=st.text_input("Topic (optional)",value="")
    with st.expander("Source (from upload) — optional",expanded=False):
        source2=st.text_area("",value=st.session_state.upload_text,height=160,label_visibility="collapsed",key="source_activities")
    if st.button("Generate Activities"):
        st.session_state.act_df=generate_activities(int(st.session_state.ref_act_n),int(st.session_state.ref_act_d),tier,topic2,lesson,week)
    if st.session_state.act_df is not None:
        df2=st.data_editor(st.session_state.act_df,use_container_width=True,num_rows="dynamic")
        st.download_button("Download Word (.docx)",df_to_docx_activities(df2,topic2 or "Module"),file_name="adi_activities.docx")
    else:
        st.info("No activities yet.")
