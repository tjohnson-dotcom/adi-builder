# app.py — ADI Builder (Lesson Activities & Questions)
# Streamlit single-file app; API-free generators; stable pill UI

import os
import io
import re
import json
import zipfile
from datetime import datetime
from collections import defaultdict

import streamlit as st

# --- Optional parsers (graceful if missing) ---
try:
    import fitz  # PyMuPDF (fast & robust)
except Exception:
    fitz = None

try:
    from pypdf import PdfReader  # fallback
except Exception:
    PdfReader = None

try:
    from pptx import Presentation
except Exception:
    Presentation = None

try:
    import docx  # python-docx
except Exception:
    docx = None

# --- NLP / classic ML (API-free) ---
try:
    import nltk
    from nltk.corpus import wordnet as wn
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
except Exception:
    nltk = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:
    TfidfVectorizer = None


# ==========================
# Theme / constants
# ==========================
ADI_GREEN = "#245a34"
ADI_GREEN_SOFT = "#e9f2ec"
ADI_GOLD = "#d2bf85"
BORDER = "#eaeaea"
TEXT_MUTED = "#6c6c6c"

VERBS = {
    "LOW":  ["define", "identify", "list", "recall", "describe", "label"],
    "MED":  ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"],
    "HIGH": ["evaluate", "synthesize", "design", "justify", "critique", "create"],
}

WEEK_FOCUS = {
    "LOW":  list(range(1, 5)),
    "MED":  list(range(5, 10)),
    "HIGH": list(range(10, 15)),
}

# ==========================
# Helpers
# ==========================
def _safe_init_nltk():
    """Initialize NLTK data if available; avoid crashing on hosted FS."""
    if not nltk:
        return
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        try:
            nltk.download("punkt", quiet=True)
        except Exception:
            pass
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except Exception:
        # new punkt tables in recent nltk
        try:
            nltk.download("punkt_tab", quiet=True)
        except Exception:
            pass
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        try:
            nltk.download("stopwords", quiet=True)
        except Exception:
            pass
    try:
        nltk.data.find("corpora/wordnet")
    except LookupError:
        try:
            nltk.download("wordnet", quiet=True)
        except Exception:
            pass

def _rerun():
    try:
        st.rerun()
    except Exception:
        pass

def week_to_focus(week:int)->str:
    if week in WEEK_FOCUS["LOW"]:
        return "LOW"
    if week in WEEK_FOCUS["MED"]:
        return "MED"
    return "HIGH"

def clean_text(t: str) -> str:
    t = re.sub(r"\s+", " ", t)
    return t.strip()

# ==========================
# Text Extraction
# ==========================
def extract_text_from_pdf(file_bytes: bytes, deep: bool = False) -> str:
    # Prefer PyMuPDF
    if fitz:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages = range(len(doc)) if deep else range(min(8, len(doc)))
            chunks = []
            for i in pages:
                try:
                    chunks.append(doc[i].get_text("text"))
                except Exception:
                    pass
            doc.close()
            return clean_text(" ".join(chunks))
        except Exception:
            pass
    # Fallback pypdf
    if PdfReader:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages = range(len(reader.pages)) if deep else range(min(8, len(reader.pages)))
            chunks = []
            for i in pages:
                try:
                    chunks.append(reader.pages[i].extract_text() or "")
                except Exception:
                    pass
            return clean_text(" ".join(chunks))
        except Exception:
            pass
    return ""

def extract_text_from_pptx(file_bytes: bytes) -> str:
    if not Presentation:
        return ""
    try:
        prs = Presentation(io.BytesIO(file_bytes))
        texts = []
        for slide in prs.slides:
            for shp in slide.shapes:
                if hasattr(shp, "text") and shp.text:
                    texts.append(shp.text)
                if shp.shape_type == 1 and hasattr(shp, "table"):  # table
                    tbl = shp.table
                    for r in tbl.rows:
                        for c in r.cells:
                            if c.text:
                                texts.append(c.text)
        return clean_text(" ".join(texts))
    except Exception:
        return ""

