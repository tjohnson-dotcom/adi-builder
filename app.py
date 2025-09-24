# ADI Builder — Lesson Activities & Questions
# Polished UI • PDF/DOCX/PPTX parsing • Bloom policy highlight
# Exports: Word (print-ready), GIFT, CSV

import base64
import io
import os
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation

# ----------------------------- Page setup -----------------------------
st.set_page_config(
    page_title="ADI Builder",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
  --ink:#1f2937; --muted:#6b7280; --bg:#F7F7F4; --card:#ffffff; --border:#E3E8E3;
  --shadow:0 12px 28px rgba(0,0,0,.07);
}
html,body{background:var(--bg);} main .block-container{max-width:1180px; padding-top:0.6rem}

/* HERO */
.adi-hero{display:flex; align-items:center; gap:14px; padding:18px 20px; border-radius:22px; color:#fff;
  background:linear-gradient(95deg,var(--adi-green),var(--adi-green-600)); box-shadow:var(--shadow); margin-bottom:14px}
.logo{width:48px;height:48px;border-radius:12px;background:rgba(0,0,0,.12);display:flex;align-items:center;justify-content:center;overflow:hidden}
.logo img{width:100%;height:100%;object-fit:contain}
.h-title{font-size:22px;font-weight:800;margin:0}
.h-sub{font-size:12px;opacity:.95;margin:2px 0 0 0}

