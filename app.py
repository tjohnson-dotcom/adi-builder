# app.py — ADI Builder (policy-aligned MCQs & Activities, editors, sidebar polish)

import base64
import io
import os
import re
from datetime import datetime
from typing import Any, List, Dict

import pandas as pd
import streamlit as st

# Optional parsers (install if you want PDF/DOCX/PPTX ingestion)
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

# ----------------------------- ONE CSS block -----------------------------
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

/* SIDEBAR (only) */
section[data-testid='stSidebar']>div{background:linear-gradient(180deg,#F3F2ED,#F7F7F4); height:100%}
section[data-testid='stSidebar'] * { box-sizing: border-box; }
.side-card{background:#fff; border:1px solid var(--border); border-radius:18px; padding:14px 14px 16px; margin:14px 8px; box-shadow:0 8px 18px rgba(0,0,0,.06)}
.side-cap{display:flex; align-items:center; gap:10px; font-size:12px; color:var(--adi-green); text-transform:uppercase; letter-spacing:.08em; font-weight:700; margin:0 0 8px}
.side-cap .dot{width:9px;height:9px;border-radius:999px;background:var(--adi-gold); box-shadow:0 0 0 4px rgba(200,168,90,.18)}
.rule{height:2px; background:linear-gradient(90deg,var(--adi-gold),transparent); border:0; margin:8px 0 10px}

/* uploader */
section[data-testid='stSidebar'] div[data-testid="stFileUploaderDropzone"]{border-radius:14px; border:1px dashed #cfd6cf; background:#ffffff; margin-top:8px}
section[data-testid='stSidebar'] div[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--adi-green); box-shadow:0 0 0 3px rgba(36,90,52,.12)}
section[data-testid='stSidebar'] [data-testid="stFileUploader"] p{color:#6b7280; font-size:12px}

/* inputs focus consistency */
section[data-testid='stSidebar'] input, 
section[data-testid='stSidebar'] select,
section[data-testid='stSidebar'] textarea{border-radius:12px!important}
section[data-testid='stSidebar'] .stNumberInput > div > input,
section[data-testid='stSidebar'] .stSelectbox > div > div { border:1.5px solid #cfd6cf!important; }
section[data-testid='stSidebar'] .stNumberInput > div > input:focus,
section[data-testid='stSidebar'] .stSelectbox > div > div:focus-within{
  box-shadow:0 0 0 3px rgba(36,90,52,.18)!important; border-color: var(--adi-green)!important;
}

/* radio → pill style */
section[data-testid='stSidebar'] [role='radiogroup'] label {
  border:1px solid var(--border); padding:6px 10px; margin-right:8px; border-radius:999px;
  background:#fff; box-shadow:0 2px 6px rgba(0,0,0,.04);
}
section[data-testid='stSidebar'] [role='radiogroup'] input:checked + div {
  border-color:var(--adi-gold); box-shadow:0 0 0 3px rgba(200,168,90,.25);
}

/* MAIN */
.card{background:var(--card); border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow); padding:16px; margin:10px 0}
.cap{color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; font-size:12px; margin:0 0 10px}

/* INPUTS in main content */
.stTextArea textarea, .stTextInput input{border:2px solid var(--adi-green)!important; border-radius:12px!important}
.stTextArea textarea:focus, .stTextInput input:focus{box-shadow:0 0 0 3px rgba(36,90,52,.18)!important}

/* BUTTONS */
div.stButton>button{background:var(--adi-green); color:#fff; border:none; border-radius:999px; padding:.6rem 1.1rem; font-weight:700; box-shadow:0 8px 18px rgba(31,76,44,.25)}
div.stButton>button:hover{filter:brightness(.98); box-shadow:0 0 0 3px rgba(200,168,90,.35)}

/* TABS */
[data-testid='stTabs'] button{font-weight:700; color:#445; border-bottom:3px solid transparent}
[data-testid='stTabs'] button[aria-selected='true']{color:var(--adi-green)!important; border-bottom:3px solid var(--adi-gold)!important}

/* BLOOM badges */
.badge{display:inline-flex; align-items:center; justify-content:center; padding:6px 10px; border-radius:999px; border:1px solid var(--border); margin:2px 6px 2px 0; font-weight:600}
.low{background:#eaf5ec; color:#245a34}
.med{background:#f8f3e8; color:#6a4b2d}
.high{background:#f3f1ee; color:#4a4a45}
.active-glow{box-shadow:0 0 0 3px rgba(36,90,52,.25)}
.active-amber{box-shadow:0 0 0 3px rgba(200,168,90,.35)}
.active-gray{box-shadow:0 0 0 3px rgba(120,120,120,.25)}

/* BLOOM POLICY GROUP PANELS (shaded in main) */
.policy-group{position:relative; border:1px solid var(--border); border-radius:16px; box-shadow:var(--shadow); padding:12px 12px; margin:10px 0}
.policy-group.low{background:linear-gradient(180deg,#eef6f0,#ffffff)}
.policy-group.med{background:linear-gradient(180deg,#fbf6ec,#ffffff)}
.policy-group.high{background:linear-gradient(180deg,#f5f4f1,#ffffff)}
.policy-label{position:absolute; right:12px; top:10px; font-size:11px; color:#6b7280}

/* DOWNLOAD STRIP */
.dl-row{display:flex; gap:10px; flex-wrap:wrap}

/* Badge to confirm CSS loaded */
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

ensure_state()

LOW_VERBS = ["define","identify","list","recall","describe","label"]
MED_VERBS = ["apply","demonstrate","solve","illustrate","analyze"]
HIGH_VERBS = ["evaluate","synthesize","design","justify"]

ADI_VERBS = {  # for activities
    "Low":    ["define", "identify", "recall", "list", "describe", "label"],
    "Medium": ["apply", "demonstrate", "interpret", "compare", "solve", "illustrate"],
    "High":   ["analyze", "evaluate", "justify", "synthesize", "design", "formulate"],
}


# ----------------------------- Utilities -----------------------------
def _fallback(text: str | None, default: str) -> str:
    return text.strip() if text and str(text).strip() else default

def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"


# ----------------------------- Smarter parsing (eBook-aware) -----------------------------
_HEADING_HINTS = re.compile(
    r"^(chapter|lesson|module|section|unit|overview|contents|glossary|appendix|faq|frequently|table of contents|figure|table)\b",
    re.I,
)
_PAGE_JUNK = re.compile(r"^(page|p\.?)[\s\-]*\d+\b", re.I)
_VERB_HINTS = re.compile(
    r"\b(is|are|was|were|be|has|have|includes?|consists?|requires?|ensures?|supports?|improves?|reduces?|uses?|applies?|follows?|selects?|choose|designs?|evaluates?|measures?|calculates?)\b",
    re.I,
)

def extract_text_from_upload(up_file) -> str:
    """Extract compact text from PDF/DOCX/PPTX for the source box."""
    if up_file is None:
        return ""
    name = up_file.name.lower()
    text = ""
    try:
        if name.endswith(".pdf") and PdfReader:
            reader = PdfReader(up_file)
            for page in reader.pages[:15]:
                txt = (page.extract_text() or "").strip()
                if txt:
                    text += txt + "\n"
        elif name.endswith(".docx") and Document:
            doc = Document(up_file)
            for p in doc.paragraphs[:300]:
                text += (p.text or "") + "\n"
        elif name.endswith(".pptx") and Presentation:
            prs = Presentation(up_file)
            for slide in prs.slides[:40]:
                for shp in slide.shapes:
                    if hasattr(shp, "text") and shp.text:
                        text += shp.text + "\n"
        # tidy
        text = text.replace("\r", "\n")
        lines = [ln.strip() for ln in text.split("\n")]
        lines = [ln for ln in lines if ln]
        return "\n".join(lines)[:6000]
    except Exception as e:
        return f"[Could not parse file: {e}]"


# ----------------------------- Tiny NLP helpers -----------------------------
_STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","as","is","are","be","was","were",
    "this","that","these","those","it","its","at","from","into","over","under","about","between","within",
    "use","used","using","also","than","which","such","may","can","could","should","would","will","not",
    "if","when","while","after","before","each","per","via","more","most","less","least","other","another",
    "module","lesson","overview","content","contents","terms","questions","glossary","sheet","faq","frequently",
    "figure","table"
}

def _sentences(text: str) -> list[str]:
    """Split text and keep only teaching sentences (drop headings/page junk)."""
    rough: list[str] = []
    for chunk in text.split("\n"):
        parts = [p.strip() for p in re.split(r"[.\u2022\u2023\u25CF]", chunk)]
        for p in parts:
            if p:
                rough.append(p)
    out, seen = [], set()
    for s in rough:
        s_clean = re.sub(r"\s+", " ", s).strip()
        words = s_clean.split()
        if not (8 <= len(words) <= 35):
            continue
        if s_clean.isupper() or _PAGE_JUNK.match(s_clean) or _HEADING_HINTS.match(s_clean):
            continue
        if sum(ch.isdigit() for ch in s_clean) > max(6, len(s_clean)//5):
            continue
        if not _VERB_HINTS.search(s_clean):
            continue
        k = s_clean.lower()
        if k not in seen:
            out.append(s_clean); seen.add(k)
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
    return roots

def _find_sentence_with(term: str, sentences: list[str]) -> str | None:
    t = term.lower()
    for s in sentences:
        if t in s.lower():
            return s.strip()
    return None

def _extract_glossary(sentences: list[str]) -> dict:
    """Detect simple definition-like sentences → {term: definition}."""
    glos = {}
    for s in sentences:
        m = re.match(r"([A-Z][A-Za-z0-9\- ]{2,40})\s+(is|means|refers to|defines?)\s+(.*)$", s)
        if m:
            term = m.group(1).strip().rstrip("-:")
            glos.setdefault(term.lower(), s); continue
        m2 = re.match(r"([A-Z][A-Za-z0-9\- ]{2,40})\s*[:\-]\s+(.*)$", s)
        if m2 and len(m2.group(2).split()) > 4:
            term = m2.group(1).strip().rstrip("-:")
            glos.setdefault(term.lower(), s)
    return glos

def _distractors_from_sentences(correct: str, pool: list[str], n: int) -> list[str]:
    """Near-miss distractors chosen from other good sentences."""
    import random
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
    return out

_TEMPLATED_WRONGS = [
    "The statement is partially true but misses a required constraint.",
    "This describes a related concept that does not apply in this context.",
    "The option generalizes beyond the scope defined in the module.",
    "This is a common misconception rather than a correct statement.",
]


# ----------------------------- Generators (ADI policy) -----------------------------
def generate_mcq_blocks(topic: str, source: str, num_blocks: int, week: int) -> pd.DataFrame:
    """
    ADI policy MCQs:
    - Exactly 3 questions per block (Q1 Low, Q2 Medium, Q3 High)
    - Stems rotate across Bloom-appropriate templates (not all 'Which…')
    - Correct options mined from eBook sentences; distractors are near-miss sentences
    """
    topic = _fallback(topic, "the module")
    src = _fallback(source, "")
    sents = _sentences(src)
    glossary = _extract_glossary(sents)
    keys = _keywords(src or topic, top_n=max(24, num_blocks * 6)) or \
           ["principles","process","safety","quality","evidence","procedure","criteria","constraints","standards"]

    # Stem templates (rotation)
    low_stems = [
        lambda t: f"Define {t}: which statement is correct in *{topic}*?",
        lambda t: f"Identify the accurate description of {t}.",
        lambda t: f"Recall: what does {t} mean in the context of *{topic}*?",
        lambda t: f"Which option best describes {t}?"
    ]
    med_stems = [
        lambda t: f"How would you apply {t} when working on *{topic}*?",
        lambda t: f"Interpretation: which action correctly uses {t}?",
        lambda t: f"Compare the options — which best operationalises {t}?",
        lambda t: f"What is the next appropriate step when using {t}?"
    ]
    high_stems = [
        lambda t: f"Which option best evaluates/justifies a decision involving {t} for *{topic}*?",
        lambda t: f"Analyze: which reasoning is strongest regarding {t}?",
        lambda t: f"Which design choice best satisfies constraints related to {t}?",
        lambda t: f"Which response best synthesizes the considerations for {t}?"
    ]

    rows: list[dict[str, Any]] = []

    def add_row(block: int, tier: str, stem_txt: str, correct: str, wrongs: list[str]):
        wr = wrongs[:3]
        i = 0
        while len(wr) < 3:
            wr.append(_TEMPLATED_WRONGS[i % len(_TEMPLATED_WRONGS)])
            i += 1
        options = [correct, wr[0], wr[1], wr[2]]
        import random
        rnd = random.Random(2025 + block + len(rows))
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(correct)]
        rows.append({
            "Block": block,
            "Tier": tier,
            "Q#": {"Low": 1, "Medium": 2, "High": 3}[tier],
            "Question": stem_txt.strip(),
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans, "Explanation": "Chosen option aligns with the source context.",
            "Order": {"Low": 1, "Medium": 2, "High": 3}[tier],
        })

    for b in range(1, num_blocks + 1):
        # choose distinct terms so questions feel different
        t_low  = keys[(b*3 - 3) % len(keys)]
        t_med  = keys[(b*3 - 2) % len(keys)]
        t_high = keys[(b*3 - 1) % len(keys)]

        # LOW (prefer glossary/definition)
        c1 = glossary.get(t_low.lower()) or _find_sentence_with(t_low, sents) \
             or f"{t_low.capitalize()} is a foundational element of {topic}."
        d1 = _distractors_from_sentences(c1, sents, 3)
        stem1 = low_stems[(b-1) % len(low_stems)](t_low)
        add_row(b, "Low", stem1, c1, d1)

        # MEDIUM (apply/interpret/compare)
        c2 = _find_sentence_with(t_med, sents) \
             or f"When applying {t_med} in {topic}, follow steps that respect constraints and safety."
        d2 = _distractors_from_sentences(c2, sents, 3)
        stem2 = med_stems[(b-1) % len(med_stems)](t_med)
        add_row(b, "Medium", stem2, c2, d2)

        # HIGH (evaluate/justify/design)
        c3 = _find_sentence_with(t_high, sents) \
             or f"An effective approach to {t_high} in {topic} prioritizes evidence, feasibility, and constraints."
        d3 = _distractors_from_sentences(c3, sents, 3)
        stem3 = high_stems[(b-1) % len(high_stems)](t_high)
        add_row(b, "High", stem3, c3, d3)

    df = pd.DataFrame(rows)
    df = df.sort_values(["Block","Order"], kind="stable").reset_index(drop=True)
    return df


def generate_activities(count: int, duration: int, tier: str, topic: str, source: str = "",
                        lesson: int = 1, week: int = 1) -> pd.DataFrame:
    """
    Activities aligned to ADI Bloom levels.
    - Verbs chosen from ADI_VERBS[tier]
    - If the eBook contains procedural hints (first/then/ensure…), weave one into the Main step
    - Includes Lesson, Week, and Policy focus in titles/columns
    """
    topic = _fallback(topic, "the module")
    verbs = ADI_VERBS.get(tier, ADI_VERBS["Medium"])

    # mine procedural hints from source
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
            "Medium": "Performance check using worked example rubric.",
            "High":   "Criteria-based critique or design justification; short reflective write-up.",
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


# ----------------------------- Editors (MCQ/Activities text round-trip) -----------------------------
def mcq_df_to_text(df: pd.DataFrame) -> str:
    out = []
    for b in sorted(df["Block"].unique()):
        blk = df[df["Block"] == b].sort_values(["Q#"] if "Q#" in df.columns else ["Tier"])
        out.append(f"=== Block {b} ===")
        for _, r in blk.reset_index(drop=True).iterrows():
            qn = int(r.get("Q#", 0)) or {"Low":1,"Medium":2,"High":3}.get(r["Tier"],1)
            out.append(f"Q{qn}. [{r['Tier']}] {r['Question']}")
            out.append(f"A) {r['Option A']}")
            out.append(f"B) {r['Option B']}")
            out.append(f"C) {r['Option C']}")
            out.append(f"D) {r['Option D']}")
            out.append(f"Answer: {r['Answer']}")
            out.append(f"Explanation: {r['Explanation']}")
            out.append("")
    return "\n".join(out).strip()

def mcq_text_to_df(text: str, df_template: pd.DataFrame) -> pd.DataFrame:
    lesson_override = None
    week_override = None
    rows, block = [], None
    for line in text.splitlines():
        line = line.rstrip()

        m_les = re.match(r"Lesson\s*:\s*(\d+)", line, re.I)
        m_wk  = re.match(r"Week\s*:\s*(\d+)", line, re.I)
        if m_les:
            lesson_override = int(m_les.group(1));  continue
        if m_wk:
            week_override = int(m_wk.group(1));     continue

        if line.startswith("=== Block"):
            block = int(re.findall(r"Block\s+(\d+)", line)[0]); continue
        if not line:
            continue
        m_q = re.match(r"Q(\d+)\.\s*\[(Low|Medium|High)\]\s*(.*)", line, re.I)
        if m_q:
            qnum, tier, qtxt = int(m_q.group(1)), m_q.group(2).title(), m_q.group(3).strip()
            rows.append({"Block": block, "Q#": qnum, "Tier": tier, "Question": qtxt}); continue
        if rows:
            cur = rows[-1]
            if   line.startswith("A) "): cur["Option A"] = line[3:].strip()
            elif line.startswith("B) "): cur["Option B"] = line[3:].strip()
            elif line.startswith("C) "): cur["Option C"] = line[3:].strip()
            elif line.startswith("D) "): cur["Option D"] = line[3:].strip()
            elif line.startswith("Answer: "): cur["Answer"] = line.split(":",1)[1].strip().upper()[:1]
            elif line.startswith("Explanation: "): cur["Explanation"] = line.split(":",1)[1].strip()

    cols = ["Block","Q#","Tier","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]
    for r in rows:
        for c in cols:
            r.setdefault(c, "")
    df = pd.DataFrame(rows)[cols] if rows else df_template
    if lesson_override is not None: st.session_state.lesson = lesson_override
    if week_override   is not None: st.session_state.week   = week_override
    if df is df_template:
        return df_template
    return df.sort_values(["Block","Q#"], kind="stable").reset_index(drop=True)

def acts_df_to_text(df: pd.DataFrame) -> str:
    out = []
    if {"Lesson","Week"}.issubset(df.columns) and not df.empty:
        out.append(f"Lesson: {int(df.iloc[0]['Lesson'])}")
        out.append(f"Week: {int(df.iloc[0]['Week'])}")
        out.append("")
    for _, r in df.iterrows():
        title = r.get("Title", "")
        out.append(f"### {title}")
        out.append(f"Objective: {r.get('Objective','')}")
        out.append(f"Steps: {r.get('Steps','')}")
        out.append(f"Materials: {r.get('Materials','')}")
        out.append(f"Assessment: {r.get('Assessment','')}")
        out.append(f"Duration: {r.get('Duration (mins)','')} mins")
        out.append("")
    return "\n".join(out).strip()

def acts_text_to_df(text: str, df_template: pd.DataFrame) -> pd.DataFrame:
    lesson_override = None
    week_override = None
    rows, cur = [], {}

    # capture overrides at top
    for line in text.splitlines():
        line = line.rstrip()
        if re.match(r"Lesson\s*:\s*\d+", line, re.I):
            lesson_override = int(re.findall(r"\d+", line)[0]); continue
        if re.match(r"Week\s*:\s*\d+", line, re.I):
            week_override = int(re.findall(r"\d+", line)[0]); continue
        if line.startswith("### "):
            break

    # parse items
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("### "):
            if cur: rows.append(cur); cur = {}
            cur["Title"] = line[4:].strip()
        elif line.startswith("Objective:"):  cur["Objective"] = line.split(":",1)[1].strip()
        elif line.startswith("Steps:"):      cur["Steps"] = line.split(":",1)[1].strip()
        elif line.startswith("Materials:"):  cur["Materials"] = line.split(":",1)[1].strip()
        elif line.startswith("Assessment:"): cur["Assessment"] = line.split(":",1)[1].strip()
        elif line.startswith("Duration:"):
            nums = re.findall(r"\d+", line)
            cur["Duration (mins)"] = int(nums[0]) if nums else df_template.get("Duration (mins)", [45])[0]
    if cur: rows.append(cur)
    if not rows:
        return df_template

    # defaults & carry context
    out_rows = []
    for i, r in enumerate(rows, 1):
        o = {
            "Lesson": lesson_override if lesson_override is not None else int(st.session_state.get("lesson", 1)),
            "Week": week_override if week_override is not None else int(st.session_state.get("week", 1)),
            "Policy focus": df_template.iloc[0].get("Tier", "Medium") if not df_template.empty else "Medium",
            "Title": r.get("Title", f"Activity {i}"),
            "Tier": df_template.iloc[0].get("Tier", "Medium") if not df_template.empty else "Medium",
            "Objective": r.get("Objective", ""),
            "Steps": r.get("Steps", ""),
            "Materials": r.get("Materials", "Slides/board, markers, handouts (optional), timer"),
            "Assessment": r.get("Assessment", "Performance check / exit ticket"),
            "Duration (mins)": r.get("Duration (mins)", df_template.iloc[0].get("Duration (mins)", 45) if not df_template.empty else 45),
        }
        out_rows.append(o)

    if lesson_override is not None: st.session_state.lesson = lesson_override
    if week_override is not None:   st.session_state.week   = week_override
    return pd.DataFrame(out_rows)


# ----------------------------- Exporters (DOCX, CSV, GIFT) -----------------------------
def df_to_docx_mcqs(df: pd.DataFrame, topic: str) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument()
    doc.add_heading(f"ADI MCQs — {topic}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    p = doc.add_paragraph("Each block: Low → Medium → High")
    p.runs[0].italic = True
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
            doc.add_paragraph(f"Explanation: {r['Explanation']}")
            doc.add_paragraph("")
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def mcq_to_gift(df: pd.DataFrame, topic: str) -> bytes:
    lines = [f"// ADI MCQs — {topic}", f"// Exported {datetime.now():%Y-%m-%d %H:%M}", ""]
    df = df.sort_values(["Block","Q#"], kind="stable")
    for _, row in df.reset_index(drop=True).iterrows():
        qnum = int(row.get("Q#", 0))
        qname = f"Block{row['Block']}-Q{qnum}-{row['Tier']}"
        stem = row["Question"].replace("\n", " ").strip()
        opts = [row["Option A"], row["Option B"], row["Option C"], row["Option D"]]
        ans_idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(row["Answer"].strip().upper(), 0)

        def esc(s: str) -> str:
            return s.replace("{", r"\{").replace("}", r"\}")

        lines.append(f"::{qname}:: {esc(stem)} {{")
        for j, o in enumerate(opts):
            lines.append(f"={esc(o)}" if j == ans_idx else f"~{esc(o)}")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO()
    df.to_csv(bio, index=False)
    return bio.getvalue()

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
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


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

# ----------------------------- Sidebar (styled) -----------------------------
with st.sidebar:
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>UPLOAD (OPTIONAL)</div><hr class='rule'/>", unsafe_allow_html=True)
        up_file = st.file_uploader("Choose a file", type=["pdf","docx","pptx"], label_visibility="collapsed",
                                   help="Drop an eBook, lesson plan, or PPT to prefill Source text.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>COURSE CONTEXT</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.lesson = st.selectbox("Lesson", list(range(1,7)), index=st.session_state.lesson-1)
        st.session_state.week = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1)
        bloom = bloom_focus_for_week(st.session_state.week)
        st.markdown(
            f"<span class='policy-chip'><span class='pill'></span> Week {st.session_state.week} • <strong>{bloom}</strong> focus</span>"
            "<div style='font-size:11px;color:#6b7280;margin-top:6px'>ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.</div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>KNOWLEDGE MCQs (ADI POLICY)</div><hr class='rule'/>", unsafe_allow_html=True)
        pick = st.radio("Quick pick blocks", [5,10,20,30], horizontal=True,
                        index=[5,10,20,30].index(st.session_state.mcq_blocks) if st.session_state.mcq_blocks in [5,10,20,30] else 1)
        st.session_state.mcq_blocks = pick
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>SKILLS ACTIVITIES</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.setdefault("ref_act_n",3)
        st.session_state.setdefault("ref_act_d",45)
        st.session_state.ref_act_n = st.number_input("Activities count", min_value=1, value=st.session_state.ref_act_n, step=1)
        st.session_state.ref_act_d = st.number_input("Duration (mins)", min_value=5, value=st.session_state.ref_act_d, step=5)
        st.markdown("</div>", unsafe_allow_html=True)

    if up_file:
        st.session_state.upload_text = extract_text_from_upload(up_file)


# ----------------------------- Tabs (main area) -----------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

with mcq_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>MCQ Generator</p>", unsafe_allow_html=True)

    # Inline Lesson/Week pickers (keep in sync with sidebar)
    cL, cW, _ = st.columns([1,1,6])
    with cL:
        _les_mcq = st.selectbox("Lesson", list(range(1,7)), index=st.session_state.lesson-1, key="lesson_inline_mcq")
    with cW:
        _wek_mcq = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1, key="week_inline_mcq")
    if (_les_mcq != st.session_state.lesson) or (_wek_mcq != st.session_state.week):
        st.session_state.lesson = int(_les_mcq)
        st.session_state.week = int(_wek_mcq)
        bloom = bloom_focus_for_week(st.session_state.week)

    col1, col2 = st.columns([1,1])
    with col1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with col2:
        st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom}", disabled=True)

    # eBook source in expander (optional)
    with st.expander("Source (from upload) — optional", expanded=False):
        source = st.text_area("", value=st.session_state.upload_text, height=160, label_visibility="collapsed")

    # Bloom legend (shaded)
    st.markdown("**Bloom’s verbs (ADI Policy)**  \n<small>Grouped by policy tiers and week ranges</small>", unsafe_allow_html=True)
    low_class = "badge low " + ("active-glow" if bloom=="Low" else "")
    med_class = "badge med " + ("active-amber" if bloom=="Medium" else "")
    high_class = "badge high " + ("active-gray" if bloom=="High" else "")
    st.markdown(
        f"""
        <div class='policy-group low'>
          <div class='policy-label'>Remember / Understand</div>
          <div style='margin-bottom:6px; font-weight:700;'>Low (Weeks 1–4)</div>
          {" ".join([f"<span class='{low_class}'>{w}</span>" for w in LOW_VERBS])}
        </div>
        <div class='policy-group med'>
          <div class='policy-label'>Apply / Analyze</div>
          <div style='margin-bottom:6px; font-weight:700;'>Medium (Weeks 5–9)</div>
          {" ".join([f"<span class='{med_class}'>{w}</span>" for w in MED_VERBS])}
        </div>
        <div class='policy-group high'>
          <div class='policy-label'>Evaluate / Create</div>
          <div style='margin-bottom:6px; font-weight:700;'>High (Weeks 10–14)</div>
          {" ".join([f"<span class='{high_class}'>{w}</span>" for w in HIGH_VERBS])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Generate MCQ Blocks"):
        with st.spinner("Building MCQ blocks…"):
            st.session_state.mcq_df = generate_mcq_blocks(topic, source, int(st.session_state.mcq_blocks), int(st.session_state.week))

    if st.session_state.mcq_df is None or st.session_state.mcq_df.empty:
        st.info("No MCQs yet. Use the button above to generate.")
    else:
        # ensure sorted & numbered
        st.session_state.mcq_df = st.session_state.mcq_df.sort_values(["Block","Q#"], kind="stable").reset_index(drop=True)

        cols = ["Block","Q#","Tier","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]
        view = st.session_state.mcq_df[cols] if all(c in st.session_state.mcq_df.columns for c in cols) else st.session_state.mcq_df
        edited = st.data_editor(view, num_rows="dynamic", use_container_width=True, key="mcq_editor")
        st.session_state.mcq_df = edited

        # Text editor for MCQs
        with st.expander("Edit MCQs as text", expanded=False):
            txt_default = mcq_df_to_text(st.session_state.mcq_df)
            txt_edit = st.text_area("", value=txt_default, height=320, label_visibility="collapsed", key="mcq_text_box")
            if st.button("Apply text edits to MCQs"):
                st.session_state.mcq_df = mcq_text_to_df(txt_edit, st.session_state.mcq_df)

        st.markdown("<div class='dl-row'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", df_to_docx_mcqs(st.session_state.mcq_df, _fallback(topic,"Module")),
                           file_name="adi_mcqs.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download Moodle (GIFT)", mcq_to_gift(st.session_state.mcq_df, _fallback(topic,"Module")),
                           file_name="adi_mcqs_gift.txt", mime="text/plain")
        st.download_button("Download CSV", df_to_csv_bytes(st.session_state.mcq_df),
                           file_name="adi_mcqs.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with act_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>Activities Planner</p>", unsafe_allow_html=True)

    # Inline Lesson/Week pickers for Activities
    cL2, cW2, _ = st.columns([1,1,6])
    with cL2:
        _les_act = st.selectbox("Lesson", list(range(1,7)), index=st.session_state.lesson-1, key="lesson_inline_act")
    with cW2:
        _wek_act = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1, key="week_inline_act")
    if (_les_act != st.session_state.lesson) or (_wek_act != st.session_state.week):
        st.session_state.lesson = int(_les_act)
        st.session_state.week = int(_wek_act)
        bloom = bloom_focus_for_week(st.session_state.week)

    default_idx = ["Low","Medium","High"].index(bloom if bloom in ["Low","Medium","High"] else "Medium")
    tier = st.radio("Emphasis", ["Low","Medium","High"], horizontal=True, index=default_idx)
    topic2 = st.text_input("Topic (optional)", value="", placeholder="Module or unit focus")

    # eBook source (same var as MCQs, harmless if edited)
    with st.expander("Source (from upload) — optional", expanded=False):
        source2 = st.text_area("", value=st.session_state.upload_text, height=160, label_visibility="collapsed")

    if st.button("Generate Activities"):
        with st.spinner("Assembling activities…"):
            st.session_state.act_df = generate_activities(
                int(st.session_state.ref_act_n),
                int(st.session_state.ref_act_d),
                tier,
                topic2,
                source2,
                lesson=int(st.session_state.lesson),
                week=int(st.session_state.week),
            )

    if st.session_state.act_df is None or st.session_state.act_df.empty:
        st.info("No activities yet. Use the button above to generate.")
    else:
        act_edit_cols = ["Lesson","Week","Policy focus","Title","Tier","Objective","Steps","Materials","Assessment","Duration (mins)"]
        act_view = st.session_state.act_df[act_edit_cols] if all(c in st.session_state.act_df.columns for c in act_edit_cols) else st.session_state.act_df
        act_edit = st.data_editor(act_view, num_rows="dynamic", use_container_width=True, key="act_editor")
        st.session_state.act_df = act_edit

        # Text editor for Activities
        with st.expander("Edit activities as text", expanded=False):
            txt_default = acts_df_to_text(st.session_state.act_df)
            txt_edit = st.text_area("", value=txt_default, height=320, label_visibility="collapsed", key="act_text_box")
            if st.button("Apply text edits to Activities"):
                st.session_state.act_df = acts_text_to_df(txt_edit, st.session_state.act_df)

        st.markdown("<div class='dl-row'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", df_to_docx_activities(st.session_state.act_df, _fallback(topic2,"Module")),
                           file_name="adi_activities.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download CSV", df_to_csv_bytes(st.session_state.act_df),
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
