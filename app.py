# --------------------------------------------
# ADI Builder (Streamlit)  — Knowledge & Activities
# Branded, simple, and staff-friendly
# --------------------------------------------
from pathlib import Path
import io
import random
import re
from datetime import date

import streamlit as st
from docx import Document
from docx.shared import Pt
from pptx import Presentation
import fitz  # PyMuPDF

# ========= Brand / Theme =========
BRAND = "#15563d"      # ADI deep green
ACCENT = "#b79e82"     # ADI beige
BG = "#f7f7f7"

st.set_page_config(
    page_title="ADI Builder",
    page_icon="✅",
    layout="wide",
)

CUSTOM_CSS = f"""
<style>
/* Background + fonts */
.reportview-container .main .block-container{{padding-top:1.5rem;}}
.stApp {{ background: {BG}; }}
h1, h2, h3, h4 {{ color: {BRAND}; }}
/* Cards */
.card {{
  background: #fff; border-radius:16px; padding: 18px 18px 10px 18px;
  box-shadow: 0 4px 12px rgba(0,0,0,.05); border: 1px solid rgba(0,0,0,.04);
}}
/* Buttons */
.stButton>button {{
  background:{BRAND}; color:#fff; font-weight:600; border-radius:10px;
  padding: .6rem 1.1rem; border: 0;
}}
.stButton>button:hover {{ filter: brightness(0.95); }}
/* Selects & inputs */
.css-1d391kg, .stTextInput>div>div>input, .stSelectbox>div>div>div {{
  border-radius:10px !important;
}}
/* Tabs underline accent */
.stTabs [data-baseweb="tab-list"] [data-baseweb="tab"]::after {{
  background: {ACCENT};
}}
/* Tiny footnote */
.small {{ color:#666; font-size:0.85rem }}
.badge {{
  display:inline-block; background:{ACCENT}; color:#fff; padding:.15rem .5rem;
  border-radius:.5rem; font-size:.78rem; margin-left:.4rem;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ========= Header / Logo =========
top_left, top_right = st.columns([1,1])
with top_left:
    logo_path = Path(__file__).with_name("logo.png")
    if logo_path.exists():
        st.image(str(logo_path), width=140)
    st.markdown("### ADI Builder")
    st.markdown(
        "A clean, staff-friendly tool to create **Level 4 FE** knowledge questions "
        "and **skills activities** in minutes."
    )
with top_right:
    st.markdown(f"""
    <div class="card">
      <div><b>Status:</b> Ready<span class="badge">v1.0</span></div>
      <div class="small">Upload an eBook/lesson (PDF/DOCX/PPTX), pick week & lesson, then generate.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========= Helpers: File parsing & text =========
def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text.append(page.get_text("text"))
    return "\n".join(text)

def extract_text_from_docx(file_bytes: bytes) -> str:
    bio = io.BytesIO(file_bytes)
    doc = Document(bio)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_pptx(file_bytes: bytes) -> str:
    bio = io.BytesIO(file_bytes)
    prs = Presentation(bio)
    texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                texts.append(shape.text)
    return "\n".join(texts)

def safe_extract_text(upload) -> str:
    if upload is None:
        return ""
    fname = upload.name.lower()
    raw = upload.getvalue()
    if fname.endswith(".pdf"):
        return extract_text_from_pdf(raw)
    if fname.endswith(".docx"):
        return extract_text_from_docx(raw)
    if fname.endswith(".pptx"):
        return extract_text_from_pptx(raw)
    return ""

def guess_topics(raw_text: str, max_topics: int = 12):
    """Very simple topic finder: grab likely headings / short bold lines / bullets.
       Falls back to sentence snippets."""
    lines = [l.strip() for l in raw_text.splitlines()]
    # pick lines that look like headings or bullets
    cands = []
    for l in lines:
        if 3 <= len(l) <= 90 and re.match(r"^[A-Z0-9].+", l) and not l.endswith(":"):
            cands.append(l)
        elif l.startswith(("-", "•", "*")) and len(l) > 6:
            cands.append(l.lstrip("-•* ").strip())
    # Deduplicate
    seen = set(); topics = []
    for c in cands:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            topics.append(c)
        if len(topics) >= max_topics:
            break
    # fallback
    if not topics:
        snips = re.split(r"(?<=[.?!])\s+", raw_text)
        topics = [s.strip()[:80] for s in snips if len(s.strip()) > 12][:max_topics]
    return topics

