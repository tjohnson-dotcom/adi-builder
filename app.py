# app.py
# ADI Builder — Lesson Activities & Questions
# API-free generators with Course Packs, Lesson Plan ingestion, .docx exports

import io, os, re, time, hashlib, random, textwrap
from typing import List, Optional, Tuple, Dict

import streamlit as st

# Light NLP
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt', quiet=True)

from sklearn.feature_extraction.text import TfidfVectorizer

# Document parsers
from docx import Document as DocxDocument
from pptx import Presentation as PptxPresentation

try:
    import fitz  # PyMuPDF (optional)
except Exception:
    fitz = None

from pypdf import PdfReader

# ──────────────────────────────────────────────────────────────────────────────
# Theming (use config.toml for global theme; CSS here only for minor accents)
# ──────────────────────────────────────────────────────────────────────────────

PRIMARY = "#245a34"          # deep green
ACCENT_BG = "#eef5ef"        # very light green
PILL_BG = "#f3f4f3"          # light neutral for pills

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

CUSTOM_CSS = f"""
<style>
/* top banner */
.adi-banner {{
  background:{PRIMARY}; color:#fff; border-radius:12px; padding:12px 18px; margin:8px 0 10px 0;
}}
.adi-subtle {{ color:#dfe9e1; font-size:12px; }}

/* tabs underline accent */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  border-bottom: 3px solid {PRIMARY};
}}

/* shaded Bloom rows */
.bloom-row.low  {{ background:#f7faf7; border-radius:10px; padding:10px; }}
.bloom-row.med  {{ background:#f1f7f1; border-radius:10px; padding:10px; }}
.bloom-row.high {{ background:#ebf4eb; border-radius:10px; padding:10px; }}

/* verb pills */
.verb-pill {{
  display:inline-block; margin:6px 10px 6px 0; padding:10px 18px; border-radius:999px;
  background:{PILL_BG}; border:1px solid #e6e6e6; color:#222; font-weight:500;
}}
.verb-pill.active {{
  background:{ACCENT_BG}; border-color:{PRIMARY}; box-shadow:0 0 0 1px {PRIMARY} inset; color:#1f3a25;
}}

/* tiny badges */
.badge {{
  display:inline-block; padding:4px 10px; border-radius:999px; background:#f2ecdc; color:#5c4b12; font-weight:600; font-size:12px;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────

def safe_get(d, k, default):
    return d[k] if k in d else default

def sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    sents = [s.strip() for s in sent_tokenize(text)]
    # prune super short / super long
    return [s for s in sents if 40 <= len(s) <= 240]

def tfidf_keyterms(text: str, top_k: int = 40) -> List[str]:
    sents = sentences(text)
    if not sents:
        return []
    vec = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1,2),
        min_df=1,
        max_df=0.9
    )
    X = vec.fit_transform(sents)
    scores = X.sum(axis=0).A1
    terms = vec.get_feature_names_out()
    ranked = [t for _, t in sorted(zip(scores, terms), reverse=True)]
    # keep only alpha-ish tokens
    ranked = [r for r in ranked if re.search(r"[A-Za-z]", r)]
    return ranked[:top_k]

def hash_seed(*parts) -> int:
    s = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) % (2**32)

# ──────────────────────────────────────────────────────────────────────────────
# Course Packs (glossary + activity templates)
# ──────────────────────────────────────────────────────────────────────────────

TEMPLATES: Dict[str, List[Tuple[str, List[str], List[str], str]]] = {
    "Low": [
        ("Quick Definitions", [
            "Individually write one-sentence definitions for 6 key terms.",
            "Swap with a peer and refine any unclear wording."
        ], ["Index cards"], "Accurate and concise definitions for all terms."),
    ],
    "Medium": [
        ("Worked Example → Variation", [
            "Solve the worked example collaboratively.",
            "Create and solve one variation that changes a parameter.",
            "Compare answers with another group."
        ], ["Worksheet"], "Correct solution and rationale for both versions."),
    ],
    "High": [
        ("Critique & Redesign", [
            "Review a provided solution; identify 3 weaknesses.",
            "Propose and justify 2 improvements.",
        ], ["A3 paper"], "Clear critiques linked to criteria; viable redesign.")
    ]
}

COURSE_PACKS = {
    "General": {"glossary": [], "activities": {}},

    "CNC Machining": {
        "glossary": [
            "toolpath","G-code","M-code","workpiece","spindle speed","feed rate",
            "coolant","fixture","tolerance","profiling","pocketing","chip load",
            "end mill","lathe","roughing","finishing"
        ],
        "activities": {
            "Medium": [
                ("Program & Simulate", [
                    "Load part drawing; identify features and tolerances.",
                    "Write toolpath (profile + pocket); set feeds/speeds.",
                    "Simulate; fix collisions and gouges."
                ], ["CAM software","example part"], "Runnable program and verified path.")
            ],
            "High": [
                ("Fixture Redesign (Quick)", [
                    "Audit current fixture faults (rigidity, access).",
                    "Sketch a fix that improves clamping and repeatability.",
                    "Pitch changes + risks."
                ], ["A3 paper"], "Design justifications aligned to tolerance stack.")
            ]
        }
    },

    "Explosives Safety": {
        "glossary": [
            "net explosive quantity","blast overpressure","fragmentation","standoff distance",
            "detonation","deflagration","risk zone","donor","acceptor","barrier",
            "PPE","hazard class","magazine","arc flash"
        ],
        "activities": {
            "Low": [
                ("Terminology Match", [
                    "Match hazard terms to definitions.",
                    "Whole-class check with quick scenarios."
                ], ["Term cards"], "Shared safety vocabulary established.")
            ],
            "Medium": [
                ("Distance–Risk Estimator", [
                    "Given NEQ, compute minimum standoff.",
                    "Compare three site layouts; pick the safest."
                ], ["Calculator","Site plans"], "Correct calculations and reasoning.")
            ],
            "High": [
                ("Incident Critique", [
                    "Review incident summary; identify hazard breaks.",
                    "Propose 3 controls ranked by effectiveness."
                ], ["Case sheet"], "Controls map to hierarchy of hazard control.")
            ]
        }
    },

    "Process Simulation (DWSIM)": {
        "glossary": [
            "PID controller","setpoint","controlled variable","manipulated variable",
            "heater duty","cooler duty","disturbance","steady state","NRTL"
        ],
        "activities": {
            "High": [
                ("DWSIM – Heater–Cooler PID Stability (Worksheet)", [
                    "Build flowsheet: Feed → Heater → Cooler → Product (NRTL).",
                    "Define Feed 1000 kg/h, 25 °C, 1 atm; 70% H₂O / 30% EtOH.",
                    "Set duties: Heater 200 kW; Cooler −150 kW.",
                    "Insert PID: CV=Product T; MV=Heater Duty; SP=40 °C.",
                    "Disturbance: raise Feed T to 35 °C; observe response.",
                    "Record Initial / Disturbance / PID-ON results.",
                    "Plot and overlay Product T vs time; save screenshots."
                ], ["DWSIM","PCs"], "Completed table and overlaid plots.")
            ]
        }
    }
}

def apply_glossary_bias(keyterms: List[str], course: str) -> List[str]:
    glossary = COURSE_PACKS.get(course, {}).get("glossary", [])
    seen = set()
    out = []
    for g in glossary:
        g2 = g.strip()
        if g2 and g2.lower() not in seen:
            out.append(g2); seen.add(g2.lower())
    for k in keyterms:
        if k.lower() not in seen:
            out.append(k); seen.add(k.lower())
    return out

# ──────────────────────────────────────────────────────────────────────────────
# File parsing
# ──────────────────────────────────────────────────────────────────────────────

def parse_pdf(path: str, deep: bool = False, time_budget: int = 120) -> Tuple[str, str]:
    """Return (text, notes)"""
    start = time.time()
    notes = []
    text_chunks = []

    # Try pypdf first (fast and robust)
    pages_done = 0
    try:
        reader = PdfReader(path)
        for i, page in enumerate(reader.pages):
            if deep and (time.time() - start) > time_budget:
                notes.append(f"pypdf timeout • pypdf ({pages_done}/{len(reader.pages)} pages)")
                break
            txt = page.extract_text() or ""
            if txt.strip():
                text_chunks.append(txt)
            pages_done += 1
        if pages_done:
            notes.append(f"pypdf ({pages_done}/{len(reader.pages)} pages)")
    except Exception as e:
        notes.append(f"pypdf failed: {e}")

    # Try PyMuPDF if installed and budget allows
    if fitz and (deep and (time.time() - start) <= time_budget):
        try:
            doc = fitz.open(path)
            mu_done = 0
            for i, page in enumerate(doc):
                if (time.time() - start) > time_budget:
                    notes.append(f"PyMuPDF timeout • PyMuPDF ({mu_done}/{len(doc)} pages)")
                    break
                txt = page.get_text() or ""
                if txt.strip():
                    text_chunks.append(txt)
                mu_done += 1
            if mu_done:
                notes.append(f"PyMuPDF ({mu_done}/{len(doc)} pages)")
        except Exception as e:
            notes.append(f"PyMuPDF failed: {e}")
    elif fitz is None:
        notes.append("PyMuPDF not installed (optional).")

    text = "\n".join(text_chunks)
    if not text.strip():
        notes.append("No extractable text found (likely image-only).")
    else:
        notes.append("Parsed successfully")
    return text, " • ".join(notes)

def parse_docx(path: str) -> Tuple[str, str]:
    try:
        d = DocxDocument(path)
        text = "\n".join([p.text for p in d.paragraphs if p.text.strip()])
        return text, "Parsed successfully (DOCX)"
    except Exception as e:
        return "", f"DOCX parse failed: {e}"

def parse_pptx(path: str) -> Tuple[str, str]:
    try:
        prs = PptxPresentation(path)
        out = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    t = shape.text or ""
                    if t.strip():
                        out.append(t)
        return "\n".join(out), "Parsed successfully (PPTX)"
    except Exception as e:
        return "", f"PPTX parse failed: {e}"

def parse_lesson_plan_docx(path: str) -> Dict[str, any]:
    """Very lightweight lesson plan extraction."""
    info = {"topic":"", "los":[], "times":[]}
    try:
        d = DocxDocument(path)
        lines = [p.text.strip() for p in d.paragraphs if p.text.strip()]
        # Topic
        for L in lines[:8]:
            if re.search(r"topic", L, re.I):
                info["topic"] = re.sub(r"(?i).*topic[:\-\s]*", "", L).strip()
                break
        # LOs
        for L in lines:
            if re.match(r"(LO\d+|Learning Objective|\- )", L, re.I) or re.search(r"\bdefine\b|\bdescribe\b|\bexplain\b|\bdistinguish\b", L, re.I):
                info["los"].append(L)
        # Times
        times = []
        for L in lines:
            m = re.findall(r"(\d+)\s*(?:min|minutes)", L, re.I)
            times += [int(x) for x in m]
        info["times"] = times[:10]
    except Exception:
        pass
    return info

# ──────────────────────────────────────────────────────────────────────────────
# MCQ generation (simple, API-free)
# ──────────────────────────────────────────────────────────────────────────────

class MCQ:
    def __init__(self, stem: str, options: List[str], answer: int):
        self.stem = stem
        self.options = options
        self.answer = answer

def distractors_from_terms(correct: str, pool: List[str], rng: random.Random, k: int = 3) -> List[str]:
    # pick near terms not equal to correct
    c = correct.lower().strip()
    candidates = [p for p in pool if p.lower() != c and len(p) > 2]
    rng.shuffle(candidates)
    # reduce overlong options
    candidates = [re.sub(r"^[\-\•]\s*", "", t).strip().capitalize()[:80] for t in candidates]
    uniq = []
    seen = set()
    for t in candidates:
        if t.lower() not in seen:
            uniq.append(t); seen.add(t.lower())
        if len(uniq) >= k: break
    # filler if needed
    while len(uniq) < k:
        uniq.append(re.sub(r"[^\w\s\-]", "", correct[::-1])[: max(5, min(12, len(correct)))])
    return uniq

def build_mcqs(text: str, n: int, bloom_focus: str,
               rng: Optional[random.Random]=None, course: str="General") -> List[MCQ]:
    rng = rng or random
    text = (text or "").strip()
    if not text:
        return []
    sents = sentences(text)
    if not sents:
        return []

    keyterms = tfidf_keyterms(text, top_k=40)
    keyterms = apply_glossary_bias(keyterms, course)

    rng.shuffle(sents)
    out = []
    for s in sents:
        # build a definition/meaning question for a top term appearing in s
        term = None
        for t in keyterms[:20]:
            if re.search(rf"\b{re.escape(t)}\b", s, re.I):
                term = t; break
        if not term:
            continue
        stem = f"What best describes '{term}' in this lesson?"
        correct = s
        # compress correct into a short phrase
        correct = re.sub(r"\s+", " ", correct)
        correct = re.sub(rf".*?\b{re.escape(term)}\b", term, correct, flags=re.I)
        correct = correct[:120].strip(" .")
        distractors = distractors_from_terms(correct, keyterms[5:30], rng=rng, k=3)

        options = [correct] + distractors
        rng.shuffle(options)
        answer = options.index(correct)
        out.append(MCQ(stem=stem, options=options, answer=answer))
        if len(out) >= n:
            break

    # Fallback: if too few, use generic stems from keyterms
    while len(out) < n and keyterms:
        t = keyterms.pop(0)
        stem = f"Which statement relates most closely to '{t}'?"
        correct = f"{t.capitalize()} is relevant to this topic."
        distractors = distractors_from_terms(correct, keyterms, rng=rng, k=3)
        options = [correct] + distractors
        rng.shuffle(options)
        out.append(MCQ(stem, options, options.index(correct)))
    return out

# ──────────────────────────────────────────────────────────────────────────────
# Activities + Revision
# ──────────────────────────────────────────────────────────────────────────────

def build_activities(topic: str, focus: str, count: int, minutes: int,
                     rng: Optional[random.Random]=None, course: str="General") -> List[dict]:
    rng = rng or random
    course_bank = COURSE_PACKS.get(course, {}).get("activities", {}).get(focus, [])
    global_bank = TEMPLATES.get(focus, [])
    bank = (course_bank + global_bank)[:] or global_bank[:]
    if not bank:
        return []
    rng.shuffle(bank)

    out = []
    for i in range(count):
        title, steps, materials, assess = bank[i % len(bank)]
        # light numeric variation (for worksheets like DWSIM)
        varied_steps = []
        for s in steps:
            varied = re.sub(r"(\d+)\s*°\s*C", lambda m: f"{int(m.group(1))+rng.choice([-2,-1,0,1,2])} °C", s)
            varied_steps.append(varied)
        out.append({
            "title": f"{title} — {topic or 'Lesson'}",
            "minutes": minutes,
            "objective": f"{focus} focus activity for {topic or 'the topic'}.",
            "steps": varied_steps,
            "materials": materials,
            "assessment": assess
        })
    return out

def build_revision_plan(focus: str, topic: str) -> List[str]:
    return [
        "## Day 1 – Fundamentals (45–60 min)",
        f"• Read key notes for {topic or 'the topic'}; summarise each section in one line.",
        "• Self-quiz with 3 MCQs.",
        "## Day 2 – Apply (45–60 min)",
        "• Re-work a short example; create 2 new practice items.",
        "## Day 3 – Analyse (45–60 min)",
        "• Draw a concept/process map; annotate assumptions.",
        "## Day 4 – Evaluate (45–60 min)",
        "• Critique a case or sample answer; propose 2 improvements.",
        "## Day 5 – Create (45–60 min)",
        "• Produce a one-page cheat-sheet + 5 MCQs with answers."
    ]

# ──────────────────────────────────────────────────────────────────────────────
# Exports (.docx)
# ──────────────────────────────────────────────────────────────────────────────

def mcqs_docx(mcqs: List[MCQ]) -> bytes:
    doc = DocxDocument()
    doc.add_heading("Knowledge MCQs", level=1)
    for i, q in enumerate(mcqs or [], 1):
        doc.add_paragraph(f"{i}. {q.stem}")
        for j, opt in enumerate(q.options, 1):
            doc.add_paragraph(f"{chr(64+j)}. {opt}", style="List Bullet")
        doc.add_paragraph(f"Answer: {chr(65+q.answer)}")
        doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def activities_docx(acts: List[dict]) -> bytes:
    doc = DocxDocument()
    doc.add_heading("Skills Activities", level=1)
    for i, a in enumerate(acts or [], 1):
        doc.add_heading(f"{i}. {a['title']} — {a['minutes']} mins", level=2)
        doc.add_paragraph(f"Objective: {a['objective']}")
        doc.add_paragraph("Steps:")
        for s in a["steps"]:
            doc.add_paragraph(s, style="List Number")
        if a["materials"]:
            doc.add_paragraph("Materials: " + ", ".join(a["materials"]))
        doc.add_paragraph("Check: " + a["assessment"])
        doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def revision_docx(plan: List[str], title: str = "1-Week Revision Plan") -> bytes:
    doc = DocxDocument()
    doc.add_heading(title, level=1)
    for line in plan:
        if line.startswith("## "):
            doc.add_heading(line.replace("## ",""), level=2)
        elif line.startswith("• "):
            doc.add_paragraph(line[2:], style="List Bullet")
        else:
            doc.add_paragraph(line)
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def bundle_docx(mcqs: List[MCQ], acts: List[dict], rev_lines: List[str], topic: str) -> bytes:
    doc = DocxDocument()
    doc.add_heading("ADI Lesson Pack", level=0)
    doc.add_paragraph(f"Topic: {topic or 'Lesson'}")
    doc.add_paragraph("Auto-generated with ADI Builder")
    doc.add_page_break()

    if mcqs:
        doc.add_heading("Knowledge MCQs", level=1)
        for i, q in enumerate(mcqs or [], 1):
            doc.add_paragraph(f"{i}. {q.stem}")
            for j, opt in enumerate(q.options, 1):
                doc.add_paragraph(f"{chr(64+j)}. {opt}", style="List Bullet")
            doc.add_paragraph(f"Answer: {chr(65+q.answer)}")
            doc.add_paragraph("")
        doc.add_page_break()

    if acts:
        doc.add_heading("Skills Activities", level=1)
        for i,a in enumerate(acts,1):
            doc.add_heading(f"{i}. {a['title']} — {a['minutes']} mins", level=2)
            doc.add_paragraph(f"Objective: {a['objective']}")
            doc.add_paragraph("Steps:")
            for s in a["steps"]:
                doc.add_paragraph(s, style="List Number")
            if a["materials"]:
                doc.add_paragraph("Materials: " + ", ".join(a["materials"]))
            doc.add_paragraph("Check: " + a["assessment"])
            doc.add_paragraph("")
        doc.add_page_break()

    if rev_lines:
        doc.add_heading("1-Week Revision Plan", level=1)
        for line in rev_lines:
            if line.startswith("## "):
                doc.add_heading(line.replace("## ",""), level=2)
            elif line.startswith("• "):
                doc.add_paragraph(line[2:], style="List Bullet")
            else:
                doc.add_paragraph(line)
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

# ──────────────────────────────────────────────────────────────────────────────
# UI — Sidebar
# ──────────────────────────────────────────────────────────────────────────────

st.sidebar.header("Upload (optional)")
uploaded = st.sidebar.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"], help="Limit 200MB per file • PDF, DOCX, PPTX")

deep_scan = st.sidebar.checkbox("Deep scan (all pages, slower)", value=False, help="Tries more pages and engines under a time budget.")
course_names = list(COURSE_PACKS.keys())
st.session_state.course = st.sidebar.selectbox("Course", course_names, index=course_names.index(st.session_state.get("course","General")))
variant_tag = st.sidebar.text_input("Instructor / variant (optional)", value=st.session_state.get("variant_tag",""))
st.session_state.variant_tag = variant_tag

st.sidebar.markdown("---")
st.sidebar.subheader("Course context")
st.session_state.lesson = st.sidebar.selectbox("Lesson", [1,2,3,4,5,6,7,8,9,10], index=0)
st.session_state.week   = st.sidebar.selectbox("Week", list(range(1,15)), index=6)

st.sidebar.markdown("---")
st.sidebar.subheader("Number of MCQs")
st.session_state.mcq_count = st.sidebar.selectbox("How many questions?", [5,10,15,20,30], index=1)

st.sidebar.markdown("---")
st.sidebar.subheader("Activities")
st.session_state.act_count = st.sidebar.selectbox("How many activities?", [1,2,3,4], index=1)
st.session_state.act_minutes = st.sidebar.selectbox("Time each (mins)", [5,10,15,20,30,45,60], index=4)

st.sidebar.markdown("---")
use_lesson_plan = st.sidebar.checkbox("Use lesson plan (DOCX) to pre-fill", value=False)

# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="adi-banner">
  <div><strong>ADI Builder — Lesson Activities & Questions</strong></div>
  <div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

# Auto Bloom focus from week
def bloom_from_week(week: int) -> str:
    if week <= 4: return "Low"
    if week <= 9: return "Medium"
    return "High"

bloom_focus = bloom_from_week(int(st.session_state.week))

# Topic + Source text
colA, colB = st.columns([4,1.2], gap="large")
with colA:
    st.session_state.topic = st.text_input("Topic / Outcome (optional)", value=st.session_state.get("topic",""))
with colB:
    st.markdown(f"<span class='badge'>Week {st.session_state.week}: {bloom_focus}</span>", unsafe_allow_html=True)

use_sample = st.checkbox("Use sample text (for a quick test)", value=False, help="Adds a small sample to generate quickly.")

# Source text area
source_default = st.session_state.get("source_text","")
source_area = st.text_area("Source text (editable)", value=source_default, height=180, help="Paste or jot key notes, vocab, facts here…")

# Upload parse status & “Insert extracted text”
uploaded_text = ""
parse_notes = ""

if uploaded is not None:
    # Save file locally
    tmp_path = os.path.join(st.session_state.get("tmpdir", "."), uploaded.name)
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())
    kind = uploaded.name.split(".")[-1].lower()
    if use_lesson_plan and kind == "docx":
        info = parse_lesson_plan_docx(tmp_path)
        if info.get("topic"):
            st.session_state.topic = info["topic"]
        los_text = "\n".join(info.get("los", []))
        uploaded_text = los_text
        parse_notes = f"Lesson plan parsed • topic='{info.get('topic','')}' • LOs={len(info.get('los',[]))} • times={info.get('times', [])}"
    else:
        if kind == "pdf":
            uploaded_text, parse_notes = parse_pdf(tmp_path, deep=deep_scan, time_budget=120 if deep_scan else 25)
        elif kind == "docx":
            uploaded_text, parse_notes = parse_docx(tmp_path)
        elif kind == "pptx":
            uploaded_text, parse_notes = parse_pptx(tmp_path)

    with st.expander("Upload status", expanded=True):
        st.success("Parsed successfully" if "Parsed successfully" in parse_notes else "Parsed with notes")
        st.write(parse_notes)
        if uploaded_text.strip():
            if st.button("Insert extracted text"):
                st.session_state.source_text = (source_area + "\n\n" + uploaded_text).strip() if source_area else uploaded_text
                st.experimental_rerun()

# Update stored source
st.session_state.source_text = source_area if not use_sample else ("Bearings reduce friction and support rotating elements. Actuators convert control signals into motion. Maintenance strategies include repair, reconditioning, and renovation. Documentation ensures traceability and safety compliance for life-extension programmes.")

# Verb pills (visual only)
def render_bloom_row(level: str, verbs: List[str], active: bool):
    cls = {"Low":"low", "Medium":"med", "High":"high"}[level]
    st.markdown(f"<div class='bloom-row {cls}'>", unsafe_allow_html=True)
    st.caption(f"**{level}** (Weeks { '1–4' if level=='Low' else ('5–9' if level=='Medium' else '10–14') }): " + \
               ("Remember / Understand" if level=="Low" else ("Apply / Analyse" if level=="Medium" else "Evaluate / Create")))
    # verbs
    row = ""
    for v in verbs:
        pill_cls = "verb-pill active" if active else "verb-pill"
        row += f"<span class='{pill_cls}'>{v}</span>"
    st.markdown(row, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

render_bloom_row("Low",    ["define","identify","list","recall","describe","label"], bloom_focus=="Low")
render_bloom_row("Medium", ["apply","demonstrate","solve","illustrate","classify","compare"], bloom_focus=="Medium")
render_bloom_row("High",   ["evaluate","synthesize","design","justify","critique","create"], bloom_focus=="High")

# ──────────────────────────────────────────────────────────────────────────────
# Variant seed (different instructors get different outputs)
# ──────────────────────────────────────────────────────────────────────────────
seed_base = f"{st.session_state.get('topic','')}|L{st.session_state.lesson}|W{st.session_state.week}|{variant_tag}|{time.strftime('%Y-%m-%d')}"
seed = hash_seed(seed_base)
rng = random.Random(seed)

# ──────────────────────────────────────────────────────────────────────────────
# Tab 1: MCQs
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("#### ")
    if st.button("✨ Generate MCQs", type="primary"):
        mcqs = build_mcqs(st.session_state.get("source_text",""), st.session_state.mcq_count,
                          bloom_focus, rng=rng, course=st.session_state.course)
        st.session_state.mcqs = mcqs

    for i, q in enumerate(st.session_state.get("mcqs", []), 1):
        with st.expander(f"{i}. {q.stem}"):
            for j, opt in enumerate(q.options):
                st.write(f"{chr(65+j)}. {opt}")
            st.write(f"**Answer:** {chr(65+q.answer)}")

    if st.session_state.get("mcqs"):
        doc = mcqs_docx(st.session_state.mcqs)
        st.download_button("⬇️ Download MCQs (.docx)", data=doc,
                           file_name="adi_mcqs.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        rev_lines = build_revision_plan(bloom_focus, st.session_state.get("topic",""))
        bundle = bundle_docx(st.session_state.mcqs, st.session_state.get("acts", []), rev_lines, st.session_state.get("topic",""))
        st.download_button("⬇️ Download Lesson Pack (.docx)", data=bundle,
                           file_name="adi_lesson_pack.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ──────────────────────────────────────────────────────────────────────────────
# Tab 2: Activities
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    if st.button("🛠️ Generate activities"):
        acts = build_activities(st.session_state.get("topic",""), bloom_focus,
                                st.session_state.act_count, st.session_state.act_minutes,
                                rng=rng, course=st.session_state.course)
        st.session_state.acts = acts

    for i, a in enumerate(st.session_state.get("acts", []), 1):
        with st.expander(f"{i}. {a['title']} — {a['minutes']} mins"):
            st.write("**Objective:**", a["objective"])
            st.write("**Steps:**")
            for s in a["steps"]:
                st.write(f"- {s}")
            if a["materials"]:
                st.write("**Materials:**", ", ".join(a["materials"]))
            st.write("**Check:**", a["assessment"])

    if st.session_state.get("acts"):
        doc = activities_docx(st.session_state.acts)
        st.download_button("⬇️ Download Activities (.docx)", data=doc,
                           file_name="adi_activities.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        # also offer revision & bundle here
        rev_lines = build_revision_plan(bloom_focus, st.session_state.get("topic",""))
        rev_doc = revision_docx(rev_lines)
        st.download_button("⬇️ Download Revision Plan (.docx)", data=rev_doc,
                           file_name="adi_revision_plan.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        bundle = bundle_docx(st.session_state.get("mcqs", []), st.session_state.acts, rev_lines, st.session_state.get("topic",""))
        st.download_button("⬇️ Download Lesson Pack (.docx)", data=bundle,
                           file_name="adi_lesson_pack.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ──────────────────────────────────────────────────────────────────────────────
# Tab 3: Revision
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    rev_lines = build_revision_plan(bloom_focus, st.session_state.get("topic",""))
    st.write("### 1-Week Revision Plan")
    for line in rev_lines:
        if line.startswith("## "):
            st.subheader(line.replace("## ",""))
        elif line.startswith("• "):
            st.write(line)
        else:
            st.write(line)

    rev_doc = revision_docx(rev_lines)
    st.download_button("⬇️ Download Revision Plan (.docx)", data=rev_doc,
                       file_name="adi_revision_plan.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
