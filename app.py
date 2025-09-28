# app.py — ADI Builder (single-file Streamlit app)
# Tom Johnson (@tjohnson) — ADI / LCI Workspace
# Dependencies (install as needed):
#   pip install streamlit python-docx python-pptx pymupdf
# Optional: pip install lxml
#
# This app follows the ADI brand palette:
#   Green #245a34, Gold #C8A85A, stone background, minimal UI.
#   Pill-style radios for Lesson (1–5) and Week (1–14).
#   Bloom policy mapping: Weeks 1–4 Low, 5–9 Medium, 10–14 High.
#
# NOTE: No API keys required. If you later add a model, keep keys in env/secrets only.

from __future__ import annotations
import io
import re
import textwrap
from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st

# Try optional parsers for file types
def _safe_imports():
    mods = {}
    try:
        import fitz  # PyMuPDF
        mods["fitz"] = fitz
    except Exception:
        mods["fitz"] = None
    try:
        from pptx import Presentation
        mods["pptx"] = Presentation
    except Exception:
        mods["pptx"] = None
    try:
        import docx  # python-docx
        mods["docx"] = docx
    except Exception:
        mods["docx"] = None
    return mods

MODS = _safe_imports()

# ---------- Config ----------
st.set_page_config(
    page_title="ADI Builder — Upload → Setup → Generate → Export",
    page_icon="📘",
    layout="wide"
)

