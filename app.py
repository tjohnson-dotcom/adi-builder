# ADI Builder — Lesson Activities & Questions
# Full one-file Streamlit app.
# UI look preserved (ADI banner, sidebar cards, chips).
# Upgraded parsing (PDF/DOCX/PPTX), MCQs (Low→Med→High), Activities,
# CSV + Word (.docx) exports.

import io, re, random
from typing import Any, List

import pandas as pd
import streamlit as st

# ----------------------------- Optional parsers -----------------------------
try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None
try:
    from pptx import Presentation
except Exception:
    Presentation = None

# Word exports
from io import BytesIO
try:
    from docx import Document
    from docx.shared import Pt, Inches
except Exception:
    Document = None
    Pt = None
    Inches = None

# ----------------------------- Page config & CSS (keeps your look) -----------------------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="📚", layout="wide")

ADI_CSS = """
<style>
:root{ --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-gold:#C8A85A; --ink:#1f2937; --border:#E3E8E3; --bg:#F7F7F4; }
html,body{background:var(--bg);} main .block-container{max-width:1180px; padding-top:0.6rem}
.adi-hero{display:flex; align-items:center; gap:14px; padding:18px 20px; border-radius:22px; color:#fff;
  background:linear-gradient(95deg,var(--adi-green),var(--adi-green-600)); box-shadow:0 12px 28px rgba(0,0,0,.07); margin-bottom:14px}
.h-title{font-size:22px;font-weight:800;margin:0}
.h-sub{font-size:12px;opacity:.95;margin:2px 0 0 0}
.side-card{background:#fff; border:1px solid var(--border); border-radius:16px; padding:10px 16px; margin:14px 8px; box-shadow:0 8px 18px rgba(0,0,0,.06)}
.side-cap{display:flex; align-items:center; gap:10px; font-size:11px; text-transform:uppercase; letter-spacing:.08em; font-weight:700; margin:0 0 8px}
.side-cap .dot{width:9px;height:9px;border-radius:999px;background:var(--adi-gold); box-shadow:0 0 0 4px rgba(200,168,90,.18)}
.rule{height:2px; background:linear-gradient(90deg,var(--adi-gold),transparent); border:0; margin:8px 0 10px}
.card{background:#fff; border:1px solid var(--border); border-radius:18px; box-shadow:0 12px 28px rgba(0,0,0,.07); padding:16px; margin:10px 0}
.cap{color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; font-size:12px; margin:0 0 10px}
.context-banner{background:#fff; border:1px solid var(--border); border-radius:12px; padding:10px 12px; display:flex; gap:10px; align-items:center}
.badge{display:inline-flex; align-items:center; border-radius:999px; padding:2px 8px; font-size:12px; border:1px solid var(--border); margin:2px 6px 2px 0; font-weight:600}
.low{background:#eaf5ec; color:#245a34}
.med{background:#fbf6ec; color:#6a4b2d}
.high{background:#f3f1ee; color:#4a4a45}
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

st.markdown("""
<div class='adi-hero'>
  <div>
    <div class='h-title'>ADI Builder — Lesson Activities & Questions</div>
    <div class='h-sub'>Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------- Bloom Policy -----------------------------
LOW_VERBS  = ["define","identify","list","describe","recall","label"]
MED_VERBS  = ["apply","demonstrate","solve","illustrate","analyze","interpret","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","formulate","critique"]
ADI_VERBS  = {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}

def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    return "High"

# ----------------------------- Upload parsing -----------------------------
def _clean_lines(text: str) -> str:
    lines = [ln.strip() for ln in (text or "").replace("\r","\n").split("\n") if ln.strip()]
    lines = [ln for ln in lines if not re.fullmatch(r"(page\s*\d+|\d+)", ln, flags=re.I)]
    seen, out = set(), []
    for ln in lines:
        k = ln[:80].lower()
        if k in seen: 
            continue
        seen.add(k); out.append(ln)
    return "\n".join(out)[:6000]

