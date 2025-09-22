import streamlit as st
from pathlib import Path
import io
import random
import re

# Safe optional imports (PDF/DOCX/PPTX parsing)
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


# -------------------------------------------------------------------
# Page + Theme
# -------------------------------------------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="🧩", layout="wide")

BRAND  = "#15563d"   # ADI green
ACCENT = "#b79e82"   # beige
BG     = "#f7f8f7"   # light background

CUSTOM_CSS = f"""
<style>
:root {{
  --brand: {BRAND};
  --accent: {ACCENT};
  --bg: {BG};
  --ink: #1d252d;
}}

html, body, .stApp {{ background: var(--bg); color: var(--ink); }}

h1, h2, h3, h4 {{ color: var(--brand); font-weight: 800; letter-spacing: .2px; }}
h1 {{ font-size: 2.2rem; }}
h2 {{ font-size: 1.55rem; }}
h3 {{ font-size: 1.2rem; }}

.brandband {{
  margin: -1rem -1rem 1rem -1rem;
  padding: 22px 28px;
  background: linear-gradient(90deg, var(--brand), #0e3d2a 60%, var(--accent));
  color: #fff;
  border-bottom: 3px solid rgba(0,0,0,.06);
}}
.brandtitle {{ font-weight: 900; font-size: 1.8rem; line-height: 1.15; }}
.brandsub   {{ opacity:.95; font-weight:600; margin-top:.15rem; }}

.card {{
  background: #fff;
  border-radius: 16px;
  padding: 18px;
  border: 1px solid rgba(13,32,23,.06);
  box-shadow: 0 10px 24px rgba(0,0,0,.04);
  transition: transform .12s ease, box-shadow .12s ease;
}}
.card:hover {{ transform: translateY(-2px); box-shadow: 0 16px 32px rgba(0,0,0,.06); }}

.stButton>button {{
  background: var(--brand);
  color: #fff !important;
  font-weight: 700; letter-spacing: .3px;
  border-radius: 12px; border: 0;
  padding: .62rem 1.15rem;
  box-shadow: 0 6px 14px rgba(21,86,61,.18);
}}
.stButton>button:hover {{ filter: brightness(.96); transform: translateY(-1px); }}
.stButton>button:active {{ transform: translateY(0); }}

.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea textarea {{
  border-radius: 12px !important;
  border-color: rgba(13,32,23,.18) !important;
}}
.stSlider [data-baseweb="slider"]>div>div {{ background: var(--brand); }}
.stSlider [role="slider"] {{ box-shadow: 0 0 0 4px rgba(21,86,61,.15) !important; }}

.stTabs [data-baseweb="tab-list"] {{ gap:.25rem; }}
.stTabs [data-baseweb="tab"] {{
  font-weight: 700;
  border-radius: 10px 10px 0 0;
  padding: .6rem 1rem;
  background: #eef2ef;
  color: #14382a;
}}
.stTabs [aria-selected="true"] {{
  background: #fff !important; color: var(--brand) !important;
  border-bottom: 3px solid var(--accent);
}}

.small  {{ color:#5d6a6b; font-size:.86rem }}
.badge  {{
  display:inline-block; background: var(--accent); color:#fff;
  padding:.12rem .55rem; border-radius: 10px; font-size:.78rem; margin-left:.4rem;
}}
.divider {{ height: 1px; background: rgba(13,32,23,.08); margin: 12px 0; }}
.kpi {{ color:#41564b; font-size:.95rem; padding:.35rem .6rem; background:#eef2ef; border-radius:10px; display:inline-block; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="brandband">
      <div class="brandtitle">ADI Builder <span class="badge">v1.1</span></div>
      <div class="brandsub">Create crisp questions or skills activities from your lesson content.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

logo_path = Path(__file__).with_name("logo.png")
if logo_path.exists():
    cols = st.columns([1,3])
    with cols[0]:
        st.image(str(logo_path), width=120)
    with cols[1]:
        st.markdown(
            "<div class='card'><b>Status:</b> Ready · Drop a PDF/DOCX/PPTX or paste text, pick week & lesson, then generate.</div>",
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        "<div class='card'><b>Status:</b> Ready · Drop a PDF/DOCX/PPTX or paste text, pick week & lesson, then generate.</div>",
        unsafe_allow_html=True,
    )
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# -------------------------------------------------------------------
# Helpers: text extraction
# -------------------------------------------------------------------
def extract_text_from_pdf(file) -> str:
    if not fitz:
        return ""
    text = []
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text.append(page.get_text("text"))
    return "\n".join(text)


def extract_text_from_docx(file) -> str:
    if not DocxDocument:
        return ""
    bio = io.BytesIO(file.read())
    doc = DocxDocument(bio)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_from_pptx(file) -> str:
    if not Presentation:
        return ""
    bio = io.BytesIO(file.read())
    prs = Presentation(bio)
    slides_text = []
    for slide in prs.slides:
        slide_buf = []
        for shp in slide.shapes:
            if hasattr(shp, "text"):
                t = (shp.text or "").strip()
                if t:
                    slide_buf.append(t)
        if slide_buf:
            slides_text.append("\n".join(slide_buf))
    return "\n\n".join(slides_text)


def clean_and_segments(raw: str) -> list[str]:
    """Light cleanup and segment into short topic lines."""
    if not raw:
        return []
    # remove repeated spaces and normalize bullets
    raw = re.sub(r"[•·▪▶►]+", "-", raw)
    raw = re.sub(r"\s+", " ", raw)
    # split by headings / punctuation to get bite-sized "topics"
    parts = re.split(r"(?:\n|\. |\? |\! | - )", raw)
    # keep only medium-length lines with letters
    topics = [p.strip() for p in parts if 6 <= len(p.strip()) <= 110 and re.search(r"[A-Za-z]", p)]
    # deduplicate (preserve order)
    seen = set()
    uniq = []
    for t in topics:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            uniq.append(t)
    return uniq[:120]  # safety cap


# -------------------------------------------------------------------
# Simple generation utilities
# -------------------------------------------------------------------
BLOOMS = {
    "Remember":   ["define", "list", "recall", "state", "identify"],
    "Understand": ["explain", "summarise", "describe", "classify", "illustrate"],
    "Apply":      ["demonstrate", "use", "solve", "implement", "show how"],
    "Analyse":    ["compare", "contrast", "differentiate", "categorise", "break down"],
    "Evaluate":   ["judge", "critique", "assess", "recommend", "prioritise"],
    "Create":     ["design", "develop", "construct", "propose", "draft"],
}

FORBIDDEN = {"all of the above", "none of the above", "true", "false", "both a and b"}

def carve_topics(text_segments: list[str], want: int) -> list[str]:
    """Pick concise distinct topics from extracted lines."""
    if not text_segments:
        return []
    base = [t for t in text_segments if len(t.split()) <= 14]
    pool = base or text_segments
    random.shuffle(pool)
    picked = []
    seen = set()
    for t in pool:
        key = re.sub(r"[^a-z0-9]+", "", t.lower())
        if key not in seen:
            seen.add(key)
            picked.append(t)
        if len(picked) >= want:
            break
    return picked


def build_mcq(topic: str, verb: str, bank: list[str]) -> dict:
    """Very crisp 1-sentence MCQ. No 'All of the above' / True/False."""
    stem = f"{verb.capitalize()} the key point about: {topic}"
    # Correct answer from the same topic (trimmed)
    correct = f"{verb.capitalize()}s {topic}".strip()
    # Distractors from other topics
    distractors = []
    random.shuffle(bank)
    for t in bank:
        if t != topic:
            distractors.append(f"{verb.capitalize()}s {t}".strip())
        if len(distractors) >= 3:
            break
    # If short pool, pad safe generics
    while len(distractors) < 3:
        distractors.append(f"{verb.capitalize()}s an unrelated concept")

    options = [correct] + distractors[:3]
    # ensure cleanliness
    filtered = []
    for opt in options:
        s = opt.strip().lower()
        if any(bad in s for bad in FORBIDDEN):
            s = "A plausible but incorrect statement"
        filtered.append(s.capitalize())
    options = filtered

    random.shuffle(options)
    correct_letter = "abcd"[options.index(next(o for o in options if o.startswith(verb.capitalize())))]
    return {"stem": stem, "options": options, "correct": correct_letter}


def build_activity(topic: str, week: int, lesson: int) -> dict:
    """Simple, clear activity brief focused on doing (skills)."""
    patterns = [
        ("Pair-Share Drill", [
            "Form pairs and assign roles: Speaker / Summariser.",
            f"Speaker explains '{topic}' in 60–90 seconds using real examples.",
            "Summariser repeats back the key steps and one improvement.",
            "Swap roles and repeat with a new mini-scenario.",
        ], "2 × 6 min"),
        ("Mini Case Walkthrough", [
            f"Give a short case that hinges on '{topic}'.",
            "Individually list 3 actions you would take and why.",
            "In groups of 3, agree the best two actions and risks.",
            "Share one recommendation per group.",
        ], "12–15 min"),
        ("Hands-on Checklist", [
            f"Demonstrate the steps of '{topic}' once, slowly.",
            "Learners perform the steps with a simple checklist (observer ticks).",
            "Rotate roles (doer / observer) and repeat with feedback.",
        ], "10–12 min"),
        ("Exit Ticket (Skills)", [
            f"Write one step of '{topic}' you can perform now, and one you need to practise.",
            "Hand in your ticket on the way out.",
        ], "3 min"),
    ]
    title, steps, time = random.choice(patterns)
    return {
        "title": f"{title} — Week {week}, Lesson {lesson}",
        "objective": f"Practise and perform the procedure/skill related to: {topic}",
        "materials": ["Whiteboard or slide", "Printed checklist or case blurb", "Pens"],
        "time": time,
        "steps": steps,
        "assessment": [
            "Quick instructor walk-around using the checklist",
            "One-minute verbal reflection per pair"
        ]
    }


def export_docx_mcqs(mcqs: list[dict], title: str) -> bytes:
    if not DocxDocument:
        return b""
    doc = DocxDocument()
    doc.add_heading(title, 1)
    letters = "abcd"
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{letters[j]}) {opt}", style=None).paragraph_format.left_indent = None
        doc.add_paragraph(f"Correct: {q['correct']}\n")
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def export_docx_activities(acts: list[dict], title: str) -> bytes:
    if not DocxDocument:
        return b""
    doc = DocxDocument()
    doc.add_heading(title, 1)
    for i, a in enumerate(acts, 1):
        doc.add_heading(f"{i}. {a['title']}", level=2)
        doc.add_paragraph(f"Objective: {a['objective']}")
        doc.add_paragraph(f"Time: {a['time']}")
        doc.add_paragraph("Materials: " + ", ".join(a['materials']))
        doc.add_paragraph("Steps:")
        for s in a["steps"]:
            doc.add_paragraph(f"• {s}")
        doc.add_paragraph("Quick check:")
        for c in a["assessment"]:
            doc.add_paragraph(f"• {c}")
        doc.add_paragraph("")
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


# -------------------------------------------------------------------
# UI: Upload / Schedule / Mode
# -------------------------------------------------------------------
c1, c2, c3 = st.columns([2,1,1])
with c1:
    st.subheader("1) Upload lesson / eBook (drag & drop)")
    upload = st.file_uploader("Drag and drop a file (PDF, DOCX, PPTX)", type=["pdf","docx","pptx"])
with c2:
    st.subheader("2) Schedule")
    week = st.selectbox("Week (1–14)", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson (1–4)", list(range(1,5)), index=0)
with c3:
    st.subheader("3) Mode")
    mode = st.selectbox("Choose what to build", ["Knowledge MCQs", "Skills Activities"])

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Optional paste area (useful if no file)
with st.expander("No file? Paste lesson text here (optional)"):
    pasted = st.text_area("Paste content", height=160, placeholder="Paste clean text, bullet points, or headings...")

# Extract text now (file has priority)
raw_text = ""
if upload is not None:
    ext = (upload.name.split(".")[-1] or "").lower()
    try:
        if ext == "pdf":
            raw_text = extract_text_from_pdf(upload)
        elif ext == "docx":
            raw_text = extract_text_from_docx(upload)
        elif ext == "pptx":
            raw_text = extract_text_from_pptx(upload)
        else:
            st.warning("Unsupported file type. Please upload PDF/DOCX/PPTX.")
    except Exception as e:
        st.error(f"Couldn't read file: {e}")

if not raw_text and pasted.strip():
    raw_text = pasted

segments = clean_and_segments(raw_text)

# Show a tiny summary
meta_cols = st.columns(3)
meta_cols[0].markdown(f"<span class='kpi'>Week {week} • Lesson {lesson}</span>", unsafe_allow_html=True)
meta_cols[1].markdown(f"<span class='kpi'>Segments detected: {len(segments)}</span>", unsafe_allow_html=True)
meta_cols[2].markdown(f"<span class='kpi'>Mode: {mode}</span>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# -------------------------------------------------------------------
# Mode: Knowledge MCQs
# -------------------------------------------------------------------
if mode == "Knowledge MCQs":
    st.subheader("MCQ Settings")
    cA, cB, cC = st.columns([1.2,1,1])
    with cA:
        blooms_level = st.selectbox("Bloom’s level", list(BLOOMS.keys()), index=2)
    with cB:
        total_mcqs = st.slider("Total MCQs (5–10)", 5, 10, 6)
    with cC:
        extra_verbs = st.text_input("Extra verbs (optional, comma-separated)")

    verbs = BLOOMS[blooms_level] + [v.strip() for v in extra_verbs.split(",") if v.strip()]
    verb = st.selectbox("Choose a Bloom’s verb", verbs, index=0)

    if st.button("Generate MCQs", type="primary", use_container_width=True):
        if not segments:
            st.warning("Please upload a lesson file or paste content.")
        else:
            topics = carve_topics(segments, want=total_mcqs * 3)
            if not topics:
                st.warning("Not enough clean topics found. Try pasting simpler text.")
            else:
                mcqs = []
                for i in range(min(total_mcqs, len(topics))):
                    mcqs.append(build_mcq(topics[i], verb, topics))

                st.success(f"Generated {len(mcqs)} MCQs (editable below).")
                letters = "abcd"
                text_out = []
                for i, q in enumerate(mcqs, 1):
                    st.markdown(f"**Q{i}. {q['stem']}**")
                    for j, opt in enumerate(q["options"]):
                        st.markdown(f"{letters[j]}) {opt}")
                    st.markdown(f"*Correct: {q['correct']}*")
                    st.markdown("---")
                    text_out.append(f"Q{i}. {q['stem']}")
                    for j, opt in enumerate(q["options"]):
                        text_out.append(f"{letters[j]}) {opt}")
                    text_out.append(f"Correct: {q['correct']}\n")

                txt_blob = "\n".join(text_out)
                st.download_button(
                    "Download TXT",
                    txt_blob.encode("utf-8"),
                    file_name=f"ADI_MCQs_Week{week}_Lesson{lesson}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

                docx_bytes = export_docx_mcqs(mcqs, f"ADI MCQs — Week {week}, Lesson {lesson}")
                if docx_bytes:
                    st.download_button(
                        "Download Word (DOCX)",
                        docx_bytes,
                        file_name=f"ADI_MCQs_Week{week}_Lesson{lesson}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                else:
                    st.info("DOCX export not available on this runtime.")

# -------------------------------------------------------------------
# Mode: Skills Activities
# -------------------------------------------------------------------
else:
    st.subheader("Activity Settings")
    total_acts = st.slider("Number of activities", 1, 4, 2)
    focus_hint = st.text_input("Optional skill focus (e.g., 'handover briefing', 'safe setup')")

    if st.button("Generate Activities", type="primary", use_container_width=True):
        if not segments:
            st.warning("Please upload a lesson file or paste content.")
        else:
            topics = carve_topics(segments, want=8)  # we only need a few
            if focus_hint.strip():
                topics.insert(0, focus_hint.strip())
            acts = []
            for i in range(total_acts):
                topic = topics[i % len(topics)]
                acts.append(build_activity(topic, week, lesson))

            st.success(f"Generated {len(acts)} activity brief(s).")
            out_lines = []
            for i, a in enumerate(acts, 1):
                st.markdown(f"### {i}. {a['title']}")
                st.markdown(f"**Objective:** {a['objective']}")
                st.markdown(f"**Time:** {a['time']}")
                st.markdown(f"**Materials:** {', '.join(a['materials'])}")
                st.markdown("**Steps:**")
                for s in a["steps"]:
                    st.markdown(f"- {s}")
                st.markdown("**Quick check:**")
                for c in a["assessment"]:
                    st.markdown(f"- {c}")
                st.markdown("---")

                out_lines.append(f"{i}. {a['title']}")
                out_lines.append(f"Objective: {a['objective']}")
                out_lines.append(f"Time: {a['time']}")
                out_lines.append("Materials: " + ", ".join(a['materials']))
                out_lines.append("Steps:")
                out_lines += [f"- {s}" for s in a["steps"]]
                out_lines.append("Quick check:")
                out_lines += [f"- {c}" for c in a["assessment"]]
                out_lines.append("")

            txt_blob = "\n".join(out_lines)
            st.download_button(
                "Download TXT",
                txt_blob.encode("utf-8"),
                file_name=f"ADI_Activities_Week{week}_Lesson{lesson}.txt",
                mime="text/plain",
                use_container_width=True
            )

            docx_bytes = export_docx_activities(acts, f"ADI Activities — Week {week}, Lesson {lesson}")
            if docx_bytes:
                st.download_button(
                    "Download Word (DOCX)",
                    docx_bytes,
                    file_name=f"ADI_Activities_Week{week}_Lesson{lesson}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            else:
                st.info("DOCX export not available on this runtime.")

