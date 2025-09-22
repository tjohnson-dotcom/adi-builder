# app.py — ADI Builder (Streamlit, Branded + Icons + Banner + Bloom Verbs & Auto‑Select + Tips & Chips)
# Adds: level tooltips/explanations and verb "chips" shown in activity cards.

from __future__ import annotations
import streamlit as st
from io import BytesIO
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")

# ADI Brand Colors
ADI_GREEN = "#006C35"
ADI_BEIGE = "#C8B697"
ADI_SAND = "#D9CFC2"
ADI_BROWN = "#6B4E3D"
ADI_GRAY = "#F5F5F5"

CUSTOM_CSS = f"""
<style>
.stApp {{
  background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%);
}}
html, body, [class*="css"] {{ font-family: 'Segoe UI', Roboto, Inter, sans-serif; }}
h1, h2, h3 {{ font-weight: 700; color: {ADI_GREEN}; }}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{ border-bottom: 4px solid {ADI_GREEN}; font-weight: 600; color: {ADI_GREEN}; }}
.banner {{ background: {ADI_GREEN}; color: white; padding: 18px 28px; border-radius: 0 0 10px 10px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }}
.banner h1 {{ color: white !important; font-size: 1.6rem; margin: 0; }}
.banner img {{ height: 40px; }}
.card {{ background: #fff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 20px; margin: 14px 0; border-left: 6px solid {ADI_GREEN}; }}
.card h4 {{ margin: 0 0 10px 0; color: {ADI_GREEN}; }}
.card .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 8px; }}
.card .label {{ font-weight: 600; color: {ADI_BROWN}; }}
.toolbar {{ display: flex; justify-content: flex-end; gap: 12px; margin: 16px 0; }}
.stButton>button {{ background: {ADI_GREEN}; color: white; border: none; border-radius: 10px; padding: 10px 18px; font-weight: 600; transition: background 0.2s; }}
.stButton>button:hover {{ background: {ADI_BROWN}; }}
textarea.output-box {{ width: 100%; height: 240px; border-radius: 10px; padding: 12px; font-size: 0.95rem; line-height: 1.4; border: 1px solid #ccc; }}
.badge {{ display:inline-block; padding:4px 8px; background:{ADI_SAND}; border-radius:8px; font-size:0.8rem; color:#333; margin-left:8px; }}
/* Chips for verbs */
.chips { margin-top: 10px; display:flex; flex-wrap:wrap; gap:6px; }
.chip { background:{ADI_SAND}; color:{ADI_BROWN}; border:1px solid #e7ddd2; padding:4px 8px; border-radius:999px; font-size:0.8rem; }
.chip.more { background:#f0ebe4; color:#555; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Banner header
st.markdown(
    f"""
    <div class='banner'>
        <h1>🎓 ADI Builder — Lesson Activities & Questions <span class='badge'>Branded</span></h1>
        <img src='https://i.imgur.com/F4P6o5D.png' alt='ADI Logo'>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Professional, branded, editable and export-ready.")

# ----------------------
# Bloom's Taxonomy Verbs & Tips
# ----------------------
VERBS_CATALOG = {
    "Remember": [
        "define", "duplicate", "label", "list", "match", "memorize", "name", "omit", "recall", "recognize", "record", "repeat", "reproduce", "state"
    ],
    "Understand": [
        "classify", "convert", "defend", "describe", "discuss", "distinguish", "estimate", "explain", "express", "identify", "indicate", "locate", "recognize", "report", "restate", "review", "select", "translate", "summarize"
    ],
    "Apply": [
        "apply", "change", "choose", "compute", "demonstrate", "discover", "dramatize", "employ", "illustrate", "interpret", "manipulate", "modify", "operate", "practice", "schedule", "sketch", "solve", "use"
    ],
    "Analyze": [
        "analyze", "appraise", "break down", "calculate", "categorize", "compare", "contrast", "criticize", "debate", "deduce", "diagram", "differentiate", "discriminate", "distinguish", "examine", "experiment", "infer", "inspect", "inventory", "question", "test"
    ],
    "Evaluate": [
        "appraise", "argue", "assess", "attach value", "choose", "compare", "conclude", "contrast", "criticize", "decide", "defend", "estimate", "evaluate", "explain", "grade", "judge", "justify", "measure", "predict", "rate", "revise", "score", "select", "support", "value"
    ],
    "Create": [
        "arrange", "assemble", "categorize", "collect", "combine", "compose", "construct", "create", "design", "develop", "explain solution", "formulate", "generate", "manage", "organize", "plan", "prepare", "propose", "rearrange", "reconstruct", "relate", "rewrite", "set up", "summarize", "write"
    ],
}