# ========= Knowledge MCQs (Level 4 FE) =========
BLOOM_VERBS = {
    "Remember": ["define", "list", "recall", "identify"],
    "Understand": ["explain", "summarize", "classify", "describe"],
    "Apply": ["demonstrate", "use", "implement", "illustrate"],
    "Analyze": ["differentiate", "compare", "contrast", "categorize"],
    "Evaluate": ["justify", "critique", "assess", "recommend"],
    "Create": ["design", "construct", "produce", "formulate"],
}

def build_mcq_from_topic(topic: str, level: str, verb: str):
    """Strict, crisp stems. No 'all of the above' or True/False."""
    stem = f"{verb.capitalize()} the key idea in: {topic}"
    # create plausible options by simple transformations
    base = re.sub(r"[:•*-]", " ", topic).strip()
    good = f"{verb.capitalize()} {base}"
    wrongs = [
        "List unrelated items",
        "Use motivational quotes",
        "Describe personal preferences",
    ]
    options = [good] + wrongs
    random.shuffle(options)
    correct_index = options.index(good)
    letters = ["a", "b", "c", "d"]
    text_block = [f"{stem}", ""]
    for i, opt in enumerate(options):
        text_block.append(f"{letters[i]}) {opt}")
    text_block.append(f"\nCorrect: {letters[correct_index]}")
    return "\n".join(text_block), letters[correct_index], stem, options

def mcqs_to_gift(items):
    """Convert MCQs to Moodle GIFT (multiple choice)."""
    out = []
    for i, it in enumerate(items, 1):
        stem, options, correct_letter = it["stem"], it["options"], it["key"]
        letters = ["a", "b", "c", "d"]
        correct = options[letters.index(correct_letter)]
        wrong = [opt for j, opt in enumerate(options) if letters[j] != correct_letter]
        # GIFT
        gift = f"::Q{i}:: {stem} {{\n"
        gift += f"={correct}\n"
        for w in wrong:
            gift += f"~{w}\n"
        gift += "}\n"
        out.append(gift)
    return "\n".join(out)

def build_docx(title: str, lines: list[str]) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]; style.font.name = "Calibri"; style.font.size = Pt(11)
    h = doc.add_heading(title, level=1)
    for ln in lines:
        if ln.strip():
            doc.add_paragraph(ln)
        else:
            doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); bio.seek(0)
    return bio.getvalue()

# ========= Skills Activities =========
def build_activity_briefs(week:int, lesson:int, topics:list[str], count:int=1):
    """Make short, actionable briefs suitable for Level 4 FE vocational tasks."""
    briefs = []
    chosen = topics[:3] if topics else [f"Core concept W{week}L{lesson}"]
    for i in range(count):
        focus = chosen[i % len(chosen)]
        brief = f"""Activity {i+1}: Apply learning in practice
Week {week}, Lesson {lesson}

Learning outcome (skills): Demonstrate the ability to apply knowledge of **{focus}** to a vocational scenario.

Task steps:
1. Review the key points on **{focus}** from the lesson.
2. In pairs, produce a short practical demonstration or worked example.
3. Explain the choices you made and the method you used.
4. Submit a one-page summary with a labelled photo/screenshot of your output.

Success criteria:
- Applies correct method and safe practice where relevant.
- Output is clear, labelled, and accurate.
- Reflection explains what went well and one improvement for next time.

Time: 20–30 mins   |   Evidence: 1-page summary + demonstration
"""
        briefs.append(brief.strip())
    return briefs

# ========= UI: Upload + selectors =========
left, right = st.columns([1.4, 1])
with left:
    st.subheader("1) Upload lesson / eBook (drag & drop)")
    upload = st.file_uploader(
        "Drop a PDF, DOCX, or PPTX here (optional – you can also paste text later).",
        type=["pdf","docx","pptx"],
        label_visibility="collapsed"
    )
    raw_text = safe_extract_text(upload) if upload else ""
    if upload:
        st.success(f"Loaded: **{upload.name}**  ({len(raw_text):,} characters)")
    else:
        st.info("No file? You can still type/paste content in the tabs below.")

