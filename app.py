# app.py — ADI Builder (Streamlit)
# Sleek UI with export buttons (Word/DOCX, Moodle GIFT, TXT), clean cards, tabs.
# If deploying on Streamlit Cloud, add to requirements.txt:
# streamlit
# python-docx

from __future__ import annotations
import streamlit as st
from io import BytesIO
from datetime import datetime

# Optional DOCX export
try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

# -------------------------------
# Page Config & Style
# -------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")

PRIMARY = "#0BA360"  # ADI green accent
BG_GRADIENT = "linear-gradient(180deg, #f7f9fb 0%, #eef2f6 100%)"

CUSTOM_CSS = f"""
<style>
/**** Page background ****/
.stApp {{
  background: {BG_GRADIENT};
}}

/* Typography */
html, body, [class*="css"] {{
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  letter-spacing: 0.1px;
}}

/* Headings */
h1, h2, h3, h4 {{
  font-weight: 700;
}}

/* Accent tabs */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  border-bottom: 3px solid {PRIMARY};
}}

/* Card container */
.card {{
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.06);
  padding: 18px 20px;
  margin: 12px 0 8px 0;
  border: 1px solid #eef0f3;
}}
.card h4 {{ margin: 0 0 8px 0; font-size: 1.05rem; }}
.card .meta {{ color: #556; font-size: 0.88rem; margin-bottom: 6px; }}
.card .label {{ font-weight: 600; }}

/* Toolbar */
.toolbar {{
  display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; align-items: center;
  padding: 8px; margin-top: 6px; margin-bottom: 10px;
}}
.toolbar .hint {{ font-size: 0.86rem; color: #5a6; margin-right: auto; }}

/* Buttons (slight rounding) */
.stButton>button {{
  border-radius: 12px !important;
  padding: 8px 14px !important;
  box-shadow: 0 3px 10px rgba(0,0,0,0.04);
}}

/* Inputs */
.block-container {{ padding-top: 1.2rem; }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------
# Sidebar (brand + inputs)
# -------------------------------
st.sidebar.image(
    "https://dummyimage.com/300x80/0BA360/ffffff.png&text=ADI+Builder",
    use_column_width=True,
)

st.sidebar.markdown("### Upload source (optional)")
upload = st.sidebar.file_uploader("PDF / DOCX / PPTX (≤200MB)", type=["pdf", "docx", "pptx"], help="Used to extract topics or text if you want.")

st.sidebar.markdown("---")

col1, col2 = st.sidebar.columns(2)
num_activities = col1.number_input("# Activities", min_value=1, max_value=10, value=3)
duration = col2.number_input("Duration (mins)", min_value=5, max_value=180, value=45)

level = st.sidebar.selectbox("Bloom's Level (focus)", [
    "Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"
], index=2)

verbs_default = {
    "Remember": ["list", "define", "recall"],
    "Understand": ["summarize", "classify", "explain"],
    "Apply": ["demonstrate", "solve", "use"],
    "Analyze": ["compare", "differentiate", "organize"],
    "Evaluate": ["justify", "critique", "defend"],
    "Create": ["design", "compose", "develop"]
}
verbs = st.sidebar.multiselect("Preferred verbs", verbs_default[level], default=verbs_default[level])

st.sidebar.markdown("---")

st.sidebar.caption("Tip: Export buttons appear after you generate content.")

# -------------------------------
# Helpers
# -------------------------------

def make_activity(i: int, total: int, duration: int, level: str, verbs: list[str]):
    v = verbs[(i-1) % max(1, len(verbs))] if verbs else "apply"
    task = (
        f"Work in pairs to {v} the key concept from today's topic. Use a real-world example from your context."
        if level in {"Understand", "Apply"} else
        f"In small groups, {v} alternative approaches to the problem and choose the best one."
        if level in {"Analyze", "Evaluate"} else
        f"Individually, {v} a simple artifact that demonstrates your understanding."
    )
    output = (
        "Short presentation or annotated diagram"
        if level in {"Understand", "Analyze"} else
        "One-page write‑up or screencast"
        if level in {"Apply", "Evaluate"} else
        "Prototype/mockup or concept map"
    )
    evidence = "Upload to LMS (photo, PDF, or link)."
    title = f"Activity {i} of {total} — {duration} mins"
    return {
        "title": title,
        "task": task,
        "output": output,
        "evidence": evidence,
        "duration": duration,
    }


def render_activity_card(act: dict):
    st.markdown(
        f"""
        <div class='card'>
          <h4>{act['title']}</h4>
          <div class='meta'>Designed for Bloom's focus: <b>{level}</b></div>
          <div><span class='label'>Task:</span> {act['task']}</div>
          <div><span class='label'>Output:</span> {act['output']}</div>
          <div><span class='label'>Evidence:</span> {act['evidence']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def activities_to_text(acts: list[dict]) -> str:
    lines = []
    for i, a in enumerate(acts, 1):
        lines.append(f"{i}. ({a['duration']} mins) {a['title']}")
        lines.append(f"   Task: {a['task']}")
        lines.append(f"   Output: {a['output']}")
        lines.append(f"   Evidence: {a['evidence']}")
        lines.append("")
    return "\n".join(lines).strip()


def activities_to_gift(acts: list[dict]) -> str:
    # Represent each activity as a GIFT comment block
    chunks = []
    for i, a in enumerate(acts, 1):
        body = f"Task: {a['task']}\nOutput: {a['output']}\nEvidence: {a['evidence']}"
        chunks.append(f"// Activity {i} ({a['duration']} mins)\n// {body}\n")
    return "\n".join(chunks).strip()


def activities_to_docx(acts: list[dict]) -> bytes:
    doc = Document()
    s = doc.styles['Normal']
    s.font.name = 'Calibri'
    s.font.size = Pt(11)
    doc.add_heading('ADI Builder — Skills Activities', level=1)
    doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
    for i, a in enumerate(acts, 1):
        doc.add_heading(f"{i}. ({a['duration']} mins) {a['title']}", level=2)
        p = doc.add_paragraph()
        p.add_run("Task: ").bold = True
        doc.add_paragraph(a['task'])
        p = doc.add_paragraph()
        p.add_run("Output: ").bold = True
        doc.add_paragraph(a['output'])
        p = doc.add_paragraph()
        p.add_run("Evidence: ").bold = True
        doc.add_paragraph(a['evidence'])
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()


def to_bytes(s: str) -> bytes:
    return s.encode('utf-8')

# -------------------------------
# Main UI
# -------------------------------
st.title("ADI Builder — Lesson Activities & Questions")

subtitle_left, subtitle_right = st.columns([0.6, 0.4])
with subtitle_left:
    st.caption("Sleek, engaging, and export‑ready. Upload content (optional), set your parameters, and generate.")
with subtitle_right:
    st.write("")

# Tabs
kn_tab, skills_tab = st.tabs(["Knowledge MCQs", "Skills Activities"])  # MCQ stub kept for parity

# -------------------------------
# Knowledge MCQs (readable text area + placeholder generation)
# -------------------------------
with kn_tab:
    st.subheader("Generate MCQs (placeholder)")
    colk1, colk2 = st.columns([1,1])
    with colk1:
        n_mcq = st.number_input("How many MCQs?", 1, 50, 5)
    with colk2:
        kn_topic = st.text_input("Topic (optional)", "Module description, knowledge & skills outcomes")

    gen_mcq = st.button("Generate MCQs", key="btn_mcq")

    if gen_mcq:
        # simple placeholder questions
        mcqs = []
        for i in range(1, n_mcq+1):
            stem = f"({i}) Which statement best relates to: {kn_topic}?"
            opts = ["A) Definition", "B) Example", "C) Contrast", "D) None of the above"]
            answer = "B"
            mcqs.append((stem, opts, answer))

        for i, (stem, opts, ans) in enumerate(mcqs, 1):
            st.markdown(
                f"""
                <div class='card'>
                <h4>Question {i}</h4>
                <div class='meta'>Single best answer</div>
                <div>{stem}</div>
                <div style='margin-top:6px;'>""" + "<br/>".join(opts) + f"""</div>
                <div style='margin-top:8px; font-size:0.9rem; color:#486;'>Answer: <b>{ans}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# -------------------------------
# Skills Activities
# -------------------------------
with skills_tab:
    st.subheader("Generate Skills Activities")

    colA, colB, colC = st.columns([1,1,1])
    with colA:
        st.text_input("Skills activity title (optional)", value="", key="title_hint")
    with colB:
        st.text_input("Context/notes (optional)", value="", key="notes_hint")
    with colC:
        st.text_input("Assessment link (optional)", value="", key="assess_hint")

    generate = st.button("Generate Activities", type="primary", use_container_width=False, key="btn_act")

    if generate:
        activities = [make_activity(i+1, num_activities, duration, level, verbs) for i in range(num_activities)]

        # Show toolbar with export options
        st.markdown("<div class='toolbar'><span class='hint'>Ready to export</span></div>", unsafe_allow_html=True)

        # Render activity cards
        for act in activities:
            render_activity_card(act)

        # Build export payloads
        txt_payload = activities_to_text(activities)
        gift_payload = activities_to_gift(activities)

        # TXT
        st.download_button(
            label="⬇️ Download TXT",
            file_name="adi_activities.txt",
            mime="text/plain",
            data=to_bytes(txt_payload),
            key="dl_txt"
        )

        # Moodle GIFT
        st.download_button(
            label="⬇️ Export Moodle GIFT",
            file_name="adi_activities.gift",
            mime="text/plain",
            data=to_bytes(gift_payload),
            key="dl_gift"
        )

        # DOCX (Word)
        if DOCX_AVAILABLE:
            docx_bytes = activities_to_docx(activities)
            st.download_button(
                label="⬇️ Download Word (.docx)",
                file_name="adi_activities.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                data=docx_bytes,
                key="dl_docx"
            )
        else:
            st.info("To enable Word (.docx) export, add `python-docx` to requirements.txt.")

        # Legacy .doc as plain text (Word will still open it)
        st.download_button(
            label="⬇️ Download Word (.doc)",
            file_name="adi_activities.doc",
            mime="application/msword",
            data=to_bytes(txt_payload),
            key="dl_doc"
        )

        st.success("Activities generated. Use the buttons above to download.")

# Footer
st.markdown("""
<div style='text-align:center; margin-top:24px; color:#6b7280; font-size:0.9rem;'>
  © ADI Builder — Streamlit UI. Polished with custom CSS, tabs, and export toolbar.
</div>
""", unsafe_allow_html=True)