LEVEL_TIPS = {
    "Remember": "Focus on recall and recognition of facts, terms, and basic concepts. Good for quick checks and baseline knowledge.",
    "Understand": "Demonstrate comprehension by summarizing, explaining, and classifying. Useful for discussions and concept checks.",
    "Apply": "Use knowledge in new situations—solving problems, demonstrating procedures, or practicing skills.",
    "Analyze": "Break concepts into parts, compare/contrast, and examine relationships. Great for case analysis and diagnostics.",
    "Evaluate": "Make judgments using criteria—justify, critique, or defend decisions. Ideal for reviews and debates.",
    "Create": "Produce new or original work—design, compose, develop. Capstone projects and authentic tasks fit here.",
}

# Recommended (short) defaults per level
VERBS_DEFAULT = {
    "Remember": ["define", "list", "recall"],
    "Understand": ["classify", "explain", "summarize"],
    "Apply": ["demonstrate", "solve", "use"],
    "Analyze": ["compare", "differentiate", "organize"],
    "Evaluate": ["justify", "critique", "defend"],
    "Create": ["design", "compose", "develop"],
}

# ----------------------
# Sidebar controls
# ----------------------
st.sidebar.header("Upload Source (Optional)")
upload = st.sidebar.file_uploader("PDF / DOCX / PPTX (≤200MB)", type=["pdf", "docx", "pptx"])

col1, col2 = st.sidebar.columns(2)
num_activities = col1.number_input("Activities", 1, 10, 3)
duration = col2.number_input("Duration (mins)", 5, 180, 45)

level = st.sidebar.selectbox(
    "Bloom's Level",
    list(VERBS_CATALOG.keys()),
    index=2,
    key="level",
    help=LEVEL_TIPS["Apply"],  # default help text; will also show detailed tip below
)

# Show fuller tip below the selector to ensure readability
st.sidebar.info(f"**{level}**: {LEVEL_TIPS[level]}")

# Initialize session state for verbs selection per level
if "verbs_by_level" not in st.session_state:
    st.session_state.verbs_by_level = {k: VERBS_DEFAULT[k][:] for k in VERBS_DEFAULT}

# Options available for the current level
level_options = VERBS_CATALOG[level]
current_selected = st.session_state.verbs_by_level.get(level, VERBS_DEFAULT[level])

# Select all / auto-select buttons
col_sa1, col_sa2 = st.sidebar.columns([1,1])
if col_sa1.button("Select all verbs"):
    st.session_state.verbs_by_level[level] = level_options[:]
    st.rerun()
if col_sa2.button("Auto‑select best"):
    st.session_state.verbs_by_level[level] = VERBS_DEFAULT[level][:]
    st.rerun()

# Multiselect bound to session state
verbs = st.sidebar.multiselect(
    "Preferred verbs (per level)",
    options=level_options,
    default=current_selected,
    key=f"verbs_multiselect_{level}",
)
# Keep session state in sync
st.session_state.verbs_by_level[level] = verbs if verbs else VERBS_DEFAULT[level][:]

st.sidebar.caption("Tip: Use **Select all** or **Auto‑select** to quickly choose verbs. Staff can edit outputs in the white box before exporting.")

# Chips preview of chosen verbs
def chips_html(vs:list[str], max_show:int=6) -> str:
    shown = vs[:max_show]
    rest = len(vs) - len(shown)
    chips = "".join([f"<span class='chip'>{v}</span>" for v in shown])
    more = f"<span class='chip more'>+{rest} more</span>" if rest > 0 else ""
    return f"<div class='chips'>{chips}{more}</div>"

