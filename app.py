
# streamlit_app.py — ADI Builder (Quick-win UI, fixed & polished)
# Host on Render.com; Start command:
# streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0

import os
import io
import random
from datetime import datetime
import streamlit as st
from docx import Document
from docx.shared import Pt

# ---------------------------
# Page & Theme
# ---------------------------
st.set_page_config(
    page_title="ADI Builder — Quick Win",
    page_icon="📚",
    layout="wide",
)

# ADI palette
ADI_GREEN = "#245a34"   # primary
ADI_GOLD  = "#C8A85A"   # accent
STONE_BG  = "#f5f5f4"   # soft stone background
INK       = "#1f2937"   # dark ink

# Escaped CSS (double braces) because this is an f-string
CSS = f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{
  background: {STONE_BG};
  color: {INK};
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji';
}}
/* Top bar */
.adi-topbar {{
  display:flex; align-items:center; gap:.75rem; padding:.6rem 1rem;
  background:white; border-bottom:1px solid rgba(0,0,0,.06);
  position:sticky; top:0; z-index:5;
}}
.adi-topbar .brand {{ font-weight:800; letter-spacing:.2px; color:{INK}; font-size:1.05rem; }}

/* Force ADI green button (override themes) */
.stButton > button {{
  background: {ADI_GREEN} !important; color:white !important;
  border:0; border-radius:14px; padding:.6rem 1rem; font-weight:600;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
}}
.stButton > button:hover {{ filter: brightness(1.05); }}

/* Section cards */
.adi-card {{
  background:white; border-radius:16px; padding:1rem;
  box-shadow:0 2px 8px rgba(0,0,0,.06);
}}

/* Radio as “pill” menu (hide native dots) */
div[data-baseweb="radio"] > div {{ gap:.35rem; }}
div[role="radiogroup"] input[type="radio"] {{ position:absolute; opacity:0; width:0; height:0; }}
div[role="radiogroup"] label {{
  border:2px solid transparent; border-radius:999px; padding:.35rem .75rem;
  font-weight:600; color:{INK}; background:white; box-shadow:0 1px 4px rgba(0,0,0,.06);
}}
div[role="radiogroup"] label:hover {{ border-color:{ADI_GOLD}; }}
input[type="radio"]:checked + div {{
  background: linear-gradient(90deg, {ADI_GREEN}, {ADI_GOLD}); color:white !important;
}}

/* Inputs */
.stSelectbox > div > div {{ background:white; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,.06); }}
.stTextInput>div>div>input, .stTextArea textarea {{
  background:white; border-radius:12px !important; box-shadow: inset 0 0 0 1px rgba(0,0,0,.08);
}}
.stTextInput>div>div>input:focus, .stTextArea textarea:focus {{
  outline: 2px solid {ADI_GREEN}; box-shadow: 0 0 0 3px rgba(36,90,52,.25);
}}

/* Bloom chip */
.bloom-chip {{
  display:inline-flex; align-items:center; gap:.5rem; padding:.35rem .7rem; border-radius:999px;
  background: linear-gradient(90deg, {ADI_GOLD}, {ADI_GREEN}); color:white; font-weight:700; font-size:.85rem;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
}}

</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Persist chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ---------------------------
# Sidebar (Left-hand controls)
# ---------------------------
with st.sidebar:
    # Logo or brand text
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_column_width=True)
    else:
        st.markdown("### **ADI Builder**")

    st.markdown("### Modes")
    # Icon-labelled options, with clean internal value
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

# ---------------------------
# Main layout
# ---------------------------
# Sticky header bar
st.markdown(
    "<div class='adi-topbar'><span class='brand'>📚 ADI Builder</span></div>",
    unsafe_allow_html=True,
)

left, right = st.columns([1, 1], gap="large")

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

    # Editable context
    topic = st.text_input("Topic / Objective (short)")
    notes = st.text_area("Key notes (optional)", height=100)

    if run:
        st.success("Ready! Drafts created on the right. Tweak and export.")