# ---------- Styles ----------
CSS = f"""
:root {{
  --adi-green: #245a34;
  --adi-gold: #C8A85A;
  --stone-100: #f5f5f4;
  --stone-200: #e7e5e4;
  --stone-300: #d6d3d1;
  --text-900: #111827;
}}
/* Base look */
[data-testid="stAppViewContainer"] > .main {{
  background: linear-gradient(180deg, var(--stone-100), #fff);
}}
.block-container {{
  padding-top: 1.5rem;
  padding-bottom: 3rem;
  max-width: 1200px;
}}
h1, h2, h3 {{ color: var(--text-900); }}
.smallnote {{ color:#475569; font-size:0.86rem; }}

/* Step header */
.stepbar {{
  display:flex; gap:.5rem; align-items:center; flex-wrap:wrap;
  padding: .4rem .6rem; border:1px dashed var(--stone-300); border-radius:14px; background:#fff;
}}
.stepbar .step {{
  display:flex; align-items:center; gap:.5rem;
  font-weight:700; padding:.45rem .75rem; border-radius:999px; background:var(--stone-200);
  border:1px solid var(--stone-300);
}}
.stepbar .step.active {{
  background: #fff; border-color: var(--adi-gold); box-shadow: 0 0 0 2px rgba(200,168,90,.2);
}}
.stepbar .step .num {{
  display:inline-flex; width:24px; height:24px; align-items:center; justify-content:center;
  font-weight:800; border-radius:999px; background:var(--adi-green); color:#fff;
}}

/* Pills (policy + radios look) */
.pills {{
  display:flex; flex-wrap:wrap; gap:.5rem;
}}
.pill, .stRadio > div [role="radiogroup"] label span {{
  background:#fff; border:2px solid rgba(0,0,0,.08); border-radius:999px;
  padding:.45rem .85rem; font-weight:700;
}}
.pill.current {{ border-color: var(--adi-gold); box-shadow: inset 0 0 0 3px var(--adi-gold); }}
.pill.match {{ background:#e8f5ee; border-color:#1f7a4c; }}
.pill.mismatch {{ background:#fff7ed; border-color:#fed7aa; }}

/* Bloom badge */
.badge-ok, .badge-warn {{
  display:inline-flex; align-items:center; font-weight:700; margin-top:.35rem;
  border-radius:10px; padding:.35rem .6rem; border:1px solid transparent;
}}
.badge-ok {{ background:#e8f5ee; color:#14532d; border-color:#86efac; }}
.badge-warn {{ background:#fff7ed; color:#7c2d12; border-color:#fdba74; }}

/* Buttons */
.stButton > button {{ border-radius:12px; border:2px solid var(--adi-green); }}
.stDownloadButton > button {{ border-radius:12px; border:2px solid var(--adi-gold); }}

/* Horizontal radios */
.stRadio > div[role="radiogroup"] {{ display:flex; gap:.5rem; flex-wrap:wrap; }}
.stRadio > div [role="radio"] {{ padding:.1rem 0; }}

hr.soft {{ border:none; border-top:1px solid var(--stone-300); margin: 0.75rem 0 1rem; }}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ---------- Constants ----------
BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
BLOOM_TIER = {
    "Remember": "Low",
    "Understand": "Low",
    "Apply": "Medium",
    "Analyze": "Medium",
    "Evaluate": "High",
    "Create": "High",
}

BLOOM_VERBS = {
    "Remember": ["define", "list", "recall", "identify", "label", "name", "state", "match", "recognize", "outline", "select", "repeat"],
    "Understand": ["explain", "summarize", "classify", "describe", "discuss", "interpret", "paraphrase", "compare", "illustrate", "infer"],
    "Apply": ["apply", "demonstrate", "execute", "implement", "solve", "use", "calculate", "perform", "simulate", "carry out"],
    "Analyze": ["analyze", "differentiate", "organize", "attribute", "deconstruct", "compare/contrast", "examine", "test", "investigate"],
    "Evaluate": ["evaluate", "argue", "assess", "defend", "judge", "justify", "critique", "recommend", "prioritize", "appraise"],
    "Create": ["create", "design", "compose", "construct", "develop", "plan", "produce", "propose", "assemble", "formulate"],
}

POLICY_HELP = "ADI policy: Weeks 1–4 = Low, 5–9 = Medium, 10–14 = High"

def policy_tier(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    if 5 <= week <= 9:
        return "Medium"
    return "High"  # 10–14

# ---------- Session State ----------
if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "topics" not in st.session_state:
    st.session_state.topics = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if "activities" not in st.session_state:
    st.session_state.activities = []
if "char_count" not in st.session_state:
    st.session_state.char_count = 0

# ---------- Helpers ----------
def extract_text_from_pdf(file) -> str:
    if MODS["fitz"] is None:
        st.warning("PyMuPDF is not installed. Install with: `pip install pymupdf` to parse PDFs.")
        return ""
    fitz = MODS["fitz"]
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            parts = []
            for page in doc:
                parts.append(page.get_text("text"))
            return "\n".join(parts)
    except Exception as e:
        st.error(f"PDF parse error: {e}")
        return ""

def extract_text_from_pptx(file) -> str:
    if MODS["pptx"] is None:
        st.warning("python-pptx is not installed. Install with: `pip install python-pptx` to parse PPTX.")
        return ""
    Presentation = MODS["pptx"]
    try:
        prs = Presentation(file)
        texts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    texts.append(shape.text)
        return "\n".join(texts)
    except Exception as e:
        st.error(f"PPTX parse error: {e}")
        return ""

def extract_text_from_docx(file) -> str:
    docx_mod = MODS["docx"]
    if docx_mod is None:
        st.warning("python-docx is not installed. Install with: `pip install python-docx` to parse DOCX.")
        return ""
    try:
        doc = docx_mod.Document(file)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        st.error(f"DOCX parse error: {e}")
        return ""

def simple_topic_lines(txt: str, max_topics: int = 25) -> List[str]:
    """Very light topic extraction: title-ish lines, deduped."""
    topics = []
    seen = set()
    for raw in txt.splitlines():
        line = raw.strip()
        if not line:
            continue
        if len(line) < 6 or len(line) > 90:
            continue
        # Title-ish heuristics
        if (line.istitle() or line.isupper() or re.match(r"^\d+[\).\s-]", line)) and not line.endswith(":"):
            key = line.lower()
            if key not in seen:
                topics.append(line)
                seen.add(key)
        if len(topics) >= max_topics:
            break
    # Fallback: grab first sentences
    if not topics:
        para = re.split(r"\n\s*\n", txt, maxsplit=1)[0] if txt else ""
        topics = [t.strip() for t in re.split(r"[.·••]\s+", para) if 6 <= len(t.strip()) <= 80][:8]
    return topics

def bloom_to_tier(level: str) -> str:
    return BLOOM_TIER.get(level, "Low")

def make_policy_pills(required: str, selected_tier: str) -> str:
    """Return HTML for 3 policy pills with highlighting and match status."""
    pill = {"Low":"pill", "Medium":"pill", "High":"pill"}
    pill[required] += " current"
    if selected_tier == required:
        pill[selected_tier] += " match"
        badge = '<div class="badge-ok">✓ ADI policy matched</div>'
    else:
        pill[selected_tier] += " mismatch"
        badge = f'<div class="badge-warn">Week requires {required}. Selected tier is {selected_tier}.</div>'
    return f"""
    <div class="pills">
      <span class="{pill['Low']}">Low</span>
      <span class="{pill['Medium']}">Medium</span>
      <span class="{pill['High']}">High</span>
    </div>
    {badge}
    """

def build_mcqs(topics: List[str], verbs: List[str], level: str, n: int = 5) -> List[str]:
    """Template-based MCQs (non-LLM) — simple placeholders using verbs and topics."""
    qs = []
    vcycle = (verbs * ((n // max(1, len(verbs))) + 1))[:n] if verbs else ["identify"] * n
    tcycle = (topics * ((n // max(1, len(topics))) + 1))[:n] if topics else [f"topic {i+1}" for i in range(n)]
    for i in range(n):
        v = vcycle[i].capitalize()
        t = tcycle[i]
        stem = f"{v} the MOST appropriate statement about: {t}."
        opts = [
            f"A) A correct point about {t}.",
            f"B) An incorrect detail about {t}.",
            f"C) Another incorrect detail about {t}.",
            f"D) A distractor unrelated to {t}.",
        ]
        mcq = stem + "\n" + "\n".join(opts) + "\nAnswer: A"
        qs.append(mcq)
    return qs

def build_activities(topics: List[str], verbs: List[str], level: str, n: int = 3) -> List[str]:
    acts = []
    vcycle = (verbs * ((n // max(1, len(verbs))) + 1))[:n] if verbs else ["discuss"] * n
    tcycle = (topics * ((n // max(1, len(topics))) + 1))[:n] if topics else [f"topic {i+1}" for i in range(n)]
    for i in range(n):
        v = vcycle[i].capitalize()
        t = tcycle[i]
        if level in ("Evaluate", "Create"):
            prompt = f"{v} and present a structured solution/prototype for: {t}."
        elif level in ("Apply", "Analyze"):
            prompt = f"{v} and demonstrate/apportion key components of: {t}."
        else:
            prompt = f"{v} and summarize the core idea of: {t}."
        acts.append(f"Activity {i+1}: {prompt}")
    return acts

def as_gift(mcqs: List[str]) -> str:
    gift_blocks = []
    for i, q in enumerate(mcqs, 1):
        lines = q.splitlines()
        stem = lines[0]
        choices = [ln for ln in lines[1:] if re.match(r"^[A-D]\)", ln)]
        correct = "A"  # as templated
        gift = f"::Q{i}:: {stem} {{\n"
        for ch in choices:
            letter = ch.split(")")[0]
            text = ch.split(") ", 1)[1] if ") " in ch else ch
            if letter == correct:
                gift += f"  = {text}\n"
            else:
                gift += f"  ~ {text}\n"
        gift += "}\n"
        gift_blocks.append(gift)
    return "\n".join(gift_blocks)

def download_bytes(text: str, filename: str) -> None:
    st.download_button("⬇️ Download", data=text.encode("utf-8"), file_name=filename, mime="text/plain")

def download_docx(questions: List[str], activities: List[str], filename: str = "adi_builder_export.docx"):
    if MODS["docx"] is None:
        st.warning("Install python-docx to export .docx (`pip install python-docx`).")
        return
    import docx  # type: ignore
    doc = docx.Document()
    doc.add_heading("ADI Builder Export", level=1)
    doc.add_paragraph(POLICY_HELP)
    doc.add_heading("MCQs", level=2)
    for q in questions:
        doc.add_paragraph(q)
    doc.add_heading("Activities", level=2)
    for a in activities:
        doc.add_paragraph(a)
    bio = io.BytesIO()
    doc.save(bio)
    st.download_button("⬇️ Download .docx", data=bio.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ---------- Header ----------
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://dummyimage.com/80x80/245a34/ffffff.png&text=ADI", caption="ADI", use_column_width=False)
with col2:
    st.markdown("""
    <div class="stepbar">
      <div class="step active"><span class="num">1</span> Upload</div>
      <div class="step"><span class="num">2</span> Setup</div>
      <div class="step"><span class="num">3</span> Generate</div>
      <div class="step"><span class="num">4</span> Export</div>
    </div>
    """, unsafe_allow_html=True)

tabs = st.tabs(["① Upload", "② Setup", "③ Generate", "④ Export (Step 4)"])

# ---------- Tab 1: Upload ----------
with tabs[0]:
    st.subheader("Upload source")
    st.caption("Clean, polished ADI look · Strict colors · Logo required")
    upcol1, upcol2 = st.columns([3, 2])

    with upcol1:
        file = st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)", type=["pdf", "pptx", "docx"], accept_multiple_files=False)
        pasted = st.text_area("Or paste source text manually", height=140, placeholder="Paste any relevant lesson/topic text here…")
        if st.button("Process"):
            text = ""
            if pasted and pasted.strip():
                text = pasted.strip()
            elif file is not None:
                suffix = file.name.lower().split(".")[-1]
                if suffix == "pdf":
                    text = extract_text_from_pdf(file)
                elif suffix == "pptx":
                    text = extract_text_from_pptx(file)
                elif suffix == "docx":
                    text = extract_text_from_docx(file)
                else:
                    st.error("Unsupported file type.")
                    text = ""
            else:
                st.info("Please upload a file or paste text, then click Process.")
            st.session_state.source_text = text
            st.session_state.char_count = len(text)
            st.session_state.topics = simple_topic_lines(text) if text else []
            if text:
                st.success(f"✓ Processed: {len(text):,} chars")
    with upcol2:
        if st.session_state.char_count:
            st.info(f"**Selected:** {st.session_state.char_count:,} characters loaded")
            with st.expander("Detected topics"):
                if st.session_state.topics:
                    for t in st.session_state.topics:
                        st.write("• " + t)
                else:
                    st.caption("No headings found — generation will still work.")

    st.markdown('<hr class="soft" />', unsafe_allow_html=True)
    st.caption("Security: API keys (if used) stay server-side (env or .streamlit/secrets). Never accept keys via UI.")

# ---------- Tab 2: Setup ----------
with tabs[1]:
    st.subheader("Setup")
    lcol, rcol = st.columns([2, 3], vertical_alignment="top")
    with lcol:
        lesson = st.radio("Lesson", options=[1,2,3,4,5], index=0, horizontal=True)
        week = st.radio("Week", options=list(range(1,15)), index=0, horizontal=True, help=POLICY_HELP)
        level = st.radio("Bloom’s Level", options=BLOOM_LEVELS, index=0, horizontal=True)
        required_tier = policy_tier(int(week))
        selected_tier = bloom_to_tier(level)
        st.caption("Policy vs Selected:")
        st.markdown(make_policy_pills(required_tier, selected_tier), unsafe_allow_html=True)

    with rcol:
        st.caption("Pick **5–10** verbs for your outcomes (auto-filtered by Bloom’s level).")
        verbs_all = BLOOM_VERBS.get(level, [])
        default_take = min(5, len(verbs_all))
        verbs = st.multiselect("Verbs", options=verbs_all, default=verbs_all[:default_take])
        if not (5 <= len(verbs) <= 10):
            st.warning(f"Select between 5 and 10 verbs. Currently: {len(verbs)}")
        else:
            st.success("Verb count looks good ✅")

        st.text_area("Notes (optional)", height=100, placeholder="Any constraints, context, or examples to guide generation…")

# ---------- Tab 3: Generate ----------
with tabs[2]:
    st.subheader("Generate")
    gcol1, gcol2 = st.columns([3,2], vertical_alignment="top")
    with gcol1:
        n_mcq = st.slider("How many MCQs?", 3, 20, 5, 1)
        n_act = st.slider("How many activities?", 1, 10, 3, 1)
        do_gen = st.button("⚡ Generate")
        if do_gen:
            topics = st.session_state.topics or ["Core Concepts", "Key Terms", "Use Cases", "Risks", "Summary"]
            st.session_state.questions = build_mcqs(topics, verbs, level, n_mcq)
            st.session_state.activities = build_activities(topics, verbs, level, n_act)
            st.success("Content generated. Check previews and proceed to Export.")
        if st.session_state.questions:
            st.markdown("#### MCQ Preview")
            for i, q in enumerate(st.session_state.questions, 1):
                with st.expander(f"MCQ {i}"):
                    st.text(q)
    with gcol2:
        if st.session_state.activities:
            st.markdown("#### Activities")
            for a in st.session_state.activities:
                st.write("• " + a)
        else:
            st.info("No activities yet. Click **Generate** to populate.")

# ---------- Tab 4: Export ----------
with tabs[3]:
    st.subheader("Export (Step 4)")
    if not st.session_state.questions:
        st.info("Generate content first in Step 3.")
    else:
        tcol1, tcol2, tcol3 = st.columns(3)
        with tcol1:
            txt_payload = "\n\n".join(st.session_state.questions + [""] + st.session_state.activities)
            st.download_button("⬇️ Download .txt", data=txt_payload.encode("utf-8"), file_name="adi_builder_export.txt", mime="text/plain")
        with tcol2:
            gift_payload = as_gift(st.session_state.questions)
            st.download_button("⬇️ Download Moodle GIFT", data=gift_payload.encode("utf-8"), file_name="adi_mcqs.gift", mime="text/plain")
        with tcol3:
            download_docx(st.session_state.questions, st.session_state.activities)

    st.caption("Tip: All exports are generated locally in your browser session.")