st.sidebar.markdown("**Selected verbs preview:**", unsafe_allow_html=True)
st.sidebar.markdown(chips_html(st.session_state.verbs_by_level[level]), unsafe_allow_html=True)

# ----------------------
# Main Tabs
# ----------------------
kn_tab, skills_tab = st.tabs(["Knowledge MCQs", "Skills Activities"])

with kn_tab:
    st.subheader("Generate MCQs (placeholder)")
    n_mcq = st.number_input("How many MCQs?", 1, 50, 5)
    topic = st.text_input("Topic (optional)", "Module description, knowledge & skills outcomes")
    if st.button("Generate MCQs"):
        output_lines = []
        for i in range(1, n_mcq+1):
            q = f"Q{i}. Which statement best relates to: {topic}? (Options: A–D)"
            output_lines.append(q)
            st.markdown(f"<div class='card'><h4>📝 Q{i}</h4><div>{q}</div></div>", unsafe_allow_html=True)
        mcq_text = "\n".join(output_lines)
        edited_mcq = st.text_area("✏️ Edit questions before export:", mcq_text, key="mcq_edit", height=220)
        st.download_button("⬇️ Export MCQs (TXT)", edited_mcq, file_name="mcqs.txt")

with skills_tab:
    st.subheader("Generate Skills Activities")

    # Use the selected verbs for the current level
    chosen_verbs = st.session_state.verbs_by_level[level]

    # Show chips in main area too for quick confirmation
    st.markdown("**Verbs in use:**", unsafe_allow_html=True)
    st.markdown(chips_html(chosen_verbs), unsafe_allow_html=True)

    if st.button("Generate Activities", type="primary"):
        activities = []
        for i in range(1, num_activities+1):
            verb = chosen_verbs[(i-1) % max(1, len(chosen_verbs))]
            task = f"Work in pairs to {verb} the key concept from today's topic, referencing a real-world context."
            act = (
                f"Activity {i} — {duration} mins\n"
                f"Task: {task}\n"
                f"Output: Short presentation or diagram.\n"
                f"Evidence: Upload to LMS."
            )
            activities.append(act)
            st.markdown(
                f"""
                <div class='card'>
                <h4>📌 Activity {i} — {duration} mins</h4>
                <div class='meta'>Bloom's Level: {level} · Verb in use: <b>{verb}</b></div>
                <div class='chips'>{''.join([f"<span class='chip'>{v}</span>" for v in chosen_verbs[:6]])}{'<span class=\'chip more\'>+' + str(max(0,len(chosen_verbs)-6)) + ' more</span>' if len(chosen_verbs)>6 else ''}</div>
                <div><span class='label'>📝 Task:</span> {task}</div>
                <div><span class='label'>📊 Output:</span> Short presentation or diagram.</div>
                <div><span class='label'>📤 Evidence:</span> Upload to LMS.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Editable export text box
        text_output = "\n\n".join(activities)
        edited_output = st.text_area("✏️ Review & edit before export:", text_output, key="act_edit", height=260)

        # Export toolbar
        st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
        st.download_button("📄 TXT", edited_output, file_name="adi_activities.txt")
        st.download_button("📥 Moodle GIFT", edited_output, file_name="adi_activities.gift")
        st.download_button("🗎 Word (.doc)", edited_output, file_name="adi_activities.doc")
        if DOCX_AVAILABLE:
            # Simple DOCX export
            doc = Document()
            s = doc.styles['Normal']
            s.font.name = 'Calibri'
            s.font.size = Pt(11)
            doc.add_heading('ADI Builder — Skills Activities', level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for block in activities:
                for line in block.split("\n"):
                    if line.startswith("Activity"):
                        doc.add_heading(line, level=2)
                    else:
                        doc.add_paragraph(line)
            bio = BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.download_button("📝 Word (.docx)", bio.getvalue(), file_name="adi_activities.docx")
        else:
            st.info("To enable Word (.docx) export, add `python-docx` to requirements.txt.")
        st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<hr><div style='text-align:center; color:#666;'>© Academy of Defense Industries — ADI Builder</div>", unsafe_allow_html=True)