def extract_text_from_docx(file_bytes: bytes) -> str:
    if not docx:
        return ""
    try:
        document = docx.Document(io.BytesIO(file_bytes))
        texts = []
        for p in document.paragraphs:
            texts.append(p.text)
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    texts.append(cell.text)
        return clean_text(" ".join(texts))
    except Exception:
        return ""

def extract_text(uploaded_file, deep_scan: bool) -> str:
    bytes_data = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(bytes_data, deep=deep_scan)
    if name.endswith(".pptx") or name.endswith(".ppt"):
        return extract_text_from_pptx(bytes_data)
    if name.endswith(".docx"):
        return extract_text_from_docx(bytes_data)
    return ""

# ==========================
# Generation (API-free)
# ==========================
def key_phrases_tfidf(text: str, topk: int = 25) -> list:
    if not text or not TfidfVectorizer:
        return []
    sents = re.split(r"(?<=[.!?])\s+", text)
    sents = [s for s in sents if len(s.split()) >= 5]
    if len(sents) == 0:
        sents = [text]

    vec = TfidfVectorizer(ngram_range=(1, 3), max_features=3000, stop_words="english")
    try:
        X = vec.fit_transform(sents)
    except Exception:
        return []
    vocab = vec.get_feature_names_out()
    scores = X.sum(axis=0).A1
    pairs = list(zip(vocab, scores))
    pairs.sort(key=lambda x: x[1], reverse=True)
    phrases = [p for p, _ in pairs[:topk]]
    # keep meaningful ones
    phrases = [p for p in phrases if len(p.split()) <= 5 and len(p) > 2]
    return phrases

def sentence_pool(text: str) -> list:
    if not nltk:
        return [text]
    try:
        sents = sent_tokenize(text)
    except Exception:
        sents = re.split(r"(?<=[.!?])\s+", text)
    sents = [clean_text(s) for s in sents if len(s.split()) >= 6]
    return sents[:800]

def make_distractors(term: str, all_phrases: list, k: int = 3) -> list:
    cands = []
    # wordnet synonyms/related (soft)
    if nltk and wn:
        for syn in wn.synsets(term):
            for l in syn.lemmas():
                w = l.name().replace("_", " ")
                if w.lower() != term.lower() and w.isalpha():
                    cands.append(w)
    # fallback: near phrases
    for p in all_phrases:
        if p.lower() != term.lower() and len(p.split()) <= 3:
            cands.append(p)
    # simple uniqueness
    uniq = []
    for x in cands:
        if x.lower() not in [u.lower() for u in uniq] and x.lower() != term.lower():
            uniq.append(x)
        if len(uniq) >= 12:
            break
    return uniq[:k] if len(uniq) >= k else uniq

def generate_mcqs(text: str, verbs: list, n_q: int = 10) -> list:
    """
    Super-light MCQ generator: pick key phrases, find host sentences,
    mask the phrase, build distractors.
    """
    if not text:
        return []
    phrases = key_phrases_tfidf(text, topk=80)
    sents = sentence_pool(text)
    out = []
    used = set()
    i = 0
    for ph in phrases:
        if len(out) >= n_q:
            break
        # find a sentence containing the phrase
        host = None
        for s in sents:
            if ph.lower() in s.lower():
                host = s
                break
        if not host:
            continue
        # Avoid repeats
        if host in used:
            continue
        used.add(host)

        # cloze
        blank = re.sub(re.escape(ph), "_____", host, flags=re.I)
        opts = make_distractors(ph, phrases, k=3)
        if len(opts) < 3:
            continue
        choices = opts + [ph]
        # shuffle deterministically
        order = [3, 0, 2, 1] if i % 2 == 0 else [1, 3, 0, 2]
        choices = [choices[j % len(choices)] for j in order]
        answer = ph

        verb = verbs[i % len(verbs)] if verbs else None
        stem = f"({verb}) {blank}" if verb else blank

        out.append({
            "stem": stem,
            "choices": choices,
            "answer": answer
        })
        i += 1
    return out[:n_q]

