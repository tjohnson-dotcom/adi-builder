
import io
import random
from datetime import datetime
from typing import List, Dict

import streamlit as st

# Optional deps; guarded imports so the app still loads even if missing.
try:
    from pptx import Presentation  # python-pptx
except Exception:
    Presentation = None

try:
    from docx import Document      # python-docx
    from docx.shared import Pt
except Exception:
    Document = None

ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
STONE_BG = "#F3F3F0"

st.set_page_config(page_title="ADI Builder", page_icon="🧰", layout="wide")

# ---------- THEME / CSS ----------
st.markdown(f"""
<style>
/* Base */
:root {{
  --adi-green: {ADI_GREEN};
  --adi-gold: {ADI_GOLD};
  --stone: {STONE_BG};
}}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; }}
/* Header */
h1, h2, h3, h4 {{ color: var(--adi-green) !important; }}
/* Segmented controls (Streamlit radio horizontal) */
div[role="radiogroup"] label {{
  border: 1px solid var(--adi-green) !important;
  padding: .35rem .8rem !important;
  border-radius: 999px !important;
  margin-right: .35rem !important;
  background: white !important;
}}
div[role="radiogroup"] label[data-checked="true"] {{
  background: var(--adi-green) !important;
  color: white !important;
  border-color: var(--adi-green) !important;
}}
/* Tabs styled like pills */
.stTabs [data-baseweb="tab-list"] {{
  gap: .35rem;
}}
.stTabs [data-baseweb="tab"] {{
  border: 1px solid var(--adi-green);
  background: white;
  color: #111;
  border-radius: 999px;
  padding: .35rem .9rem;
}}
.stTabs [aria-selected="true"] {{
  background: var(--adi-green) !important;
  color: white !important;
  border-color: var(--adi-green) !important;
}}
/* Cards */
.card {{
  background: #fff;
  border: 1px solid #E6E6E6;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
}}
/* Buttons */
.stButton>button {{
  border-radius: 999px;
  border: 1px solid var(--adi-green);
  color: #fff;
  background: var(--adi-green);
}}
/* Inputs */
input, textarea, .stMultiSelect, .stSelectbox {{
  border-radius: .75rem !important;
}}
/* Accents */
a, .st-emotion-cache-1wbqy5l p a {{
  color: var(--adi-green) !important;
}}
/* No red accents anywhere */
:where(*) {{ --red: var(--adi-green); }}
/* Sidebar header */
.sidebar-title {{
  font-weight: 700; color: var(--adi-green); letter-spacing: .02em;
}}
</style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
LOW_VERBS = ["define", "identify", "list", "state", "recognize"]
MED_VERBS = ["explain", "compare", "apply", "classify", "illustrate"]
HIGH_VERBS = ["analyze", "evaluate", "design", "critique", "hypothesize"]

def week_to_bloom(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    if 5 <= week <= 9:
        return "Medium"
    if 10 <= week <= 14:
        return "High"
    return "Medium"

def extract_topics_from_pptx(uploaded_file) -> List[str]:
    """Parse titles & bullet points from PPTX; return unique topics (max ~20)."""
    if Presentation is None or uploaded_file is None:
        return []
    prs = Presentation(uploaded_file)
    seen = []
    for slide in prs.slides:
        # Title
        if slide.shapes.title and slide.shapes.title.text:
            t = slide.shapes.title.text.strip()
            if t and t not in seen:
                seen.append(t)
        # Bullets
        for shape in slide.shapes:
            if hasattr(shape, "text_frame") and shape.text_frame and shape.text_frame.text:
                for p in shape.text_frame.paragraphs:
                    txt = (p.text or "").strip()
                    if txt and 3 <= len(txt) <= 80 and txt not in seen:
                        seen.append(txt)
        if len(seen) >= 40:
            break
    # Light cleaning
    topics = []
    for s in seen:
        s = " ".join(s.split())
        s = s.replace("•", "").strip("-–—: ").strip()
        if s and s not in topics:
            topics.append(s)
    return topics[:30]

def verbs_for_level(level: str) -> List[str]:
    return {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}.get(level, MED_VERBS)

def generate_mcq(topic: str, level: str) -> Dict:
    """Very simple templated MCQ generator (deterministic but shuffled)."""
    verb = random.choice(verbs_for_level(level))
    stem = f"{verb.capitalize()} the key idea related to: {topic}"
    correct = f"{topic} — core concept"
    distractors = [
        f"{topic} — unrelated detail",
        f"{topic} — common misconception",
        f"{topic} — peripheral fact",
    ]
    options = [correct] + distractors
    random.shuffle(options)
    return {"stem": stem, "options": options, "answer": correct}

def to_word_mcqs(mcqs: List[Dict]) -> bytes:
    if Document is None:
        # Fallback to plain-text if python-docx is missing
        out = io.StringIO()
        for i, q in enumerate(mcqs, 1):
            out.write(f"Q{i}. {q['stem']}\n")
            for j, opt in enumerate(q["options"], 1):
                out.write(f"   {chr(64+j)}. {opt}\n")
            out.write(f"Answer: {q['answer']}\n\n")
        return out.getvalue().encode("utf-8")

    doc = Document()
    doc.styles['Normal'].font.name = 'Arial'
    doc.styles['Normal'].font.size = Pt(11)
    doc.add_heading('ADI Knowledge MCQs', level=1)
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        for j, opt in enumerate(q["options"], 1):
            doc.add_paragraph(f"{chr(64+j)}. {opt}", style='List Bullet')
        doc.add_paragraph(f"Answer: {q['answer']}")
        doc.add_paragraph("")  # spacer
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown('<div class="sidebar-title">ADI Builder</div>', unsafe_allow_html=True)
    logo_col1, logo_col2 = st.columns([1,2])
    with logo_col1:
        st.write(" ")
    with logo_col2:
        st.caption("Simple, ADI-branded daily tool")

    st.subheader("Lesson Setup")
    lesson = st.radio("Lesson", [1, 2, 3, 4, 5], horizontal=True, key="lesson")
    week = st.radio("Week", list(range(1, 15)), horizontal=True, key="week")
    bloom_level = week_to_bloom(int(week))
    st.info(f"Recommended Bloom level for Week {week}: **{bloom_level}**")

    st.subheader("Upload Resources")
    pptx = st.file_uploader("Upload PowerPoint (.pptx)", type=["pptx"], help="We’ll extract topics and key points.")
    if pptx and "topics" not in st.session_state:
        st.session_state.topics = extract_topics_from_pptx(pptx)

    st.subheader("Selection")
    default_topics = st.session_state.get("topics", [])[:8]
    selected_topics = st.multiselect("Select 5–10 topics", st.session_state.get("topics", []), default=default_topics, max_selections=10)

# ---------- MAIN LAYOUT ----------
left, right = st.columns([0.95, 1.05], gap="large")

with left:
    st.title("ADI Builder")
    st.caption("Upload → choose Bloom’s → generate → export (Word first).")
    st.markdown(
        f"""<div class="card">
        <b>Bloom policy:</b> Weeks 1–4 <b style="color:{ADI_GREEN}">Low</b>, 5–9 <b style="color:{ADI_GREEN}">Medium</b>, 10–14 <b style="color:{ADI_GREEN}">High</b>.
        The app auto-highlights the recommended level based on your selected week.
        </div>""",
        unsafe_allow_html=True
    )

    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills", "Activities", "Revision"])

    # ---------- Knowledge Tab ----------
    with tabs[0]:
        st.subheader("Generate Knowledge MCQs")
        lvl = st.radio("Bloom’s Level", ["Low", "Medium", "High"], index=["Low","Medium","High"].index(bloom_level), horizontal=True, key="knowledge_bloom")

        n_qs = st.slider("How many questions?", min_value=5, max_value=20, value=10, step=1)
        st.write("Selected topics:")
        if selected_topics:
            st.write(", ".join(selected_topics))
        else:
            st.warning("Pick 5–10 topics from the sidebar to continue.")

        gen_clicked = st.button("Generate Questions", type="primary", use_container_width=True)
        if gen_clicked and selected_topics:
            # Create a simple pool, cycle through topics
            pool = []
            while len(pool) < n_qs:
                for t in selected_topics:
                    pool.append(t)
                    if len(pool) >= n_qs:
                        break
            random.shuffle(pool)
            mcqs = [generate_mcq(t, lvl) for t in pool]
            st.session_state["mcqs"] = mcqs

        if "mcqs" in st.session_state:
            st.success(f"Generated {len(st.session_state['mcqs'])} MCQs (randomized).")
            with st.expander("Preview MCQs", expanded=True):
                for i, q in enumerate(st.session_state["mcqs"], 1):
                    st.markdown(f"**Q{i}. {q['stem']}**")
                    for j, opt in enumerate(q["options"], 1):
                        st.write(f"{chr(64+j)}. {opt}")
                    st.caption(f"**Answer:** {q['answer']}")
                    st.divider()

            # Export
            word_bytes = to_word_mcqs(st.session_state["mcqs"])
            fname = f"ADI_Knowledge_MCQs_Week{week}_Lesson{lesson}_{datetime.now().strftime('%Y%m%d_%H%M')}.{'docx' if Document else 'txt'}"
            st.download_button("Export to Word", data=word_bytes, file_name=fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document" if Document else "text/plain", use_container_width=True)

    # ---------- Skills Tab ----------
    with tabs[1]:
        st.subheader("Skills")
        st.markdown(
            """Use this space for skills-based prompts, rubrics, or checklists.
            (Coming soon: scenario-based questions and rubric export.)"""
        )

    # ---------- Activities Tab ----------
    with tabs[2]:
        st.subheader("Activities")
        st.markdown(
            """Plan activities aligned to your topics and Bloom’s level.
            (Coming soon: activity templates and timing planner.)"""
        )

    # ---------- Revision Tab ----------
    with tabs[3]:
        st.subheader("Revision")
        st.markdown(
            """Build quick revision sheets from your selected topics.
            (Coming soon: auto-summaries & printable packs.)"""
        )

with right:
    st.markdown(f'<div class="card"><h3 style="margin-top:0">Live Preview</h3>', unsafe_allow_html=True)
    if selected_topics:
        st.write("**Topics**")
        for t in selected_topics:
            st.write(f"• {t}")
    else:
        st.info("Your selected topics will appear here.")
    st.write("---")
    st.write("**Bloom’s verbs** (by level)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("Low")
        st.write(", ".join(LOW_VERBS))
    with c2:
        st.caption("Medium")
        st.write(", ".join(MED_VERBS))
    with c3:
        st.caption("High")
        st.write(", ".join(HIGH_VERBS))
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.caption("ADI-branded, simple, and crash-safe. First export: Word; randomization included.")