with right:
    st.subheader("2) Schedule")
    week = st.selectbox("Week (1–14)", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson (1–4)", list(range(1,5)), index=0)
    st.markdown(f"<div class='small'>Date: {date.today().isoformat()}</div>", unsafe_allow_html=True)

st.markdown("---")

# ========= Tabs =========
tab1, tab2 = st.tabs(["📘 Knowledge MCQs", "🛠️ Skills Activities"])

with tab1:
    st.markdown("#### Generate crisp, staff-ready MCQs (Level 4 FE)")
    tcol1, tcol2, tcol3 = st.columns([1,1,1])
    with tcol1:
        level = st.selectbox("Bloom’s level", list(BLOOM_VERBS.keys()), index=2)
    with tcol2:
        total_q = st.slider("Total MCQs (5–10)", 5, 10, 6)
    with tcol3:
        extra_verbs = st.text_input("Extra verbs (optional, comma-separated)", "")

    # Source text
    with st.expander("Optional: paste or edit source content"):
        user_text = st.text_area("Paste lesson text here (overrides headings found in file)", value="", height=160)

    if st.button("Generate MCQs"):
        # Get topics
        source = user_text.strip() if user_text.strip() else raw_text
        topics = guess_topics(source, max_topics=total_q)
        if not topics:
            st.warning("I couldn’t find usable topics. Please paste a few lines in the text box above.")
        else:
            # update verbs if user added
            verbs = BLOOM_VERBS[level].copy()
            if extra_verbs.strip():
                for v in [v.strip() for v in extra_verbs.split(",") if v.strip()]:
                    verbs.append(v)
            # build MCQs
            mcq_items = []
            text_lines = []
            for i, tpc in enumerate(topics, 1):
                verb = random.choice(verbs)
                block, key, stem, options = build_mcq_from_topic(tpc, level, verb)
                st.markdown(f"**Q{i}.** {block}")
                st.markdown("---")
                mcq_items.append({"stem": stem, "options": options, "key": key})
                text_lines.append(f"Q{i}. {block}\n")

            # Downloads: DOCX + GIFT
            docx_bytes = build_docx(f"ADI Knowledge MCQ (Week {week} Lesson {lesson})", text_lines)
            gift_txt = mcqs_to_gift(mcq_items).encode("utf-8")

            d1, d2 = st.columns(2)
            with d1:
                st.download_button(
                    "⬇️ Download MCQs as Word (.docx)",
                    data=docx_bytes,
                    file_name=f"ADI_Knowledge_W{week}L{lesson}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            with d2:
                st.download_button(
                    "⬇️ Download Moodle GIFT",
                    data=gift_txt,
                    file_name=f"ADI_Knowledge_W{week}L{lesson}.gift.txt",
                    mime="text/plain",
                )

with tab2:
    st.markdown("#### Build simple, practical briefs for vocational learning")
    a1, a2 = st.columns([1,1])
    with a1:
        num_acts = st.slider("Number of activities", 1, 3, 1)
    with a2:
        focus_hint = st.text_input("Optional focus topic (overrides automatic pick)", "")

    if st.button("Generate Activities"):
        src = raw_text
        topics = [focus_hint] if focus_hint.strip() else guess_topics(src, max_topics=6)
        briefs = build_activity_briefs(week, lesson, topics, count=num_acts)

        all_text = []
        for i, b in enumerate(briefs, 1):
            st.markdown(f"**Activity {i}**")
            st.code(b)
            all_text.append(b + "\n")

        docx_bytes = build_docx(f"ADI Activity Briefs (Week {week} Lesson {lesson})", all_text)
        st.download_button(
            "⬇️ Download Activity Briefs (.docx)",
            data=docx_bytes,
            file_name=f"ADI_Activities_W{week}L{lesson}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

# Footer
st.markdown("---")
st.markdown(
    "<div class='small'>Tip: You can run this with only the eBook OR just paste text in the MCQ tab.</div>",
    unsafe_allow_html=True,
)