def generate_activities(text: str, verbs: list, mins: int = 20, n: int = 3) -> list:
    """Template activities seeded by verbs & key terms."""
    phrases = key_phrases_tfidf(text, topk=30) or ["key concept"]
    templates = [
        "In pairs, ({verb}) and present a 5-slide summary on: **{key}**.",
        "Small groups: ({verb}) a worked example applying **{key}**. Include assumptions and checks.",
        "Individually: ({verb}) a short troubleshooting guide for **{key}** with 3 common pitfalls.",
        "Lab corner: ({verb}) and record results for **{key}**; compare with spec/standard.",
        "Whiteboard: ({verb}) a flow/logic map that explains **{key}** end-to-end.",
    ]
    acts = []
    for i in range(min(n, len(templates))):
        verb = verbs[i % len(verbs)] if verbs else "demonstrate"
        key = phrases[(i * 3) % len(phrases)]
        acts.append({
            "title": f"{verb.title()} — {key}",
            "time": mins,
            "detail": templates[i].format(verb=verb, key=key)
        })
    return acts

def generate_revision(text: str, week: int, n: int = 5) -> list:
    """Short-answer prompts from top key phrases."""
    phrases = key_phrases_tfidf(text, topk=20) or []
    prompts = []
    stems = [
        "Explain the purpose of **{k}** in this week’s context.",
        "List the critical parameters that affect **{k}** and justify each briefly.",
        "Give a worked example involving **{k}** and show your checks.",
        "Compare **{k}** versus an alternative; when is each preferred?",
        "Describe a failure or defect related to **{k}** and how to detect it.",
    ]
    for i in range(n):
        if not phrases:
            break
        k = phrases[(i*2) % len(phrases)]
        prompts.append(stems[i % len(stems)].format(k=k))
    return prompts

# ==========================
# Exporters (DOCX / GIFT / Moodle XML)
# ==========================
def export_docx(mcqs, activities, revision) -> bytes:
    if not docx:
        return b""
    d = docx.Document()
    d.add_heading("ADI — Lesson Activities & Questions", level=1)
    d.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    d.add_heading("MCQs", level=2)
    for i, q in enumerate(mcqs, 1):
        d.add_paragraph(f"{i}. {q['stem']}")
        letters = "abcd"
        for j, c in enumerate(q["choices"]):
            d.add_paragraph(f"   {letters[j].upper()}) {c}")
        d.add_paragraph(f"   Answer: {q['answer']}")
    d.add_heading("Activities", level=2)
    for a in activities:
        d.add_paragraph(f"• {a['title']}  —  {a['time']} mins")
        d.add_paragraph(f"  {a['detail']}")
    d.add_heading("Revision", level=2)
    for r in revision:
        d.add_paragraph(f"• {r}")
    bio = io.BytesIO()
    d.save(bio)
    return bio.getvalue()

def export_gift(mcqs) -> bytes:
    lines = []
    for q in mcqs:
        stem = q["stem"].replace("\n", " ")
        correct = q["answer"]
        opts = q["choices"]
        # GIFT format
        lines.append(f"::Q:: {stem} {{")
        for o in opts:
            if o.strip().lower() == correct.strip().lower():
                lines.append(f"={o}")
            else:
                lines.append(f"~{o}")
        lines.append("}")
    return "\n".join(lines).encode("utf-8")

def export_moodle_xml(mcqs) -> bytes:
    # Minimal Moodle XML (multichoice)
    from xml.sax.saxutils import escape
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']
    for i, q in enumerate(mcqs, 1):
        parts.append("<question type='multichoice'>")
        parts.append(f"<name><text>Q{i}</text></name>")
        parts.append(f"<questiontext format='html'><text><![CDATA[{escape(q['stem'])}]]></text></questiontext>")
        parts.append("<shuffleanswers>true</shuffleanswers>")
        parts.append("<single>true</single>")
        correct = q["answer"].strip().lower()
        for opt in q["choices"]:
            is_right = (opt.strip().lower() == correct)
            frac = "100" if is_right else "0"
            parts.append(f"<answer fraction='{frac}' format='html'><text><![CDATA[{escape(opt)}]]></text></answer>")
        parts.append("</question>")
    parts.append("</quiz>")
    return "\n".join(parts).encode("utf-8")

