# app.py — ADI Builder (Streamlit)
# Stable, ADI-branded app with MCQs (answer key), Activities, and Revision.
# Safe download keys prevent StreamlitDuplicateElementId.

from __future__ import annotations
import io, re, random
from datetime import date
from dataclasses import dataclass
from typing import List

import streamlit as st

# Optional deps (we fall back to text export if python-docx is missing)
try:
    from docx import Document as Docx
    from docx.shared import Pt
except Exception:
    Docx = None

try:
    from pptx import Presentation
except Exception:
    Presentation = None

# ---------- ADI Theme ----------
ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
ADI_STONE = "#f5f5f3"
TEXT_MUTED = "#6b7280"

st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="📘",
    layout="wide",
)

def header():
    st.markdown(
        f"""
        <div style="background:{ADI_STONE};border-radius:14px;padding:14px 18px;margin:8px 0 16px 0;border:1px solid #e5e7eb">
          <div style="font-weight:800;color:{ADI_GREEN};letter-spacing:.2px;">ADI Builder — Lesson Activities & Questions</div>
          <div style="color:{TEXT_MUTED};font-size:14px">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Utilities ----------
def policy_band(week:int)->str:
    if 1 <= week <= 4: return "LOW"
    if 5 <= week <= 9: return "MEDIUM"
    return "HIGH"

LOW_VERBS = ["define","identify","list","recall","describe","label"]
MED_VERBS = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","critique","create"]
BAND_TO_VERBS = {"LOW": LOW_VERBS, "MEDIUM": MED_VERBS, "HIGH": HIGH_VERBS}

def chunk_text(s: str) -> List[str]:
    if not s: return []
    parts = re.split(r"(?<=[.!?])\s+", s.strip())
    return [p.strip() for p in parts if len(p.strip()) >= 25][:60]

def read_text_from_upload(upload) -> str:
    if upload is None: return ""
    name = upload.name.lower()
    data = upload.read()
    try:
        if name.endswith(".txt"):
            return data.decode("utf-8", errors="ignore")
        if name.endswith(".docx") and Docx:
            doc = Docx(io.BytesIO(data))
            return "\n".join([p.text for p in doc.paragraphs])
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(io.BytesIO(data))
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"): texts.append(shape.text)
            return "\n".join(texts)
    except Exception:
        pass
    return ""

# Always-unique download key wrapper
def safe_download(label: str, data: bytes, filename: str, mime: str, scope: str):
    st.download_button(label, data=data, file_name=filename, mime=mime, key=f"dl_{scope}")

# ---------- MCQs ----------
@dataclass
class MCQ:
    stem: str
    choices: List[str]  # 4 choices
    answer_idx: int     # 0..3

def make_mcq(seed_text: str, verb: str, i: int) -> MCQ:
    base = re.sub(r"\s+", " ", seed_text.strip())
    stem = f"{i+1}. {verb.capitalize()} the best answer based on the notes: {base[:160]}…"
    correct = f"{verb.capitalize()} the main concept accurately."
    distractors = [
        f"{verb.capitalize()} a partially correct idea.",
        f"{verb.capitalize()} an unrelated detail.",
        f"{verb.capitalize()} the concept but misapply it.",
    ]
    choices = [correct] + distractors
    random.shuffle(choices)  # stable variety
    answer_idx = choices.index(correct)
    return MCQ(stem=stem, choices=choices, answer_idx=answer_idx)

def build_mcqs(source: str, count: int, verbs: List[str]) -> List[MCQ]:
    sents = chunk_text(source) or [source or "Instructor-provided notes about this week’s topic."]
    out = []
    for i in range(count):
        verb = verbs[i % max(1,len(verbs))]
        text_seed = sents[i % len(sents)]
        out.append(make_mcq(text_seed, verb, i))
    return out

def mcqs_to_docx(mcqs: List[MCQ], title: str, show_key: bool) -> bytes:
    if not Docx:
        buf = io.StringIO()
        buf.write(title + "\n\n")
        for q in mcqs:
            buf.write(q.stem + "\n")
            for j, c in enumerate(q.choices): buf.write(f"  {'ABCD'[j]}. {c}\n")
            buf.write("\n")
        if show_key:
            buf.write("Answer Key:\n")
            for idx, q in enumerate(mcqs, 1):
                buf.write(f"{idx}. {'ABCD'[q.answer_idx]}\n")
        return buf.getvalue().encode("utf-8")
    doc = Docx()
    style = doc.styles["Normal"]; style.font.name = "Calibri"; style.font.size = Pt(11)
    doc.add_heading(title, level=1)
    for q in mcqs:
        doc.add_paragraph(q.stem)
        for j, c in enumerate(q.choices): doc.add_paragraph(f"{'ABCD'[j]}. {c}")
        doc.add_paragraph("")
    if show_key:
        doc.add_heading("Answer Key", level=2)
        for i, q in enumerate(mcqs, 1):
            doc.add_paragraph(f"{i}. {'ABCD'[q.answer_idx]}")
    b = io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- Activities ----------
def build_activities(source: str, verbs: List[str], count:int=6) -> List[str]:
    base = chunk_text(source) or [source or "Topic notes"]
    prompts = []
    for i in range(count):
        v = verbs[i % len(verbs or ['apply'])]
        snippet = re.sub(r"\s+", " ", base[i % len(base)])[:120]
        prompts.append(f"{i+1}. Using **{v}**: Create a short activity engaging students with: “{snippet}…”.")
    return prompts

def activities_to_docx(items: List[str], title: str) -> bytes:
    if not Docx:
        return ("\n".join([title, ""] + items)).encode("utf-8")
    doc = Docx()
    style = doc.styles["Normal"]; style.font.name = "Calibri"; style.font.size = Pt(11)
    doc.add_heading(title, level=1)
    for it in items: doc.add_paragraph(it)
    b = io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- Revision ----------
def build_revision_items(source: str, count:int=8) -> List[str]:
    bits = chunk_text(source) or [source or "Topic notes"]
    out = []
    for i in range(count):
        snippet = re.sub(r"\s+", " ", bits[i % len(bits)])[:110]
        out.append(f"{i+1}. Recall: Summarize the key point from — “{snippet}…”")
    return out

def revision_to_docx(items: List[str], title: str) -> bytes:
    if not Docx:
        return ("\n".join([title, ""] + items)).encode("utf-8")
    doc = Docx()
    style = doc.styles["Normal"]; style.font.name = "Calibri"; style.font.size = Pt(11)
    doc.add_heading(title, level=1)
    for it in items: doc.add_paragraph(it)
    b = io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- UI helpers ----------
def verbs_pills(label: str, verbs: List[str], key_prefix: str) -> List[str]:
    if label: st.markdown(f"**{label}**")
    cols = st.columns(len(verbs))
    picks = []
    for c, v in zip(cols, verbs):
        with c:
            if st.checkbox(v, key=f"{key_prefix}_{v}"): picks.append(v)
    return picks

def build_title(prefix: str, course: str, lesson: int, week: int,
                topic: str, instr: str, cohort: str, lesson_date: date) -> str:
    return " — ".join([s for s in [
        prefix,
        course or None,
        f"Lesson {lesson} Week {week}",
        topic or None,
        instr or None,
        cohort or None,
        (lesson_date.strftime("%Y-%m-%d") if lesson_date else None),
    ] if s])

# ---------- App ----------
def main():
    header()

    # Sidebar: context
    with st.sidebar:
        st.caption("Upload (optional)")
        up = st.file_uploader("Drag and drop file here", type=["txt","docx","pptx"],
                              help="We’ll parse plain text, .docx or .pptx", label_visibility="collapsed")
        st.write("")

        st.caption("Course details")
        course = st.text_input("Course name", value="")
        cohort = st.text_input("Class / Cohort", value="")
        instr = st.text_input("Instructor name (optional)", value="")
        lesson_date = st.date_input("Date", value=date.today())

        st.caption("Course context")
        col_a, col_b = st.columns(2)
        with col_a: lesson = st.selectbox("Lesson", [1,2,3,4,5], index=0)
        with col_b: week = st.selectbox("Week", list(range(1,15)), index=6)

        st.caption("Topic / outcome")
        topic = st.text_input("Module description, knowledge outcome", value="",
                              placeholder="Module description, knowledge outcome")

        col_q, col_a2 = st.columns(2)
        with col_q:
            st.caption("Number of MCQs")
            mcq_n = st.selectbox("How many questions?", [5,10,15,20], index=1)
        with col_a2:
            st.caption("Activities")
            act_n = st.selectbox("How many prompts?", [4,6,8,10], index=1)

        st.divider()
        st.markdown(
            f"<span style='color:{TEXT_MUTED};font-size:12px'>Week policy: "
            f"<b>{policy_band(int(week))}</b> — (1–4 Low, 5–9 Medium, 10–14 High)</span>",
            unsafe_allow_html=True
        )

    # Center content
    st.checkbox("Use sample text (quick test)", key="sample_toggle")
    st.caption("Source text (editable)")
    uploaded_text = read_text_from_upload(up)
    if st.session_state.get("sample_toggle") and not uploaded_text:
        uploaded_text = ("CNC milling safety requires correct PPE, machine guarding, "
                         "understanding feeds and speeds, and proper clamping of workpieces. "
                         "Operators must verify tool paths and perform dry runs before cutting.")
    src_text = st.text_area("", value=uploaded_text or "", height=180,
                            placeholder="Paste or jot key notes, vocab, facts here…")

    band = policy_band(int(week))
    st.markdown(
        f"**{band} (Weeks {'1–4' if band=='LOW' else '5–9' if band=='MEDIUM' else '10–14'}):** "
        f"{'Remember / Understand' if band=='LOW' else 'Apply / Analyse' if band=='MEDIUM' else 'Evaluate / Create'}"
    )

    with st.container():
        picks = verbs_pills("", BAND_TO_VERBS[band], key_prefix=f"verbs_{band.lower()}")
        if not picks: st.info("Pick at least one Bloom verb (you can select multiple).")

    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

    # --- Tab 1: MCQs ---
    with tabs[0]:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Generate MCQs", type="primary", key="btn_generate_mcq"):
            qs = build_mcqs(src_text, mcq_n, picks or BAND_TO_VERBS[band])
            st.success(f"Generated {len(qs)} MCQs.")
            for q in qs:
                st.markdown(f"**{q.stem}**")
                for j, c in enumerate(q.choices): st.markdown(f"- {'ABCD'[j]}. {c}")
                st.markdown("<hr/>", unsafe_allow_html=True)

            show_key = st.checkbox("Include answer key in export", value=True, key="ck_mcq_key")
            title = build_title("ADI MCQs", course, lesson, week, topic, instr, cohort, lesson_date)
            doc_bytes = mcqs_to_docx(qs, title, show_key)
            safe_download("⬇️ Download MCQs (.docx)", doc_bytes, "adi_mcqs.docx",
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="mcqs_tab")

    # --- Tab 2: Activities ---
    with tabs[1]:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Generate Activities", key="btn_generate_acts"):
            acts = build_activities(src_text, picks or BAND_TO_VERBS[band], act_n)
            for a in acts: st.markdown(a)
            title = build_title("ADI Activities", course, lesson, week, topic, instr, cohort, lesson_date)
            doc_bytes = activities_to_docx(acts, title)
            safe_download("⬇️ Download Activities (.docx)", doc_bytes, "adi_activities.docx",
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="activities_tab")

    # --- Tab 3: Revision ---
    with tabs[2]:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        rev_n = st.selectbox("How many revision items?", [6,8,10,12], index=1, key="rev_n")
        if st.button("Generate Revision Items", key="btn_generate_rev"):
            rev = build_revision_items(src_text, rev_n)
            for r in rev: st.markdown(r)
            title = build_title("ADI Revision", course, lesson, week, topic, instr, cohort, lesson_date)
            doc_bytes = revision_to_docx(rev, title)
            safe_download("⬇️ Download Revision (.docx)", doc_bytes, "adi_revision.docx",
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="revision_tab")

    st.markdown(
        f"<div style='color:{TEXT_MUTED};font-size:12px;margin-top:18px'>"
        f"ADI style: green <code>{ADI_GREEN}</code>, gold <code>{ADI_GOLD}</code>, stone background. "
        f"Avoid red accents; keep daily-use simplicity."
        f"</div>",
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()
