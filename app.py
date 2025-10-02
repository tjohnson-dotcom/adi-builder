# streamlit_app.py — ADI Builder (Quick‑win UI)
# One-file Streamlit app focusing on look & feel and simple, stable inputs (no sliders)

import os
import io
import streamlit as st

# Conversation state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ---------------------------
# Page & Theme
# ---------------------------
st.set_page_config(
    page_title="ADI Builder — Quick Win",
    page_icon="📚",
    layout="wide",
)

ADI_GREEN = "#245a34"   # primary
ADI_GOLD  = "#C8A85A"    # accent
STONE_BG  = "#f5f5f4"    # soft stone background
INK       = "#1f2937"    # dark ink for text

# Inject lightweight CSS to remove red accents and style pills/buttons
st.markdown(
    f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
        background: {STONE_BG};
        color: {INK};
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji';
    }}

    /* Header */
    .adi-header {{
        display:flex; align-items:center; gap:.75rem; padding:.75rem 0 0.25rem 0;
        border-bottom: 1px solid rgba(0,0,0,.06);
        margin-bottom:.5rem;
    }}
    .adi-title {{ font-weight:800; font-size:1.15rem; color:{INK}; letter-spacing:.2px; }}

    /* Buttons */
    .stButton>button {{
        background: {ADI_GREEN};
        color: white;
        border: 0;
        border-radius: 14px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(0,0,0,.08);
    }}
    .stButton>button:hover {{ filter: brightness(1.05); }}

    /* Sidebar headings */
    section[data-testid="stSidebar"] h2 {{
        font-size: 1rem;
        color: {INK};
        opacity: .8;
        margin-top: .5rem;
    }}

    /* Radio as vertical pill menu */
    div[data-baseweb="radio"] > div {{ gap: .35rem; }}
    div[role="radiogroup"] label {{
        border: 2px solid transparent;
        border-radius: 999px;
        padding: .35rem .75rem;
        font-weight: 600;
        color: {INK};
        background: white;
        box-shadow: 0 1px 4px rgba(0,0,0,.06);
        cursor: pointer;
    }}
    div[role="radiogroup"] label:hover {{ border-color: {ADI_GOLD}; }}
    input[type="radio"] {{ accent-color: {ADI_GREEN} !important; }}
    /* hide native radio dot to avoid red */
    div[role="radiogroup"] input[type="radio"] {{ position:absolute; opacity:0; width:0; height:0; }}
    input[type="radio"]:checked + div p {{ color: white !important; }}
    input[type="radio"]:checked + div {{
        background: linear-gradient(90deg, {ADI_GREEN}, {ADI_GOLD});
        color: white !important;
        border-color: transparent !important;
    }}

    /* Cards */
    .adi-card {{
        background:white; border-radius:16px; padding:1rem; box-shadow:0 2px 8px rgba(0,0,0,.06);
    }}

    /* Selects */
    .stSelectbox>div>div {{ background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }}

    /* Inputs */
    .stTextInput>div>div>input, .stTextArea textarea {{
        background: white; border-radius: 12px !important; box-shadow: inset 0 0 0 1px rgba(0,0,0,.08);
    }}
    .stTextInput>div>div>input:focus, .stTextArea textarea:focus {{
        outline: 2px solid {ADI_GREEN}; box-shadow: 0 0 0 3px rgba(36,90,52,.25);
    }}

    .bloom-chip {{
        display:inline-flex; align-items:center; gap:.5rem; padding:.35rem .7rem; border-radius:999px;
        background: linear-gradient(90deg, {ADI_GOLD}, {ADI_GREEN}); color:white; font-weight:700; font-size:.85rem;
        box-shadow:0 2px 6px rgba(0,0,0,.08);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Sidebar (Left-hand controls)
# ---------------------------
with st.sidebar:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_column_width=True)
    else:
        st.markdown("<div class='adi-title'>ADI Builder</div>", unsafe_allow_html=True)
    st.markdown("### Modes")
    
    # Icon-labelled options, but keep a clean internal value for logic
    _options = ["Knowledge", "Skills", "Activities", "Revision"]
    _icons = {"Knowledge": "📘", "Skills": "🛠️", "Activities": "🎯", "Revision": "📝"}
    _labels = [f"{_icons[o]} {o}" for o in _options]
    _picked = st.radio(
        "Pick a workflow",
        _labels,
        index=0,
        label_visibility="collapsed",
    )
    mode = _options[_labels.index(_picked)]

    st.markdown("### 📅 Lesson setup")
    week = st.selectbox("Week", options=list(range(1, 15)), index=0)
    lesson = st.selectbox("Lesson", options=list(range(1, 6)), index=0)

    st.markdown("### 📎 Resources (drag & drop supported)")
    with st.expander("📥 Drag & drop files here or click to browse"):
        ebook_file = st.file_uploader("📖 eBook (PDF)", type=["pdf"], key="ebook")
        plan_file = st.file_uploader("📄 Lesson Plan (DOCX/PDF)", type=["docx", "pdf"], key="plan")
        ppt_file  = st.file_uploader("📊 Slides (PPTX)", type=["pptx"], key="ppt")

    st.divider()
    run = st.button("✨ Generate for staff")

# ---------------------------
# Main layout
# ---------------------------
left, right = st.columns([1, 1])

with left:
    # Header row with optional logo and title + app icon
    st.markdown("<div class='adi-header'><span class='adi-title'>📚 ADI Builder</span></div>", unsafe_allow_html=True)
    # Optional logo next to title
    h1c, h2c = st.columns([1, 6])
    h1c, h2c = st.columns([1, 6])
    with h1c:
        if os.path.isfile("adi_logo.png"):
            st.image("adi_logo.png")
    with h2c:
        st.subheader(f"{mode} — Week {week}, Lesson {lesson}")
        st.caption("ADI-aligned prompts and activities. Zero sliders. Easy picks.")

    # Bloom policy badge based on week
    def bloom_level(w:int):
        if 1 <= w <= 4:
            return "LOW — Remember/Understand"
        if 5 <= w <= 9:
            return "MEDIUM — Apply/Analyse"
        return "HIGH — Evaluate/Create"
    st.markdown(f"<span class='bloom-chip'>Bloom: {bloom_level(week)}</span>", unsafe_allow_html=True)

    # Simple text areas for prompts so staff can edit before exporting
    topic = st.text_input("Topic / Objective (short)")
    notes = st.text_area("Key notes (optional)", height=100)

    if run:
        # Placeholder generation — replace with your real logic
        st.success("Ready! Drafts created below. Tweak and export.")

with right:
    st.markdown("### 📤 Draft outputs")

    if run:
        if mode == "Knowledge":
            st.markdown("**Sample Knowledge Questions (MCQs)**")
            st.write(
                "1. Which statement best describes the topic?\n\n"
                "2. Identify the correct sequence for …\n\n"
                "3. Which definition matches …"
            )
        elif mode == "Skills":
            st.markdown("**Skill-focused Tasks**")
            st.write("• Perform the core procedure and record observations.\n\n• Peer-check using the rubric.")
        elif mode == "Activities":
            st.markdown("**In-class Activities**")
            st.write("• Think–Pair–Share (3–2–1).\n\n• Jigsaw: split subtopics, teach-back.")
        elif mode == "Revision":
            st.markdown("**Revision Prompts**")
            st.write("• Create a one-page cheat sheet.\n\n• 5 short-answer questions from today’s lesson.")
    else:
        st.info("Load your resources on the left, set Week/Lesson, pick a mode, then click **Generate**.")

# ---------------------------
# Utility: basic file sanity checks (prevents crashes later)
# ---------------------------
problems = []
if run:
    if ebook_file and ebook_file.size > 25 * 1024 * 1024:
        problems.append("eBook exceeds 25MB; consider splitting.")
    if ppt_file and not ppt_file.name.lower().endswith(".pptx"):
        problems.append("Slides must be .pptx.")

    if problems:
        st.warning("\n".join([f"• {p}" for p in problems]))

# Conversation (chat-style)
st.markdown("### 💬 Conversation")
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask ADI Builder…"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    context = f"{mode} • Week {week} Lesson {lesson}" + (f" • Topic: {topic}" if 'topic' in locals() and topic else "")
    response = (
        "Got it. I’ll tailor activities/questions for **" + context + "**. "
        "Use the **Generate** button for structured drafts, or tell me exactly what to refine."
    )
    st.session_state["messages"].append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

# Footer
st.markdown(
    f"<div style='text-align:center; opacity:.6; padding:1rem 0;'>ADI Builder • Theming: <b>{ADI_GREEN}</b> / <b>{ADI_GOLD}</b> • No red accents</div>",
    unsafe_allow_html=True,
)
