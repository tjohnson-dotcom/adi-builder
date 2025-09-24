# app.py — ADI Builder (Full Version with File Parsing)
# ---------------------------------------------------------------
# Run locally:
#   pip install -r requirements.txt
#   streamlit run app.py
#
# Produces print‑ready Word (.docx) handouts for MCQs or Activities,
# plus Moodle GIFT and CSV. Simple, professional, ADI‑branded.

import base64
import io
import os
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
from docx import Document as DocxDocument
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation

# ---------------------------------------------------------------
# Page setup & theme
# ---------------------------------------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

LOGO_PATH = "logo.png"

def _read_logo_data_uri(path: str) -> str | None:
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass
    return None

logo_uri = _read_logo_data_uri(LOGO_PATH)

ADI_CSS = """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-gold:#C8A85A;
  --ink:#1f2937; --muted:#6b7280; --bg:#FAFAF7; --card:#fff; --border:#E6EAE6;
  --shadow:0 8px 22px rgba(0,0,0,.06); --radius:16px; --pill:999px;
}
html,body{background:var(--bg);} main .block-container{max-width:1100px;}

.adi-hero{display:flex; gap:14px; align-items:center; background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600)); color:#fff; border-radius:20px; padding:14px 16px; box-shadow:var(--shadow);}
.logo{width:40px;height:40px;border-radius:10px;background:rgba(0,0,0,.1);display:flex;align-items:center;justify-content:center;overflow:hidden}
.logo img{width:100%;height:100%;object-fit:contain}
.h-title{font-size:20px;font-weight:800;margin:0}
.h-sub{opacity:.95;font-size:12px;margin:0}

.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:14px;margin:10px 0}
.cap{color:var(--adi-green);text-transform:uppercase;letter-spacing:.05em;font-size:12px;margin:0 0 8px 0}

/* Inputs */
.stTextArea textarea, .stTextInput input{border:2px solid var(--adi-green)!important;border-radius:12px!important}
.stTextArea textarea:focus, .stTextInput input:focus{box-shadow:0 0 0 3px rgba(36,90,52,.18)!important}

/* Buttons */
div.stButton>button{background:var(--adi-green);color:#fff;border:none;border-radius:var(--pill);padding:.55rem 1rem;font-weight:700;box-shadow:0 6px 14px rgba(31,76,44,.22);}
div.stButton>button:hover{filter:brightness(.98);box-shadow:0 0 0 3px rgba(200,168,90,.35)}

.badge{display:inline-flex;align-items:center;justify-content:center;padding:6px 10px;border-radius:999px;border:1px solid var(--border);margin:2px 6px 2px 0;font-weight:600}
.low{background:#eaf5ec;color:#245a34}
.med{background:#f8f3e8;color:#6a4b2d}
.high{background:#f3f1ee;color:#4a4a45}

hr.soft{height:1px;border:0;background:var(--border);margin:8px 0}
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------
# Session state
# ---------------------------------------------------------------

def ensure_state():
    ss = st.session_state
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("mcq_blocks", 10)
    ss.setdefault("mcq_df", None)
    ss.setdefault("act_df", None)
    ss.setdefault("upload_text", "")

ensure_state()

LOW_VERBS = ["define","identify","list","recall","describe","label"]
MED_VERBS = ["apply","demonstrate","solve","illustrate"]
HIGH_VERBS = ["evaluate","synthesize","design","justify"]


def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"


def _fallback(text:str, default:str)->str:
    return text.strip() if text and str(text).strip() else default

# ---------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------

def extract_text_from_upload(up_file) -> str:
    if up_file is None:
        return ""
    name = up_file.name.lower()
    text = ""
    try:
        if name.endswith(".pdf"):
            reader = PdfReader(up_file)
            for page in reader.pages[:5]:
                text += page.extract_text() or ""
        elif name.endswith(".docx"):
            doc = DocxDocument(up_file)
            for p in doc.paragraphs[:30]:
                text += p.text + "\n"
        elif name.endswith(".pptx"):
            prs = Presentation(up_file)
            for slide in prs.slides[:10]:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
        return text.strip()[:800]  # limit for UI
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ---------------------------------------------------------------
# Generators
# ---------------------------------------------------------------

def generate_mcq_blocks(topic:str, source:str, num_blocks:int, week:int)->pd.DataFrame:
    topic = _fallback(topic, "Module topic"); src_snip = _fallback(source, "Key concepts and policy points.")
    rows:List[Dict[str,Any]] = []
    for b in range(1, num_blocks+1):
        for tier in ("Low","Medium","High"):
            if tier=="Low":
                verb = LOW_VERBS[b % len(LOW_VERBS)]; stem = f"{verb.capitalize()} a basic fact about: {topic}."
            elif tier=="Medium":
                verb = MED_VERBS[b % len(MED_VERBS)]; stem = f"{verb.capitalize()} this concept from {topic} in a practical case."
            else:
                verb = HIGH_VERBS[b % len(HIGH_VERBS)]; stem = f"{verb.capitalize()} a policy implication of {topic} given: {src_snip[:80]}"
            opts = [f"Option A ({tier})", f"Option B ({tier})", f"Option C ({tier})", f"Option D ({tier})"]
            answer_idx = (b + ["Low","Medium","High"].index(tier)) % 4
            rows.append({
                "Block": b, "Tier": tier, "Question": stem,
                "Option A": opts[0], "Option B": opts[1], "Option C": opts[2], "Option D": opts[3],
                "Answer": ["A","B","C","D"][answer_idx],
                "Explanation": f"This is a placeholder rationale linked to {topic}.",
            })
    return pd.DataFrame(rows)


def generate_activities(count:int, duration:int, tier:str, topic:str)->pd.DataFrame:
    if tier=="Low": verbs, pattern = LOW_VERBS, "Warm-up: {verb} the core terms in {topic}; Pair-check; Short recap."
    elif tier=="Medium": verbs, pattern = MED_VERBS, "Case task: {verb} key ideas from {topic} in groups; Peer review; Gallery walk."
    else: verbs, pattern = HIGH_VERBS, "Design task: {verb} a solution for {topic}; Present; Critique and refine."
    rows=[]
    for i in range(1, count+1):
        v = verbs[i % len(verbs)]
        rows.append({
            "Tier": tier,
            "Title": f"Module: Activity {i}",
            "Objective": f"Students will {v} key content from {topic}.",
            "Steps": pattern.format(verb=v.capitalize(), topic=_fallback(topic, "the module")),
            "Materials": "Projector, handouts, whiteboard",
            "Assessment": "Participation rubric; brief exit ticket",
            "Duration (mins)": duration,
        })
    return pd.DataFrame(rows)

# ---------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------

def mcq_to_docx(df:pd.DataFrame, topic:str)->bytes:
    doc = Document(); doc.add_heading(f"ADI MCQs — {topic}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    p = doc.add_paragraph("Each block: Low → Medium → High"); p.runs[0].italic=True
    for b in sorted(df["Block"].unique()):
        doc.add_heading(f"Block {b}", 2)
        for _, row in df[df["Block"]==b].iterrows():
            pr = doc.add_paragraph().add_run(f"[{row['Tier']}] {row['Question']}"); pr.bold=True
            doc.add_paragraph(f"A. {row['Option A']}")
            doc.add_paragraph(f"B. {row['Option B']}")
            doc.add_paragraph(f"C. {row['Option C']}")
            doc.add_paragraph(f"D. {row['Option D']}")
            doc.add_paragraph(f"Answer: {row['Answer']}")
            doc.add_paragraph(f"Explanation: {row['Explanation']}")
            doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()


def mcq_to_gift(df:pd.DataFrame, topic:str)->bytes:
    lines=[f"// ADI MCQs — {topic}", f"// Exported {datetime.now():%Y-%m-%d %H:%M}", ""]
    for i, row in df.reset_index(drop=True).iterrows():
        qname=f"Block{row['Block']}-{row['Tier']}-{i+1}"; stem=row['Question'].replace("\n"," ").strip()
        opts=[row['Option A'],row['Option B'],row['Option C'],row['Option D']]
        ans_idx={"A":0,"B":1,"C":2,"D":3}.get(row['Answer'].strip().upper(),0)
        def esc(s): return s.replace('{','\\{').replace('}','\\}')
        lines.append(f"::{qname}:: {esc(stem)} {{")
        for j,o in enumerate(opts):
            lines.append(f"={'=' if j==ans_idx else '~'}{esc(o)}" if j==ans_idx else f"~{esc(o)}")
        lines.append("}\n")
    return "\n".join(lines).encode("utf-8")


def df_to_csv_bytes(df:pd.DataFrame)->bytes:
    bio=io.BytesIO(); df.to_csv(bio,index=False); return bio.getvalue()


def activities_to_docx(df:pd.DataFrame, topic:str)->bytes:
    doc=Document(); doc.add_heading(f"ADI Activities — {topic}",1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    for _,row in df.iterrows():
        doc.add_heading(row['Title'],2)
        doc.add_paragraph(f"Tier: {row['Tier']}")
        doc.add_paragraph(f"Objective: {row['Objective']}")
        doc.add_paragraph(f"Steps: {row['Steps']}")
        doc.add_paragraph(f"Materials: {row['Materials']}")
        doc.add_paragraph(f"Assessment: {row['Assessment']}")
        doc.add_paragraph(f"Duration: {row['Duration (mins)']} mins")
        doc.add_paragraph("")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
with st.container():
    st.markdown(
        f"""
        <div class='adi-hero'>
          <div class='logo'>{('<img src="'+logo_uri+'" alt="ADI"/>') if logo_uri else 'ADI'}</div>
          <div>
            <div class='h-title'>ADI Builder — Lesson Activities & Questions</div>
            <div class='h-sub'>Sleek. Professional. Engaging. Print‑ready handouts for your instructors.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------
