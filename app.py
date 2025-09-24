# app.py — ADI Builder V3 (polished UI, sidebar master, mirrored context, policy-aligned MCQs & Activities)

import base64
import io
import os
import re
import random
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

# Optional parsers for uploads (install if desired):
#   pip install python-docx python-pptx PyPDF2
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

# ----------------------------- CSS (polished look + pill highlights) -----------------------------
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

/* SIDEBAR (cards + caps with gold dot) */
section[data-testid='stSidebar']>div{background:linear-gradient(180deg,#F3F2ED,#F7F7F4); height:100%}
.side-card{background:#fff; border:1px solid var(--border); border-radius:18px; padding:14px 14px 16px; margin:14px 8px; box-shadow:0 8px 18px rgba(0,0,0,.06)}
.side-cap{display:flex; align-items:center; gap:10px; font-size:12px; color:var(--adi-green); text-transform:uppercase; letter-spacing:.08em; font-weight:700; margin:0 0 8px}
.side-cap .dot{width:9px;height:9px;border-radius:999px;background:var(--adi-gold); box-shadow:0 0 0 4px rgba(200,168,90,.18)}
.rule{height:2px; background:linear-gradient(90deg,var(--adi-gold),transparent); border:0; margin:8px 0 10px}

/* uploader */
section[data-testid='stSidebar'] div[data-testid="stFileUploaderDropzone"]{border-radius:14px; border:1px dashed #cfd6cf; background:#ffffff; margin-top:8px}
section[data-testid='stSidebar'] div[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--adi-green); box-shadow:0 0 0 3px rgba(36,90,52,.12)}

/* radio pills (sidebar quick picks) */
section[data-testid='stSidebar'] [role='radiogroup'] label{
  border:1px solid var(--border); padding:6px 10px; margin-right:8px; border-radius:999px; background:#fff; box-shadow:0 2px 6px rgba(0,0,0,.04);
}
section[data-testid='stSidebar'] [role='radiogroup'] input:checked + div{
  border-color:var(--adi-gold); box-shadow:0 0 0 3px rgba(200,168,90,.25);
}

/* MAIN CARDS + inputs */
.card{background:var(--card); border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow); padding:16px; margin:10px 0}
.cap{color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; font-size:12px; margin:0 0 10px}
.stTextArea textarea, .stTextInput input{border:2px solid var(--adi-green)!important; border-radius:12px!important}
.stTextArea textarea:focus, .stTextInput input:focus{box-shadow:0 0 0 3px rgba(36,90,52,.18)!important}

/* Tabs underline gold */
[data-testid='stTabs'] button{font-weight:700; color:#445; border-bottom:3px solid transparent}
[data-testid='stTabs'] button[aria-selected='true']{color:var(--adi-green)!important; border-bottom:3px solid var(--adi-gold)!important}

/* BLOOM badges + shaded groups */
.badge{display:inline-flex; align-items:center; justify-content:center; padding:6px 10px; border-radius:999px; border:1px solid var(--border); margin:2px 6px 2px 0; font-weight:600}
.low{background:#eaf5ec; color:#245a34}
.med{background:#f8f3e8; color:#6a4b2d}
.high{background:#f3f1ee; color:#4a4a45}
.policy-group{position:relative; border:1px solid var(--border); border-radius:16px; box-shadow:var(--shadow); padding:12px 12px; margin:10px 0}
.policy-group.low{background:linear-gradient(180deg,#eef6f0,#ffffff)}
.policy-group.med{background:linear-gradient(180deg,#fbf6ec,#ffffff)}
.policy-group.high{background:linear-gradient(180deg,#f5f4f1,#ffffff)}
.policy-label{position:absolute; right:12px; top:10px; font-size:11px; color:#6b7280}

/* Selectable verb pills for Activities (multiselect tags) */
div[data-baseweb="tag"]{border-radius:999px; border:1px solid var(--border)}
div[data-baseweb="tag"][aria-selected="true"]{box-shadow:0 0 0 3px rgba(200,168,90,.25);}

/* confirm CSS loaded */
.adi-badge{position:fixed;top:10px;right:12px;z-index:9999;background:var(--adi-green);color:#fff;padding:6px 10px;border-radius:999px;font-size:12px;box-shadow:0 2px 10px rgba(0,0,0,.15)}
</style>
<div class='adi-badge'>ADI style v14</div>
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
    ss.setdefault("act_selected_verbs", [])  # for activities verb selection

ensure_state()

LOW_VERBS = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate", "analyze"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify"]

ADI_VERBS = {
    "Low": LOW_VERBS,
    "Medium": ["apply", "demonstrate", "interpret", "compare", "solve", "illustrate", "analyze"],
    "High": ["analyze", "evaluate", "justify", "synthesize", "design", "formulate"],
}

def _fallback(text: str | None, default: str) -> str:
    return text.strip() if text and str(text).strip() else default

def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    return "High"

# ----------------------------- Upload parsing -----------------------------
def extract_text_from_upload(up_file) -> str:
    if up_file is None:
        return ""
    name = up_file.name.lower()
    text = ""
    try:
        if name.endswith(".pdf") and PdfReader:
            reader = PdfReader(up_file)
            for page in reader.pages[:12]:
                txt = page.extract_text() or ""
                text += txt + "\n"
        elif name.endswith(".docx") and Document:
            doc = Document(up_file)
            for p in doc.paragraphs[:200]:
                text += (p.text or "") + "\n"
        elif name.endswith(".pptx") and Presentation:
            prs = Presentation(up_file)
            for slide in prs.slides[:35]:
                for shp in slide.shapes:
                    if hasattr(shp, "text") and shp.text:
                        text += shp.text + "\n"
        lines = [ln.strip() for ln in text.replace("\r", "\n").split("\n") if ln.strip()]
        return "\n".join(lines)[:4000]
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ----------------------------- Tiny NLP helpers -----------------------------
_STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","as","is","are","be","was","were",
    "this","that","these","those","it","its","at","from","into","over","under","about","between","within",
    "use","used","using","also","than","which","such","may","can","could","should","would","will","not",
    "if","when","while","after","before","each","per","via","more","most","less","least","other","another",
    "module","lesson","overview","content","contents","terms","questions","glossary","figure","table"
}

def _sentences(text: str) -> list[str]:
    rough = []
    for chunk in text.split("\n"):
        parts = [p.strip() for p in re.split(r"[.\u2022\u2023\u25CF]", chunk)]
        for p in parts:
            if p:
                rough.append(p)
    out = []
    seen = set()
    for s in rough:
        s_clean = re.sub(r"\s+", " ", s).strip()
        if not (30 <= len(s_clean) <= 180):
            continue
        k = s_clean.lower()
        if k not in seen:
            out.append(s_clean)
            seen.add(k)
    return out[:160]

def _keywords(text: str, top_n: int = 20) -> list[str]:
    from collections import Counter
    tokens = []
    for w in re.split(r"[^A-Za-z0-9]+", text):
        w = w.lower()
        if len(w) >= 4 and w not in _STOP:
            tokens.append(w)
    common = Counter(tokens).most_common(top_n * 2)
    roots = []
    for w, _ in common:
        if all(not w.startswith(r[:5]) and not r.startswith(w[:5]) for r in roots):
            roots.append(w)
        if len(roots) >= top_n:
            break
    return roots or ["principles","process","safety","quality","criteria","standards"]

def _find_sentence_with(term: str, sentences: list[str]) -> str | None:
    t = term.lower()
    for s in sentences:
        if t in s.lower():
            return s.strip()
    return None

def _distractors_from_sentences(correct: str, pool: list[str], n: int) -> list[str]:
    rand = random.Random(42)
    ckey = correct.lower()[:60]
    cands = [p for p in pool if p and p.lower()[:60] != ckey and p.lower() != correct.lower()]
    rand.shuffle(cands)
    out = []
    for s in cands:
        if 12 <= len(s.split()) <= 28 and s not in out:
            out.append(s)
        if len(out) == n:
            break
    filler = [
        "This option generalizes beyond the scope defined in the module.",
        "The statement is partially true but misses a required constraint.",
        "This describes a related concept that does not apply in this context.",
    ]
    i = 0
    while len(out) < n:
        out.append(filler[i % len(filler)])
        i += 1
    return out

# ----------------------------- Generators (policy aligned) -----------------------------
def generate_mcq_blocks(topic: str, source: str, num_blocks: int, week: int) -> pd.DataFrame:
    """
    3 MCQs per block (Q1 Low, Q2 Medium, Q3 High), numbered and sorted.
    Correct options mined from source sentences; distractors are near-misses.
    """
    topic = _fallback(topic, "the module")
    sents = _sentences(source) or [f"{topic} covers core concepts, key steps, and typical pitfalls."]
    keys  = _keywords(source or topic, top_n=max(24, num_blocks * 6))

    low_templates = [
        lambda t: f"Which statement correctly defines **{t}** in the context of *{topic}*?",
        lambda t: f"Identify the accurate description of **{t}**.",
        lambda t: f"Recall: what does **{t}** mean for *{topic}*?",
    ]
    med_templates = [
        lambda t: f"When applying **{t}** in *{topic}*, which action is most appropriate?",
        lambda t: f"Which option best interprets how to use **{t}**?",
        lambda t: f"Compare the options — which best operationalises **{t}**?",
    ]
    high_templates = [
        lambda t: f"Which option provides the strongest justification involving **{t}** for *{topic}*?",
        lambda t: f"Analyze: which reasoning about **{t}** is most valid?",
        lambda t: f"Which design choice best satisfies constraints related to **{t}**?",
    ]

    rows: list[dict[str, Any]] = []

    def add_row(block: int, tier: str, stem: str, correct: str, wrongs: list[str]):
        options = [correct] + wrongs[:3]
        rnd = random.Random(2025 + block + len(rows))
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(correct)]
        rows.append({
            "Block": block,
            "Tier": tier,
            "Q#": {"Low": 1, "Medium": 2, "High": 3}[tier],
            "Question": stem.strip(),
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans,
            "Explanation": "Chosen option aligns with the source context.",
            "Order": {"Low": 1, "Medium": 2, "High": 3}[tier],
        })

    for b in range(1, num_blocks + 1):
        t_low  = keys[(b*3 - 3) % len(keys)]
        t_med  = keys[(b*3 - 2) % len(keys)]
        t_high = keys[(b*3 - 1) % len(keys)]

        # LOW
        c1 = _find_sentence_with(t_low, sents) or f"{t_low.capitalize()} is a foundational element of {topic}."
        d1 = _distractors_from_sentences(c1, sents, 3)
        stem1 = low_templates[(b-1) % len(low_templates)](t_low)
        add_row(b, "Low", stem1, c1, d1)

        # MEDIUM
        c2 = _find_sentence_with(t_med, sents) or f"When applying {t_med}, follow steps that respect constraints and safety."
        d2 = _distractors_from_sentences(c2, sents, 3)
        stem2 = med_templates[(b-1) % len(med_templates)](t_med)
        add_row(b, "Medium", stem2, c2, d2)

        # HIGH
        c3 = _find_sentence_with(t_high, sents) or f"An effective approach to {t_high} prioritizes evidence, feasibility, and constraints."
        d3 = _distractors_from_sentences(c3, sents, 3)
        stem3 = high_templates[(b-1) % len(high_templates)](t_high)
        add_row(b, "High", stem3, c3, d3)

    df = pd.DataFrame(rows)
    return df.sort_values(["Block","Order"], kind="stable").reset_index(drop=True)


def generate_activities(count: int, duration: int, tier: str, topic: str, chosen_verbs: list[str],
                        source: str = "", lesson: int = 1, week: int = 1) -> pd.DataFrame:
    """
    Lesson/Week-linked activities with Bloom-appropriate verbs (user-selectable) and timed steps.
    """
    topic = _fallback(topic, "the module")
    verbs = chosen_verbs or ADI_VERBS.get(tier, ADI_VERBS["Medium"])

    # mine simple procedural hints from source (optional)
    steps_hints = []
    if source:
        sents = _sentences(source)
        for s in sents:
            if re.search(r"\b(first|then|next|after|before|ensure|use|apply|select|measure|calculate|record|verify|inspect|document)\b", s, re.I):
                steps_hints.append(s)
        steps_hints = steps_hints[:16]

    rows = []
    for i in range(1, count + 1):
        v = verbs[(i - 1) % len(verbs)]
        t1 = max(5, int(duration * 0.2))
        t2 = max(10, int(duration * 0.5))
        t3 = max(5, duration - (t1 + t2))

        main_step = (steps_hints[(i - 1) % len(steps_hints)]
                     if steps_hints else f"In small groups, {v} a case/task related to {topic}; capture outcomes on a mini-whiteboard.")

        assess = {
            "Low":    "5-item exit ticket (recall/identify).",
            "Medium": "Performance check using worked-example rubric.",
            "High":   "Criteria-based critique or design justification; short reflection.",
        }[tier]

        rows.append({
            "Lesson": lesson,
            "Week": week,
            "Policy focus": tier,
            "Title": f"Lesson {lesson} • Week {week} — {tier} Activity {i}",
            "Tier": tier,
            "Objective": f"Students will {v} key ideas from {topic}.",
            "Steps": " ".join([
                f"Starter ({t1}m): {v.capitalize()} prior knowledge of {topic} via think-pair-share.",
                f"Main ({t2}m): {main_step}",
                f"Plenary ({t3}m): Share, compare and refine answers; agree success criteria."
            ]),
            "Materials": "Slides/board, markers, handouts (optional), timer",
            "Assessment": assess,
            "Duration (mins)": duration,
        })
    return pd.DataFrame(rows)

# ----------------------------- Exporters -----------------------------
def df_to_docx_mcqs(df: pd.DataFrame, topic: str) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument()
    doc.add_heading(f"ADI MCQs — {topic}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    doc.add_paragraph("Each block: Q1 Low → Q2 Medium → Q3 High").runs[0].italic = True
    for b in sorted(df["Block"].unique()):
        doc.add_heading(f"Block {b}", 2)
        blk = df[df["Block"] == b].sort_values(["Q#"])
        for _, r in blk.iterrows():
            pr = doc.add_paragraph().add_run(f"Q{int(r.get('Q#',0))}. [{r['Tier']}] {r['Question']}")
            pr.bold = True
            doc.add_paragraph(f"A. {r['Option A']}")
            doc.add_paragraph(f"B. {r['Option B']}")
            doc.add_paragraph(f"C. {r['Option C']}")
            doc.add_paragraph(f"D. {r['Option D']}")
            doc.add_paragraph(f"Answer: {r['Answer']}")
            doc.add_paragraph(f"Explanation: {r.get('Explanation','')}")
            doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def mcq_to_gift(df: pd.DataFrame, topic: str) -> bytes:
    lines = [f"// ADI MCQs — {topic}", f"// Exported {datetime.now():%Y-%m-%d %H:%M}", ""]
    df = df.sort_values(["Block","Q#"], kind="stable")
    for _, row in df.reset_index(drop=True).iterrows():
        qnum = int(row.get("Q#", 0))
        qname = f"Block{row['Block']}-Q{qnum}-{row['Tier']}"
        stem = row["Question"].replace("\n"," ").strip()
        opts = [row["Option A"], row["Option B"], row["Option C"], row["Option D"]]
        ans_idx = {"A":0,"B":1,"C":2,"D":3}.get(row["Answer"].strip().upper(), 0)
        def esc(s:str)->str: return s.replace("{", r"\{").replace("}", r"\}")
        lines.append(f"::{qname}:: {esc(stem)} {{")
        for j, o in enumerate(opts):
            lines.append(f"={esc(o)}" if j == ans_idx else f"~{esc(o)}")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO(); df.to_csv(bio, index=False); return bio.getvalue()

def df_to_docx_activities(df: pd.DataFrame, topic: str) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument()
    doc.add_heading(f"ADI Activities — {topic}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    if {"Lesson","Week","Policy focus"}.issubset(df.columns) and not df.empty:
        doc.add_paragraph(f"Lesson {int(df.iloc[0]['Lesson'])} • Week {int(df.iloc[0]['Week'])} • Focus: {df.iloc[0]['Policy focus']}")
    for _, r in df.iterrows():
        doc.add_heading(r['Title'], 2)
        doc.add_paragraph(f"Tier: {r['Tier']}")
        doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph(f"Steps: {r['Steps']}")
        doc.add_paragraph(f"Materials: {r['Materials']}")
        doc.add_paragraph(f"Assessment: {r['Assessment']}")
        doc.add_paragraph(f"Duration: {r['Duration (mins)']} mins")
        doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

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

# ----------------------------- Sidebar (master controls) -----------------------------
with st.sidebar:
    # Upload
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>UPLOAD (OPTIONAL)</div><hr class='rule'/>", unsafe_allow_html=True)
        up_file = st.file_uploader(
            "Choose a file",
            type=["pdf","docx","pptx"],
            label_visibility="collapsed",
            help="Drop an eBook, lesson plan, or PPT to prefill Source text."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Course context (Lesson/Week live here)
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>COURSE CONTEXT</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.lesson = st.selectbox("Lesson", list(range(1,7)), index=st.session_state.lesson-1, key="sb_lesson")
        st.session_state.week   = st.selectbox("Week",   list(range(1,15)), index=st.session_state.week-1,   key="sb_week")
        bloom_now = bloom_focus_for_week(st.session_state.week)
        st.markdown(
            f"<div style='font-size:12px;color:#6b7280;margin-top:6px'>ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.</div>"
            f"<div style='margin-top:6px'><span class='badge {'low' if bloom_now=='Low' else 'med' if bloom_now=='Medium' else 'high'}'>{bloom_now} focus</span></div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # MCQ blocks
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>KNOWLEDGE MCQs (ADI POLICY)</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.mcq_blocks = st.radio(
            "Quick pick blocks", [5,10,20,30],
            horizontal=True,
            index=[5,10,20,30].index(st.session_state.mcq_blocks) if st.session_state.mcq_blocks in [5,10,20,30] else 1,
            key="sb_blocks"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Activities knobs
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>SKILLS ACTIVITIES</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.setdefault("ref_act_n", 3)
        st.session_state.setdefault("ref_act_d", 45)
        st.session_state.ref_act_n = st.number_input("Activities count", min_value=1, value=st.session_state.ref_act_n, step=1, key="sb_act_n")
        st.session_state.ref_act_d = st.number_input("Duration (mins)", min_value=5, value=st.session_state.ref_act_d, step=5, key="sb_act_d")
        st.markdown("</div>", unsafe_allow_html=True)

    # Parse upload after UI so spinner doesn't block
    if up_file:
        st.session_state.upload_text = extract_text_from_upload(up_file)

# ----------------------------- Tabs (main area) -----------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# ===== MCQs tab =====
with mcq_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>MCQ Generator</p>", unsafe_allow_html=True)

    # Mirrored (read-only) context for confidence
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        st.selectbox("Lesson", [st.session_state.lesson], index=0, disabled=True, key="mcq_mirror_lesson")
    with col2:
        st.selectbox("Week", [st.session_state.week], index=0, disabled=True, key="mcq_mirror_week")
    with col3:
        bloom = bloom_focus_for_week(int(st.session_state.week))
        st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom}", disabled=True)

    topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")

    # eBook source (optional)
    with st.expander("Source (from upload) — optional", expanded=False):
        source_mcq = st.text_area("", value=st.session_state.upload_text, height=160, label_visibility="collapsed", key="source_mcq")

    # Bloom policy groups (shaded)
    st.markdown("**Bloom’s verbs (ADI Policy)**  \n<small>Grouped by policy tiers and week ranges</small>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='policy-group low'>
          <div class='policy-label'>Remember / Understand</div>
          <div style='margin-bottom:6px; font-weight:700;'>Low (Weeks 1–4)</div>
          {" ".join([f"<span class='badge low'>{w}</span>" for w in LOW_VERBS])}
        </div>
        <div class='policy-group med'>
          <div class='policy-label'>Apply / Analyze</div>
          <div style='margin-bottom:6px; font-weight:700;'>Medium (Weeks 5–9)</div>
          {" ".join([f"<span class='badge med'>{w}</span>" for w in MED_VERBS])}
        </div>
        <div class='policy-group high'>
          <div class='policy-label'>Evaluate / Create</div>
          <div style='margin-bottom:6px; font-weight:700;'>High (Weeks 10–14)</div>
          {" ".join([f"<span class='badge high'>{w}</span>" for w in HIGH_VERBS])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Generate MCQ Blocks"):
        with st.spinner("Building MCQ blocks…"):
            st.session_state.mcq_df = generate_mcq_blocks(
                topic, source_mcq, int(st.session_state.mcq_blocks), int(st.session_state.week)
            )

    if st.session_state.mcq_df is None or st.session_state.mcq_df.empty:
        st.info("No MCQs yet. Use the button above to generate.")
    else:
        st.session_state.mcq_df = st.session_state.mcq_df.sort_values(["Block","Q#"], kind="stable").reset_index(drop=True)
        view_cols = ["Block","Q#","Tier","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]
        view = st.session_state.mcq_df[view_cols] if all(c in st.session_state.mcq_df.columns for c in view_cols) else st.session_state.mcq_df
        edited = st.data_editor(view, num_rows="dynamic", use_container_width=True, key="mcq_editor")
        st.session_state.mcq_df = edited

        st.markdown("<div style='display:flex; gap:10px; flex-wrap:wrap'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", df_to_docx_mcqs(edited, _fallback(topic,"Module")),
                           file_name="adi_mcqs.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download Moodle (GIFT)", mcq_to_gift(edited, _fallback(topic,"Module")),
                           file_name="adi_mcqs_gift.txt", mime="text/plain")
        st.download_button("Download CSV", df_to_csv_bytes(edited),
                           file_name="adi_mcqs.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ===== Activities tab =====
with act_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>Activities Planner</p>", unsafe_allow_html=True)

    # Mirrored (read-only) context for confidence
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        st.selectbox("Lesson", [st.session_state.lesson], index=0, disabled=True, key="act_mirror_lesson")
    with col2:
        st.selectbox("Week", [st.session_state.week], index=0, disabled=True, key="act_mirror_week")
    with col3:
        bloom = bloom_focus_for_week(int(st.session_state.week))
        st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom}", disabled=True, key="act_mirror_bloom")

    # Emphasis (can override week suggestion)
    default_idx = ["Low","Medium","High"].index(bloom if bloom in ["Low","Medium","High"] else "Medium")
    tier = st.radio("Emphasis", ["Low","Medium","High"], horizontal=True, index=default_idx, key="act_tier")

    # Selectable verbs (highlighted chips)
    verbs_for_tier = ADI_VERBS[tier]
    st.markdown("**Select verbs to emphasise (optional)** — defaults use the policy verbs for this tier.")
    st.session_state.act_selected_verbs = st.multiselect(
        "Bloom verbs", options=verbs_for_tier, default=verbs_for_tier[:2], key="act_verbs"
    )

    topic2 = st.text_input("Topic (optional)", value="", placeholder="Module or unit focus", key="act_topic")

    with st.expander("Source (from upload) — optional", expanded=False):
        source_activities = st.text_area("", value=st.session_state.upload_text, height=160, label_visibility="collapsed", key="source_activities")

    if st.button("Generate Activities"):
        with st.spinner("Assembling activities…"):
            st.session_state.act_df = generate_activities(
                int(st.session_state.ref_act_n),
                int(st.session_state.ref_act_d),
                tier,
                topic2,
                st.session_state.act_selected_verbs,
                source_activities,
                lesson=int(st.session_state.lesson),
                week=int(st.session_state.week),
            )

    if st.session_state.act_df is None or st.session_state.act_df.empty:
        st.info("No activities yet. Use the button above to generate.")
    else:
        act_cols = ["Lesson","Week","Policy focus","Title","Tier","Objective","Steps","Materials","Assessment","Duration (mins)"]
        act_view = st.session_state.act_df[act_cols] if all(c in st.session_state.act_df.columns for c in act_cols) else st.session_state.act_df
        act_edit = st.data_editor(act_view, num_rows="dynamic", use_container_width=True, key="act_editor")
        st.session_state.act_df = act_edit

        st.markdown("<div style='display:flex; gap:10px; flex-wrap:wrap'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", df_to_docx_activities(act_edit, _fallback(topic2,"Module")),
                           file_name="adi_activities.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download CSV", df_to_csv_bytes(act_edit),
                           file_name="adi_activities.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- Tips -----------------------------
st.divider()
st.markdown(
    """
    **Tips**  
    • If styles ever look default, use **Rerun and Clear Cache** and hard-refresh (Ctrl/Cmd+Shift+R).  
    • Look for the green **ADI style v14** badge (top-right) to confirm CSS loaded.  
    • Gold underline on the active tab indicates the correct theme.  
    """
)