def extract_text_from_upload(up_file) -> str:
    """
    Robust extractor for PDF/DOCX/PPTX. Returns ~6k chars of clean text.
    """
    if up_file is None:
        return ""
    name = (getattr(up_file, "name", "") or "").lower()
    try:
        if name.endswith(".pdf"):
            buf = up_file.read() if hasattr(up_file, "read") else up_file.getvalue()
            if pdfplumber:
                pages = []
                with pdfplumber.open(io.BytesIO(buf)) as pdf:
                    for p in pdf.pages[:30]:
                        pages.append(p.extract_text() or "")
                return _clean_lines("\n".join(pages))
            elif PdfReader:
                reader = PdfReader(io.BytesIO(buf))
                text = ""
                for page in reader.pages[:30]:
                    text += (page.extract_text() or "") + "\n"
                return _clean_lines(text)
            else:
                return "[Could not parse PDF: add PyPDF2 or pdfplumber]"
        elif name.endswith(".docx") and DocxDocument:
            doc = DocxDocument(up_file)
            text = "\n".join((p.text or "") for p in doc.paragraphs[:250])
            return _clean_lines(text)
        elif name.endswith(".pptx") and Presentation:
            prs = Presentation(up_file)
            text_parts = []
            for slide in prs.slides[:40]:
                for shp in slide.shapes:
                    if hasattr(shp, "text") and shp.text:
                        text_parts.append(shp.text)
                if getattr(slide, "has_notes_slide", False) and getattr(slide.notes_slide, "notes_text_frame", None):
                    text_parts.append(slide.notes_slide.notes_text_frame.text or "")
            return _clean_lines("\n".join(text_parts))
        else:
            return "[Unsupported file type or missing parser]"
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ----------------------------- Tiny NLP helpers -----------------------------
_STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","as","is","are","be","was","were","this","that","these","those",
    "it","its","at","from","into","over","under","about","between","within","use","used","using","also","than","which","such","may",
    "can","could","should","would","will","not","if","when","while","after","before","each","per","via","more","most","less","least",
    "other","another","see","example","examples","appendix","figure","table","chapter","section","page","pages","ref","ibid",
    "module","lesson","week","activity","activities","objective","objectives","outcome","outcomes","question","questions","topic","topics",
    "student","students","teacher","instructor","course","unit","learning","overview","summary","introduction","conclusion","content","contents"
}

def _sentences(text: str) -> List[str]:
    chunks = re.split(r"[.\u2022\u2023\u25CF•]|(?:\n\s*\-\s*)|(?:\n\s*\*\s*)", text or "")
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
    for w in re.split(r"[^A-Za-z0-9]+", text or ""):
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

# ----------------------------- MCQ generator -----------------------------
def _distractors_from_sentences(correct: str, pool: list[str], n: int) -> list[str]:
    rand = random.Random(42)  # deterministic
    base = (correct or "").strip()
    outs: list[str] = []

    def tweak(s: str) -> str:
        s2 = re.sub(r"\b(increase[s]?|higher|more)\b", "decrease", s, flags=re.I)
        s2 = re.sub(r"\b(decrease[s]?|lower|less)\b", "increase", s2, flags=re.I)
        s2 = re.sub(r"(\d{1,3})(\s?(?:km/h|mph|%|units?))", lambda m: str(max(1, int(m.group(1)) + 10)) + (m.group(2) or ""), s2)
        s2 = re.sub(r"\balways\b", "sometimes", s2, flags=re.I)
        s2 = re.sub(r"\bmust\b", "may", s2, flags=re.I)
        return s2 if s2.lower()!=s.lower() else s + " (in the wrong context)"

    if base:
        outs.append(tweak(base))
        outs.append(tweak(base[::-1])[::-1])

    ckey = base.lower()[:60]
    cands = [p for p in pool if p and 20 <= len(p) <= 160 and p.lower()[:60] != ckey]
    rand.shuffle(cands)
    for s in cands:
        if len(outs) == n: break
        if s not in outs: outs.append(s)

    while len(outs) < n:
        outs.append("This statement misinterprets a key constraint.")
    return outs[:n]