# Sidebar (inputs only)
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("### Upload (optional)")
    up_file = st.file_uploader("PDF / DOCX / PPTX", type=["pdf","docx","pptx"])
    if up_file:
        st.session_state.upload_text = extract_text_from_upload(up_file)

    st.markdown("---")
    st.markdown("### Course context")
    st.session_state.lesson = st.selectbox("Lesson", list(range(1,7)), index=st.session_state.lesson-1)
    st.session_state.week = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1)
    bloom = bloom_focus_for_week(st.session_state.week)
    st.caption(f"ADI policy → Week {st.session_state.week}: **{bloom}** focus")

    st.markdown("---")
    st.markdown("### MCQ blocks")
    pick = st.radio("Quick pick", [5,10,20,30], horizontal=True, index=[5,10,20,30].index(st.session_state.mcq_blocks) if st.session_state.mcq_blocks in [5,10,20,30] else 1)
    st.session_state.mcq_blocks = pick

    st.markdown("---")
    st.markdown("### Activities (for Activities tab)")
    st.session_state.setdefault("ref_act_n",3)
    st.session_state.setdefault("ref_act_d",45)
    st.session_state.ref_act_n = st.number_input("Activities count", min_value=1, value=st.session_state.ref_act_n, step=1)
    st.session_state.ref_act_d = st.number_input("Duration (mins)", min_value=5, value=st.session_state.ref_act_d, step=5)

# ---------------------------------------------------------------
# Tabs (outputs only)
# ---------------------------------------------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

with mcq_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>MCQ Generator</p>", unsafe_allow_html=True)
    col1, col2 = st.columns([1,1])
    with col1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with col2:
        st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom}", disabled=True)

    source = st.text_area("Source text (editable)", value=st.session_state.upload_text, height=120)

    with st.expander("Show Bloom’s verbs"):
        st.markdown("**Low** (Remember/Understand)")
        st.markdown(" ".join([f"<span class='badge low'>{w}</span>" for w in LOW_VERBS]), unsafe_allow_html=True)
        st.markdown("**Medium** (Apply/Analyze)")
        st.markdown(" ".join([f"<span class='badge med'>{w}</span>" for w in MED_VERBS]), unsafe_allow_html=True)
        st.markdown("**High** (Evaluate/Create)")
        st.markdown(" ".join([f"<span class='badge high'>{w}</span>" for w in HIGH_VERBS]), unsafe_allow_html=True)

    if st.button("Generate MCQ Blocks"):
        with st.spinner("Building MCQ blocks…"):
            st.session_state.mcq_df = generate_mcq_blocks(topic, source, st.session_state.mcq_blocks, st.session_state.week)

    if st.session_state