/* SIDEBAR */
section[data-testid='stSidebar']>div{background:#F3F2ED; height:100%}
.side-card{background:#fff; border:1px solid var(--border); border-radius:16px; padding:12px; margin:10px 6px; box-shadow:var(--shadow)}
.side-cap{font-size:12px; color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; margin:0 0 8px}
.rule{height:2px; background:linear-gradient(90deg,var(--adi-gold),transparent); border:0; margin:6px 0 10px}

/* CARDS */
.card{background:var(--card); border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow); padding:16px; margin:10px 0}
.cap{color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; font-size:12px; margin:0 0 10px}

/* INPUTS */
.stTextArea textarea, .stTextInput input{border:2px solid var(--adi-green)!important; border-radius:12px!important}
.stTextArea textarea:focus, .stTextInput input:focus{box-shadow:0 0 0 3px rgba(36,90,52,.18)!important}

/* BUTTONS */
div.stButton>button{background:var(--adi-green); color:#fff; border:none; border-radius:999px; padding:.6rem 1.1rem; font-weight:700; box-shadow:0 8px 18px rgba(31,76,44,.25)}
div.stButton>button:hover{filter:brightness(.98); box-shadow:0 0 0 3px rgba(200,168,90,.35)}

/* TABS */
[data-testid='stTabs'] button{font-weight:700; color:#445;}
[data-testid='stTabs'] button[aria-selected='true']{color:var(--adi-green)!important; border-bottom:3px solid var(--adi-gold)!important}

/* BADGES */
.badge{display:inline-flex; align-items:center; justify-content:center; padding:6px 10px; border-radius:999px; border:1px solid var(--border); margin:2px 6px 2px 0; font-weight:600}
.low{background:#eaf5ec; color:#245a34}
.med{background:#f8f3e8; color:#6a4b2d}
.high{background:#f3f1ee; color:#4a4a45}
.active-glow{box-shadow:0 0 0 3px rgba(36,90,52,.25)}
.active-amber{box-shadow:0 0 0 3px rgba(200,168,90,.35)}
.active-gray{box-shadow:0 0 0 3px rgba(120,120,120,.25)}

/* DOWNLOAD STRIP */
.dl-row{display:flex; gap:10px; flex-wrap:wrap}
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# ----------------------------- State/consts -----------------------------
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

def _fallback(text:str, default:str)->str:
    return text.strip() if text and str(text).strip() else default

def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# ----------------------------- File parsing -----------------------------
def extract_text_from_upload(up_file) -> str:
    if up_file is None:
        return ""
    name = up_file.name.lower()
    text = ""
    try:
        if name.endswith(".pdf"):
            reader = PdfReader(up_file)
            for page in reader.pages[:6]:
                # ✅ correct newline; this line caused the earlier crash
                text += (page.extract_text() or "") + "\n"
        elif name.endswith(".docx"):
            doc = Document(up_file)
            for p in doc.paragraphs[:60]:
                text += p.text + "\n"
        elif name.endswith(".pptx"):
            prs = Presentation(up_file)
            for slide in prs.slides[:15]:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        text += shape.text + "\n"
        return text.strip()[:1000]
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ----------------------------- Generators -----------------------------
def generate_mcq_blocks(topic:str, source:str, num_blocks:int, week:int)->pd.DataFrame:
    topic = _fallback(topic, "Module topic")
    src_snip = _fallback(source, "Key concepts and policy points.")
    rows:List[Dict[str,Any]] = []
    for b in range(1, num_blocks+1):
        for tier in ("Low","Medium","High"):
            if tier=="Low":
                verb = LOW_VERBS[b % len(LOW_VERBS)]
                stem = f"{verb.capitalize()} a basic fact about: {topic}."
            elif tier=="Medium":
                verb = MED_VERBS[b % len(MED_VERBS)]
                stem = f"{verb.capitalize()} this concept from {topic} in a practical case."
            else:
                verb = HIGH_VERBS[b % len(HIGH_VERBS)]
                stem = f"{verb.capitalize()} a policy implication of {topic} given: {src_snip[:80]}"
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
    if tier=="Low":
        verbs, pattern = LOW_VERBS, "Warm-up: {verb} the core terms in {topic}; Pair-check; Short recap."
    elif tier=="Medium":
        verbs, pattern = MED_VERBS, "Case task: {verb} key ideas from {topic} in groups; Peer review; Gallery walk."
    else:
        verbs, pattern = HIGH_VERBS, "Design task: {verb} a solution for {topic}; Present; Critique and refine."
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

# ----------------------------- Exporters -----------------------------
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
        qname=f"Block{row['Block']}-{row['Tier']}-{i+1}"
        stem=row['Question'].replace("\n"," ").strip()
        opts=[row['Option A'],row['Option B'],row['Option C'],row['Option D']]
        ans_idx={"A":0,"B":1,"C":2,"D":3}.get(row['Answer'].strip().upper(),0)
        def esc(s): return s.replace('{','\\{').replace('}','\\}')
        lines.append(f"::{qname}:: {esc(stem)} {{")
        for j,o in enumerate(opts):
            lines.append(f"={esc(o)}" if j==ans_idx else f"~{esc(o)}")
        lines.append("}")
        lines.append("")
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

# ----------------------------- Header -----------------------------
with st.container():
    st.markdown(
        f"""
        <div class='adi-hero'>
          <div class='logo'>{('<img src="'+logo_uri+'" alt="ADI"/>') if logo_uri else 'ADI'}</div>
          <div>
            <div class='h-title'>ADI Builder — Lesson Activities & Questions</div>
            <div class='h-sub'>Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    # Upload
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'>Upload (optional)</div><hr class='rule'/>", unsafe_allow_html=True)
        up_file = st.file_uploader(
            "Choose a file",
            type=["pdf","docx","pptx"],
            label_visibility="collapsed",
            help="Drop an eBook, lesson plan, or PPT to prefill Source text."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Course context
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'>Course Context</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.lesson = st.selectbox("Lesson", list(range(1,7)), index=st.session_state.lesson-1)
        st.session_state.week = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1)
        bloom = bloom_focus_for_week(st.session_state.week)
        st.caption(f"ADI policy → Week {st.session_state.week}: **{bloom}** focus (1–4 Low, 5–9 Medium, 10–14 High)")
        st.markdown("</div>", unsafe_allow_html=True)

    # MCQ blocks
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'>Knowledge MCQs (ADI Policy)</div><hr class='rule'/>", unsafe_allow_html=True)
        pick = st.radio(
            "Quick pick blocks", [5,10,20,30],
            horizontal=True,
            index=[5,10,20,30].index(st.session_state.mcq_blocks) if st.session_state.mcq_blocks in [5,10,20,30] else 1,
        )
        st.session_state.mcq_blocks = pick
        st.markdown("</div>", unsafe_allow_html=True)

    # Activities refs
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'>Skills Activities</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.setdefault("ref_act_n",3)
        st.session_state.setdefault("ref_act_d",45)
        st.session_state.ref_act_n = st.number_input("Activities count", min_value=1, value=st.session_state.ref_act_n, step=1)
        st.session_state.ref_act_d = st.number_input("Duration (mins)", min_value=5, value=st.session_state.ref_act_d, step=5)
        st.markdown("</div>", unsafe_allow_html=True)

    # parse after UI so spinner doesn't block
    if up_file:
        st.session_state.upload_text = extract_text_from_upload(up_file)

# ----------------------------- Tabs -----------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

with mcq_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>MCQ Generator</p>", unsafe_allow_html=True)
    col1, col2 = st.columns([1,1])
    with col1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with col2:
        st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom}", disabled=True)

    source = st.text_area("Source text (editable)", value=st.session_state.upload_text, height=140)

    # Bloom legend with policy highlight
    st.markdown("**Bloom’s verbs (ADI Policy)**")
    low_class = "badge low " + ("active-glow" if bloom=="Low" else "")
    med_class = "badge med " + ("active-amber" if bloom=="Medium" else "")
    high_class = "badge high " + ("active-gray" if bloom=="High" else "")
    st.markdown(" ".join([f"<span class='{low_class}'>{w}</span>" for w in LOW_VERBS]), unsafe_allow_html=True)
    st.markdown(" ".join([f"<span class='{med_class}'>{w}</span>" for w in MED_VERBS]), unsafe_allow_html=True)
    st.markdown(" ".join([f"<span class='{high_class}'>{w}</span>" for w in HIGH_VERBS]), unsafe_allow_html=True)

    if st.button("Generate MCQ Blocks"):
        with st.spinner("Building MCQ blocks…"):
            st.session_state.mcq_df = generate_mcq_blocks(topic, source, st.session_state.mcq_blocks, st.session_state.week)

    if st.session_state.mcq_df is None:
        st.info("No MCQs yet. Use the button above to generate.")
    else:
        edited = st.data_editor(st.session_state.mcq_df, num_rows="dynamic", use_container_width=True, key="mcq_editor")
        st.session_state.mcq_df = edited
        st.markdown("<div class='dl-row'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", mcq_to_docx(edited, _fallback(topic,"Module")),
                           file_name="adi_mcqs.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download Moodle (GIFT)", mcq_to_gift(edited, _fallback(topic,"Module")),
                           file_name="adi_mcqs_gift.txt", mime="text/plain")
        st.download_button("Download CSV", df_to_csv_bytes(edited),
                           file_name="adi_mcqs.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with act_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>Activities Planner</p>", unsafe_allow_html=True)
    default_idx = ["Low","Medium","High"].index(bloom if bloom in ["Low","Medium","High"] else "Medium")
    tier = st.radio("Emphasis", ["Low","Medium","High"], horizontal=True, index=default_idx)
    topic2 = st.text_input("Topic (optional)", value="", placeholder="Module or unit focus")

    if st.button("Generate Activities"):
        with st.spinner("Assembling activities…"):
            st.session_state.act_df = generate_activities(int(st.session_state.ref_act_n),
                                                          int(st.session_state.ref_act_d),
                                                          tier, topic2)

    if st.session_state.act_df is None:
        st.info("No activities yet. Use the button above to generate.")
    else:
        act_edit = st.data_editor(st.session_state.act_df, num_rows="dynamic", use_container_width=True, key="act_editor")
        st.session_state.act_df = act_edit
        st.markdown("<div class='dl-row'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", activities_to_docx(act_edit, _fallback(topic2,"Module")),
                           file_name="adi_activities.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download CSV", df_to_csv_bytes(act_edit),
                           file_name="adi_activities.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

