

import streamlit as st
import io, random, textwrap
from datetime import date
from pathlib import Path

# ------------------------
# Optional PDF support
# ------------------------
try:
    import fitz  # PyMuPDF
    PDF_ENABLED = True
except Exception:
    fitz = None
    PDF_ENABLED = False

# Optional DOCX/PPTX parsing (we only import when needed)
def read_docx_bytes(file_bytes: bytes) -> str:
    from docx import Document
    bio = io.BytesIO(file_bytes)
    doc = Document(bio)
    return "\n".join([p.text for p in doc.paragraphs])

def read_pptx_bytes(file_bytes: bytes) -> str:
    from pptx import Presentation
    prs = Presentation(io.BytesIO(file_bytes))
    texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                texts.append(shape.text)
    return "\n".join(texts)

# ------------------------
# Utility
# ------------------------
def detect_filetype(uploaded_file) -> str:
    name = (uploaded_file.name or "").lower()
    if name.endswith(".pdf"):   return "pdf"
    if name.endswith(".pptx"):  return "pptx"
    if name.endswith(".docx"):  return "docx"
    if name.endswith(".txt"):   return "txt"
    mime = (uploaded_file.type or "").lower()
    if "pdf" in mime:    return "pdf"
    if "ppt" in mime:    return "pptx"
    if "word" in mime:   return "docx"
    if "text" in mime:   return "txt"
    return "txt"

