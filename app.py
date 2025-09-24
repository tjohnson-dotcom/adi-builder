# app.py — ADI Builder V3 (content-first MCQs & Activities, ADI styling, policy-aware)

import base64, io, os, re, random
from datetime import datetime
from typing import Any, List

import pandas as pd
import streamlit as st

# Optional parsers (install if needed): pip install python-docx python-pptx PyPDF2
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

def _read_logo_data_uri(path: str) -> str | None:
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass
    return None

logo_uri = _read_logo_data_uri(LOGO_PATH)

# ----------------------------- CSS (ADI look + live Bloom highlight) -----------------------------
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
section[data-testid='stSidebar']>div{background:linear-gradient(180deg,#F3F2ED,#F7F7F4); height:100%}
.side-card{background:#fff; border:1px solid var(--border); border-radius:18px; padding:14px 14px 16px; margin:14px 8px; box-shadow:0 8px 18px rgba(0,0,0,.06)}
.side-cap{display:flex; align-items:center; gap:10px; font-size:12px; color:var(--adi-green); text-transform:uppercase; letter-spacing:.08em; font-weight:700; margin:0 0 8px}
.side-cap .dot{width:9px;height:9px;border-radius:999px;background:var(--adi-gold); box-shadow:0 0 0 4px rgba(200,168,90,.18)}
.rule{height:2px; background:linear-gradient(90deg,var(--adi-gold),transparent); border:0; margin:8px 0 10px}

/* uploader */
section[data-testid='stSidebar'] div[data-testid="stFileUploaderDropzone"]{border-radius:14px; border:1px dashed #cfd6cf; background:#ffffff; margin-top:8px}
section[data-testid='stSidebar'] div[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--adi-green); box-shadow:0 0 0 3px rgba(36,90,52,.12)}

/* radio pills */
section[data-testid='stSidebar'] [role='radiogroup'] label{
  border:1px solid var(--border); padding:6px 10px; margin-right:8px; border-radius:999px; background:#fff; box-shadow:0 2px 6px rgba(0,0,0,.04);
}
section[data-testid='stSidebar'] [role='radiogroup'] input:checked + div{
  border-color:var(--adi-gold); box-shadow:0 0 0 3px rgba(200,168,90,.25);
}

/* MAIN */
.card{background:var(--card); border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow); padding:16px; margin:10px 0}
.cap{color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; font-size:12px; margin:0 0 10px}
.context-banner{background:#fff; border:1px solid var(--border); border-radius:12px; padding:8px 12px; margin:4px 0 12px; display:flex; gap:14px; align-items:center}

/* Inputs */
.stTextArea textarea, .stTextInput input{border:2px solid var(--adi-green)!important; border-radius:12px!important}
.stTextArea textarea:focus, .stTextInput input:focus{box-shadow:0 0 0 3px rgba(36,90,52,.18)!important}

/* Tabs */
[data-testid='stTabs'] button{font-weight:700; color:#445; border-bottom:3px solid transparent}
[data-testid='stTabs'] button[aria-selected='true']{color:var(--adi-green)!important; border-bottom:3px solid var(--adi-gold)!important}

/* Bloom badges & panels */
.badge{display:inline-flex; align-items:center; justify-content:center; padding:6px 10px; border-radius:999px; border:1px solid var(--border); margin:2px 6px 2px 0; font-weight:600}
.low{background:#eaf5ec; color:#245a34}
.med{background:#fbf6ec; color:#6a4b2d}
.high{background:#f3f1ee; color:#4a4a45}

.policy-group{position:relative; border:1px solid var(--border); border-radius:16px; box-shadow:var(--shadow); padding:12px 12px; margin:10px 0}
.policy-group.low{background:linear-gradient(180deg,#eef6f0,#ffffff)}
.policy-group.med{background:linear-gradient(180deg,#fbf6ec,#ffffff)}
.policy-group.high{background:linear-gradient(180deg,#f5f4f1,#ffffff)}
.policy-label{position:absolute; right:12px; top:10px; font-size:11px; color:#6b7280}

/* ACTIVE highlight for selected tier */
.panel-active{border-color:var(--adi-gold); box-shadow:0 0 0 3px rgba(200,168,90,.28) inset}

/* Activities verb chips (multiselect) — ADI colors */
div[data-baseweb="tag"]{
  border-radius:999px; border:1px solid var(--border);
  background:#eaf5ec; color:#245a34;
}
div[data-baseweb="tag"] [data-baseweb="tag-label"]{font-weight:600}
div[data-baseweb="tag"] svg{color:#1f4c2c}
div[data-baseweb="tag"][aria-selected="true"]{
  border-color: var(--adi-gold);
  box-shadow:0 0 0 3px rgba(200,168,90,.28);
  background:#fff;
}

/* CSS loaded badge */
.adi-badge{position:fixed;top:10px;right:12px;z-index:9999;background:var(--adi-green);color:#fff;padding:6px 10px;border-radius:999px;font-size:12px;box-shadow:0 2px 10px rgba(0,0,0,.15)}
</style>
<div class='adi-badge'>ADI style v18</div>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# ----------------------------- State -----------------------------
def ensure_state():
    ss = st.session_state
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("mcq_blocks", 10)
    ss.setdefault("mcq_df", None)
    ss.setdefault("act_df", None)
    ss.setdefault("upload_text", "")
    ss.setdefault("act_selected_verbs", [])
ensure_state()

LOW_VERBS = ["define","identify","list","recall","describe","label"]
MED_VERBS = ["apply","demonstrate","solve","illustrate","analyze","interpret","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","formulate","critique"]

ADI_VERBS = {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}

def _fallback(s: str|None, default: str) -> str:
    return s.strip() if s and str(s).strip() else default

def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    return "High"

# ----------------------------- Upload parsing (content-first) -----------------------------
def extract_text_from_upload(up_file) -> str:
    if up_file is None:
        return ""
    name = up_file.name.lower()
    text = ""
    try:
        if name.endswith(".pdf") and PdfReader:
            reader = PdfReader(up_file)
            for page in reader.pages[:15]:
                txt = page.extract_text() or ""
                text += txt + "\n"
        elif name.endswith(".docx") and Document:
            doc = Document(up_file)
            for p in doc.paragraphs[:250]:
                text += (p.text or "") + "\n"
        elif name.endswith(".pptx") and Presentation:
            prs = Presentation(up_file)
            for slide in prs.slides[:40]:
                for shp in slide.shapes:
                    if hasattr(shp, "text") and shp.text:
                        text += shp.text + "\n"
        # tidy
        lines = [ln.strip() for ln in text.replace("\r","\n").split("\n") if ln.strip()]
        return "\n".join(lines)[:6000]
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ----------------------------- Tiny NLP helpers -----------------------------
_STOP = {
    # function words
    "the","a","an","and","or","of","to","in","on","for","with","by","as","is","are","be","was","were","this","that","these","those",
    "it","its","at","from","into","over","under","about","between","within","use","used","using","also","than","which","such","may",
    "can","could","should","would","will","not","if","when","while","after","before","each","per","via","more","most","less","least",
    "other","another","see","example","examples","appendix","figure","table","chapter","section","page","pages","ref","ibid",
    # generic course words (avoid bad stems)
    "module","lesson","week","activity","activities","objective","objectives","outcome","outcomes","question","questions","topic","topics",
    "student","students","teacher","instructor","course","unit","learning","overview","summary","introduction","conclusion","content","contents"
}

def _sentences(text: str) -> List[str]:
    # split on sentence boundaries and bullets; keep 30–180 chars; deduplicate
    chunks = re.split(r"[.\u2022\u2023\u25CF•]|(?:\n\s*\-\s*)|(?:\n\s*\*\s*)", text)
    rough = [re.sub(r"\s+", " ", c).strip() for c in chunks if c and c.strip()]
    out, seen = [], set()
    for s in rough:
        if 30 <= len(s) <= 180:
            k = s.lower()
            if k not in seen:
                out.append(s); seen.add(k)
    return out[:200]

def _keywords(text: str, top_n: int = 24) -> List[str]:
    from collections import Counter
    toks = []
    for w in re.split(r"[^A-Za-z0-9]+", text):
        w = w.lower()
        if len(w) >= 4 and w not in _STOP:
            toks.append(w)
    common = Counter(toks).most_common(top_n * 2)
    roots = []
    for w,_ in common:
        if all(not w.startswith(r[:5]) and not r.startswith(w[:5]) for r in roots):
            roots.append(w)
        if len(roots) >= top_n: break
    return roots

def _find_sentence_with(term: str, sentences: List[str]) -> str | None:
    t = term.lower()
    for s in sentences:
        if t in s.lower():
            return s
    return None

def _distractors_from_sentences(correct: str, pool: List[str], n: int) -> List[str]:
    rand = random.Random(42)
    ckey = correct.lower()[:60]
    cands = [p for p in pool if p and p.lower()[:60] != ckey and p.lower() != correct.lower()]
    rand.shuffle(cands)
    out = []
    for s in cands:
        if 20 <= len(s) <= 160 and s not in out:
            out.append(s)
        if len(out) == n: break
    filler = [
        "This option is incomplete and omits a key constraint.",
        "This describes a related idea but does not apply here.",
        "The statement overgeneralises beyond the context."
    ]
    i = 0
    while len(out) < n:
        out.append(filler[i % len(filler)]); i += 1
    return out

# ----------------------------- MCQ generator (content-first) -----------------------------
def generate_mcq_blocks(topic: str, source: str, num_blocks: int, week: int, lesson: int) -> pd.DataFrame:
    """
    3 MCQs per block (Low/Medium/High) based on uploaded content:
    - Keywords and correct sentences mined from 'source'
    - If topic is empty, context banner uses Lesson/Week but content still uses source
    """
    ctx_banner = (topic or "").strip() or f"Lesson {lesson} • Week {week}"
    src_text = (source or "").strip()
    sents = _sentences(src_text)
    keys = _keywords(src_text or topic or "", top_n=max(24, num_blocks * 6))

    # Hard stop: if no usable source, warn and fall back to topic-only
    if not sents:
        sents = [f"{ctx_banner}: core concepts, steps, constraints, and safety considerations."]
        # add a couple of lightweight pseudo-sents from topic words to diversify
        for k in keys[:5]:
            sents.append(f"{k.capitalize()} relates to practical application and typical pitfalls.")

    low_templates = [
        lambda t,ctx: f"Which statement correctly defines **{t}** in the context of *{ctx}*?",
        lambda t,ctx: f"Identify the accurate description of **{t}** for *{ctx}*.",
        lambda t,ctx: f"Recall: what does **{t}** mean in *{ctx}*?",
    ]
    med_templates = [
        lambda t,ctx: f"When applying **{t}** in *{ctx}*, which action is most appropriate?",
        lambda t,ctx: f"Which option best interprets how to use **{t}** in *{ctx}*?",
        lambda t,ctx: f"Compare the options — which best operationalises **{t}** for *{ctx}*?",
    ]
    high_templates = [
        lambda t,ctx: f"Which option provides the strongest justification involving **{t}** for *{ctx}*?",
        lambda t,ctx: f"Analyze: which reasoning about **{t}** is most valid in *{ctx}*?",
        lambda t,ctx: f"Which design choice best satisfies constraints related to **{t}** within *{ctx}*?",
    ]

    rows: List[dict[str, Any]] = []

    def add_row(block: int, tier: str, stem: str, correct: str, wrongs: List[str]):
        options = [correct] + wrongs[:3]
        rnd = random.Random(2025 + block + len(rows))
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(correct)]
        rows.append({
            "Block": block,
            "Tier": tier,
            "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": stem.strip(),
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans,
            "Explanation": "Chosen option aligns with the source sentence/context.",
            "Order": {"Low":1,"Medium":2,"High":3}[tier],
        })

    for b in range(1, num_blocks + 1):
        # rotate through real keywords to avoid repetition
        t_low  = keys[(b*3 - 3) % len(keys)] if keys else "principles"
        t_med  = keys[(b*3 - 2) % len(keys)] if keys else "process"
        t_high = keys[(b*3 - 1) % len(keys)] if keys else "criteria"

        c1 = _find_sentence_with(t_low, sents)  or f"{t_low.capitalize()} is a foundational element in this context."
        c2 = _find_sentence_with(t_med, sents)  or f"When applying {t_med}, follow steps that respect constraints and safety."
        c3 = _find_sentence_with(t_high, sents) or f"An effective approach to {t_high} prioritizes evidence and feasibility."

        add_row(b, "Low",    low_templates[(b-1) % len(low_templates)](t_low,  ctx_banner), c1, _distractors_from_sentences(c1, sents, 3))
        add_row(b, "Medium", med_templates[(b-1) % len(med_templates)](t_med,  ctx_banner), c2, _distractors_from_sentences(c2, sents, 3))
        add_row(b, "High",   high_templates[(b-1) % len(high_templates)](t_high, ctx_banner), c3, _distractors_from_sentences(c3, sents, 3))

    df = pd.DataFrame(rows).sort_values(["Block","Order"], kind="stable").reset_index(drop=True)
    return df

# ----------------------------- Activities generator (content-first) -----------------------------
def generate_activities(count: int, duration: int, tier: str, topic: str, chosen_verbs: List[str],
                        source: str = "", lesson: int = 1, week: int = 1) -> pd.DataFrame:
    """
    Lesson/Week-linked activities with ADI verbs + mined content cues.
    - Titles show Lesson/Week (and topic if provided)
    - Objective and Steps use selected verbs
    - 'Main' pulls a procedural sentence from source when available
    """
    topic = (topic or "").strip()
    ctx = f"Lesson {lesson} • Week {week}" + (f" — {topic}" if topic else "")
    verbs = (chosen_verbs or ADI_VERBS.get(tier, ADI_VERBS["Medium"]))[:6]

    # Mine hints from source (procedural verbs)
    steps_hints = []
    if source:
        sents = _sentences(source)
        for s in sents:
            if re.search(r"\b(first|then|next|after|before|ensure|use|apply|select|measure|calculate|record|verify|inspect|document|compare|interpret|justify|design)\b", s, re.I):
                steps_hints.append(s.strip())
        steps_hints = steps_hints[:24]

    rows = []
    for i in range(1, count + 1):
        v = verbs[(i - 1) % len(verbs)]
        t1 = max(5, int(duration * 0.2))
        t2 = max(10, int(duration * 0.5))
        t3 = max(5, duration - (t1 + t2))

        main_step = (steps_hints[(i - 1) % len(steps_hints)]
                     if steps_hints else f"In small groups, {v} a case/task related to the content; capture outcomes on a mini-whiteboard.")

        assess = {"Low": "5-item exit ticket (recall/identify).",
                  "Medium": "Performance check using worked-example rubric.",
                  "High": "Criteria-based critique/design justification; short reflection."}[tier]

        rows.append({
            "Lesson": lesson,
            "Week": week,
            "Policy focus": tier,
            "Title": f"{ctx} — {tier} Activity {i}",
            "Tier": tier,
            "Objective": f"Students will {v} key ideas from the uploaded content{(' on ' + topic) if topic else ''}.",
            "Steps": " ".join([
                f"Starter ({t1}m): {v.capitalize()} prior knowledge using a quick think–pair–share tied to {('the topic ' + topic) if topic else 'today’s content'}.",
                f"Main ({t2}m): {main_step}",
                f"Plenary ({t3}m): Share, compare and refine answers; agree success criteria."
            ]),
            "Materials": "Slides/board, markers, handouts (optional), timer",
            "Assessment": assess,
            "Duration (mins)": duration,
        })
    return pd.DataFrame(rows)

# ----------------------------- Exporters -----------------------------
def df_to_docx_mcqs(df: pd.DataFrame, header_ctx: str) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument()
    doc.add_heading(f"ADI MCQs — {header_ctx}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    doc.add_paragraph("Each block: Q1 Low → Q2 Medium → Q3 High").runs[0].italic = True
    for b in sorted(df["Block"].unique()):
        doc.add_heading(f"Block {b}", 2)
        blk = df[df["Block"] == b].sort_values(["Q#"])
        qn = 1
        for _, r in blk.iterrows():
            pr = doc.add_paragraph().add_run(f"Q{qn}. [{r['Tier']}] {r['Question']}")
            pr.bold = True
            doc.add_paragraph(f"A. {r['Option A']}")
            doc.add_paragraph(f"B. {r['Option B']}")
            doc.add_paragraph(f"C. {r['Option C']}")
            doc.add_paragraph(f"D. {r['Option D']}")
            doc.add_paragraph(f"Answer: {r['Answer']}")
            doc.add_paragraph(f"Explanation: {r.get('Explanation','')}")
            doc.add_paragraph("")
            qn += 1
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def mcq_to_gift(df: pd.DataFrame, header_ctx: str) -> bytes:
    lines = [f"// ADI MCQs — {header_ctx}", f"// Exported {datetime.now():%Y-%m-%d %H:%M}", ""]
    df = df.sort_values(["Block","Q#"], kind="stable")
    for idx, row in df.reset_index(drop=True).iterrows():
        qname = f"Block{row['Block']}-Q{int(row.get('Q#',0))}-{row['Tier']}"
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

def df_to_docx_activities(df: pd.DataFrame, header_ctx: str) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument()
    doc.add_heading(f"ADI Activities — {header_ctx}", 1)
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
            <div class='h-sub'>Sleek, professional and engaging. Print-ready handouts based on your uploaded content.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------- Sidebar (master controls) -----------------------------
with st.sidebar:
    # Upload
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>UPLOAD SOURCE</div><hr class='rule'/>", unsafe_allow_html=True)
        up_file = st.file_uploader("PDF / DOCX / PPTX", type=["pdf","docx","pptx"], label_visibility="collapsed",
                                   help="Drop an eBook, lesson plan, or PPT — the content will drive MCQs and Activities.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Course context
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
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>KNOWLEDGE MCQs</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.mcq_blocks = st.radio("Quick pick blocks", [5,10,20,30], horizontal=True,
                                               index=[5,10,20,30].index(st.session_state.mcq_blocks) if st.session_state.mcq_blocks in [5,10,20,30] else 1,
                                               key="sb_blocks")
        st.markdown("</div>", unsafe_allow_html=True)

    # Activities knobs
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>SKILLS ACTIVITIES</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.setdefault("ref_act_n", 3)
        st.session_state.setdefault("ref_act_d", 45)
        st.session_state.ref_act_n = st.number_input("Activities count", min_value=1, value=st.session_state.ref_act_n, step=1, key="sb_act_n")
        st.session_state.ref_act_d = st.number_input("Duration (mins)", min_value=5, value=st.session_state.ref_act_d, step=5, key="sb_act_d")
        st.markdown("</div>", unsafe_allow_html=True)

    # Parse upload late to not block UI
    if up_file:
        st.session_state.upload_text = extract_text_from_upload(up_file)

# ----------------------------- Tabs (main area) -----------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# ===== MCQs tab =====
with mcq_tab:
    bloom = bloom_focus_for_week(int(st.session_state.week))
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>MCQ Generator</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='context-banner'><strong>Context:</strong> Lesson {st.session_state.lesson} • Week {st.session_state.week} • <em>{bloom} focus</em></div>", unsafe_allow_html=True)

    topic = st.text_input("Topic / Outcome (optional)", placeholder="If empty, we'll still use the upload to generate content", key="mcq_topic")
    with st.expander("Show/edit parsed source (from upload)", expanded=False):
        source_mcq = st.text_area("", value=st.session_state.upload_text, height=180, label_visibility="collapsed", key="source_mcq")

    # Bloom panels with active highlight
    low_active  = " panel-active" if bloom=="Low" else ""
    med_active  = " panel-active" if bloom=="Medium" else ""
    high_active = " panel-active" if bloom=="High" else ""
    st.markdown(
        f"""
        <div class='policy-group low{low_active}'>
          <div class='policy-label'>Remember / Understand</div>
          <div style='margin-bottom:6px; font-weight:700;'>Low (Weeks 1–4)</div>
          {" ".join([f"<span class='badge low'>{w}</span>" for w in LOW_VERBS])}
        </div>
        <div class='policy-group med{med_active}'>
          <div class='policy-label'>Apply / Analyze</div>
          <div style='margin-bottom:6px; font-weight:700;'>Medium (Weeks 5–9)</div>
          {" ".join([f"<span class='badge med'>{w}</span>" for w in MED_VERBS])}
        </div>
        <div class='policy-group high{high_active}'>
          <div class='policy-label'>Evaluate / Create</div>
          <div style='margin-bottom:6px; font-weight:700;'>High (Weeks 10–14)</div>
          {" ".join([f"<span class='badge high'>{w}</span>" for w in HIGH_VERBS])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Generate MCQ Blocks"):
        with st.spinner("Building MCQ blocks from your content…"):
            st.session_state.mcq_df = generate_mcq_blocks(
                topic, source_mcq, int(st.session_state.mcq_blocks),
                int(st.session_state.week), int(st.session_state.lesson)
            )

    if st.session_state.mcq_df is None or st.session_state.mcq_df.empty:
        if not st.session_state.upload_text:
            st.warning("Upload a PDF/DOCX/PPTX or paste text in the expander to generate content-based MCQs.")
        else:
            st.info("No MCQs yet. Use the button above to generate.")
    else:
        st.session_state.mcq_df = st.session_state.mcq_df.sort_values(["Block","Q#"], kind="stable").reset_index(drop=True)
        view_cols = ["Block","Q#","Tier","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]
        view = st.session_state.mcq_df[view_cols] if all(c in st.session_state.mcq_df.columns for c in view_cols) else st.session_state.mcq_df
        edited = st.data_editor(view, num_rows="dynamic", use_container_width=True, key="mcq_editor")
        st.session_state.mcq_df = edited

        header_ctx = _fallback(topic, f"Lesson {st.session_state.lesson} • Week {st.session_state.week}")
        st.markdown("<div style='display:flex; gap:10px; flex-wrap:wrap'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", df_to_docx_mcqs(edited, header_ctx),
                           file_name="adi_mcqs.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download Moodle (GIFT)", mcq_to_gift(edited, header_ctx),
                           file_name="adi_mcqs_gift.txt", mime="text/plain")
        st.download_button("Download CSV", df_to_csv_bytes(edited),
                           file_name="adi_mcqs.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ===== Activities tab =====
with act_tab:
    bloom = bloom_focus_for_week(int(st.session_state.week))
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>Activities Planner</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='context-banner'><strong>Context:</strong> Lesson {st.session_state.lesson} • Week {st.session_state.week} • <em>{bloom} focus</em></div>", unsafe_allow_html=True)

    # Emphasis (override allowed)
    default_idx = ["Low","Medium","High"].index(bloom if bloom in ["Low","Medium","High"] else "Medium")
    tier = st.radio("Emphasis", ["Low","Medium","High"], horizontal=True, index=default_idx, key="act_tier")

    verbs_for_tier = ADI_VERBS[tier]
    st.markdown("**Bloom verbs** (select 1–6 to emphasise; defaults provided):")
    st.session_state.act_selected_verbs = st.multiselect("Verb chips", options=verbs_for_tier, default=verbs_for_tier[:2], key="act_verbs")

    topic2 = st.text_input("Topic (optional)", value="", placeholder="Unit focus (optional — content still comes from the upload)", key="act_topic")
    with st.expander("Show/edit parsed source (from upload)", expanded=False):
        source_activities = st.text_area("", value=st.session_state.upload_text, height=180, label_visibility="collapsed", key="source_activities")

    if st.button("Generate Activities"):
        with st.spinner("Assembling activities from your content…"):
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
        if not st.session_state.upload_text:
            st.warning("Upload a PDF/DOCX/PPTX or paste text in the expander to generate content-based activities.")
        else:
            st.info("No activities yet. Use the button above to generate.")
    else:
        act_cols = ["Lesson","Week","Policy focus","Title","Tier","Objective","Steps","Materials","Assessment","Duration (mins)"]
        act_view = st.session_state.act_df[act_cols] if all(c in st.session_state.act_df.columns for c in act_cols) else st.session_state.act_df
        act_edit = st.data_editor(act_view, num_rows="dynamic", use_container_width=True, key="act_editor")
        st.session_state.act_df = act_edit

        header_ctx = _fallback(topic2, f"Lesson {st.session_state.lesson} • Week {st.session_state.week}")
        st.markdown("<div style='display:flex; gap:10px; flex-wrap:wrap'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", df_to_docx_activities(act_edit, header_ctx),
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
    • For best results, upload a source (PDF/DOCX/PPTX). The generator mines *that* text for terms, stems and steps.  
    • If styles look default, use **Rerun and Clear Cache** and hard-refresh (Ctrl/Cmd+Shift+R).  
    • Look for the green **ADI style v18** badge to confirm CSS loaded.  
    """
)
