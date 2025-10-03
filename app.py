
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADI Builder — Lesson Activities & Questions (compact, stable, green theme)
- File upload with robust text extraction (PDF, DOCX, PPTX) + OCR fallback when available
- Debounced parsing (no flicker) with st.session_state
- "Use extracted text" toggle to fill the editable textarea
- Bloom focus auto (by week) + row highlighting (LOW/MEDIUM/HIGH)
- Compact pickers (lesson, week, #MCQs, activities 1–4, activity time 5/10/15/20/30)
- MCQ generator: lightweight rule-based fallback
"""
import io
import os
import re
import base64
from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st

# -------------------------
# Page & global config
# -------------------------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="🧪",
    layout="wide",
)

# Guarded init for session state
def _init_state():
    ss = st.session_state
    ss.setdefault("file_bytes", None)
    ss.setdefault("file_name", None)
    ss.setdefault("extracted_text", "")
    ss.setdefault("loaded_once", False)      # used to prevent flicker on first render
    ss.setdefault("use_extracted", False)
    ss.setdefault("topic", "")
    ss.setdefault("mcq_count", 10)
    ss.setdefault("activities_count", 1)
    ss.setdefault("activity_minutes", 10)
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 7)
    ss.setdefault("bloom_focus", "Medium")   # auto by week
    ss.setdefault("last_hash", None)

_init_state()

# -------------------------
# Utilities
# -------------------------

def _safe_import(name: str):
    try:
        return __import__(name)
    except Exception:
        return None

def human_join(items: List[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" and {items[-1]}"

def file_hash(name: str, data: bytes) -> str:
    import hashlib
    h = hashlib.sha256()
    h.update(name.encode("utf-8"))
    h.update(data)
    return h.hexdigest()

# -------------------------
# Text extraction
# -------------------------
def extract_text(file: io.BytesIO, file_name: str) -> Tuple[str, List[str]]:
    """
    Returns (text, notes). 'notes' includes what parser/ocr was used.
    """
    raw = file.read()
    notes = []
    text = ""

    # Try type by extension
    lower = file_name.lower()
    if lower.endswith(".pdf"):
        # 1) Try PyPDF2 / pypdf text extraction
        try:
            from pypdf import PdfReader  # pypdf>=3
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join([p.extract_text() or "" for p in reader.pages])
            notes.append("Used pypdf text extraction")
        except Exception as e:
            notes.append(f"pypdf failed: {e!s}")
        # 2) Try PyMuPDF if poor text
        if len(text.strip()) < 100:
            fitz = _safe_import("fitz")
            if fitz:
                try:
                    doc = fitz.open(stream=raw, filetype="pdf")
                    text_blocks = []
                    for page in doc:
                        text_blocks.append(page.get_text("text"))
                    maybe = "\n".join(text_blocks)
                    if len(maybe.strip()) > len(text.strip()):
                        text = maybe
                        notes.append("Used PyMuPDF (fitz) extraction")
                except Exception as e:
                    notes.append(f"fitz failed: {e!s}")
        # 3) OCR fallback (if it's a scanned PDF)
        if len(text.strip()) < 50:
            pdf2image = _safe_import("pdf2image")
            pytesseract = _safe_import("pytesseract")
            if pdf2image and pytesseract:
                try:
                    from pdf2image import convert_from_bytes
                    pages = convert_from_bytes(raw, dpi=200)[:10]  # cap to 10 pages for speed
                    ocr_chunks = []
                    for img in pages:
                        ocr_chunks.append(pytesseract.image_to_string(img))
                    maybe = "\n".join(ocr_chunks)
                    if len(maybe.strip()) > len(text.strip()):
                        text = maybe
                        notes.append("Used Tesseract OCR (first 10 pages)")
                except Exception as e:
                    notes.append(f"OCR fallback failed: {e!s}")
            else:
                notes.append("OCR fallback not available in this environment")
    elif lower.endswith(".pptx"):
        try:
            from pptx import Presentation
            prs = Presentation(io.BytesIO(raw))
            chunks = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        chunks.append(shape.text)
            text = "\n".join(chunks)
            notes.append("Used python-pptx extraction")
        except Exception as e:
            notes.append(f"pptx extraction failed: {e!s}")
    elif lower.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(raw))
            text = "\n".join(p.text for p in doc.paragraphs)
            notes.append("Used python-docx extraction")
        except Exception as e:
            notes.append(f"docx extraction failed: {e!s}")
    else:
        notes.append("Unsupported file type")
    return text, notes

# -------------------------
# Bloom helpers
# -------------------------
LOW_VERBS = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

def bloom_focus_from_week(week: int) -> str:
    if week <= 4:
        return "Low"
    if week <= 9:
        return "Medium"
    return "High"

# -------------------------
# MCQ generator (rule-of-thumb)
# -------------------------
@dataclass
class MCQ:
    stem: str
    options: List[str]
    answer: str

def make_mcqs(source: str, n: int) -> List[MCQ]:
    text = re.sub(r"\s+", " ", source).strip()
    # Grab candidate sentences (keep medium length)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    candidates = [s for s in sentences if 60 <= len(s) <= 220]
    if len(candidates) < n:
        candidates = (sentences + candidates)[: n]  # fallback
    out: List[MCQ] = []
    rng = __import__("random")
    for s in candidates[:n]:
        # crude key phrase: first noun-ish chunk
        words = re.findall(r"[A-Za-z][A-Za-z-]{2,}", s)
        key = words[rng.randrange(min(5, len(words)))] if words else "the concept"
        stem = f"Which option best completes: “{s.split(key)[0].strip()} ___ ”?"
        # Create distractors by replacing key with similar-length strings from the pool
        pool = [w for w in set(words) if w.lower() != key.lower() and 4 <= len(w) <= 18]
        rng.shuffle(pool)
        opts = [key]
        for w in pool[:3]:
            opts.append(w)
        # pad
        while len(opts) < 4:
            opts.append(key[::-1] if key not in opts else key.upper())
        rng.shuffle(opts)
        out.append(MCQ(stem=stem, options=opts, answer=key))
    return out

def mcqs_to_docx(mcqs: List[MCQ]) -> bytes:
    try:
        import docx
    except Exception:
        return b""
    doc = docx.Document()
    doc.add_heading("Knowledge MCQs", level=1)
    for i, q in enumerate(mcqs, 1):
        p = doc.add_paragraph(f"{i}. {q.stem}")
        for j, opt in enumerate(q.options, 1):
            doc.add_paragraph(f"{chr(64+j)}. {opt}", style="List Bullet")
        doc.add_paragraph(f"Answer: {q.answer}", style=None)
        doc.add_paragraph("")
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

# -------------------------
# Sidebar: upload + context
# -------------------------
with st.sidebar:
    st.subheader("Upload (optional)")
    up = st.file_uploader("Drag and drop file here", type=["pdf", "docx", "pptx"], accept_multiple_files=False)
    if up is not None:
        data = up.getvalue()
        h = file_hash(up.name, data)
        if h != st.session_state.last_hash:
            with st.spinner("Parsing file…"):
                text, notes = extract_text(io.BytesIO(data), up.name)
            st.session_state.file_bytes = data
            st.session_state.file_name = up.name
            st.session_state.extracted_text = text or ""
            st.session_state.last_hash = h
            st.session_state.loaded_once = True
            st.session_state.use_extracted = bool(text and len(text.strip()) > 0)
            st.toast("Uploaded & parsed" + (" ✅" if st.session_state.use_extracted else " (no embedded text found)"), icon="✅" if st.session_state.use_extracted else "⚠️")
            if notes:
                st.caption("• " + " • ".join(notes))

    st.markdown("---")
    st.subheader("Course context")
    lesson = st.selectbox("Lesson", options=list(range(1, 15)), index=st.session_state.lesson-1, key="lesson")
    week = st.selectbox("Week", options=list(range(1, 15)), index=st.session_state.week-1, key="week")
    st.session_state.bloom_focus = bloom_focus_from_week(week)

    st.markdown("---")
    st.subheader("Number of MCQs")
    st.selectbox("How many questions?", options=[5,10,15,20,30], key="mcq_count")
    st.caption("Typical handout: 10–15")

    st.markdown("---")
    st.subheader("Activities")
    st.selectbox("How many activities?", options=[1,2,3,4], key="activities_count")
    st.selectbox("Time each (mins)", options=[5,10,15,20,30], key="activity_minutes")

# -------------------------
# Header
# -------------------------
st.markdown(
    """
    <div style="background:#244e34;border-radius:14px;padding:16px 20px;color:#fff;margin-top:6px;margin-bottom:8px;">
        <div style="font-weight:700;font-size:18px;">ADI Builder — Lesson Activities & Questions</div>
        <div style="opacity:.85;font-size:12px;">Sleek, professional and engaging. Print‑ready handouts for your instructors.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Tabs
tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

with tabs[0]:
    # Top hint bar (value preview + Bloom chip)
    st.progress(0, text="")  # subtle baseline like a hairline
    colA, colB = st.columns([3,1])
    with colA:
        topic = st.text_input("Topic / Outcome (optional)", key="topic", placeholder="Module description, knowledge & skills outcomes")
    with colB:
        st.markdown(f"""
            <div style="text-align:right;padding-top:18px;">
                <span style="background:#e7dbc0;border-radius:20px;padding:6px 10px;font-size:12px;">
                    Week {st.session_state.week}: <b>{st.session_state.bloom_focus}</b>
                </span>
            </div>
        """, unsafe_allow_html=True)

    # Use extracted
    st.checkbox("Use sample text (for a quick test)", key="use_sample")

    st.markdown("**Source text (editable)**")

    # Textarea with optional autofill from extracted/sample; debounced to avoid flicker
    if st.session_state.use_extracted and not st.session_state.get("text_seeded", False):
        st.session_state["source_text"] = st.session_state.extracted_text[:15000]  # cap to 15k
        st.session_state["text_seeded"] = True
    elif st.session_state.use_sample and not st.session_state.get("text_seeded_sample", False):
        st.session_state["source_text"] = "Cells are the basic structural and functional units of life. Prokaryotic cells lack a nucleus, while eukaryotic cells have membrane-bound organelles. Mitochondria generate ATP through cellular respiration. DNA stores genetic information in chromosomes inside the nucleus."
        st.session_state["text_seeded_sample"] = True

    source_text = st.text_area("",
                               key="source_text",
                               height=220,
                               placeholder="Paste or jot key notes, vocab, facts here…")

    # Bloom verbs section with row highlighting
    focus = st.session_state.bloom_focus.lower()
    row_bg = {"low":"#e8f2ec", "medium":"#eef1e8", "high":"#f0efe8"}[focus]
    st.markdown(
        f"""
        <style>
          .verb-chip {{ display:inline-block;padding:10px 22px;margin:6px 10px 10px 0;border-radius:28px;background:#f6f6f4;border:1px solid #e6e3dd; }}
          .row-title {{ font-weight:700;margin-top:14px;margin-bottom:6px; }}
          .row {{ background:{row_bg};border:1px solid #e6e3dd;border-radius:12px;padding:8px 10px;margin-bottom:10px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    def row(title: str, verbs: List[str], active: bool):
        bg = "row" if active else ""
        st.markdown(f"<div class='{bg}'><div class='row-title'>{title}</div>", unsafe_allow_html=True)
        cols = st.columns(6)
        for i, v in enumerate(verbs):
            with cols[i % 6]:
                st.markdown(f"<div class='verb-chip'>{v}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    row("LOW (Weeks 1–4): Remember / Understand", LOW_VERBS, focus=="low")
    row("MEDIUM (Weeks 5–9): Apply / Analyse", MED_VERBS, focus=="medium")
    row("HIGH (Weeks 10–14): Evaluate / Create", HIGH_VERBS, focus=="high")

    # Action buttons
    can_generate = bool(source_text and len(source_text.strip()) > 40)
    col1, col2 = st.columns([1,1])
    with col1:
        btn = st.button("✨ Generate MCQs", disabled=not can_generate)
    with col2:
        rbtn = st.button("⟳ Regenerate", disabled=not can_generate)

    if btn or rbtn:
        with st.spinner("Creating questions…"):
            mcqs = make_mcqs(source_text, st.session_state.mcq_count)
        # Show MCQs
        for i, q in enumerate(mcqs, 1):
            st.markdown(f"**{i}. {q.stem}**")
            for j, opt in enumerate(q.options, 1):
                st.markdown(f"- {chr(64+j)}. {opt}")
            st.markdown(f"<span style='opacity:.6'>Answer: <b>{q.answer}</b></span>", unsafe_allow_html=True)
            st.markdown("---")

        # Download button (docx)
        doc_bytes = mcqs_to_docx(mcqs)
        if doc_bytes:
            st.download_button("⬇️ Download MCQs (.docx)", data=doc_bytes, file_name="adi_mcqs.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.info("Install `python-docx` in your environment to enable the DOCX download.")

with tabs[1]:
    st.write("Activities builder coming next (uses the same context).")
with tabs[2]:
    st.write("Revision generator coming next.")
