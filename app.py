import os
import io
import re
import hashlib
from pathlib import Path
from datetime import datetime
import random

import streamlit as st

# =====================
# PAGE SETUP
# =====================
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# =====================
# THEME & STYLES
# =====================
STYLES = """
<style>
:root { --adi-green: #245a34; }
[data-testid="stHeader"] { height: 0px; }
.block-container { padding-top: 56px !important; }

.stButton>button { background: var(--adi-green) !important; color: #fff !important; border: 1px solid rgba(0,0,0,0.06); border-radius: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
.stButton>button:hover { filter: brightness(0.95); }

.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { background-color: rgba(36,90,52,0.08); color: var(--adi-green); border-radius: 999px; padding: 8px 16px; border: 1px solid rgba(36,90,52,0.25); }
.stTabs [aria-selected="true"] { background-color: var(--adi-green) !important; color: #fff !important; border: 1px solid var(--adi-green) !important; }

[data-baseweb="tag"] { background: rgba(36,90,52,0.12) !important; color: var(--adi-green) !important; border: 1px solid rgba(36,90,52,0.35) !important; }
.stTextArea textarea, .stTextInput input, .stSelectbox div[role="combobox"], .stMultiSelect div[role="combobox"] { box-shadow: 0 0 0 2px rgba(36,90,52,0.25) !important; }
input[type="range"], .stSlider input[type="range"] { accent-color: var(--adi-green) !important; }

/* compact preview text */
.mcq-item { margin-bottom: 10px; }
.mcq-q { font-weight: 600; }
.mcq-opt { margin-left: 12px; }
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)

# =====================
# SESSION DEFAULTS
# =====================
if "week" not in st.session_state: st.session_state["week"] = 1
if "lesson" not in st.session_state: st.session_state["lesson"] = 1
if "src_text" not in st.session_state: st.session_state["src_text"] = ""

# =====================
# BLOOM / POLICY VERBS
# =====================
DEFAULT_VERBS = {
    "Remember": ["define","list","recall","name","identify","label","match","recognize","select","state"],
    "Understand": ["describe","explain","summarize","classify","compare","discuss","illustrate","interpret","paraphrase","report"],
    "Apply": ["apply","execute","implement","solve","use","demonstrate","carry out","perform"],
    "Analyze": ["analyze","differentiate","organize","attribute","compare/contrast","structure","examine","question","test"],
    "Evaluate": ["evaluate","argue","assess","critique","defend","judge","justify","select (criteria)","support","value"],
    "Create": ["design","assemble","construct","develop","formulate","author","plan","produce","compose"]
}
def uniq(seq): return sorted(dict.fromkeys([str(s).strip().lower() for s in seq if str(s).strip()]))
def policy_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    return "High"
POLICY_VERBS = {
    "Low":    uniq(DEFAULT_VERBS["Remember"] + DEFAULT_VERBS["Understand"]),
    "Medium": uniq(DEFAULT_VERBS["Apply"]    + DEFAULT_VERBS["Analyze"]),
    "High":   uniq(DEFAULT_VERBS["Evaluate"] + DEFAULT_VERBS["Create"]),
}
def policy_caption(week:int) -> str:
    pol = policy_for_week(week)
    rng = "Weeks 1–4" if pol=="Low" else ("Weeks 5–9" if pol=="Medium" else "Weeks 10–14")
    return f"**ADI Policy:** {rng} → {pol} level verbs are recommended and preselected."

# =====================
# FILE EXTRACTION (CACHED)
# =====================
@st.cache_data(show_spinner=False, ttl=3600)
def extract_text_from_file(path: str, ext: str, max_chars: int = 6000) -> str:
    ext = (ext or "").lower()
    text = ""
    try:
        if ext == ".pdf":
            import fitz  # PyMuPDF
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

# =====================
# UTILS
# =====================
def seeded_random(seed_str: str):
    rnd = random.Random(); rnd.seed(seed_str); return rnd
def now_str() -> str: return datetime.now().strftime("%Y-%m-%d")
def sanitize_filename(name: str) -> str: return re.sub(r"[^A-Za-z0-9_\\-]+", "_", name).strip("_")

# =====================
# GENERATORS (LLM-FREE PLACEHOLDERS)
# =====================
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
    letters = ["A","B","C","D"]
    out = []
    for i in range(1, n+1):
        verb = rnd.choice(verbs)
        stem = rnd.choice(stems).format(verb=verb, topic=topic)
        correct = f"A precise choice that aligns with '{verb}' for {topic}."
        distractors = [
            f"A loosely related idea not focused on '{verb}'.",
            f"An off-topic detail unrelated to {topic}.",
            f"A common misconception about {topic}.",
        ]
        opts = [correct] + distractors
        order = list(range(4))
        if enable_mix: rnd.shuffle(order)
        mixed = [opts[idx] for idx in order]
        correct_key = letters[order.index(0)]
        out.append({"q": stem, "options": list(zip(letters, mixed)), "correct_key": correct_key})
    return out

def build_activities(topic_text: str, verbs: list[str], week: int, lesson: int, count: int = 6):
    topic = (topic_text or "this topic").strip()
    seed = f"acts::{week}::{lesson}::{hashlib.sha1(topic.encode('utf-8')).hexdigest()}"
    rnd = seeded_random(seed)
    if not verbs: verbs = POLICY_VERBS[policy_for_week(week)]
    verbs = uniq(verbs)
    templates = [
        "Small-group task: {verb} key points from {topic} and share back in 3 bullets.",
        "Pair work: {verb} a real-world example related to {topic}.",
        "Individual: {verb} a 5‑step checklist for {topic}.",
        "Whole-class: {verb} misconceptions around {topic} and correct them.",
        "Hands‑on: {verb} a quick demo to illustrate {topic}.",
        "Exit ticket: {verb} one insight from {topic}.",
    ]
    ideas = []
    for i in range(count):
        ideas.append(templates[i % len(templates)].format(verb=rnd.choice(verbs), topic=topic))
    return ideas

# =====================
# EXPORTERS (DOCX + GIFT)
# =====================
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

def export_lesson_plan_docx(acts, week:int, lesson:int, topic_preview:str="") -> bytes:
    try:
        from docx import Document
    except Exception:
        st.error("python-docx is required to export .docx. Add it to requirements.txt")
        return b""
    doc = Document()
    doc.add_heading(f"ADI Lesson Plan – Week {week}, Lesson {lesson}", level=1)
    if topic_preview:
        p = doc.add_paragraph(f"Topic: {topic_preview[:120]}"); p.runs[0].italic = True
    doc.add_heading("Objectives (verb-aligned)", level=2)
    doc.add_paragraph("• See activities below; each uses an ADI policy-aligned verb.")
    doc.add_heading("Activities", level=2)
    for i, a in enumerate(acts, start=1):
        doc.add_paragraph(f"{i}. {a}")
    doc.add_heading("Assessment", level=2)
    doc.add_paragraph("• Use exported MCQ paper or short written responses based on policy verbs.")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_moodle_gift(mcqs) -> bytes:
    # Simple GIFT: one correct (first match of correct_key), 3 distractors
    lines = []
    for i, item in enumerate(mcqs, start=1):
        prompt = re.sub(r"[{}~=#:]", "", item["q"])  # strip reserved
        correct_key = item["correct_key"]
        correct = ""
        wrongs = []
        for key, text in item["options"]:
            cleaned = re.sub(r"[{}~=#:]", "", text)
            if key == correct_key:
                correct = cleaned
            else:
                wrongs.append(cleaned)
        if not correct:  # safety
            correct = wrongs.pop(0) if wrongs else "Correct"
        body = "{" + "=" + correct + "~" + "~".join(wrongs) + "}"
        lines.append(f"::Q{i}:: {prompt} {body}")
    return ("\n\n".join(lines)).encode("utf-8")

# =====================
# SIDEBAR (UPLOAD + CONTROLS)
# =====================
with st.sidebar:
    try:
        st.image("Logo.png", width=140)
    except Exception:
        pass

    st.header("Upload PDF / DOCX / PPTX")
    uploaded = st.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"], key="uploader")
    if uploaded:
        buf = uploaded.getbuffer(); fhash = hashlib.sha1(buf).hexdigest()
        meta = st.session_state.get("_file_meta")
        if not meta or meta.get("hash") != fhash:
            ext = Path(uploaded.name).suffix.lower()
            save_path = f"/tmp/adi_{fhash}{ext}"
            with open(save_path, "wb") as f: f.write(buf)
            st.session_state["_file_meta"] = {"name": uploaded.name, "size": uploaded.size, "hash": fhash, "path": save_path, "ext": ext}
            if st.session_state.get("_last_uploaded_hash") != fhash:
                st.toast(f"Uploaded ✓ {uploaded.name}", icon="✅")
                st.session_state["_last_uploaded_hash"] = fhash
        meta = st.session_state["_file_meta"]
        st.success(f"File ready: **{meta['name']}**")

    # Week / Lesson
    st.write("Week")
    st.session_state["week"] = st.selectbox("Week", list(range(1,15)), index=st.session_state["week"]-1, key="week_select")
    st.write("Lesson")
    st.session_state["lesson"] = st.selectbox("Lesson", list(range(1,21)), index=st.session_state["lesson"]-1, key="lesson_select")

    # Policy sync; clear verb picks on week change to avoid widget default warnings
    policy_now = policy_for_week(int(st.session_state["week"]))
    _prev_week = st.session_state.get("_prev_week")
    if _prev_week != st.session_state["week"]:
        st.session_state.pop("verbs_mcq", None)
        st.session_state.pop("verbs_acts", None)
    st.session_state["_prev_week"] = st.session_state["week"]
    st.caption(policy_caption(int(st.session_state["week"])))

# =====================
# TOP ACTION BAR (Lesson Plan / E‑Book / Moodle)
# =====================
col_lp, col_eb, col_md = st.columns([1,1,1])
export_lp = col_lp.button("📘 Export Lesson Plan (.docx)")
export_eb = col_eb.button("📖 Export E‑Book (.docx)")
export_md = col_md.button("🎓 Export Moodle (.gift)")

# =====================
# TABS
# =====================
tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ---------- MCQs ----------
with tabs[0]:
    st.subheader("MCQ Generator")
    st.markdown("**Source text (optional)**")
    c1, c2 = st.columns([1, 0.35])
    with c1:
        st.session_state["src_text"] = st.text_area(
            "Paste lesson/topic text (improves MCQs)",
            value=st.session_state.get("src_text", ""),
            height=140, label_visibility="collapsed"
        )
    with c2:
        meta = st.session_state.get("_file_meta")
        if meta and st.button("📄 Use uploaded text", help="Extract text from the uploaded file and drop it here"):
            txt = extract_text_from_file(meta["path"], meta["ext"])
            if txt:
                st.session_state["src_text"] = txt; st.success("Text extracted from file.")
            else:
                st.warning("Couldn’t extract text from this file—paste content manually.")

    policy_now = policy_for_week(int(st.session_state["week"]))
    options_mcq = POLICY_VERBS[policy_now]
    if "verbs_mcq" not in st.session_state:
        st.multiselect("Verb picker", options=options_mcq, default=options_mcq, key="verbs_mcq")
    else:
        st.multiselect("Verb picker", options=options_mcq, key="verbs_mcq")

    ca, cb, cc = st.columns([0.5,0.5,1])
    with ca: n_q = st.number_input("# of MCQs", min_value=3, max_value=30, value=10, step=1)
    with cb: mix_answers = st.checkbox("Mix answer letters", value=True)
    with cc: variant = st.number_input("Variant (deterministic seed)", min_value=0, max_value=9999, value=0, step=1)

    if st.button("Generate MCQs", type="primary"):
        mcqs = build_mcqs(st.session_state.get("src_text",""), st.session_state.get("verbs_mcq", []),
                          int(n_q), int(variant), bool(mix_answers),
                          int(st.session_state["week"]), int(st.session_state["lesson"]))
        st.session_state["_mcqs"] = mcqs

    mcqs = st.session_state.get("_mcqs", [])
    if mcqs:
        st.success(f"Generated {len(mcqs)} MCQs.")
        with st.expander("Preview (compact)", expanded=True):
            for i, item in enumerate(mcqs, start=1):
                st.markdown(f"<div class='mcq-item'><div class='mcq-q'>{i}. {item['q']}</div>" +
                            "".join([f\"<div class='mcq-opt'>{k}. {re.sub(r'[<>]', '', v)}</div>\" for k,v in item['options']]) +
                            \"</div>\", unsafe_allow_html=True)

# ---------- ACTIVITIES ----------
with tabs[1]:
    st.subheader("Skills Activities")
    policy_now = policy_for_week(int(st.session_state["week"]))
    options_acts = POLICY_VERBS[policy_now]
    if "verbs_acts" not in st.session_state:
        st.multiselect("Pick verbs", options=options_acts, default=options_acts, key="verbs_acts")
    else:
        st.multiselect("Pick verbs", options=options_acts, key="verbs_acts")
    act_count = st.slider("How many ideas?", min_value=3, max_value=10, value=6)
    if st.button("Generate Activities", type="primary"):
        acts = build_activities(st.session_state.get("src_text",""),
                                st.session_state.get("verbs_acts", []),
                                int(st.session_state["week"]), int(st.session_state["lesson"]), int(act_count))
        st.session_state["_acts"] = acts
    acts = st.session_state.get("_acts", [])
    if acts:
        with st.expander("Activity ideas", expanded=True):
            for i, idea in enumerate(acts, start=1): st.markdown(f"**{i}.** {idea}")

# ---------- REVISION ----------
with tabs[2]:
    st.subheader("Revision Prompts")
    st.caption("Quick prompts learners can answer after class. Based on the same policy verbs.")
    policy_now = policy_for_week(int(st.session_state["week"]))
    verbs = POLICY_VERBS[policy_now]
    topic = (st.session_state.get("src_text","") or "this topic").split("\\n")[0]
    rnd = seeded_random(f"rev::{policy_now}::{topic}")
    prompts = [
        f"In 2–3 sentences, **{rnd.choice(verbs)}** the key idea from {topic}.",
        f"Create one MCQ that **{rnd.choice(verbs)}** {topic} and provide the answer.",
        f"Write a real‑life example that **{rnd.choice(verbs)}** {topic}.",
    ]
    for p in prompts: st.markdown(f"- {p}")

# =====================
# ACTION BAR HANDLERS
# =====================
topic_preview = (st.session_state.get("src_text","") or "this topic").split("\\n")[0]
week, lesson = int(st.session_state["week"]), int(st.session_state["lesson"])

if export_lp:
    acts = st.session_state.get("_acts")
    if not acts:
        st.warning("Generate activities first in the 'Skills Activities' tab.")
    else:
        data = export_lesson_plan_docx(acts, week, lesson, topic_preview)
        fname = sanitize_filename(f"ADI_LessonPlan_Week{week}_Lesson{lesson}_{now_str()}.docx")
        st.download_button("⬇️ Download Lesson Plan (.docx)", data=data, file_name=fname,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

if export_eb:
    text = st.session_state.get("src_text","").strip()
    if not text:
        st.warning("Add source text or click '📄 Use uploaded text' first.")
    else:
        # Build a simple 'ebook' as a .docx from the source text (placeholder)
        try:
            from docx import Document
            doc = Document(); doc.add_heading(f"Lesson E‑Book – Week {week}, Lesson {lesson}", level=1)
            for para in text.split("\\n"):
                if para.strip(): doc.add_paragraph(para.strip())
            bio = io.BytesIO(); doc.save(bio); data = bio.getvalue()
            fname = sanitize_filename(f"ADI_EBook_Week{week}_Lesson{lesson}_{now_str()}.docx")
            st.download_button("⬇️ Download E‑Book (.docx)", data=data, file_name=fname,
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception:
            st.error("python-docx is required for E‑Book export. Add it to requirements.txt")

if export_md:
    mcqs = st.session_state.get("_mcqs")
    if not mcqs:
        st.warning("Generate MCQs first in the 'Knowledge MCQs' tab.")
    else:
        gift = export_moodle_gift(mcqs)
        fname = sanitize_filename(f"ADI_Moodle_Week{week}_Lesson{lesson}_{now_str()}.gift")
        st.download_button("⬇️ Download Moodle GIFT (.gift)", data=gift, file_name=fname, mime="text/plain")

# Footer
st.caption("ADI Builder • v1.4 • Green UI • Stable upload • Policy verbs • Lesson Plan / E‑Book / Moodle exports")