def parse_upload(uploaded_file, filetype: str) -> str:
    data = uploaded_file.read()
    if filetype == "pdf":
        if not PDF_ENABLED:
            st.info("PDF parsing temporarily disabled on this build.")
            return ""
        text = []
        doc = fitz.open(stream=data, filetype="pdf")
        for page in doc:
            text.append(page.get_text("text"))
        return "\n".join(text)

    if filetype == "pptx":
        return read_pptx_bytes(data)

    if filetype == "docx":
        return read_docx_bytes(data)

    # txt default
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def ensure_state():
    defaults = {
        "gen_mcqs": [],
        "gen_acts": [],
        "gen_rev": [],
        "answer_key": [],
        "export_ready": False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

# ------------------------
# Simple content generation (rule-based placeholders)
# ------------------------
BLOOM_VERBS_LOW = ["define", "identify", "list", "recall", "describe", "label"]
BLOOM_VERBS_MED = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
BLOOM_VERBS_HIGH = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

def pick_terms(text, k=20):
    """Pick candidate keywords from the source text (very simple heuristic)."""
    if not text:
        corpus = ["safety", "procedure", "system", "component", "principle", "policy", "mission", "calibration", "diagnostics", "maintenance"]
    else:
        tokens = [t.strip(".,:;()[]{}!?\"'").lower() for t in text.split()]
        tokens = [t for t in tokens if t.isalpha() and 3 <= len(t) <= 14]
        common_stops = set("the of and to in for is are be a an on from with that this these those which using as by or it at we you they can may into over under".split())
        corpus = [t for t in tokens if t not in common_stops]
        if not corpus:
            corpus = ["concept", "process", "system", "protocol", "hazard", "control"]
    random.shuffle(corpus)
    return corpus[:k]

def generate_mcqs(n, verbs, source_text, include_answers=True):
    terms = pick_terms(source_text, k=max(20, n*5))
    mcqs, key = [], []
    for i in range(n):
        term = random.choice(terms)
        verb = random.choice(verbs or BLOOM_VERBS_LOW)
        question = f"{i+1}. {verb.capitalize()} the following term as it relates to the lesson: **{term}**."
        # Make 4 options: one correct + 3 distractors
        correct = f"Accurate statement about {term}."
        distractors = [
            f"Unrelated detail about {random.choice(terms)}.",
            f"Common misconception about {term}.",
            f"Vague statement with {random.choice(terms)}."
        ]
        options = distractors + [correct]
        random.shuffle(options)
        mcqs.append((question, options))
        if include_answers:
            key.append(options.index(correct) + 1)
    return mcqs, key

def generate_activities(n, verbs, source_text):
    terms = pick_terms(source_text, k=max(10, n*2))
    acts = []
    for i in range(n):
        verb = random.choice(verbs or BLOOM_VERBS_MED)
        focus = random.choice(terms)
        acts.append(f"{i+1}. {verb.capitalize()} a short activity where learners work in pairs to address **{focus}** and present findings in 3 minutes.")
    return acts

def generate_revision(n, verbs, source_text):
    terms = pick_terms(source_text, k=max(10, n*2))
    revs = []
    for i in range(n):
        verb = random.choice(verbs or BLOOM_VERBS_LOW)
        focus = random.choice(terms)
        revs.append(f"{i+1}. {verb.capitalize()} key points on **{focus}** in a 5-bullet summary.")
    return revs

# ------------------------
# Exporters
# ------------------------
def export_docx(title, mcqs=None, acts=None, rev=None, include_answers=False, answer_key=None) -> bytes:
    from docx import Document
    doc = Document()
    doc.add_heading(title, level=1)

    if mcqs:
        doc.add_heading("Knowledge MCQs", level=2)
        for idx, (q, options) in enumerate(mcqs, start=1):
            p = doc.add_paragraph()
            run = p.add_run(q)
            run.bold = True
            for j, opt in enumerate(options, start=1):
                doc.add_paragraph(f"{chr(64+j)}. {opt}", style=None)

    if acts:
        doc.add_heading("Skills Activities", level=2)
        for i, a in enumerate(acts, start=1):
            doc.add_paragraph(a)

    if rev:
        doc.add_heading("Revision", level=2)
        for i, r in enumerate(rev, start=1):
            doc.add_paragraph(r)

    if include_answers and answer_key:
        doc.add_heading("Answer Key", level=2)
        for i, ans in enumerate(answer_key, start=1):
            doc.add_paragraph(f"Q{i}: {['A','B','C','D'][ans-1]}")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def export_txt_mcqs(mcqs, answer_key=None, include_answers=False) -> bytes:
    lines = []
    for idx, (q, options) in enumerate(mcqs, start=1):
        lines.append(q)
        for j, opt in enumerate(options, start=1):
            lines.append(f"{chr(64+j)}. {opt}")
        lines.append("")
    if include_answers and answer_key:
        lines.append("Answer Key")
        for i, ans in enumerate(answer_key, start=1):
            lines.append(f"Q{i}: {['A','B','C','D'][ans-1]}")
    return ("\n".join(lines)).encode("utf-8")

# ------------------------
# UI
# ------------------------
ensure_state()
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🗂️", layout="wide")

with st.sidebar:
    st.subheader("Upload (optional)")
    uploaded_file = st.file_uploader("Drag and drop file here", type=["txt", "docx", "pptx", "pdf"])
    deep_scan = st.toggle("Deep scan source (slower, better coverage)", value=False)
    st.divider()

    st.subheader("Course details")
    course = st.text_input("Course name", value="Defense Technologies 101")
    cohort = st.text_input("Class / Cohort", value="D1-C01")
    instructor = st.text_input("Instructor name", value="")
    the_date = st.date_input("Date", value=date.today())

    st.subheader("Context")
    colA, colB = st.columns(2)
    lesson = colA.number_input("Lesson", 1, 5, 1, step=1)
    week = colB.number_input("Week", 1, 14, 1, step=1)

st.markdown("### ADI Builder — Lesson Activities & Questions")
topic = st.text_area("Topic / Outcome (optional)", height=80, placeholder="e.g., Integrated Project and ...")

# Bloom policy bands
st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")
low_expander = st.expander("**Low (Weeks 1–4)** — Remember / Understand", expanded=True)
med_expander = st.expander("**Medium (Weeks 5–9)** — Apply / Analyse", expanded=True)
high_expander = st.expander("**High (Weeks 10–14)** — Evaluate / Create", expanded=True)

with low_expander:
    low = st.multiselect("Low verbs", BLOOM_VERBS_LOW, default=BLOOM_VERBS_LOW[:3], key="lowverbs")
with med_expander:
    med = st.multiselect("Medium verbs", BLOOM_VERBS_MED, default=BLOOM_VERBS_MED[:3], key="medverbs")
with high_expander:
    high = st.multiselect("High verbs", BLOOM_VERBS_HIGH, default=BLOOM_VERBS_HIGH[:3], key="highverbs")

tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision", "Print Summary"])

# Source text
source_text = ""
if uploaded_file is not None:
    ftype = detect_filetype(uploaded_file)
    source_text = parse_upload(uploaded_file, ftype)
    if deep_scan:
        source_text = "\n".join([t for t in textwrap.wrap(source_text, width=120)])

# Tab 1 — MCQs
with tabs[0]:
    cols = st.columns([2,1,1])
    with cols[0]:
        n_mcq = st.selectbox("How many MCQs?", [5,10,15,20], index=1)
    with cols[1]:
        include_key = st.checkbox("Include answer key in export", value=True)
    if st.button("Generate MCQs", type="primary"):
        mcqs, key = generate_mcqs(n_mcq, (low or BLOOM_VERBS_LOW), source_text, include_answers=include_key)
        st.session_state.gen_mcqs = mcqs
        st.session_state.answer_key = key if include_key else []
        st.session_state.export_ready = True

    if st.session_state.get("gen_mcqs"):
        for i, (q, options) in enumerate(st.session_state.gen_mcqs, start=1):
            st.markdown(f"**{q}**")
            for j, opt in enumerate(options, start=1):
                st.markdown(f"{chr(64+j)}. {opt}")
            st.write("")

        colDL = st.columns(2)
        with colDL[0]:
            docx_bytes = export_docx(
                title=f"{course} — Lesson {lesson} (Week {week})",
                mcqs=st.session_state.gen_mcqs,
                acts=None,
                rev=None,
                include_answers=include_key,
                answer_key=st.session_state.answer_key,
            )
            st.download_button("⬇️ Download DOCX", data=docx_bytes, file_name="ADI_Knowledge_MCQs.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with colDL[1]:
            txt_bytes = export_txt_mcqs(st.session_state.gen_mcqs, st.session_state.answer_key, include_answers=include_key)
            st.download_button("⬇️ Download TXT", data=txt_bytes, file_name="ADI_Knowledge_MCQs.txt", mime="text/plain")

# Tab 2 — Activities
with tabs[1]:
    n_act = st.selectbox("How many activities?", [3,5,8,10], index=1, key="n_act")
    if st.button("Generate Activities"):
        acts = generate_activities(n_act, (med or BLOOM_VERBS_MED), source_text)
        st.session_state.gen_acts = acts
        st.session_state.export_ready = True

    if st.session_state.get("gen_acts"):
        for a in st.session_state.gen_acts:
            st.markdown(f"- {a}")

# Tab 3 — Revision
with tabs[2]:
    n_rev = st.selectbox("How many revision prompts?", [3,5,8,10], index=1, key="n_rev")
    if st.button("Generate Revision"):
        revs = generate_revision(n_rev, (low or BLOOM_VERBS_LOW), source_text)
        st.session_state.gen_rev = revs
        st.session_state.export_ready = True

    if st.session_state.get("gen_rev"):
        for r in st.session_state.gen_rev:
            st.markdown(f"- {r}")

# Tab 4 — Print Summary
with tabs[3]:
    st.subheader("Print Summary")
    st.markdown(f"**Course:** {course}  \n**Cohort:** {cohort}  \n**Instructor:** {instructor}  \n**Date:** {the_date}  \n**Lesson:** {lesson}  \n**Week:** {week}")
    st.divider()
    if st.session_state.get("gen_mcqs"):
        st.markdown("### Knowledge MCQs")
        for i, (q, options) in enumerate(st.session_state.gen_mcqs, start=1):
            st.markdown(f"**{q}**")
            for j, opt in enumerate(options, start=1):
                st.markdown(f"{chr(64+j)}. {opt}")
            st.write("")

    if st.session_state.get("gen_acts"):
        st.markdown("### Skills Activities")
        for a in st.session_state.gen_acts:
            st.markdown(f"- {a}")

    if st.session_state.get("gen_rev"):
        st.markdown("### Revision")
        for r in st.session_state.gen_rev:
            st.markdown(f"- {r}")

st.caption("ADI Builder — sleek, professional and engaging. Print‑ready handouts for your instructors.")