def generate_mcq_blocks(topic: str, source: str, num_blocks: int, week: int, lesson: int = 1) -> pd.DataFrame:
    """
    Generates 3 MCQs per block (Low/Medium/High) from uploaded content.
    Deterministic; same inputs -> same outputs.
    """
    ctx_banner = (topic or "").strip() or f"Lesson {lesson} • Week {week}"
    src_text = (source or "").strip()
    sents = _sentences(src_text)
    keys = _keywords(src_text or topic or "", top_n=max(24, num_blocks * 6))

    if not sents:
        sents = [f"{ctx_banner}: core concepts, steps, constraints, and safety considerations."]
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

    rows: list[dict[str, Any]] = []
    rnd = random.Random(2025)

    def add_row(block: int, tier: str, stem: str, correct: str, wrongs: list[str]):
        options = [correct] + wrongs[:3]
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(correct)]
        rows.append({
            "Block": block,
            "Tier": tier,
            "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": stem.strip(),
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans,
            "Explanation": "Chosen option aligns with the source context.",
            "Order": {"Low":1,"Medium":2,"High":3}[tier],
        })

    for b in range(1, num_blocks + 1):
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

def assert_policy(df: pd.DataFrame):
    for b in sorted(set(df["Block"])):
        sub = df[df["Block"]==b].sort_values("Q#")
        assert len(sub)==3, f"Block {b} must have exactly 3 questions."
        assert list(sub["Tier"]) == ["Low","Medium","High"], f"Block {b} must be Low→Medium→High."
        assert list(sub["Q#"]) == [1,2,3], f"Block {b} Q# must be 1..3."

# ----------------------------- Activities -----------------------------
def generate_activities(count: int, duration: int, tier: str, topic: str,
                        lesson: int, week: int, source: str = "", selected_verbs: list[str] | None = None) -> pd.DataFrame:
    """
    Lesson/Week-linked activities with ADI verbs + mined content cues.
    Deterministic and safe to run multiple times.
    """
    topic = (topic or "").strip()
    ctx = f"Lesson {lesson} • Week {week}" + (f" — {topic}" if topic else "")
    verbs = (selected_verbs or ADI_VERBS.get(tier, ADI_VERBS["Medium"]))[:6]

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
                f"Starter ({t1}m): {v.capitalize()} prior knowledge with a quick think–pair–share tied to {('the topic ' + topic) if topic else 'today’s content'}.",
                f"Main ({t2}m): {main_step}",
                f"Plenary ({t3}m): Share, compare and refine answers; agree success criteria."
            ]),
            "Materials": "Slides/board, markers, timer; optional handout",
            "Assessment": assess + " Collect: Team submits artefact photo + 3-sentence rationale.",
            "Duration (mins)": duration,
        })
    return pd.DataFrame(rows)

# ----------------------------- Word (.docx) exports -----------------------------
def _docx_heading(doc, text, level=0):
    p = doc.add_paragraph()
    run = p.add_run(text)
    if level == 0:
        run.bold = True; run.font.size = Pt(16)
    elif level == 1:
        run.bold = True; run.font.size = Pt(13)
    else:
        run.font.size = Pt(11)