# ==========================
# UI — CSS
# ==========================
CUSTOM_CSS = f"""
<style>
/* Page polish */
.block-container {{ padding-top: 1.0rem; }}
header, footer {{ display:none; }}
/* ADI brand header */
.adi-banner {{
  background:{ADI_GREEN}; color:#fff; padding:16px 18px; border-radius:10px;
  font-weight:700; letter-spacing:.2px; box-shadow: 0 1px 0 rgba(0,0,0,.04) inset;
}}
.adi-sub {{ font-size:.85rem; opacity:.88; font-weight:500; }}

/* Tabs ribbon */
div[data-baseweb="tab-highlight"] > div {{
  border-bottom: 1px solid {BORDER};
}}

/* Input background */
textarea, .stTextInput input {{
  background:#f4f4f2 !important; border:1px solid {BORDER} !important;
}}

/* Shaded bands */
.band {{
  background:#f7f8f7; border:1px solid {BORDER}; border-radius:10px; padding:14px 14px 6px 14px; margin-top:12px;
}}
.band.low   {{ background:#fafbf9; }}
.band.med   {{ background:#f6fbf7; }}
.band.high  {{ background:#f8fafc; }}
.band-title {{ color:{TEXT_MUTED}; font-weight:700; margin-bottom:8px; }}

/* Focus outline for current week band */
.band.focus {{ outline:3px solid {ADI_GREEN}; outline-offset:2px; }}

/* Pill buttons (version-proof) */
.pill-wrap{{ display:flex; flex-wrap:wrap; gap:10px; margin:8px 0 2px 0; }}
.pill {{
  display:inline-block; border:1px solid #e8e8e8; background:#f8f8f7; color:#333;
  padding:10px 18px; border-radius:999px; font-weight:600; cursor:pointer;
  transition:all .12s; user-select:none;
}}
.pill:hover{{ background:#efefee; }}
.pill.selected{{ background:{ADI_GREEN}; color:#fff; border-color:{ADI_GREEN}; }}

/* Callouts */
.hint {{ background:#fff9e6; border:1px solid #ffe8a3; color:#6f5a00; padding:10px 12px; border-radius:8px; }}
.success {{ background:{ADI_GREEN_SOFT}; border:1px solid {ADI_GREEN}; color:#12391f; padding:10px 12px; border-radius:8px; }}
</style>
"""

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🧪", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
_safe_init_nltk()

# ==========================
# Session defaults
# ==========================
if "selected_verbs" not in st.session_state:
    st.session_state.selected_verbs = {"LOW": [], "MED": [], "HIGH": []}
if "parsed_text" not in st.session_state:
    st.session_state.parsed_text = ""
if "upload_name" not in st.session_state:
    st.session_state.upload_name = ""
if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "acts" not in st.session_state:
    st.session_state.acts = []
if "rev" not in st.session_state:
    st.session_state.rev = []
if "deep_scan" not in st.session_state:
    st.session_state.deep_scan = True

# ==========================
# Header
# ==========================
st.markdown(
    f"""
<div class="adi-banner">
  ADI Builder — <span>Lesson Activities & Questions</span><br/>
  <span class="adi-sub">Sleek, professional and engaging. Print-ready handouts for your instructors.</span>
</div>
""",
    unsafe_allow_html=True,
)

tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

