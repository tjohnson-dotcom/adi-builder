

# ADI Builder — Lesson Activities & Questions
# Version: 2.5.6 (stable, no flicker)
# Features: Upload (PDF/DOCX/PPTX), MCQs (random A-D), Activities, Revision bands, DOCX & GIFT exports
# Requirements: streamlit, python-docx, python-pptx, pymupdf, lxml, Pillow

import io
import random
import textwrap
from datetime import datetime
from typing import List, Tuple

import streamlit as st

# Optional dependencies (guarded imports so app loads even if one is missing)
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None
try:
    from pptx import Presentation
except Exception:
    Presentation = None

# ------------------------- Page & Theme ---------------------------------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="🧠",
    layout="wide",
)

def inject_adi_css():
    st.markdown(
        """
        <style>
          /* Base */
          .block-container { padding-top: 0.75rem; }
          /* Header band */
          .adi-hero {
            background: #22382b;
            color:#fff; border-radius: 14px; padding: 14px 18px; margin: 8px 0 18px 0;
          }
          .adi-badge {
            display:inline-block; background:#2e4c3a; color:#fff; padding:6px 10px; border-radius:10px;
            font-weight:600; font-size:.85rem; margin-right:10px;
          }
          .adi-sub { color:#d6e2db; font-size:.9rem; margin-top: 4px; }

          /* Buttons */
          .stButton>button, .stDownloadButton>button{
            background:#245a34!important; color:#fff!important;
            border:1px solid #1e4c2b!important; border-radius:10px;
            box-shadow:0 1px 2px rgba(0,0,0,.08); transition:transform .02s, box-shadow .2s;
          }
          .stButton>button:hover, .stDownloadButton>button:hover{ filter:brightness(1.02); transform:translateY(-1px); }

          /* Pills / chips */
          [data-baseweb="tag"]{
            background:#eaf3ed!important; color:#245a34!important; border:1px solid #cfe3d6!important;
          }
          [data-baseweb="tag"][aria-selected="true"]{
            background:#245a34!important; color:#fff!important; border-color:#1e4c2b!important;
          }

          /* Tabs */
          .stTabs [data-baseweb="tab"]{ font-weight:600; color:#1f3b27; }
          .stTabs [data-baseweb="tab"][aria-selected="true"]{
            color:#245a34!important; border-bottom:3px solid #245a34!important;
          }

          /* Cards */
          .section-card{ background:#fff; border:1px solid #e8ece9; border-radius:14px; padding:1rem 1.25rem;
                        box-shadow:0 1px 3px rgba(0,0,0,.05); margin-bottom: 10px;}
          .small-note{ color:#687a70; font-size:.86rem; }
          .muted{ color:#6d7a71; }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_adi_css()

# ------------------------- Constants ------------------------------------

DEFAULT_VERBS = {
    "Understand": ["define", "identify", "list", "recall", "describe", "label"],
    "Apply": ["apply", "demonstrate", "solve", "illustrate"],
    "Analyse": ["analyse", "compare", "contrast", "distinguish", "categorise"],
    "Evaluate": ["evaluate", "critique", "justify", "recommend"],
    "Create": ["design", "synthesize", "compose", "construct"],
}

WEEK_BANDS = [
    ("Weeks 1–3", "Low focus"),
    ("Weeks 4–8", "Medium focus"),
    ("Weeks 9–14", "High focus"),
]

# ------------------------- Helpers --------------------------------------

def initialise_state():
    ss = st.session_state
    ss.setdefault("mcq_blocks", 10)
    ss.setdefault("verbs_mcq", DEFAULT_VERBS["Understand"][:4])
    ss.setdefault("verbs_act", ["apply", "demonstrate", "evaluate", "design"])
    ss.setdefault("policy3", False)
    ss.setdefault("uploaded_text", "")

initialise_state()

def safe_file_uploader(label, types):
    """Uploader with simple dedupe to avoid flicker on rerun."""
    f = st.file_uploader(label, type=types, accept_multiple_files=False, label_visibility="collapsed")
    if f is None:
        return None
    st.session_state.setdefault("_upload_seen", set())
    key = (f.name, f.size)
    if key in st.session_state["_upload_seen"]:
        return f
    st.session_state["_upload_seen"].add(key)
    return f

def extract_text_from_file(upload) -> str:
    name = upload.name.lower()
    data = upload.read()
    if name.endswith(".pdf"):
        if fitz is None:
            return ""
        try:
            doc = fitz.open(stream=data, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"
            return text.strip()
        except Exception:
            return ""
    elif name.endswith(".docx"):
        if DocxDocument is None:
            return ""
        try:
            with io.BytesIO(data) as mem:
                doc = DocxDocument(mem)
                return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""
    elif name.endswith(".pptx"):
        if Presentation is None:
            return ""
        try:
            with io.BytesIO(data) as mem:
                prs = Presentation(mem)
                text = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text.append(shape.text)
                return "\n".join(text)
        except Exception:
            return ""
    return ""

def normalise_text(src: str, limit: int = 5000) -> str:
    s = " ".join(src.split())
    if len(s) > limit:
        return s[:limit] + "..."
    return s

def split_chunks(text: str, n: int) -> List[str]:
    words = text.split()
    chunks = []
    size = max(80, len(words)//max(1, n))
    for i in range(0, len(words), size):
        chunks.append(" ".join(words[i:i+size]))
    if not chunks:
        chunks = [""]
    return chunks[:n]

uploaded = st.file_uploader("Upload PDF / DOCX / PPTX", type=["pdf", "docx", "pptx"], key="uploader")
if uploaded:
    # one-time toast per new file
    if st.session_state.get("last_upload_name") != uploaded.name:
        st.session_state["last_upload_name"] = uploaded.name
        kb = uploaded.size / 1024
        st.toast(f"Uploaded **{uploaded.name}** ({kb:.1f} KB)", icon="✅")
    st.success(f"File ready: **{uploaded.name}**")


# ------------------------- MCQ generation -------------------------------

mix_mode = st.toggle("Mixture mode (varied question types)", value=False, key="mix_mode")


def generate_mcq_block(src_text: str, verbs: List[str], block_size: int = 3) -> List[dict]:
    """Generate a small block of MCQs. One correct + 3 distractors (A-D)."""
    base_pool = verbs if verbs else ["define", "identify", "list", "apply"]
    nouns = ["process", "concept", "term", "principle", "method", "model", "diagram", "policy"]
    blocks = []
    import random as _random
    for _ in range(block_size):
        v = _random.choice(base_pool)
        n = _random.choice(nouns)
        stem = f"Which option best {v}s the {n}?"
        correct = f"The best {n} {v}ed is highlighted in the course material."
        wrongs = [
            f"A partial {n} unrelated to the question.",
            f"A common misconception about the {n}.",
            f"An example that does not {v} the {n}.",
        ]
        options = [correct] + wrongs
        _random.shuffle(options)
        answer_label = "ABCD"[options.index(correct)]
        blocks.append({"question": stem, "options": options, "answer": answer_label})
    return blocks

def generate_mcqs(src_text: str, verbs: List[str], num_blocks: int, policy3: bool) -> List[List[dict]]:
    blocks = []
    for _ in range(num_blocks):
        size = 3 if policy3 else 5
        blocks.append(generate_mcq_block(src_text, verbs, block_size=size))
    return blocks
MIX_TEMPLATES = {
    "define":   lambda t: f"Which statement best defines **{t}**?",
    "identify": lambda t: f"Which option correctly identifies **{t}**?",
    "apply":    lambda t: f"Which option best applies **{t}** to a real case?",
    "analyze":  lambda t: f"Which option best analyzes **{t}** (evidence vs. trade-offs)?",
    "evaluate": lambda t: f"Which option best evaluates **{t}** using clear criteria?",
    "create":   lambda t: f"Which option proposes a sound design using **{t}**?",
}

# Balanced mix for N questions (no need to be perfect – just varied)
def choose_mix(n: int):
    order = (["define","identify","apply","apply","analyze","evaluate","create"] * 10)[:n]
    return order[:n]

# ------------------------- Activities -----------------------------------

def generate_activities(count: int, duration: int, verbs: List[str], src_text: str) -> List[str]:
    starters = ["In pairs,", "Individually,", "As a group,", "With A3 paper,", "Using the e-book,"]
    templates = [
        " {starter} {verb} the core ideas from the text and present a 2-minute summary.",
        " {starter} {verb} a real-world example that fits the module content.",
        " {starter} {verb} a short poster explaining today’s key concept.",
        " {starter} {verb} three questions you would ask a peer about this topic.",
        " {starter} {verb} a flowchart that maps the process described."
    ]
    verbs_pool = verbs if verbs else ["apply","demonstrate","evaluate","design"]
    acts = []
    import random as _random
    for _ in range(count):
        t = _random.choice(templates)
        v = _random.choice(verbs_pool)
        s = _random.choice(starters)
        acts.append((t.format(starter=s, verb=v)).strip() + f" (≈ {duration} mins)")
    return acts

# ------------------------- Revision -------------------------------------

def build_revision_plan(src_text: str, week: int, lesson: int) -> List[str]:
    if not src_text:
        return ["Add key points or upload content to generate a revision outline."]
    chunks = split_chunks(src_text, 5)
    out = []
    for i, c in enumerate(chunks, 1):
        out.append(f"Rev-{i}: " + textwrap.shorten(c, width=160, placeholder='…'))
    return out

# ------------------------- Exports --------------------------------------

def export_docx(mcq_blocks: List[List[dict]], activities: List[str], title: str = "ADI Pack") -> bytes:
    if DocxDocument is None:
        return b""
    doc = DocxDocument()
    doc.add_heading(title, 0)
    # MCQs
    if mcq_blocks:
        doc.add_heading("MCQ Paper", level=1)
        qn = 1
        for block in mcq_blocks:
            for q in block:
                doc.add_paragraph(f"{qn}. {q['question']}")
                for i, opt in enumerate(q["options"]):
                    label = "ABCD"[i]
                    doc.add_paragraph(f"   {label}. {opt}")
                qn += 1
    # Activities
    if activities:
        doc.add_heading("Activities", level=1)
        for i, a in enumerate(activities, 1):
            doc.add_paragraph(f"{i}. {a}")
    # Answers
    if mcq_blocks:
        doc.add_heading("Answer Key", level=1)
        qn = 1
        for block in mcq_blocks:
            for q in block:
                doc.add_paragraph(f"{qn}. {q['answer']}")
                qn += 1
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def export_gift(mcq_blocks: List[List[dict]]) -> bytes:
    lines = []
    qn = 1
    for block in mcq_blocks:
        for q in block:
            stem = q["question"].replace("\\n", " ")
            opts = q["options"]
            correct_idx = "ABCD".index(q["answer"])
            choices = []
            for i, opt in enumerate(opts):
                opt = opt.replace("\\n"," ")
                if i == correct_idx:
                    choices.append(f"={opt}")
                else:
                    choices.append(f"~{opt}")
            lines.append(f"::{qn}:: {stem} {{ {' '.join(choices)} }}")
            qn += 1
    return ("\\n\\n".join(lines)).encode("utf-8")

# ------------------------- UI -------------------------------------------

# Sidebar — upload & selectors
with st.sidebar:
    st.header("Upload PDF / DOCX / PPTX")
    upload = safe_file_uploader("Upload", ["pdf","docx","pptx"])
    st.caption("Limit 200MB per file · PDF, DOCX, PPTX")

    st.divider()
    week = st.selectbox("Week", [i for i in range(1,15)], index=0)
    lesson = st.selectbox("Lesson", [i for i in range(1,11)], index=0)
    st.caption(f"Policy: Low • Weeks 1–3")

# Header band
st.markdown(
    f"""
    <div class="adi-hero">
      <div style="display:flex; align-items:center; gap:12px;">
        <div style="font-size:1.25rem; font-weight:700;">ADI Builder — Lesson Activities & Questions</div>
      </div>
      <div class="adi-sub">Professional, branded, editable and export-ready.</div>
      <div style="margin-top:8px;">
        <span class="adi-badge">{WEEK_BANDS[0][0]}</span>
        <span class="adi-badge">{WEEK_BANDS[1][0]}</span>
        <span class="adi-badge">{WEEK_BANDS[2][0]}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Pull text from upload (once)
if upload is not None:
    text = extract_text_from_file(upload)
    st.session_state["uploaded_text"] = normalise_text(text)
src_text = st.session_state.get("uploaded_text", "")

tabs = st.tabs(["🧠 Knowledge MCQs", "🛠️ Skills Activities", "📘 Revision"])

# ---------------- MCQs Tab ----------------
with tabs[0]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    colL, colR = st.columns([3,2])
    with colL:
        st.toggle("ADI 3-question policy mode (Low ➜ Medium ➜ High)", key="policy3", help="If ON, each MCQ block has 3 items. If OFF, 5 items.")
        bloom = st.multiselect(
            "Bloom’s levels",
            ["Understand","Apply","Analyse","Evaluate","Create"],
            default=["Understand","Apply","Analyse"],
        )
    with colR:
        with st.expander("Verbs per level", expanded=True):
            pool = []
            for b in bloom:
                options = DEFAULT_VERBS.get(b, [])
                verbs = st.multiselect(f"Verbs for {b}", options, default=options[:max(1, min(3, len(options)))])
                pool.extend(verbs)
            st.session_state["verbs_mcq"] = pool

    topic = st.text_input("Topic (optional)")

    c1, c2, c3, c4 = st.columns([1,1,3,3])
    with c1:
        quick = st.radio("Quick pick", [5,10,20,30], horizontal=True, index=1, label_visibility="collapsed")
    with c2:
        st.number_input("Or custom number of MCQ blocks", min_value=1, max_value=100, step=1, key="mcq_blocks")
    with c3:
        gen_mcq_btn = st.button("🧩 Generate MCQ Blocks", use_container_width=True)
    with c4:
        regen_mcq_btn = st.button("🔁 Regenerate (new random set)", use_container_width=True)

    if gen_mcq_btn or regen_mcq_btn:
        nblocks = st.session_state["mcq_blocks"] or quick
        st.session_state["mcq_data"] = generate_mcqs(src_text, st.session_state.get("verbs_mcq", []), nblocks, st.session_state["policy3"])

    mcq_blocks = st.session_state.get("mcq_data", [])

    st.markdown('</div>', unsafe_allow_html=True)

    # Show results + exports
    if mcq_blocks:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        qn = 1
        for bi, block in enumerate(mcq_blocks, 1):
            st.markdown(f"**Block {bi}**")
            for q in block:
                st.write(f"**{qn}.** {q['question']}")
                for i, opt in enumerate(q["options"]):
                    st.write(f" &nbsp;&nbsp;&nbsp; **{'ABCD'[i]}.** {opt}")
                st.caption(f"Answer: **{q['answer']}**")
                qn += 1
            st.divider()
        # Exports
        colA, colB = st.columns(2)
        with colA:
            docx_bytes = export_docx(mcq_blocks, [], title=f"MCQ Paper — Week {week} Lesson {lesson}")
            st.download_button("⬇️ Download MCQ Paper (.docx)", data=docx_bytes, file_name=f"mcq_paper_w{week}_l{lesson}.docx")
        with colB:
            gift_bytes = export_gift(mcq_blocks)
            st.download_button("⬇️ Download Moodle GIFT (.gift)", data=gift_bytes, file_name=f"mcq_w{week}_l{lesson}.gift")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("Upload content or set blocks and click **Generate MCQ Blocks**.")

# ---------------- Activities Tab ----------------
with tabs[1]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    colL, colR = st.columns([2,2])
    with colL:
        count = st.number_input("Activities", min_value=1, max_value=20, value=3, step=1)
    with colR:
        duration = st.number_input("Duration per activity (mins)", min_value=5, max_value=180, value=45, step=5)

    with st.expander("Preferred action verbs", expanded=True):
        opts = sorted(set(DEFAULT_VERBS["Apply"] + DEFAULT_VERBS["Evaluate"] + DEFAULT_VERBS["Create"]))
        verbs_act = st.multiselect("Pick verbs", opts, default=["apply","demonstrate","evaluate","design"])
        st.session_state["verbs_act"] = verbs_act

    col1, col2 = st.columns([1,1])
    with col1:
        gen_act = st.button("✅ Generate Activities", use_container_width=True)
    with col2:
        regen_act = st.button("🔁 Regenerate Activities", use_container_width=True)

    if gen_act or regen_act:
        st.session_state["act_data"] = generate_activities(count, duration, st.session_state.get("verbs_act", []), src_text)

    activities = st.session_state.get("act_data", [])
    st.markdown('</div>', unsafe_allow_html=True)

    if activities:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        for i, a in enumerate(activities, 1):
            st.write(f"**{i}.** {a}")
        # Export activities + answers (empty answer key here since activities are open-ended)
        pack = export_docx([], activities, title=f"Activities — Week {week} Lesson {lesson}")
        st.download_button("⬇️ Download Activities (.docx)", data=pack, file_name=f"activities_w{week}_l{lesson}.docx")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("Pick count/duration and verbs, then **Generate Activities**.")

# ---------------- Revision Tab ----------------
with tabs[2]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    src_override = st.text_area("Source text (editable)", value=src_text, height=160, help="Paste key concepts or summaries here.")
    topic = st.text_input("Topic / Unit title", value="Module / Unit")
    if st.button("📘 Build revision plan"):
        st.session_state["rev_plan"] = build_revision_plan(src_override, week, lesson)
    plan = st.session_state.get("rev_plan", [])
    st.markdown('</div>', unsafe_allow_html=True)

    if plan:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.write(f"### Revision outline — {topic}")
        for item in plan:
            st.write(f"- {item}")
        # Export to DOCX
        if DocxDocument is not None:
            doc = DocxDocument()
            doc.add_heading(f"Revision — {topic}", 0)
            for item in plan:
                doc.add_paragraph(item)
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("⬇️ Download Revision (.docx)", data=buf.getvalue(), file_name=f"revision_w{week}_l{lesson}.docx")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("Paste or upload content, then click **Build revision plan**.")

# Footer
st.write(" ")
st.caption("v2.5.6 • Built for ADI • Exports: DOCX & GIFT • Upload size ≤ 200MB")
