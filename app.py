# streamlit_app.py — ADI Builder (Larger UI scale)
# Start command (Render):
# streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0

import os
import io
import random
from datetime import datetime
import streamlit as st
from docx import Document
from docx.shared import Pt

st.set_page_config(page_title="ADI Builder — Quick Win (Large)", page_icon="📚", layout="wide")

# ADI palette
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
STONE_BG  = "#f5f5f4"
INK       = "#1f2937"

CSS = f"""
<style>
/***** ADI size & spacing scale *****/
:root {{
  --adi-font-base: 18px;  /* bump up base text */
  --adi-font-ui:   17px;  /* inputs, buttons, radios */
}}

html, body, [data-testid="stAppViewContainer"] {{
  background: {STONE_BG};
  color: {INK};
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji';
  font-size: var(--adi-font-base);
}}

/* widen main column */
.main .block-container {{
  max-width: 1360px;
  padding-top: 0.8rem;
  padding-bottom: 2rem;
  margin-left: auto;
  margin-right: auto;
}}
[data-testid="stAppViewBlockContainer"] {{
  max-width: 1360px;
  margin-left: auto; margin-right: auto;
}}

/* Top bar */
.adi-topbar {{
  display:flex; align-items:center; gap:.75rem; padding:.6rem 1rem;
  background:white; border-bottom:1px solid rgba(0,0,0,.06);
  position:sticky; top:0; z-index:5;
}}
.adi-topbar .brand {{ font-weight:800; letter-spacing:.2px; color:{INK}; font-size:1.1rem; }}

/* Cards */
.adi-card {{
  background:white; border-radius:16px; padding:1.2rem;
  box-shadow:0 2px 8px rgba(0,0,0,.06);
}}

/* Buttons larger + ADI green */
.stButton > button {{
  background: {ADI_GREEN} !important; color:white !important;
  border:0; border-radius:16px; padding:.75rem 1.2rem; font-weight:600;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
  font-size: var(--adi-font-ui);
}}
.stButton > button:hover {{ filter: brightness(1.05); }}

/* Inputs larger */
.stTextInput input, .stTextArea textarea,
.stSelectbox div, [data-baseweb="select"] * {{
  font-size: var(--adi-font-ui);
}}
.stTextInput>div>div>input, .stTextArea textarea {{
  background:white; border-radius:12px !important; box-shadow: inset 0 0 0 1px rgba(0,0,0,.08);
}}
.stTextInput>div>div>input:focus, .stTextArea textarea:focus {{
  outline: 2px solid {ADI_GREEN}; box-shadow: 0 0 0 3px rgba(36,90,52,.25);
}}

/* Radio pill menu */
div[data-baseweb="radio"] > div {{ gap:.4rem; }}
div[role="radiogroup"] input[type="radio"] {{ position:absolute; opacity:0; width:0; height:0; }}
div[role="radiogroup"] label {{
  border:2px solid transparent; border-radius:999px; padding:.45rem .9rem;
  font-weight:600; color:{INK}; background:white; box-shadow:0 1px 4px rgba(0,0,0,.06);
  font-size: var(--adi-font-ui);
}}
div[role="radiogroup"] label:hover {{ border-color:{ADI_GOLD}; }}
input[type="radio"]:checked + div {{
  background: linear-gradient(90deg, {ADI_GREEN}, {ADI_GOLD}); color:white !important;
}}

/* Bloom chip */
.bloom-chip {{
  display:inline-flex; align-items:center; gap:.5rem; padding:.4rem .8rem; border-radius:999px;
  background: linear-gradient(90deg, {ADI_GOLD}, {ADI_GREEN}); color:white; font-weight:700; font-size: .95rem;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
}}

/* Headings */
h2, .stMarkdown h2 {{ font-size: 1.55rem; }}
h3, .stMarkdown h3 {{ font-size: 1.25rem; }}

/* Chat input size */
[data-testid="stChatInput"] textarea {{
  font-size: var(--adi-font-ui);
  line-height: 1.35;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Sidebar
with st.sidebar:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_container_width=True)
    else:
        st.markdown("### **ADI Builder**")

    st.markdown("### Modes")
    _options = ["Knowledge", "Skills", "Activities", "Revision"]
    _icons   = {"Knowledge": "📘", "Skills": "🛠️", "Activities": "🎯", "Revision": "📝"}
    _labels  = [f"{_icons[o]} {o}" for o in _options]
    _picked  = st.radio("Pick a workflow", _labels, index=0, label_visibility="collapsed")
    mode     = _options[_labels.index(_picked)]

    st.markdown("### 📅 Lesson setup")
    week   = st.selectbox("Week", options=list(range(1, 15)), index=0)
    lesson = st.selectbox("Lesson", options=list(range(1, 6)), index=0)

    st.markdown("### 📎 Resources (drag & drop supported)")
    with st.expander("📥 Drag & drop files here or click to browse"):
        ebook_file = st.file_uploader("📖 eBook (PDF)", type=["pdf"], key="ebook")
        plan_file  = st.file_uploader("📄 Lesson Plan (DOCX/PDF)", type=["docx", "pdf"], key="plan")
        ppt_file   = st.file_uploader("📊 Slides (PPTX)", type=["pptx"], key="ppt")

    st.divider()
    run = st.button("✨ Generate for staff")

# Sticky header
st.markdown("<div class='adi-topbar'><span class='brand'>📚 ADI Builder</span></div>", unsafe_allow_html=True)

left, right = st.columns([1,1], gap="large")

def bloom_level(w: int) -> str:
    if 1 <= w <= 4:
        return "LOW — Remember/Understand"
    if 5 <= w <= 9:
        return "MEDIUM — Apply/Analyse"
    return "HIGH — Evaluate/Create"

with left:
    st.subheader(f"{mode} — Week {week}, Lesson {lesson}")
    st.caption("ADI-aligned prompts and activities. Zero sliders. Easy picks.")
    st.markdown(f"<span class='bloom-chip'>Bloom: {bloom_level(week)}</span>", unsafe_allow_html=True)

    topic = st.text_input("Topic / Objective (short)")
    notes = st.text_area("Key notes (optional)", height=120)

with right:
    st.markdown("### 📤 Draft outputs")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    if run:
        if mode == "Knowledge":
            items = [
                "Which statement best describes the topic?",
                "Identify the correct sequence for …",
                "Which definition matches …",
                "Choose the correct term for …",
                "Which example fits the concept best?",
            ]
        elif mode == "Skills":
            items = [
                "Perform the core procedure and record observations.",
                "Peer-check using the provided rubric.",
                "Demonstrate the process and explain each step.",
                "Complete a worked example and annotate decisions.",
                "Reflect on one improvement for next time.",
            ]
        elif mode == "Activities":
            items = [
                "Think–Pair–Share (3–2–1).",
                "Jigsaw: split subtopics, teach-back.",
                "Gallery walk with sticky-notes feedback.",
                "Case vignette → small-group solution.",
                "Concept mapping in pairs.",
            ]
        else:
            items = [
                "Create a one-page cheat sheet.",
                "Five short-answer questions from today’s lesson.",
                "Flashcard set: 10 key terms.",
                "Past-paper question (timed 7 min).",
                "Exit ticket: 2 things learned, 1 question.",
            ]

        shuffled = items[:]
        random.shuffle(shuffled)

        st.markdown("**Draft list (randomized):**")
        for i, s in enumerate(shuffled, start=1):
            st.write(f"{i}. {s}")

        def build_docx():
            doc = Document()
            title = f"ADI {mode} — Week {week} Lesson {lesson}"
            doc.add_heading(title, level=1)

            meta = doc.add_paragraph()
            meta.add_run("Generated: ").bold = True
            meta.add_run(datetime.now().strftime("%Y-%m-%d %H:%M"))
            if topic:
                meta.add_run("   |   Topic: ").bold = True
                meta.add_run(topic)
            if notes:
                doc.add_heading("Notes", level=2)
                doc.add_paragraph(notes)

            doc.add_heading("Items", level=2)
            for i, s in enumerate(shuffled, start=1):
                p = doc.add_paragraph(f"{i}. {s}")
                for run in p.runs:
                    run.font.size = Pt(11)

            doc.add_paragraph().add_run("Bloom: " + bloom_level(week)).italic = True

            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            return bio

        docx_bytes = build_docx()
        st.download_button(
            "⬇️ Export to Word (DOCX)",
            data=docx_bytes,
            file_name=f"ADI_{mode}_W{week}_L{lesson}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    else:
        st.info("Load your resources on the left, set Week/Lesson, pick a mode, then click **Generate**.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### 💬 Conversation")
st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
if "messages" not in st.session_state:
    st.session_state["messages"] = []
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
if prompt := st.chat_input("Ask ADI Builder…"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    context = f"{mode} • Week {week} Lesson {lesson}" + (f" • Topic: {topic}" if topic else "")
    response = ("Got it. I’ll tailor items for **" + context + "**. Use **Generate** for structured drafts, or tell me what to refine.")
    st.session_state["messages"].append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
st.markdown("</div>", unsafe_allow_html=True)

# sanity checks
problems = []
if run:
    if ebook_file and getattr(ebook_file, "size", 0) and ebook_file.size > 25 * 1024 * 1024:
        problems.append("eBook exceeds 25MB; consider splitting.")
    if ppt_file and not ppt_file.name.lower().endswith(".pptx"):
        problems.append("Slides must be .pptx.")
if problems:
    st.warning("\n".join([f"• {p}" for p in problems]))
