import io
import re
import random
from datetime import date

import streamlit as st

# File parsers
import fitz  # PyMuPDF (PDF)
from pptx import Presentation  # python-pptx
from docx import Document  # python-docx
from docx.shared import Pt

# =========================
# THEME & GLOBAL CSS
# =========================

st.set_page_config(
    page_title="ADI Builder",
    page_icon="🧩",
    layout="wide"
)

# ---- ADI palette (tweak if you need) ----
ADI_GREEN = "#15563d"
ADI_GREEN_TINT = "rgba(21, 86, 61, .08)"
ADI_BEIGE = "#b79e82"           # accents
ADI_SAND = "#efeae3"            # page background tint
CARD_BG = "#ffffff"

CUSTOM_CSS = f"""
<style>
:root {{
  --adi-green: {ADI_GREEN};
  --adi-beige: {ADI_BEIGE};
  --adi-sand: {ADI_SAND};
}}

html, body, [data-testid="stAppViewContainer"] {{
  background: linear-gradient(180deg, #fbfbfb 0%, var(--adi-sand) 100%) !important;
}}

section.main > div:first-child {{
  padding-top: 8px !important;
}}

/* Headings */
h1, h2, h3 {{
  letter-spacing: .2px;
}}

h1 {{
  font-size: 2.15rem !important;
  font-weight: 800 !important;
  color: var(--adi-green) !important;
}}

h2 {{
  font-size: 1.35rem !important;
  font-weight: 700 !important;
  color: #1c2a28 !important;
  margin-top: .2rem !important;
  border-left: 6px solid var(--adi-green);
  padding-left: .5rem;
}}

/* Cards */
.adi-card {{
  background: {CARD_BG};
  border: 1px solid #e8e2d9;
  box-shadow: 0 8px 24px rgba(21, 86, 61, .06);
  border-radius: 14px;
  padding: 18px 18px 10px 18px;
  margin-bottom: 14px;
}}

/* Tabs active underline = ADI green line */
[data-baseweb="tab-list"] > div[aria-selected="true"]::after {{
  background-color: var(--adi-green) !important;
  height: 3px !important;
}}

/* Inputs: subtle beige borders + focus */
.adi-field > div > div > input,
.adi-field > div[data-baseweb="select"] > div {{
  border: 1px solid #ccbca9 !important;
  border-radius: 12px !important;
}}

.adi-field:focus-within * {{
  box-shadow: 0 0 0 3px {ADI_GREEN_TINT} !important;
  border-color: var(--adi-green) !important;
}}

/* Result panels */
.adi-panel {{
  border: 1px solid #ccbca9;
  border-left: 6px solid var(--adi-green);
  background: #fff;
  border-radius: 12px;
  padding: 14px;
}}

/* The green guideline line beneath the section title */
.adi-line {{
  height: 3px;
  width: 100%;
  background: var(--adi-green);
  border-radius: 2px;
  margin: 8px 0 14px 0;
}}

/* ---- FILE UPLOADER OUTLINE (robust across Streamlit versions) ---- */

/* Newer Streamlit builds */
div[data-testid="stFileUploadDropzone"]{{
  border:2px dashed var(--adi-green) !important;
  border-radius:12px !important;
  background:#fff !important;
}}

/* Some builds wrap the dropzone; hit the first child of the uploader */
section[data-testid="stFileUploader"] > div:first-child{{
  border:2px dashed var(--adi-green) !important;
  border-radius:12px !important;
  background:#fff !important;
}}

/* Older fallback (baseweb dropzone) */
div[data-baseweb="dropzone"]{{
  border:2px dashed var(--adi-green) !important;
  border-radius:12px !important;
  background:#fff !important;
}}

div[data-testid="stFileUploadDropzone"]:hover,
section[data-testid="stFileUploader"] > div:first-child:hover,
div[data-baseweb="dropzone"]:hover{{
  box-shadow:0 0 0 4px rgba(21,86,61,.12) !important;
}}

/* Buttons */
.stButton>button {{
  background: var(--adi-green) !important;
  color:#fff !important;
  border: 1px solid var(--adi-green) !important;
  border-radius: 12px !important;
  padding: .6rem 1.1rem !important;
  font-weight: 600;
}}
.stButton>button:hover {{
  filter: brightness(.95);
}}

.small-note {{
  color:#67716c;
  font-size:.9rem;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =========================
# HELPERS: TEXT EXTRACTION
# =========================

def extract_text_from_pdf(file) -> str:
    text = []
    with fitz.open(stream=file.read(), filetype="pdf") as pdf:
        for page in pdf:
            text.append(page.get_text("text"))
    return "\n".join(text)

def extract_text_from_docx(file) -> str:
    data = file.read()
    bio = io.BytesIO(data)
    doc = Document(bio)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_pptx(file) -> str:
    data = file.read()
    prs = Presentation(io.BytesIO(data))
    slides = []
    for idx, slide in enumerate(prs.slides, start=1):
        bits = []
        for shp in slide.shapes:
            if hasattr(shp, "text"):
                bits.append(shp.text)
        if bits:
            slides.append(f"Slide {idx}: " + " ".join(bits))
    return "\n".join(slides)

def extract_text_from_upload(uploaded) -> str:
    if uploaded is None:
        return ""
    name = uploaded.name.lower()
    if name.endswith(".pdf"):
        uploaded.seek(0)
        return extract_text_from_pdf(uploaded)
    if name.endswith(".docx"):
        uploaded.seek(0)
        return extract_text_from_docx(uploaded)
    if name.endswith(".pptx"):
        uploaded.seek(0)
        return extract_text_from_pptx(uploaded)
    return ""

# =========================
# KNOWLEDGE GENERATION
# =========================

BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]

DEFAULT_VERBS = {
    "Remember": ["define", "list", "recall", "state"],
    "Understand": ["explain", "summarise", "describe", "classify"],
    "Apply": ["demonstrate", "use", "illustrate", "solve"],
    "Analyze": ["differentiate", "compare", "contrast", "categorise"],
    "Evaluate": ["justify", "critique", "assess", "recommend"],
    "Create": ["design", "develop", "compose", "produce"]
}

FORBIDDEN_STEMS = ["all of the above", "none of the above", "true or false", "true/false", "true - false", "true false"]

def clean_topic(txt: str) -> str:
    # Simple squeeze
    return re.sub(r"\s+", " ", txt).strip()

def guess_topics(raw_text: str, max_topics: int = 10) -> list[str]:
    """
    Pulls likely 'topics' from headings/slide labels; falls back to sentences.
    """
    if not raw_text.strip():
        return []

    # Prefer "Slide X:" or headings
    candidates = re.findall(r"(?:^|\n)(?:Slide\s*\d+:|\s*#{1,3}\s*)(.*)", raw_text)
    if not candidates:
        # split by sentences as fallback
        candidates = re.split(r"[\.\n]{1,2}", raw_text)

    # Clean and keep mid-length fragments
    topics = [t for t in (clean_topic(c) for c in candidates) if 6 <= len(t.split()) <= 18]
    # De-dup preserve order
    seen = set()
    uniq = []
    for t in topics:
        key = t.lower()
        if key not in seen:
            uniq.append(t)
            seen.add(key)
        if len(uniq) >= max_topics:
            break
    return uniq or [clean_topic(raw_text)[:160] + ("..." if len(raw_text) > 160 else "")]

def safe_options(stem: str) -> list[str]:
    """
    Make four options, avoid forbidden patterns & duplicates.
    """
    # A very light distractor generator: split key nouns/verbs into variants
    base = re.sub(r"[^a-z0-9\s-]", "", stem.lower())
    tokens = [t for t in base.split() if len(t) > 3][:5]
    pool = set()
    for t in tokens:
        pool.update([f"{t} process", f"{t} concept", f"{t} example", f"not {t}", f"{t} step"])
    pool = [p for p in pool if not any(bad in p for bad in FORBIDDEN_STEMS)]

    random.shuffle(pool)
    distractors = []
    for p in pool:
        if len(distractors) >= 3:
            break
        if p not in distractors:
            distractors.append(p)

    if len(distractors) < 3:
        distractors += [f"unrelated factor {i}" for i in range(3 - len(distractors))]

    correct = f"Defines key elements and criteria for {stem.rstrip('?')}."
    correct = re.sub(r"\s+", " ", correct).strip()

    options = distractors + [correct]
    random.shuffle(options)
    return options

def make_mcq(stem: str, level: str, verb: str) -> dict:
    # build a crisp stem and enforce verb
    stem_txt = f"Q. {verb.capitalize()} the key points of: {stem.rstrip('.')}"
    opts = safe_options(stem)
    # ensure one looks answer-like
    if not any("Defines key elements and criteria" in o for o in opts):
        opts[0] = f"Defines key elements and criteria for {stem.rstrip('?')}."
    correct_idx = [i for i, o in enumerate(opts) if "Defines key elements and criteria" in o]
    ans_letter = "abcd"[correct_idx[0]] if correct_idx else "a"
    return {
        "stem": stem_txt,
        "level": level,
        "verb": verb,
        "options": opts,
        "answer": ans_letter
    }

def generate_mcqs(
    raw_text: str,
    selected_levels: list[str],
    verbs_map: dict[str, list[str]],
    total_q: int,
    auto_verbs: bool,
    level_mix: bool
) -> list[dict]:
    topics = guess_topics(raw_text, max_topics=20)
    if not topics:
        return []

    # Build cycle for levels
    if not selected_levels:
        selected_levels = ["Apply"]

    if level_mix:
        levels_seq = [random.choice(selected_levels) for _ in range(total_q)]
    else:
        # keep the first selected (or Apply) for all
        levels_seq = [selected_levels[0]] * total_q

    mcqs = []
    used_pairs = set()
    ti = 0

    for i in range(total_q):
        level = levels_seq[i]

        if auto_verbs:
            # pick a verb at random for that level
            verb = random.choice(DEFAULT_VERBS.get(level, ["explain"]))
        else:
            custom = verbs_map.get(level) or []
            # fallback to default if user left it empty
            pool = custom or DEFAULT_VERBS.get(level, ["explain"])
            verb = random.choice(pool)

        # ensure variety (level+verb)
        tries = 0
        while (level, verb) in used_pairs and tries < 5:
            tries += 1
            if auto_verbs:
                verb = random.choice(DEFAULT_VERBS.get(level, ["explain"]))
            else:
                pool = (verbs_map.get(level) or DEFAULT_VERBS.get(level, ["explain"]))
                verb = random.choice(pool)
        used_pairs.add((level, verb))

        topic = topics[ti % len(topics)]
        ti += 1

        q = make_mcq(topic, level, verb)
        # Final safety filter
        if any(bad in q["stem"].lower() for bad in FORBIDDEN_STEMS):
            continue
        if any(bad in " ".join(q["options"]).lower() for bad in FORBIDDEN_STEMS):
            continue
        mcqs.append(q)

    return mcqs[:total_q]

def mcqs_to_txt(mcqs: list[dict]) -> str:
    out = []
    for i, q in enumerate(mcqs, start=1):
        letters = ["a", "b", "c", "d"]
        out.append(f"Q{i}. {q['stem']}")
        for j, opt in enumerate(q["options"]):
            out.append(f"  {letters[j]}) {opt}")
        out.append(f"Correct: {q['answer']}")
        out.append("")
    return "\n".join(out).strip()

def write_mcqs_docx(mcqs: list[dict], header: str = "ADI Knowledge MCQs") -> bytes:
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    h = doc.add_paragraph()
    run = h.add_run(header)
    run.bold = True
    run.font.size = Pt(14)

    for i, q in enumerate(mcqs, start=1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        letters = ["a", "b", "c", "d"]
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{letters[j]}) {opt}", style=None)
        doc.add_paragraph(f"Correct: {q['answer']}")
        doc.add_paragraph("")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# =========================
# SKILLS ACTIVITIES
# =========================

ACTIVITY_TEMPLATES = [
    "Paired practice: In pairs, {verb} a worked example drawn from this lesson, then swap and peer-review using the success criteria.",
    "Small-group task: In groups of 3–4, {verb} a short procedure/checklist and rehearse it once. Capture one improvement you would make.",
    "Hands-on mini-lab: Individually, {verb} a quick practical based on Slide/Section '{topic}'. Record one risk and a mitigation.",
    "Coach & perform: One explains, one performs, one observes. Rotate roles after each cycle to {verb} the target skill.",
    "Gallery walk: Produce a concise A4 artefact (diagram, flow or pseudo-steps) to {verb} the process. Display, compare and refine."
]

def generate_activities(raw_text: str, n: int, minutes: int, verbs_pool: list[str]) -> list[str]:
    topics = guess_topics(raw_text, max_topics=10)
    out = []
    for i in range(n):
        topic = topics[i % len(topics)]
        tpl = random.choice(ACTIVITY_TEMPLATES)
        verb = random.choice(verbs_pool)
        brief = tpl.format(topic=topic, verb=verb)
        out.append(f"{i+1}. ({minutes} min) {brief}")
    return out

def write_activities_docx(activities: list[str], header: str = "ADI Skills Activities") -> bytes:
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    h = doc.add_paragraph()
    run = h.add_run(header)
    run.bold = True
    run.font.size = Pt(14)

    for a in activities:
        doc.add_paragraph(a)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# =========================
# UI
# =========================

st.markdown("## ADI Builder")
st.caption("Create staff-ready knowledge questions and skills activities in minutes.")

with st.container():
    colL, colR = st.columns([1, 1])

    with colL:
        st.markdown("#### Upload PDF / DOCX / PPTX")
        uploaded = st.file_uploader(
            "Drag and drop file here",
            type=["pdf", "docx", "pptx"],
            label_visibility="collapsed"
        )
        st.markdown('<div class="small-note">Limit 200MB per file • PDF, DOCX, PPTX</div>', unsafe_allow_html=True)

    with colR:
        st.markdown("#### Schedule")
        week = st.selectbox("Week", list(range(1, 15)), index=0, key="week", help="Weeks 1–14")
        lesson = st.selectbox("Lesson", list(range(1, 5)), index=0, key="lesson", help="Lesson 1–4")
        st.caption(f"Date: {date.today().isoformat()}")

# Optional paste content
with st.expander("No file? Paste some source text here"):
    pasted = st.text_area("Paste lesson/eBook text (optional)", height=160)

st.markdown('<div class="adi-line"></div>', unsafe_allow_html=True)

tab_mcq, tab_act = st.tabs(["Knowledge MCQs", "Skills Activities"])

# ------------- Knowledge MCQs Tab -------------
with tab_mcq:
    st.markdown("### Knowledge MCQs")
    st.markdown('<div class="adi-line"></div>', unsafe_allow_html=True)

    level_cols = st.columns([3, 2, 2, 2])
    with level_cols[0]:
        chosen_levels = st.multiselect(
            "Bloom’s levels",
            BLOOM_LEVELS,
            default=["Understand", "Apply", "Analyze"],
            key="levels",
            help="Select one or more levels"
        )

    with level_cols[1]:
        auto_verbs = st.checkbox("Auto-select verbs (balanced)", value=True, key="auto_verbs")

    with level_cols[2]:
        level_mix = st.checkbox("Level mix", value=False, help="If on, each question can use a different level.")

    with level_cols[3]:
        total_q = st.slider("Total MCQs (5–10)", 5, 10, 6, key="total_q")

    # Verb pickers (only when auto is OFF)
    user_verbs: dict[str, list[str]] = {}
    if not auto_verbs:
        st.markdown("#### Verbs by level")
        for lev in chosen_levels or ["Apply"]:
            default_list = DEFAULT_VERBS.get(lev, [])
            verbs = st.multiselect(
                f"Verbs for {lev}",
                sorted(set(default_list + ["outline", "identify", "map", "illustrate"])),
                default=default_list[:2],
                key=f"verbs_{lev}"
            )
            user_verbs[lev] = verbs

    st.markdown("#### Generate")
    mcq_button = st.button("Generate MCQs", type="primary")

    if mcq_button:
        # Source text priority: uploaded > pasted
        raw_text = extract_text_from_upload(uploaded) if uploaded else pasted
        if not raw_text.strip():
            st.warning("Please upload a file or paste some source text.")
        else:
            mcqs = generate_mcqs(
                raw_text=raw_text,
                selected_levels=chosen_levels or ["Apply"],
                verbs_map=user_verbs,
                total_q=total_q,
                auto_verbs=auto_verbs,
                level_mix=level_mix
            )
            if not mcqs:
                st.info("No questions generated. Try different levels or provide more text.")
            else:
                txt = mcqs_to_txt(mcqs)
                st.markdown("##### Preview / Edit")
                st.text_area("You can edit before exporting:", txt, height=280, key="mcq_preview")

                colA, colB = st.columns(2)
                with colA:
                    st.download_button(
                        "Download TXT",
                        data=txt.encode("utf-8"),
                        file_name=f"ADI_MCQs_Week{week}_Lesson{lesson}.txt",
                        mime="text/plain"
                    )
                with colB:
                    doc_bytes = write_mcqs_docx(mcqs, header=f"ADI Knowledge MCQs (Week {week}, Lesson {lesson})")
                    st.download_button(
                        "Download DOCX",
                        data=doc_bytes,
                        file_name=f"ADI_MCQs_Week{week}_Lesson{lesson}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

# ------------- Skills Activities Tab -------------
with tab_act:
    st.markdown("### Skills Activities")
    st.markdown('<div class="adi-line"></div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns([2, 2, 2])
    with a1:
        act_count = st.slider("Number of activities", 1, 4, 2)
    with a2:
        duration = st.selectbox("Activity duration", list(range(10, 65, 5)), index=2, help="10–60 min")
    with a3:
        act_verbs = st.multiselect(
            "Action verbs",
            sorted(set(DEFAULT_VERBS["Apply"] + ["practice", "rehearse", "perform", "prototype"])),
            default=["demonstrate", "use", "practice"]
        )

    act_btn = st.button("Generate activities", type="primary")

    if act_btn:
        raw_text = extract_text_from_upload(uploaded) if uploaded else pasted
        if not raw_text.strip():
            st.warning("Please upload a file or paste some source text.")
        else:
            activities = generate_activities(raw_text, n=act_count, minutes=duration, verbs_pool=act_verbs or ["demonstrate"])
            st.markdown("##### Preview / Edit")
            act_txt = "\n".join(activities)
            st.text_area("You can edit before exporting:", act_txt, height=220, key="act_preview")

            colC, colD = st.columns(2)
            with colC:
                st.download_button(
                    "Download TXT",
                    data=act_txt.encode("utf-8"),
                    file_name=f"ADI_Activities_Week{week}_Lesson{lesson}.txt",
                    mime="text/plain"
                )
            with colD:
                doc_bytes = write_activities_docx(activities, header=f"ADI Skills Activities (Week {week}, Lesson {lesson})")
                st.download_button(
                    "Download DOCX",
                    data=doc_bytes,
                    file_name=f"ADI_Activities_Week{week}_Lesson{lesson}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# Footer
st.markdown(
    f"""
<div class="small-note" style="margin-top:12px;">
<strong>Status:</strong> Ready · Week <em>{week}</em>, Lesson <em>{lesson}</em>.
</div>
""",
    unsafe_allow_html=True
)
