import os
import io
import re
import hashlib
from pathlib import Path
from datetime import datetime
import random

import streamlit as st

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

STYLES = """
<style>
:root { --adi-green: #245a34; }
.stButton>button { background: var(--adi-green) !important; color: #fff !important; border: 1px solid rgba(0,0,0,0.06); border-radius: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
.stButton>button:hover { filter: brightness(0.95); }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { background-color: rgba(36,90,52,0.08); color: var(--adi-green); border-radius: 999px; padding: 8px 16px; border: 1px solid rgba(36,90,52,0.25); }
.stTabs [aria-selected="true"] { background-color: var(--adi-green) !important; color: #fff !important; border: 1px solid var(--adi-green) !important; }
[data-baseweb="tag"] { background: rgba(36,90,52,0.12) !important; color: var(--adi-green) !important; border: 1px solid rgba(36,90,52,0.35) !important; }
.stTextArea textarea, .stTextInput input, .stSelectbox div[role="combobox"], .stMultiSelect div[role="combobox"] { box-shadow: 0 0 0 2px rgba(36,90,52,0.25) !important; }
input[type="range"], .stSlider input[type="range"] { accent-color: var(--adi-green) !important; }
.block-container { padding-top: 1.2rem; }
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)

if "week" not in st.session_state: st.session_state["week"] = 1
if "lesson" not in st.session_state: st.session_state["lesson"] = 1
if "verbs_mcq" not in st.session_state: st.session_state["verbs_mcq"] = []
if "verbs_acts" not in st.session_state: st.session_state["verbs_acts"] = []
if "src_text" not in st.session_state: st.session_state["src_text"] = ""

DEFAULT_VERBS = {
    "Remember": ["define","list","recall","name","identify","label","match","recognize","select","state"],
    "Understand": ["describe","explain","summarize","classify","compare","discuss","illustrate","interpret","paraphrase","report"],
    "Apply": ["apply","execute","implement","solve","use","demonstrate","carry out","perform"],
    "Analyze": ["analyze","differentiate","organize","attribute","compare/contrast","structure","examine","question","test"],
    "Evaluate": ["evaluate","argue","assess","critique","defend","judge","justify","select (criteria)","support","value"],
    "Create": ["design","assemble","construct","develop","formulate","author","plan","produce","compose"]
}
def uniq(seq): return sorted(dict.fromkeys([str(s).strip().lower() for s in seq if str(s).strip()]))
def policy_for_week(week:int) -> str: return "Low" if 1<=week<=4 else ("Medium" if 5<=week<=9 else "High")
POLICY_VERBS = {
    "Low":    uniq(DEFAULT_VERBS["Remember"] + DEFAULT_VERBS["Understand"]),
    "Medium": uniq(DEFAULT_VERBS["Apply"]    + DEFAULT_VERBS["Analyze"]),
    "High":   uniq(DEFAULT_VERBS["Evaluate"] + DEFAULT_VERBS["Create"]),
}
def policy_caption(week:int) -> str:
    pol = policy_for_week(week)
    rng = "Weeks 1–4" if pol=="Low" else ("Weeks 5–9" if pol=="Medium" else "Weeks 10–14")
    return f"**ADI Policy:** {rng} → {pol} level verbs are recommended and preselected."

@st.cache_data(show_spinner=False, ttl=3600)
def extract_text_from_file(path: str, ext: str, max_chars: int = 6000) -> str:
    ext = (ext or "").lower()
    text = ""
    try:
        if ext == ".pdf":
            import fitz
            with fitz.open(path) as doc:
                text = "\\n".join(page.get_text() for page in doc)
        elif ext == ".docx":
            from docx import Document
            d = Document(path)
            text = "\\n".join(p.text for p in d.paragraphs)
        elif ext == ".pptx":
            from pptx import Presentation
            prs = Presentation(path)
            slides = []
            for s in prs.slides:
                lines = []
                for shp in s.shapes:
                    if hasattr(shp, "text") and shp.text:
                        lines.append(shp.text)
                slides.append("\\n".join(lines))
            text = "\\n".join(slides)
    except Exception:
        text = ""
    return (text or "").strip()[:max_chars]

def seeded_random(seed_str: str): rnd = random.Random(); rnd.seed(seed_str); return rnd
def now_str() -> str: return datetime.now().strftime("%Y-%m-%d")
def sanitize_filename(name: str) -> str: return re.sub(r"[^A-Za-z0-9_\\-]+", "_", name).strip("_")

def build_mcqs(topic_text: str, verbs: list[str], n: int, variant: int, enable_mix: bool, week: int, lesson: int):
    topic = (topic_text or "this topic").strip()
    seed = f"mcq::{variant}::{week}::{lesson}::{hashlib.sha1(topic.encode('utf-8')).hexdigest()}"
    rnd = seeded_random(seed)
    if not verbs: verbs = POLICY_VERBS[policy_for_week(week)]
    verbs = uniq(verbs)
    stems = [
        "Using the verb **{verb}**, which option best fits {topic}?",
        "Select the option that **{verb}s** {topic} most accurately.",
        "Which statement **best {verb}s** the idea in {topic}?",
        "Identify the choice that **{verb}s** {topic} correctly.",
        "What is the **best** option to **{verb}** {topic}?",
        "Choose the response that **{verb}s** {topic}.",
    ]
    mcqs, letters = [], ["A","B","C","D"]
    for i in range(1, n+1):
        verb = rnd.choice(verbs)
        stem = rnd.choice(stems).format(verb=verb, topic=topic)
        correct = f"A precise choice that aligns with '{verb}' for {topic}."
        distractors = [f"A loosely related idea not focused on '{verb}'.", f"An off-topic detail unrelated to {topic}.", f"A common misconception about {topic}."]
        opts = [correct] + distractors
        order = list(range(4))
        if enable_mix: rnd.shuffle(order)
        mixed = [opts[idx] for idx in order]
        correct_key = letters[order.index(0)]
        mcqs.append({"q": stem, "options": list(zip(letters, mixed)), "correct_key": correct_key})
    return mcqs

def build_activities(topic_text: str, verbs: list[str], week: int, lesson: int, count: int = 6):
    topic = (topic_text or "this topic").strip()
    seed = f"acts::{week}::{lesson}::{hashlib.sha1(topic.encode('utf-8')).hexdigest()}"
    rnd = seeded_random(seed)
    if not verbs: verbs = POLICY_VERBS[policy_for_week(week)]
    verbs = uniq(verbs)
    ideas, templates = [], [
        "Small-group task: {verb} key points from {topic} and share back in 3 bullets.",
        "Pair work: {verb} a real-world example related to {topic}.",
        "Individual: {verb} a 5‑step checklist for {topic}.",
        "Whole-class: {verb} misconceptions around {topic} and correct them.",
        "Hands‑on: {verb} a quick demo to illustrate {topic}.",
        "Exit ticket: {verb} one insight from {topic}.",
    ]
    for i in range(count):
        ideas.append(templates[i % len(templates)].format(verb=rnd.choice(verbs), topic=topic))
    return ideas

def export_mcq_docx(mcqs, week: int, lesson: int, topic_preview: str = "") -> bytes:
    try:
        from docx import Document
    except Exception:
        st.error("python-docx is required to export .docx. Add it to requirements.txt")
        return b""
    doc = Document()
    doc.add_heading(f"ADI MCQ Paper – Week {week}, Lesson {lesson}", level=1)
    if topic_preview:
        p = doc.add_paragraph(f"Topic: {topic_preview[:120]}"); p.runs[0].italic = True
    for i, item in enumerate(mcqs, start=1):
        doc.add_paragraph(f"{i}. {item['q']}")
        for key, text in item["options"]:
            doc.add_paragraph(f"   {key}. {text}")
        doc.add_paragraph("")
    doc.add_heading("Answer Key", level=2)
    for i, item in enumerate(mcqs, start=1):
        doc.add_paragraph(f"{i}. {item['correct_key']}")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

with st.sidebar:
    try: st.image("Logo.png", use_column_width=False, width=140)
    except Exception: pass
    st.header("Upload PDF / DOCX / PPTX")
    uploaded = st.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"], key="uploader")
    if uploaded:
        buf = uploaded.getbuffer(); fhash = hashlib.sha1(buf).hexdigest()
        meta = st.session_state.get("_file_meta")
        if not meta or meta.get("hash") != fhash:
            ext = Path(uploaded.name).suffix.lower(); save_path = f"/tmp/adi_{fhash}{ext}"
            with open(save_path, "wb") as f: f.write(buf)
            st.session_state["_file_meta"] = {"name": uploaded.name, "size": uploaded.size, "hash": fhash, "path": save_path, "ext": ext}
            if st.session_state.get("_last_uploaded_hash") != fhash:
                st.toast(f"Uploaded ✓ {uploaded.name}", icon="✅"); st.session_state["_last_uploaded_hash"] = fhash
        meta = st.session_state.get("_file_meta"); st.success(f"File ready: **{meta['name']}**")
    st.write("Week");   st.session_state["week"] = st.selectbox("Week", list(range(1,15)), index=st.session_state["week"]-1, key="week_select")
    st.write("Lesson"); st.session_state["lesson"] = st.selectbox("Lesson", list(range(1,21)), index=st.session_state["lesson"]-1, key="lesson_select")
    policy_now = policy_for_week(int(st.session_state["week"])); st.session_state["_policy"] = policy_now
    _prev_week = st.session_state.get("_prev_week")
    if _prev_week != st.session_state["week"]:
        st.session_state["verbs_mcq"]  = POLICY_VERBS[policy_now][:]
        st.session_state["verbs_acts"] = POLICY_VERBS[policy_now][:]
        st.session_state["_verbs_mcq_initialized"] = False
        st.session_state["_verbs_acts_initialized"] = False
    st.session_state["_prev_week"] = st.session_state["week"]
    st.caption(policy_caption(int(st.session_state["week"])))

TABS = st.tabs(["Knowledge MCQs (ADI Policy)","Skills Activities","Revision"])

with TABS[0]:
    st.subheader("MCQ Generator")
    st.markdown("**Source text (optional)**")
    src_left, src_right = st.columns([1, 0.35])
    with src_left:
        st.session_state["src_text"] = st.text_area("Paste lesson/topic text (improves MCQs)", value=st.session_state.get("src_text",""), height=140, label_visibility="collapsed")
    with src_right:
        meta = st.session_state.get("_file_meta")
        if meta and st.button("📄 Use uploaded text", help="Extract text from the uploaded file and drop it here"):
            txt = extract_text_from_file(meta["path"], meta["ext"])
            if txt: st.session_state["src_text"] = txt; st.success("Text extracted from file.")
            else:   st.warning("Couldn’t extract text from this file—paste content manually.")
    policy_now = st.session_state.get("_policy", policy_for_week(int(st.session_state["week"])))
    options_mcq = POLICY_VERBS[policy_now]
    if not st.session_state.get("_verbs_mcq_initialized"):
        default_mcq = [v for v in st.session_state.get("verbs_mcq", []) if v in options_mcq] or options_mcq
        st.multiselect("Verb picker", options=options_mcq, default=default_mcq, key="verbs_mcq")
        st.session_state["_verbs_mcq_initialized"] = True
    else:
        st.multiselect("Verb picker", options=options_mcq, key="verbs_mcq")
    col_a, col_b, col_c = st.columns([0.5,0.5,1])
    with col_a: n_q = st.number_input("# of MCQs", min_value=3, max_value=30, value=10, step=1)
    with col_b: mix_answers = st.checkbox("Mix answer letters", value=True)
    with col_c: variant = st.number_input("Variant (deterministic seed)", min_value=0, max_value=9999, value=0, step=1)
    if st.button("Generate MCQs", type="primary"):
        mcqs = build_mcqs(st.session_state.get("src_text",""), st.session_state["verbs_mcq"], int(n_q), int(variant), bool(mix_answers), int(st.session_state["week"]), int(st.session_state["lesson"]))
        st.session_state["_mcqs"] = mcqs
    mcqs = st.session_state.get("_mcqs", [])
    if mcqs:
        st.success(f"Generated {len(mcqs)} MCQs.")
        with st.expander("Preview", expanded=True):
            for i, item in enumerate(mcqs, start=1):
                st.markdown(f"**{i}. {item['q']}**")
                for key, text in item["options"]:
                    st.markdown(f"{key}. {text}")
                st.write("")
        topic_preview = (st.session_state.get("src_text","") or "this topic").split("\\n")[0]
        date_str = now_str()
        file_name = sanitize_filename(f"ADI_Lesson{st.session_state['lesson']}_Week{st.session_state['week']}_{date_str}_MCQPaper.docx")
        docx_bytes = export_mcq_docx(mcqs, int(st.session_state["week"]), int(st.session_state["lesson"]), topic_preview)
        if docx_bytes:
            st.download_button("⬇️ Download MCQ Paper (.docx)", data=docx_bytes, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

with TABS[1]:
    st.subheader("Skills Activities")
    policy_now = st.session_state.get("_policy", policy_for_week(int(st.session_state["week"])))
    options_acts = POLICY_VERBS[policy_now]
    if not st.session_state.get("_verbs_acts_initialized"):
        default_acts = [v for v in st.session_state.get("verbs_acts", []) if v in options_acts] or options_acts
        st.multiselect("Pick verbs", options=options_acts, default=default_acts, key="verbs_acts")
        st.session_state["_verbs_acts_initialized"] = True
    else:
        st.multiselect("Pick verbs", options=options_acts, key="verbs_acts")
    act_count = st.slider("How many ideas?", min_value=3, max_value=10, value=6)
    if st.button("Generate Activities", type="primary"):
        acts = build_activities(st.session_state.get("src_text",""), st.session_state["verbs_acts"], int(st.session_state["week"]), int(st.session_state["lesson"]), int(act_count))
        st.session_state["_acts"] = acts
    acts = st.session_state.get("_acts", [])
    if acts:
        with st.expander("Activity ideas", expanded=True):
            for i, idea in enumerate(acts, start=1): st.markdown(f"**{i}.** {idea}")

with TABS[2]:
    st.subheader("Revision Prompts")
    st.caption("Quick prompts learners can answer after class. Based on the same policy verbs.")
    policy_now = st.session_state.get("_policy", policy_for_week(int(st.session_state["week"]))); verbs = POLICY_VERBS[policy_now]
    topic = (st.session_state.get("src_text","") or "this topic").split("\\n")[0]
    rnd = seeded_random(f"rev::{policy_now}::{topic}")
    for p in [f"In 2–3 sentences, **{rnd.choice(verbs)}** the key idea from {topic}.", f"Create one MCQ that **{rnd.choice(verbs)}** {topic} and provide the answer.", f"Write a real‑life example that **{rnd.choice(verbs)}** {topic}."]:
        st.markdown(f"- {p}")
st.caption("ADI Builder • Green UI • Stable upload • Policy verbs auto‑select • v1.2")
