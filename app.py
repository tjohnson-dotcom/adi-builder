import streamlit as st
import random
import re
from io import BytesIO

# Optional dependencies (we guard in try/except so the app still runs if missing)
try:
    import fitz  # PyMuPDF for PDF
except Exception:
    fitz = None

try:
    from docx import Document  # python-docx
except Exception:
    Document = None

try:
    from pptx import Presentation  # python-pptx
except Exception:
    Presentation = None


# -------------------------------
#   THEME / CSS  (ADI style)
# -------------------------------
CUSTOM_CSS = """
<style>
    .block-container {padding-top:2rem; padding-bottom:2rem; max-width:1040px;}
    h1, h2, h3 {color:#004d40; font-weight:800;}
    .subtle {color:#5f6b6b;}
    .stTabs [data-baseweb="tab"] p {font-weight: 700;}
    .stSelectbox, .stMultiSelect, .stTextInput, .stNumberInput {font-size:1rem;}
    .stSlider {padding-top:.25rem;}
    .stButton>button {
        background:#004d40; color:white; font-weight:700;
        border-radius:10px; padding:.65rem 1.2rem; border:0;
    }
    .stButton>button:hover {background:#00695c;}
    .pill {
        display:inline-block; background:#e8f5e9; color:#004d40;
        border:1px solid #b2dfdb; border-radius:999px; padding:.25rem .7rem;
        font-size:.85rem; margin-left:.5rem;
    }
    .card {
        border:1px solid #e0e0e0; border-radius:12px; padding:1rem 1rem .75rem 1rem; background:#fff;
        box-shadow: 0 2px 6px rgba(0,0,0,.03);
    }
    .muted {color:#6f7a7a}
    .tiny {font-size:.9rem}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------
#   BLOOM LEVELS & VERBS
# -------------------------------
BLOOMS = {
    "Remember":   ["define", "list", "recall", "state", "identify"],
    "Understand": ["explain", "summarize", "describe", "classify", "discuss"],
    "Apply":      ["apply", "demonstrate", "use", "illustrate", "practice"],
    "Analyse":    ["analyze", "compare", "differentiate", "categorize", "examine"],
    "Evaluate":   ["evaluate", "justify", "critique", "assess", "defend"],
    "Create":     ["design", "compose", "construct", "propose", "develop"]
}

LEVEL_ORDER = list(BLOOMS.keys())


# -------------------------------
#   FILE PARSING
# -------------------------------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not fitz:
        return ""
    text = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text.append(page.get_text("text"))
    return "\n".join(text)


def extract_text_from_docx(file_bytes: bytes) -> str:
    if not Document:
        return ""
    bio = BytesIO(file_bytes)
    doc = Document(bio)
    parts = []
    for p in doc.paragraphs:
        parts.append(p.text)
    # include table text if present
    for t in doc.tables:
        for row in t.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def extract_text_from_pptx(file_bytes: bytes) -> str:
    if not Presentation:
        return ""
    bio = BytesIO(file_bytes)
    prs = Presentation(bio)
    parts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                parts.append(shape.text)
    return "\n".join(parts)


def extract_text(uploaded_file) -> str:
    """Return plain text from uploaded file; fallback to empty string if unknown."""
    if not uploaded_file:
        return ""
    data = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(data)
    if name.endswith(".docx"):
        return extract_text_from_docx(data)
    if name.endswith(".pptx"):
        return extract_text_from_pptx(data)
    return ""


# -------------------------------
#   TOPIC CARVING
# -------------------------------
def carve_topics(raw_text: str, want: int = 10) -> list[str]:
    """
    Split into lines, keep reasonable sized items, and pick 'want' topics.
    """
    lines = [re.sub(r"\s+", " ", L).strip() for L in raw_text.splitlines()]
    lines = [L for L in lines if 6 <= len(L) <= 160]  # filter tiny/huge lines
    # de-duplicate while preserving order
    seen = set()
    filt = []
    for L in lines:
        key = L.lower()
        if key not in seen:
            seen.add(key)
            filt.append(L)
    random.shuffle(filt)
    if not filt:
        # fallback placeholders if nothing parsed
        filt = [f"Topic {i}" for i in range(1, 50)]
    return filt[:want]


# -------------------------------
#   MCQ GENERATION
# -------------------------------
FORBIDDEN_STRINGS = {"all of the above", "none of the above", "true", "false"}

def clean_option(opt: str) -> str:
    s = opt.strip()
    for bad in FORBIDDEN_STRINGS:
        s = re.sub(rf"\b{re.escape(bad)}\b", "", s, flags=re.I)
    return re.sub(r"\s{2,}", " ", s).strip() or "—"


def build_mcq(topic: str, verb: str, distractor_pool: list[str]) -> dict:
    stem = f"In one sentence, {verb} the key idea: **{topic}**."
    correct = f"A concise {verb} of: {topic}"
    wrong = random.sample(distractor_pool, k=min(3, len(distractor_pool))) if distractor_pool else [
        "Irrelevant personal example",
        "Unrelated motivational quote",
        "List of unused resources"
    ]
    options = [correct] + wrong
    options = [clean_option(o) for o in options]
    random.shuffle(options)
    letters = "abcd"
    return {
        "stem": stem,
        "options": options,
        "correct": letters[options.index(clean_option(correct))]
    }


def export_docx_mcqs(mcqs: list[dict], title: str) -> bytes | None:
    if not Document:
        return None
    doc = Document()
    doc.add_heading(title, 1)
    letters = "abcd"
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{letters[j]}) {opt}", style="List Bullet")
        doc.add_paragraph(f"Correct: {q['correct']}")
        doc.add_paragraph("")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()


# -------------------------------
#   SKILLS ACTIVITY GENERATION
# -------------------------------
ACTIVITY_TEMPLATES = [
    # name, brief, structure
    ("Guided Practice",
     "Individually complete a short, authentic task linked to today’s lesson.",
     ["Read the brief and success criteria.",
      "Complete the task step-by-step.",
      "Self-check using the checklist.",
      "Submit work for quick feedback."]),
    ("Pair & Share",
     "Work in pairs to apply knowledge and explain your decisions.",
     ["In pairs, agree roles (Speaker / Notetaker).",
      "Discuss the prompt and capture key points.",
      "Swap roles and refine answers.",
      "Share your final points with another pair."]),
    ("Mini Case",
     "Analyse a short scenario and recommend actions.",
     ["Read the case and highlight key facts.",
      "Identify risks/constraints.",
      "Recommend two actions and justify them.",
      "Prepare a 60-second summary."]),
    ("Procedure Drill",
     "Follow a procedure safely and accurately.",
     ["Review the SOP steps.",
      "Perform steps in order.",
      "Record any deviations.",
      "Reflect: what would you improve?"]),
    ("Reflect & Improve",
     "Evaluate your output and plan a small improvement.",
     ["Compare against success criteria.",
      "Identify one strength and one area to improve.",
      "Write a short improvement plan.",
      "Share one insight with the group."])
]

def activity_outcome(level: str, verbs: list[str], topic: str) -> str:
    v = random.choice(verbs) if verbs else "apply"
    out_map = {
        "Remember":   f"Identify and {v} key facts about {topic}.",
        "Understand": f"{v.capitalize()} main ideas and explain their relevance to {topic}.",
        "Apply":      f"{v.capitalize()} the concept in a practical task related to {topic}.",
        "Analyse":    f"{v.capitalize()} components and relationships within {topic}.",
        "Evaluate":   f"{v.capitalize()} options and justify decisions for {topic}.",
        "Create":     f"{v.capitalize()} a clear output or solution based on {topic}."
    }
    return out_map.get(level, f"{v.capitalize()} core ideas about {topic}.")

def build_activity(level: str, verbs: list[str], topic: str) -> dict:
    name, brief, steps = random.choice(ACTIVITY_TEMPLATES)
    outcome = activity_outcome(level, verbs, topic)
    resources = ["Lesson slides or eBook extract", "Worksheet or template", "Marker/pen"]
    assess = ["Tutor walk-by check", "Peer two-stars-and-a-wish", "Self checklist"]
    return {
        "title": f"{name} — {level}",
        "brief": f"{brief} (Topic: {topic})",
        "outcome": outcome,
        "steps": steps,
        "resources": resources,
        "assessment": random.choice(assess),
        "timing_min": random.choice([10, 12, 15])
    }

def export_docx_activities(acts: list[dict], title: str) -> bytes | None:
    if not Document:
        return None
    doc = Document()
    doc.add_heading(title, 1)
    for i, a in enumerate(acts, 1):
        doc.add_heading(f"Activity {i}: {a['title']}", level=2)
        doc.add_paragraph(a["brief"])
        doc.add_paragraph(f"**Outcome:** {a['outcome']}")
        doc.add_paragraph("**Steps:**")
        for s in a["steps"]:
            doc.add_paragraph(s, style="List Number")
        doc.add_paragraph("**Resources:**")
        for r in a["resources"]:
            doc.add_paragraph(r, style="List Bullet")
        doc.add_paragraph(f"**Assessment:** {a['assessment']}")
        doc.add_paragraph(f"**Timing:** ~{a['timing_min']} minutes")
        doc.add_paragraph("")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()


# -------------------------------
#   PAGE HEADER
# -------------------------------
st.title("📘 ADI Builder")
st.caption("A clean, staff-friendly tool to create **knowledge MCQs** and **skills activities** in minutes.")


# -------------------------------
#   UPLOAD + SCHEDULE
# -------------------------------
with st.container():
    st.subheader("1) Upload lesson / eBook")
    uploaded = st.file_uploader("Drag & drop (PDF, DOCX, PPTX)", type=["pdf", "docx", "pptx"])
    st.markdown('<span class="tiny muted">Limit ~200MB per file. If no file, you can still type/paste a short topic below.</span>', unsafe_allow_html=True)

st.subheader("2) Schedule")
c1, c2, c3 = st.columns([1,1,2])
with c1:
    week = st.selectbox("Week (1–14)", list(range(1, 15)), index=0)
with c2:
    lesson = st.selectbox("Lesson (1–4)", list(range(1, 5)), index=0)
with c3:
    manual_topic = st.text_input("Optional: custom topic line (overrides parsing)", placeholder="e.g., Project charter purpose and contents")

# parse file text (lazy; only when needed)
parsed_cache = {"text": None}


# -------------------------------
#   MODE TABS
# -------------------------------
tab_mcq, tab_skills = st.tabs(["🧠 Knowledge MCQs", "🛠️ Skills Activities"])

# ====== MCQ TAB ======
with tab_mcq:
    st.subheader("Generate Crisp, Staff-Ready MCQs")
    st.markdown('<div class="tiny muted">No “all of the above”, “true/false”, or vague distractors. Download as DOCX.</div>', unsafe_allow_html=True)

    mix_levels = st.checkbox("Mix Bloom’s levels automatically", value=True)
    if mix_levels:
        level_list = LEVEL_ORDER[:]  # all
    else:
        level_list = [st.selectbox("Bloom’s Level", LEVEL_ORDER, index=2)]

    chosen_verbs = []
    with st.expander("Bloom’s verbs (choose per level)", expanded=not mix_levels):
        for lvl in level_list:
            default = BLOOMS[lvl][:1] if not mix_levels else BLOOMS[lvl][:2]
            verbs = st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=default, key=f"verbs_{lvl}_mcq")
            chosen_verbs.extend(verbs)

    total_qs = st.slider("Total MCQs", 5, 10, 6)

    if st.button("Generate MCQs"):
        # get text (once)
        if parsed_cache["text"] is None:
            parsed_cache["text"] = extract_text(uploaded) if uploaded else ""
        base_text = parsed_cache["text"]

        # topics
        topics = carve_topics(manual_topic or base_text, want=total_qs)

        # if user gave no verbs (edge), pick defaults
        if not chosen_verbs:
            chosen_verbs = sum(BLOOMS.values(), [])

        distractor_pool = [
            "Unrelated quote", "Off-topic statistic", "Vague reflection", "Overly broad claim"
        ]

        mcqs = []
        for t in topics:
            vrb = random.choice(chosen_verbs)
            mcqs.append(build_mcq(t, vrb, distractor_pool))

        # Show
        letters = "abcd"
        for i, q in enumerate(mcqs, 1):
            st.markdown(f"**Q{i}.** {q['stem']}")
            for j, opt in enumerate(q["options"]):
                st.write(f"- {letters[j]}) {opt}")
            st.write(f"**Correct:** {q['correct']}")
            st.markdown("---")

        # Export
        docx = export_docx_mcqs(mcqs, f"ADI MCQs — Week {week}, Lesson {lesson}")
        if docx:
            st.download_button(
                "⬇ Download MCQs (DOCX)",
                data=docx,
                file_name=f"ADI_MCQs_Week{week}_Lesson{lesson}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.info("Install `python-docx` to enable DOCX export.")

# ====== SKILLS TAB ======
with tab_skills:
    st.subheader("Generate Skills Activities")
    st.markdown('<div class="tiny muted">Clear outcomes, numbered steps, simple resources and timing. Download as DOCX.</div>', unsafe_allow_html=True)

    mix_levels_s = st.checkbox("Mix Bloom’s levels automatically ", value=False, key="mix_s")
    if mix_levels_s:
        level_list_s = LEVEL_ORDER[:]
    else:
        level_list_s = [st.selectbox("Bloom’s Level", LEVEL_ORDER, index=2, key="lvl_s")]

    chosen_verbs_s = []
    with st.expander("Bloom’s verbs (choose per level)", expanded=not mix_levels_s):
        for lvl in level_list_s:
            default = BLOOMS[lvl][:1]
            verbs = st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=default, key=f"verbs_{lvl}_skills")
            chosen_verbs_s.extend(verbs)

    n_acts = st.slider("Number of activities", 1, 4, 2)

    if st.button("Generate Activities"):
        if parsed_cache["text"] is None:
            parsed_cache["text"] = extract_text(uploaded) if uploaded else ""
        base_text = parsed_cache["text"]

        topics = carve_topics(manual_topic or base_text, want=n_acts)

        if not chosen_verbs_s:
            chosen_verbs_s = sum(BLOOMS.values(), [])

        activities = []
        for idx in range(n_acts):
            topic = topics[idx % len(topics)]
            lvl   = level_list_s[idx % len(level_list_s)]
            # pick 1–2 verbs for flavour
            verbs = random.sample(chosen_verbs_s, k=min(2, len(chosen_verbs_s)))
            activities.append(build_activity(lvl, verbs, topic))

        # Show cards
        for i, a in enumerate(activities, 1):
            with st.container():
                st.markdown(f"### Activity {i}: {a['title']}")
                st.markdown(f"**Brief:** {a['brief']}")
                st.markdown(f"**Outcome:** {a['outcome']}")
                st.markdown("**Steps:**")
                for s in a["steps"]:
                    st.write(f"1. {s}")
                st.markdown("**Resources:**")
                st.write(", ".join(a["resources"]))
                st.markdown(f"**Assessment:** {a['assessment']} &nbsp;&nbsp; | &nbsp;&nbsp; **Timing:** ~{a['timing_min']} min")
                st.markdown("---")

        docx = export_docx_activities(activities, f"ADI Activities — Week {week}, Lesson {lesson}")
        if docx:
            st.download_button(
                "⬇ Download Activities (DOCX)",
                data=docx,
                file_name=f"ADI_Activities_Week{week}_Lesson{lesson}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.info("Install `python-docx` to enable DOCX export.")
