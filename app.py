#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADI Builder — Lesson Activities & Questions (API-free)
Look & feel: green banding + active verb pills (unchanged).
Improvements:
- Bounded parsing with progress (PDF: pypdf + PyMuPDF plain+blocks), Deep scan toggle
- No re-parse on Week change (session-keyed)
- Stronger MCQ generator: cleaner distractors, relaxed sentence rules, top-up to N
- .docx downloads for MCQs & Activities
"""

from __future__ import annotations

import io
import re
import time
import random
import hashlib
from dataclasses import dataclass
from typing import List, Tuple, Optional

import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Page setup
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="✅",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# Session init
# ──────────────────────────────────────────────────────────────────────────────
def _init():
    ss = st.session_state
    ss.setdefault("last_file_sig", None)
    ss.setdefault("file_name", None)
    ss.setdefault("extracted_text", "")
    ss.setdefault("source_text", "")
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 7)
    ss.setdefault("topic", "")
    ss.setdefault("mcq_count", 10)
    ss.setdefault("act_count", 2)
    ss.setdefault("act_minutes", 10)
    ss.setdefault("use_sample", False)
    ss.setdefault("use_extracted", False)
    ss.setdefault("acts", [])

_init()

# ──────────────────────────────────────────────────────────────────────────────
# Small helpers
# ──────────────────────────────────────────────────────────────────────────────
def file_sig(name: str, data: bytes) -> str:
    h = hashlib.sha256()
    h.update(name.encode())
    h.update(data)
    return h.hexdigest()

def bloom_from_week(week: int) -> str:
    if week <= 4:
        return "Low"
    if week <= 9:
        return "Medium"
    return "High"

LOW_VERBS  = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS  = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

# ──────────────────────────────────────────────────────────────────────────────
# Extraction with budgets + progress; robust fallbacks
# ──────────────────────────────────────────────────────────────────────────────
def extract_text_from_upload(
    name: str,
    data: bytes,
    max_pages: Optional[int] = 40,
    time_budget_sec: int = 25,
    progress_cb=None,  # callable(done, total) or None
) -> Tuple[str, List[str]]:
    """
    Returns (text, notes). Stops within time_budget_sec and up to max_pages.
    Detects 'image-only' PDFs by low text density and exits early with guidance.
    """
    notes, txt = [], ""
    lower = name.lower()
    bio = io.BytesIO(data)
    t0 = time.time()

    def timed_out():
        return (time.time() - t0) > time_budget_sec

    if lower.endswith(".pdf"):
        total = None
        pages_done = 0
        # 1) pypdf — page-by-page to respect budgets
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            total = len(reader.pages)
            limit = total if max_pages is None else min(total, max_pages)
            out = []
            for i in range(limit):
                if timed_out():
                    notes.append("pypdf timeout")
                    break
                page_txt = reader.pages[i].extract_text() or ""
                out.append(page_txt)
                pages_done += 1
                if progress_cb and total:
                    progress_cb(pages_done, total)
            txt = "\n".join(out)
            notes.append(f"pypdf ({pages_done}/{total or limit} pages)")
        except Exception as e:
            notes.append(f"pypdf fail: {e!s}")

        # 2) PyMuPDF — richer extraction, still bounded
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=data, filetype="pdf")
            total = total or len(doc)
            limit = len(doc) if max_pages is None else min(len(doc), max_pages)

            plain_parts, block_parts = [], []
            pages_done2 = 0

            def page_blocks(p):
                blocks = p.get_text("blocks") or []
                blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))
                return "\n".join(b[4] for b in blocks if isinstance(b[4], str))

            for i in range(limit):
                if timed_out():
                    notes.append("PyMuPDF timeout")
                    break
                pg = doc[i]
                plain_parts.append(pg.get_text("text"))
                block_parts.append(page_blocks(pg))
                pages_done2 += 1
                if progress_cb and total:
                    progress_cb(pages_done + pages_done2, total)

            plain = "\n".join(plain_parts)
            blocks = "\n".join(block_parts)
            pick = max([txt, plain, blocks], key=lambda s: len((s or "").strip()))
            if len((pick or "").strip()) > len((txt or "").strip()):
                txt = pick
            notes.append(f"PyMuPDF ({pages_done2}/{total} pages)")
        except Exception as e:
            notes.append(f"fitz fail: {e!s}")

        # Image-only heuristic: low characters per page across several pages
        pages_scanned = (pages_done or 0) + (locals().get("pages_done2", 0) or 0)
        if pages_scanned:
            density = len((txt or "").strip()) / max(pages_scanned, 1)
            if density < 80 and pages_scanned >= 10:
                notes.append("Likely image-only PDF (no selectable text). Try DOCX/PPTX or OCR.")
                txt = txt.strip()

    elif lower.endswith(".pptx"):
        try:
            from pptx import Presentation
            prs = Presentation(bio)
            chunks = []

            def shape_text(sh):
                parts = []
                try:
                    if hasattr(sh, "has_text_frame") and sh.has_text_frame and sh.text_frame:
                        for p in sh.text_frame.paragraphs:
                            parts.append(" ".join(r.text for r in p.runs) or p.text)
                    if hasattr(sh, "table") and sh.table:
                        for row in sh.table.rows:
                            for cell in row.cells:
                                if cell.text:
                                    parts.append(cell.text)
                    if hasattr(sh, "shapes"):  # group shapes
                        for s in sh.shapes:
                            nested = shape_text(s)
                            if nested:
                                parts.append(nested)
                except Exception:
                    pass
                return "\n".join([p for p in parts if p])

            total = len(prs.slides)
            done = 0
            for slide in prs.slides:
                for s in slide.shapes:
                    t = shape_text(s)
                    if t:
                        chunks.append(t)
                done += 1
                if progress_cb and total:
                    progress_cb(done, total)
            txt = "\n".join(chunks)
            notes.append("python-pptx")
        except Exception as e:
            notes.append(f"pptx fail: {e!s}")

    elif lower.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(bio)
            txt = "\n".join(p.text for p in doc.paragraphs)
            notes.append("python-docx")
        except Exception as e:
            notes.append(f"docx fail: {e!s}")
    else:
        notes.append("Unsupported type")

    return txt or "", notes

# ──────────────────────────────────────────────────────────────────────────────
# Keyword helpers (API-free, optional libs)
# ──────────────────────────────────────────────────────────────────────────────
try:
    import nltk
    from nltk.corpus import wordnet as wn
    try:
        wn.synsets("test")
    except LookupError:
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
except Exception:
    wn = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:
    TfidfVectorizer = None

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except Exception:
    nlp = None

STOP = set("""
the a an and or for with from by to of on in at is are was were be as it its this that these those which who whom whose
""".split())

def tfidf_phrases(text: str, top_k=15) -> List[str]:
    if not TfidfVectorizer:
        return []
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text) if len(s) > 30][:200]
    docs = sents if len(sents) >= 3 else [text]
    vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=4000)
    X = vec.fit_transform(docs)
    scores = X.mean(axis=0).A1
    vocab = vec.get_feature_names_out()
    order = [vocab[i] for i in scores.argsort()[::-1]]
    out = [w for w in order if w.lower() not in STOP]
    return out[:top_k]

def spacy_chunks(text: str, top_k=20) -> List[str]:
    if not nlp:
        return []
    try:
        doc = nlp(text[:20000])
        cand = []
        for ch in doc.noun_chunks:
            t = ch.text.strip()
            if t and len(t) > 2:
                cand.append(t)
        for t in doc:
            if t.pos_ == "VERB" and t.lemma_.isalpha() and t.lemma_.lower() not in STOP:
                cand.append(t.lemma_.lower())
        seen, out = set(), []
        for c in cand:
            if c not in seen:
                seen.add(c); out.append(c)
            if len(out) >= top_k:
                break
        return out
    except Exception:
        return []

def extract_keyterms(text: str, top_k=20) -> List[str]:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return []
    keys = spacy_chunks(text, top_k) + tfidf_phrases(text, top_k)
    seen, out = set(), []
    for k in keys:
        if k not in seen and k.lower() not in STOP:
            seen.add(k); out.append(k)
        if len(out) >= top_k:
            break
    return out or ["concept", "process", "component", "system"]

def antonyms(word: str) -> List[str]:
    if not wn or not word or " " in word:
        return []
    ants = set()
    for syn in wn.synsets(word):
        for lem in syn.lemmas():
            for a in lem.antonyms():
                ants.add(a.name().replace("_", " "))
    return list(ants)[:3]

def near_miss(term: str) -> List[str]:
    out = set()
    t = term.strip()
    if len(t) > 4:
        out.update([t[:-1], t+"s", t.replace("ization","isation"), t.replace("isation","ization")])
    return list(out)[:3]

def make_distractors(term: str, pool: List[str]) -> List[str]:
    def ok(tok: str) -> bool:
        t = tok.strip()
        return t and t.isalpha() and 3 <= len(t) <= 20 and t.lower() != term.lower()
    d = set()
    for x in antonyms(term):
        if ok(x): d.add(x)
    for x in near_miss(term):
        if ok(x): d.add(x)
    for x in pool:
        if ok(x) and len(x.split()) <= 3:
            d.add(x)
        if len(d) >= 6:
            break
    return list(d)[:3]

def lint_item(stem: str, options: List[str], ans_idx: int) -> List[str]:
    issues = []
    if not stem or len(stem.split()) < 5: issues.append("Stem too short.")
    if any("all of the above" in o.lower() or "none of the above" in o.lower() for o in options):
        issues.append("Avoid 'All/None of the above'.")
    if any(len(o.split()) > 12 for o in options): issues.append("Option too long.")
    if len(set(o.lower() for o in options)) < len(options): issues.append("Duplicate options.")
    if not (0 <= ans_idx < 4): issues.append("Bad answer index.")
    return issues

# ──────────────────────────────────────────────────────────────────────────────
# MCQ generator (relaxed rules + top-up)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class MCQ:
    stem: str
    options: List[str]
    answer: int
    bloom: str

def build_mcqs(text: str, n: int, bloom_focus: str) -> List[MCQ]:
    text = (text or "").strip()
    if not text:
        return []
    keyterms = extract_keyterms(text, top_k=40)

    # Accept normal sentences or bullet-ish items
    candidates = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n-\s+|\n•\s+", text)]
    sents = [s for s in candidates if 35 <= len(s) <= 260][:600]
    random.shuffle(sents)

    mcqs: List[MCQ] = []
    used_stems = set()

    # Main cloze loop
    for s in sents:
        term = next((k for k in keyterms if re.search(rf"\b{re.escape(k)}\b", s, re.I)), None)
        if not term:
            continue
        cloze = re.sub(rf"\b{re.escape(term)}\b", "_____", s, flags=re.I, count=1).strip()
        if cloze.lower() in used_stems:
            continue
        distractors = make_distractors(term, [k for k in keyterms if k.lower()!=term.lower()])
        if len(distractors) < 3:
            continue
        opts = distractors + [term]
        random.shuffle(opts)
        ans = opts.index(term)
        issues = lint_item(cloze, opts, ans)
        if not issues:
            mcqs.append(MCQ(cloze, opts, ans, bloom_focus))
            used_stems.add(cloze.lower())
        if len(mcqs) >= n:
            return mcqs

    # Top-up: definition-style items if we’re short
    ctx = re.sub(r"\s+", " ", text)[:4000]
    defs = []
    for k in keyterms:
        m = re.search(rf"\b{k}\b\s+(is|are|means|refers to)\s+([^\.]{{10,120}})\.", ctx, re.I)
        if m:
            defs.append((k, m.group(0)))
        if len(defs) >= n:
            break

    for k, sentence in defs:
        if len(mcqs) >= n:
            break
        stem = sentence.replace(k, "_____")
        distractors = make_distractors(k, [t for t in keyterms if t.lower()!=k.lower()])
        if len(distractors) < 3:
            continue
        opts = distractors + [k]
        random.shuffle(opts)
        ans = opts.index(k)
        if not lint_item(stem, opts, ans):
            mcqs.append(MCQ(stem, opts, ans, bloom_focus))

    return mcqs[:n]

def mcqs_docx(mcqs: List[MCQ]) -> bytes:
    try:
        import docx
    except Exception:
        return b""
    doc = docx.Document()
    doc.add_heading("Knowledge MCQs", level=1)
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"{i}. {q.stem}")
        for j, opt in enumerate(q.options, 1):
            doc.add_paragraph(f"{chr(64+j)}. {opt}", style="List Bullet")
        doc.add_paragraph(f"Answer: {chr(65+q.answer)}")
        doc.add_paragraph("")
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ──────────────────────────────────────────────────────────────────────────────
# Activities generator + export
# ──────────────────────────────────────────────────────────────────────────────
TEMPLATES = {
    "Low":[
        ("Vocabulary Snap", ["Match key terms to definitions.","Peer-check.","Whole-class reveal."], ["Term cards","Timer"], "Recall via matching."),
        ("3-2-1 Recall", ["Write 3 facts, 2 terms, 1 question.","Pair-share.","Collect exemplars."], ["Paper","Pens"], "Recall & form questions.")
    ],
    "Medium":[
        ("Worked Example → Variation", ["Demo a worked example.","Pairs adapt parameters.","Swap & check."], ["Example sheet"], "Apply method to variants."),
        ("Classify & Justify", ["Groups sort examples.","One-sentence justification each.","Gallery walk."], ["Cut strips or slides"], "Classification with reasoning.")
    ],
    "High":[
        ("Mini-Case Critique", ["Read short case.","Propose a decision + justification.","Group synthesize best response."], ["Case handout"], "Evaluate options vs criteria."),
        ("Design a Quick Fix", ["Teams draft an improvement.","Note assumptions & risks.","2-min pitch."], ["A3 paper"], "Create and justify design choices.")
    ],
}

def build_activities(topic: str, focus: str, count: int, minutes: int) -> List[dict]:
    bank = TEMPLATES.get(focus, TEMPLATES["Medium"])[:]
    random.shuffle(bank)
    out = []
    for i in range(count):
        title, steps, materials, assess = bank[i % len(bank)]
        out.append({
            "title": f"{title} — {topic or 'Lesson'}",
            "minutes": minutes,
            "objective": f"{focus} focus activity for {topic or 'the topic'}.",
            "steps": steps,
            "materials": materials,
            "assessment": assess
        })
    return out

def activities_docx(acts: List[dict]) -> bytes:
    try:
        import docx
    except Exception:
        return b""
    doc = docx.Document()
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
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ──────────────────────────────────────────────────────────────────────────────
# UI — Sidebar (upload with progress + budgets; selectors)
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Upload (optional)")
    up = st.file_uploader(
        "Drag and drop file here",
        type=["pdf","pptx","docx"],
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    deep = st.checkbox(
        "Deep scan (all pages, slower)",
        value=False,
        help="If off, scans first ~40 pages for speed. Deep scan has a longer time budget.",
    )

    if up is not None:
        data = up.getvalue()
        sig = file_sig(up.name, data) + ("-deep" if deep else "-quick")

        if sig != st.session_state.last_file_sig:
            with st.status("Parsing file…", expanded=True) as status:
                prog = st.progress(0)

                def update_progress(done, total):
                    try:
                        prog.progress(min(int(done / max(total, 1) * 100), 100))
                    except Exception:
                        pass

                max_pages = None if deep else 40
                time_budget = 120 if deep else 25

                text, notes = extract_text_from_upload(
                    up.name,
                    data,
                    max_pages=max_pages,
                    time_budget_sec=time_budget,
                    progress_cb=update_progress,
                )

                st.session_state.last_file_sig = sig
                st.session_state.file_name = up.name
                st.session_state.extracted_text = text or ""
                st.session_state.use_extracted = bool((text or "").strip())

                if st.session_state.use_extracted:
                    status.update(label="Parsed successfully ✅", state="complete")
                    st.toast(f"Uploaded & parsed: {up.name}", icon="✅")
                else:
                    status.update(label="Parsed with issues ⚠️", state="error")
                    st.toast(
                        "No selectable text found (likely scanned). "
                        "Try DOCX/PPTX or export a text-based PDF.",
                        icon="⚠️",
                    )

                if notes:
                    st.caption(" • ".join(notes))

    st.markdown("---")
    st.subheader("Course context")
    st.session_state.lesson = st.selectbox("Lesson", list(range(1,15)), index=st.session_state.lesson-1)
    st.session_state.week   = st.selectbox("Week",   list(range(1,15)), index=st.session_state.week-1)
    st.session_state.topic  = st.text_input("Topic / outcome", value=st.session_state.topic, placeholder="Module description, knowledge & skills outcomes")

    st.markdown("---")
    st.subheader("Number of MCQs")
    st.session_state.mcq_count = st.selectbox("How many questions?", [5,10,15,20,30], index=[5,10,15,20,30].index(st.session_state.mcq_count))
    st.caption("Typical handout: 10–15")

    st.markdown("---")
    st.subheader("Activities")
    st.session_state.act_count   = st.selectbox("How many?",        [1,2,3,4], index=[1,2,3,4].index(st.session_state.act_count))
    st.session_state.act_minutes = st.selectbox("Time each (mins)", [5,10,15,20,30], index=[5,10,15,20,30].index(st.session_state.act_minutes))

# ──────────────────────────────────────────────────────────────────────────────
# Header banner (unchanged styling)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#244e34;color:#fff;border-radius:14px;padding:16px 20px;margin-top:6px;margin-bottom:8px;">
  <div style="font-weight:700;font-size:18px;">ADI Builder — Lesson Activities & Questions</div>
  <div style="opacity:.85;font-size:12px;">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["Knowledge MCQs", "Skills Activities"])

# ── MCQs tab ──────────────────────────────────────────────────────────────────
with tabs[0]:
    focus = bloom_from_week(st.session_state.week)
    st.markdown(
        f"<div style='text-align:right'><span style='background:#e7dbc0;border-radius:20px;padding:6px 10px;font-size:12px;'>Week {st.session_state.week}: <b>{focus}</b></span></div>",
        unsafe_allow_html=True,
    )

    st.checkbox("Use sample text (quick test)", value=st.session_state.use_sample, key="use_sample")

    # insert parsed text helper
    if st.session_state.extracted_text:
        colA, colB = st.columns([1,2])
        with colA:
            st.caption(f"Extracted from upload: ~{len(st.session_state.extracted_text):,} chars")
        with colB:
            if st.button("Insert extracted text"):
                st.session_state.source_text = st.session_state.extracted_text[:15000]

    # seed source text if requested
    if st.session_state.use_extracted and not st.session_state.source_text:
        st.session_state.source_text = st.session_state.extracted_text[:15000]
    if st.session_state.use_sample and not st.session_state.source_text:
        st.session_state.source_text = (
            "Cells are the basic structural and functional units of life. "
            "Prokaryotic cells lack a nucleus, while eukaryotic cells have membrane-bound organelles. "
            "Mitochondria generate ATP through cellular respiration. DNA stores genetic information."
        )

    st.text_area("Source text (editable)", key="source_text", height=240, placeholder="Paste or jot key notes, vocab, facts here…")

    # Styles: green rows + active verb pills (unchanged)
    row_bg = {"Low":"#e7f2ea", "Medium":"#ecf4e7", "High":"#eef3e8"}[focus]
    st.markdown(f"""
    <style>
      .row {{ background:{row_bg}; border:1px solid #e2e7df; border-radius:12px; padding:10px 12px; margin:10px 0; }}
      .title {{ font-weight:700; margin:6px 0 2px; color:#2d4737; }}
      .chip {{ display:inline-block; padding:10px 22px; margin:8px 10px 4px 0; border-radius:999px;
               background:#f6f6f4; border:1px solid #e2e7df; color:#2a2a2a; }}
      .chip.active {{ background:#2d6a4f; color:#ffffff; border-color:#2d6a4f; }}
    </style>
    """, unsafe_allow_html=True)

    active_set = {"Low": set(LOW_VERBS), "Medium": set(MED_VERBS), "High": set(HIGH_VERBS)}[focus]

    def verb_row(title, verbs, highlight=False):
        st.markdown(f"<div class='row'><div class='title'>{title}</div>", unsafe_allow_html=True)
        cols = st.columns(6)
        for i, v in enumerate(verbs):
            klass = "chip active" if (highlight and v in active_set) else "chip"
            with cols[i % 6]:
                st.markdown(f"<div class='{klass}'>{v}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    verb_row("LOW (Weeks 1–4): Remember / Understand", LOW_VERBS, highlight=(focus=="Low"))
    verb_row("MEDIUM (Weeks 5–9): Apply / Analyse",    MED_VERBS, highlight=(focus=="Medium"))
    verb_row("HIGH (Weeks 10–14): Evaluate / Create",  HIGH_VERBS, highlight=(focus=="High"))

    can_go = bool((st.session_state.source_text or "").strip())
    c1, _ = st.columns(2)
    gen = c1.button("✨ Generate MCQs", disabled=not can_go, type="primary")

    if gen:
        with st.spinner("Building questions…"):
            mcqs = build_mcqs(st.session_state.source_text, st.session_state.mcq_count, focus)
        if not mcqs:
            st.warning("No suitable sentences found. Paste clearer paragraphs or upload DOCX/PPTX.", icon="⚠️")
        else:
            st.success(f"Generated {len(mcqs)} MCQs.")
            for i, q in enumerate(mcqs, 1):
                st.markdown(f"**{i}. {q.stem}**")
                for j, opt in enumerate(q.options, 1):
                    st.markdown(f"- {chr(64+j)}. {opt}")
                st.caption(f"Answer: {chr(65+q.answer)} • Bloom: {q.bloom}")
                st.markdown("---")
            doc = mcqs_docx(mcqs)
            if doc:
                st.download_button(
                    "⬇️ Download MCQs (.docx)",
                    data=doc,
                    file_name="adi_mcqs.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

# ── Activities tab ────────────────────────────────────────────────────────────
with tabs[1]:
    focus = bloom_from_week(st.session_state.week)
    st.markdown(f"**Bloom focus:** {focus}")
    if st.button("🧩 Generate activities"):
        st.session_state.acts = build_activities(
            st.session_state.topic, focus, st.session_state.act_count, st.session_state.act_minutes
        )
    acts = st.session_state.get("acts", [])
    if acts:
        for a in acts:
            st.subheader(f"{a['title']} — {a['minutes']} mins")
            st.write(a["objective"])
            st.write("**Steps**")
            for s in a["steps"]:
                st.write(f"- {s}")
            st.write("**Materials:** " + ", ".join(a["materials"]))
            st.write("**Check:** " + a["assessment"])
            st.markdown("---")
        doc = activities_docx(acts)
        if doc:
            st.download_button(
                "⬇️ Download Activities (.docx)",
                data=doc,
                file_name="adi_activities.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