with right:
    st.markdown("### 📤 Draft outputs")
    drafts_container = st.container()
    with drafts_container:
        if run:
            # Simple placeholder generation; replace with your real logic.
            if mode == "Knowledge":
                items = [
                    "Which statement best describes the topic?",
                    "Identify the correct sequence for …",
                    "Which definition matches …",
                    "Choose the correct term for …",
                    "Which example fits the concept best?"
                ]
            elif mode == "Skills":
                items = [
                    "Perform the core procedure and record observations.",
                    "Peer-check using the provided rubric.",
                    "Demonstrate the process and explain each step.",
                    "Complete a worked example and annotate decisions.",
                    "Reflect on one improvement for next time."
                ]
            elif mode == "Activities":
                items = [
                    "Think–Pair–Share (3–2–1).",
                    "Jigsaw: split subtopics, teach-back.",
                    "Gallery walk with sticky-notes feedback.",
                    "Case vignette → small-group solution.",
                    "Concept mapping in pairs."
                ]
            else:  # Revision
                items = [
                    "Create a one-page cheat sheet.",
                    "Five short-answer questions from today’s lesson.",
                    "Flashcard set: 10 key terms.",
                    "Past-paper question (timed 7 min).",
                    "Exit ticket: 2 things learned, 1 question."
                ]

            # Randomize for variety
            shuffled = items[:]
            random.shuffle(shuffled)

            st.markdown("**Draft list (randomized):**")
            for i, s in enumerate(shuffled, start=1):
                st.write(f"{i}. {s}")

            # ---- Export to Word (DOCX) ----
            def build_docx():
                doc = Document()

                # Title
                title = f"ADI {mode} — Week {week} Lesson {lesson}"
                doc.add_heading(title, level=1)

                # Meta
                meta = doc.add_paragraph()
                meta.add_run("Generated: ").bold = True
                meta.add_run(datetime.now().strftime("%Y-%m-%d %H:%M"))
                if topic:
                    meta.add_run("   |   Topic: ").bold = True
                    meta.add_run(topic)

                # Notes
                if notes:
                    doc.add_heading("Notes", level=2)
                    doc.add_paragraph(notes)

                # Content
                doc.add_heading("Items", level=2)
                for i, s in enumerate(shuffled, start=1):
                    p = doc.add_paragraph(f"{i}. {s}")

                    # Optional: slightly larger font for readability
                    for run in p.runs:
                        run.font.size = Pt(11)

                # Footer
                doc.add_paragraph().add_run("Bloom: " + bloom_level(week)).italic = True

                bio = io.BytesIO()
                doc.save(bio)
                bio.seek(0)
                return bio

            docx_bytes = build_docx()
            st.download_button(
                label="⬇️ Export to Word (DOCX)",
                data=docx_bytes,
                file_name=f"ADI_{mode}_W{week}_L{lesson}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        else:
            st.info("Load your resources on the left, set Week/Lesson, pick a mode, then click **Generate**.")

# ---------------------------
# Conversation (chat-style)
# ---------------------------
st.markdown("### 💬 Conversation")
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask ADI Builder…"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    context = f"{mode} • Week {week} Lesson {lesson}" + (f" • Topic: {topic}" if topic else "")
    response = (
        "Got it. I’ll tailor items for **" + context +
        "**. Use **Generate** for structured drafts, or tell me what to refine."
    )
    st.session_state["messages"].append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

# ---------------------------
# Basic file sanity checks (to avoid crashes)
# ---------------------------
problems = []
if run:
    if ebook_file and ebook_file.size and ebook_file.size > 25 * 1024 * 1024:
        problems.append("eBook exceeds 25MB; consider splitting.")
    if ppt_file and not ppt_file.name.lower().endswith(".pptx"):
        problems.append("Slides must be .pptx.")
if problems:
    st.warning("\n".join([f"• {p}" for p in problems]))