def export_mcqs_to_docx(df, lesson:int, week:int, topic:str="") -> bytes:
    if Document is None:
        return b""
    doc = Document()
    sec = doc.sections[0]
    if Inches:
        sec.left_margin = Inches(0.8); sec.right_margin = Inches(0.8)
    _docx_heading(doc, f"Knowledge MCQs — Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else ""), 0)
    doc.add_paragraph()
    for b in sorted(df["Block"].unique()):
        _docx_heading(doc, f"Block {b}", 1)
        sub = df[df["Block"]==b].sort_values("Q#")
        for _, r in sub.iterrows():
            doc.add_paragraph(f"{r['Q#']}. ({r['Tier']}) {r['Question']}")
            doc.add_paragraph(f"A. {r['Option A']}")
            doc.add_paragraph(f"B. {r['Option B']}")
            doc.add_paragraph(f"C. {r['Option C']}")
            doc.add_paragraph(f"D. {r['Option D']}")
            doc.add_paragraph()
        doc.add_paragraph()
    _docx_heading(doc, "Answer Key", 1)
    for b in sorted(df["Block"].unique()):
        sub = df[df["Block"]==b].sort_values("Q#")
        for _, r in sub.iterrows():
            doc.add_paragraph(f"Block {int(b)} Q{int(r['Q#'])}: {r['Answer']}")
    bio = BytesIO(); doc.save(bio); bio.seek(0)
    return bio.getvalue()

def export_activities_to_docx(df, lesson:int, week:int, topic:str="") -> bytes:
    if Document is None:
        return b""
    doc = Document()
    sec = doc.sections[0]
    if Inches:
        sec.left_margin = Inches(0.8); sec.right_margin = Inches(0.8)
    _docx_heading(doc, f"Skills Activities — Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else ""), 0)
    doc.add_paragraph()
    for i, r in df.iterrows():
        _docx_heading(doc, r.get("Title", f"Activity {i+1}"), 1)
        doc.add_paragraph(f"Policy focus: {r['Policy focus']}")
        doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph(f"Steps: {r['Steps']}")
        doc.add_paragraph(f"Materials: {r['Materials']}")
        doc.add_paragraph(f"Assessment: {r['Assessment']}")
        doc.add_paragraph(f"Duration: {r['Duration (mins)']} mins")
        doc.add_paragraph()
    bio = BytesIO(); doc.save(bio); bio.seek(0)
    return bio.getvalue()

# ----------------------------- Sidebar (unchanged look) -----------------------------
with st.sidebar:
    st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>SOURCE</div><hr class='rule'/>", unsafe_allow_html=True)
    up_file = st.file_uploader("Upload e-book or lesson (PDF/DOCX/PPTX)", type=["pdf","docx","pptx"], accept_multiple_files=False)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>CONTEXT</div><hr class='rule'/>", unsafe_allow_html=True)
    st.session_state.setdefault("lesson", 1)
    st.session_state.setdefault("week", 3)
    st.session_state.lesson = st.number_input("Lesson", 1, 20, st.session_state.lesson)
    st.session_state.week = st.number_input("Week", 1, 14, st.session_state.week)
    topic = st.text_input("Topic (optional)", "")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>KNOWLEDGE MCQs (ADI POLICY)</div><hr class='rule'/>", unsafe_allow_html=True)
    st.session_state.setdefault("mcq_blocks", 5)
    st.session_state.mcq_blocks = st.radio("Quick pick blocks", [5,10,20,30], horizontal=True, index=[5,10,20,30].index(st.session_state.mcq_blocks))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>SKILLS ACTIVITIES</div><hr class='rule'/>", unsafe_allow_html=True)
    st.session_state.setdefault("ref_act_n", 3)
    st.session_state.setdefault("ref_act_d", 45)
    st.session_state.ref_act_n = st.number_input("Activities (count)", min_value=1, value=st.session_state.ref_act_n, step=1)
    st.session_state.ref_act_d = st.number_input("Duration (mins)", min_value=5, value=st.session_state.ref_act_d, step=5)
    st.markdown("</div>", unsafe_allow_html=True)

    # Parse upload late so UI loads instantly
    st.session_state.upload_text = extract_text_from_upload(up_file) if up_file else st.session_state.get("upload_text", "")

# ----------------------------- Tabs -----------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# ===== MCQs tab =====
with mcq_tab:
    bloom = bloom_focus_for_week(int(st.session_state.week))
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>MCQ GENERATOR</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='context-banner'><strong>Context:</strong> Lesson {int(st.session_state.lesson)} • Week {int(st.session_state.week)} • <em>{bloom} focus</em></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([3,1])
    with col1:
        source_mcq = st.text_area("(Optional) Add/override source text", value=st.session_state.upload_text or "", height=160)
    with col2:
        st.markdown("<div class='badge low'>Low</div><div class='badge med'>Medium</div><div class='badge high'>High</div>", unsafe_allow_html=True)
        st.caption("Each block generates 3 MCQs: Low → Medium → High")