# ==========================
# Sidebar — upload & context
# ==========================
with st.sidebar:
    st.markdown("### Upload (optional)")
    st.checkbox("Deep scan (all pages, slower)", value=st.session_state.deep_scan, key="deep_scan",
                help="If off, we scan the first few pages (faster).")
    up = st.file_uploader("Drag and drop file here", type=["pdf", "pptx", "docx"], label_visibility="collapsed")
    parsed_ok = False
    if up is not None:
        with st.spinner("Parsing file…"):
            text = extract_text(up, deep_scan=st.session_state.deep_scan)
        st.session_state.parsed_text = text
        st.session_state.upload_name = up.name
        if text:
            st.markdown(f"<div class='success'>Parsed successfully <b>{up.name}</b></div>", unsafe_allow_html=True)
            parsed_ok = True
        else:
            st.info("We uploaded your file but found little or no extractable text. "
                    "Try a text-based PDF/DOCX/PPTX, or paste key notes into the box.")

    st.markdown("### Course context")
    colA, = st.columns(1)
    lesson = colA.selectbox("Lesson", list(range(1, 15)), index=0)
    week = st.selectbox("Week", list(range(1, 15)), index=0)
    topic = st.text_input("Topic / outcome", placeholder="Module description, knowledge & skills outcomes")
    n_mcq = st.selectbox("How many questions?", [5, 10, 15, 20, 30], index=1)

    st.markdown("---")
    st.markdown("### Download")
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        if st.session_state.mcqs or st.session_state.acts or st.session_state.rev:
            docx_bytes = export_docx(st.session_state.mcqs, st.session_state.acts, st.session_state.rev)
            st.download_button("📄 Word (DOCX)", data=docx_bytes, file_name="adi_pack.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.button("📄 Word (DOCX)", disabled=True)
    with col_d2:
        if st.session_state.mcqs:
            gift_bytes = export_gift(st.session_state.mcqs)
            st.download_button("🧩 GIFT", data=gift_bytes, file_name="adi_mcqs.gift", mime="text/plain")
        else:
            st.button("🧩 GIFT", disabled=True)
    with col_d3:
        if st.session_state.mcqs:
            xml_bytes = export_moodle_xml(st.session_state.mcqs)
            st.download_button("📦 Moodle XML", data=xml_bytes, file_name="adi_mcqs.xml", mime="application/xml")
        else:
            st.button("📦 Moodle XML", disabled=True)
    with col_d4:
        pack_json = json.dumps({
            "lesson": lesson, "week": week, "topic": topic,
            "mcqs": st.session_state.mcqs,
            "activities": st.session_state.acts,
            "revision": st.session_state.rev
        }, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button("🧰 Course Pack (JSON)", data=pack_json, file_name="adi_course_pack.json", mime="application/json")

# ==========================
# Main switchboard
# ==========================
def band(title: str, level: str, focus: str):
    cls = {"LOW": "low", "MED": "med", "HIGH": "high"}[level]
    focus_cls = " focus" if level == focus else ""
    st.markdown(f'<div class="band {cls}{focus_cls}"><div class="band-title">{title}</div>', unsafe_allow_html=True)

def endband():
    st.markdown("</div>", unsafe_allow_html=True)

def _toggle_key(level, verb):
    return f"sel_{level}_{verb}"

def verb_pill(level, verb):
    k = _toggle_key(level, verb)
    if k not in st.session_state:
        st.session_state[k] = (verb in st.session_state.selected_verbs[level])

    # render a tiny form so clicking the pill posts back reliably
    with st.form(key=k, border=False):
        selected = st.session_state[k]
        cls = "pill selected" if selected else "pill"
        st.markdown(f'<div class="{cls}">{verb.title()}</div>', unsafe_allow_html=True)
        if st.form_submit_button(" ", use_container_width=False):
            st.session_state[k] = not selected
            if st.session_state[k] and verb not in st.session_state.selected_verbs[level]:
                st.session_state.selected_verbs[level].append(verb)
            if (not st.session_state[k]) and verb in st.session_state.selected_verbs[level]:
                st.session_state.selected_verbs[level].remove(verb)

def render_verb_band(level: str, focus: str):
    title = {
        "LOW":"LOW (Weeks 1–4): Remember / Understand",
        "MED":"MEDIUM (Weeks 5–9): Apply / Analyse",
        "HIGH":"HIGH (Weeks 10–14): Evaluate / Create"
    }[level]
    band(title, level, focus)
    st.markdown('<div class="pill-wrap">', unsafe_allow_html=True)
    for v in VERBS[level]:
        verb_pill(level, v)
    st.markdown('</div>', unsafe_allow_html=True)
    endband()

focus = week_to_focus(week)

with tabs[0]:
    st.caption("Bloom focus (auto)")
    st.markdown(f"<span class='hint'>Week {week}: <b>{'Low' if focus=='LOW' else 'Medium' if focus=='MED' else 'High'}</b></span>", unsafe_allow_html=True)
    st.write("")
    src = st.text_area("Source text (editable)", value=st.session_state.parsed_text, height=160,
                       placeholder="Paste or jot key notes, vocab, facts here…")

    # Bands
    render_verb_band("LOW", focus)
    render_verb_band("MED", focus)
    render_verb_band("HIGH", focus)

    # Controls
    cols = st.columns([1,1,1,1])
    with cols[0]:
        gen_btn = st.button("✨ Generate MCQs", type="primary", use_container_width=True)
    with cols[1]:
        regen_btn = st.button("↻ Regenerate", use_container_width=True)

    if gen_btn or regen_btn:
        picked = (st.session_state.selected_verbs["LOW"] +
                  st.session_state.selected_verbs["MED"] +
                  st.session_state.selected_verbs["HIGH"])
        if not src.strip():
            st.warning("Please add source text (or upload and parse) to generate MCQs.")
        else:
            st.session_state.mcqs = generate_mcqs(src, picked, n_q=int(n_mcq))

    # Preview
    st.markdown("#### Preview — MCQs")
    if not st.session_state.mcqs:
        st.info("No questions yet. Click **Generate MCQs** to create a set.")
    else:
        for i, q in enumerate(st.session_state.mcqs, 1):
            st.markdown(f"**{i}. {q['stem']}**")
            cols = st.columns(4)
            letters = ["A", "B", "C", "D"]
            for j, c in enumerate(q["choices"]):
                cols[j].write(f"{letters[j]}) {c}")
            st.markdown(f"<span style='color:{TEXT_MUTED}'>Answer: <b>{q['answer']}</b></span>", unsafe_allow_html=True)
            st.divider()

with tabs[1]:
    st.markdown("### Skills Activities")
    colA, colB = st.columns([1,1])
    with colA:
        minutes = st.selectbox("Activity time (mins)", [10, 15, 20, 30, 45, 60], index=2)
    with colB:
        n_acts = st.selectbox("How many activities?", [2,3,4,5], index=1)

    do_acts = st.button("🛠️ Propose activities", type="primary")
    if do_acts:
        src_text = st.session_state.parsed_text or src
        picked = (st.session_state.selected_verbs["LOW"] +
                  st.session_state.selected_verbs["MED"] +
                  st.session_state.selected_verbs["HIGH"]) or ["apply","demonstrate","evaluate"]
        st.session_state.acts = generate_activities(src_text, picked, mins=int(minutes), n=int(n_acts))

    if not st.session_state.acts:
        st.info("Click **Propose activities** to populate this section.")
    else:
        for a in st.session_state.acts:
            st.markdown(f"**{a['title']}** — {a['time']} mins")
            st.write(a["detail"])
            st.divider()

with tabs[2]:
    st.markdown("### Revision")
    n_rev = st.selectbox("How many prompts?", [3,4,5,6,8], index=2)
    do_rev = st.button("🧠 Build revision prompts", type="primary")
    if do_rev:
        src_text = st.session_state.parsed_text or src
        st.session_state.rev = generate_revision(src_text, week, n=int(n_rev))

    if not st.session_state.rev:
        st.info("Click **Build revision prompts** to populate this section.")
    else:
        for r in st.session_state.rev:
            st.markdown(f"• {r}")
