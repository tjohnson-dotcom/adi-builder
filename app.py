# app.py — ADI Builder (Streamlit, Branded + Upload + Lesson/Week Extractor + Bloom Verbs + Auto‑Select + Tips/Chips)
# Sleek, professional, and staff‑friendly. Upload eBook/Plan/PPT → pick Lesson/Week → edit in white box → export.

from __future__ import annotations
import streamlit as st
from io import BytesIO
from datetime import datetime
import re

# === Optional libraries and graceful fallbacks ===
try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except Exception:
    PPTX_AVAILABLE = False

st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")

# === ADI Brand Colors ===
ADI_GREEN = "#006C35"
ADI_BEIGE = "#C8B697"
ADI_SAND  = "#D9CFC2"
ADI_BROWN = "#6B4E3D"
ADI_GRAY  = "#F5F5F5"

CUSTOM_CSS = f"""
<style>
.stApp {{ background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%); }}
html, body, [class*="css"] {{ font-family: 'Segoe UI', Roboto, Inter, sans-serif; }}
h1, h2, h3 {{ font-weight: 700; color: {ADI_GREEN}; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  border-bottom: 4px solid {ADI_GREEN};
  font-weight: 600; color: {ADI_GREEN};
}}

/* Banner */
.banner {{ background: {ADI_GREEN}; color: white; padding: 18px 28px; border-radius: 0 0 12px 12px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }}
.banner h1 {{ color: white !important; font-size: 1.6rem; margin: 0; }}
.banner img {{ height: 40px; }}

/* Cards */
.card {{ background:#fff; border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,0.08); padding:20px; margin:14px 0; border-left:6px solid {ADI_GREEN}; }}
.card h4 {{ margin:0 0 10px 0; color:{ADI_GREEN}; }}
.card .meta {{ color:#666; font-size:0.9rem; margin-bottom:8px; }}
.card .label {{ font-weight:600; color:{ADI_BROWN}; }}

/* Toolbar */
.toolbar {{ display:flex; justify-content:flex-end; gap:12px; margin:16px 0; flex-wrap: wrap; }}

/* Buttons */
.stButton>button { background:"+ "{ADI_GREEN}" +"; color:#fff; border:none; border-radius:10px; padding:8px 14px; font-weight:600; font-size:0.9rem; white-space:nowrap; transition:background .2s; }; color:#fff; border:none; border-radius:10px; padding:10px 18px; font-weight:600; transition:background .2s; }}
.stButton>button:hover {{ background:{ADI_BROWN}; }}

/* White editable areas */
textarea.output-box {{ width:100%; height:240px; border-radius:10px; padding:12px; font-size:.95rem; line-height:1.45; border:1px solid #ccc; background:#fff; }}

/* Badges + Chips */
.badge {{ display:inline-block; padding:4px 8px; background:{ADI_SAND}; border-radius:8px; font-size:.8rem; color:#333; margin-left:8px; }}
.chips {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }}
.chip {{ background:{ADI_SAND}; color:{ADI_BROWN}; border:1px solid #e7ddd2; padding:4px 8px; border-radius:999px; font-size:.8rem; }}
.chip.more {{ background:#f0ebe4; color:#555; }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# === Banner ===
st.markdown(
    f"""
    <div class='banner'>
        <h1>🎓 ADI Builder — Lesson Activities & Questions <span class='badge'>Branded</span></h1>
        <img src='https://i.imgur.com/F4P6o5D.png' alt='ADI Logo'>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Professional, branded, editable and export‑ready.")

# === Bloom's Taxonomy ===
VERBS_CATALOG = {
    "Remember": ["define","duplicate","label","list","match","memorize","name","omit","recall","recognize","record","repeat","reproduce","state"],
    "Understand": ["classify","convert","defend","describe","discuss","distinguish","estimate","explain","express","identify","indicate","locate","recognize","report","restate","review","select","translate","summarize"],
    "Apply": ["apply","change","choose","compute","demonstrate","discover","dramatize","employ","illustrate","interpret","manipulate","modify","operate","practice","schedule","sketch","solve","use"],
    "Analyze": ["analyze","appraise","break down","calculate","categorize","compare","contrast","criticize","debate","deduce","diagram","differentiate","discriminate","distinguish","examine","experiment","infer","inspect","inventory","question","test"],
    "Evaluate": ["appraise","argue","assess","attach value","choose","compare","conclude","contrast","criticize","decide","defend","estimate","evaluate","explain","grade","judge","justify","measure","predict","rate","revise","score","select","support","value"],
    "Create": ["arrange","assemble","categorize","collect","combine","compose","construct","create","design","develop","explain solution","formulate","generate","manage","organize","plan","prepare","propose","rearrange","reconstruct","relate","rewrite","set up","summarize","write"],
}
LEVEL_TIPS = {
    "Remember":"Recall/recognize facts & terms.",
    "Understand":"Explain & summarize concepts.",
    "Apply":"Use knowledge in new situations.",
    "Analyze":"Compare/contrast; examine relationships.",
    "Evaluate":"Judge/justify using criteria.",
    "Create":"Produce original work; design & develop.",
}
VERBS_DEFAULT = {
    "Remember":["define","list","recall"],
    "Understand":["classify","explain","summarize"],
    "Apply":["demonstrate","solve","use"],
    "Analyze":["compare","differentiate","organize"],
    "Evaluate":["justify","critique","defend"],
    "Create":["design","compose","develop"],
}

# === Sidebar: Upload + Extractor + Controls ===
st.sidebar.header("Upload eBook / Lesson Plan / PPT")
upload = st.sidebar.file_uploader("PDF / DOCX / PPTX (≤200MB)", type=["pdf","docx","pptx"])

@st.cache_resource(show_spinner=False)
def parse_file(file):
    if file is None:
        return ""
    name = file.name.lower()
    if name.endswith(".pdf") and PDF_AVAILABLE:
        reader = PdfReader(file)
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages)
    if name.endswith(".docx") and DOCX_AVAILABLE:
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)
    if name.endswith(".pptx") and PPTX_AVAILABLE:
        prs = Presentation(file)
        parts = []
        for s in prs.slides:
            for shp in s.shapes:
                if hasattr(shp, "text"):
                    parts.append(shp.text)
        return "\n".join(parts)
    return ""

@st.cache_resource(show_spinner=False)
def index_sections(full_text:str):
    if not full_text:
        return {}, {}
    text = re.sub(r"\u00a0", " ", full_text)
    # Capture headings like "Lesson 1" / "Week 3" at line starts (case‑insensitive)
    lesson_matches = list(re.finditer(r"(?im)^(lesson\s*(\d{1,2}))\b.*$", text))
    week_matches   = list(re.finditer(r"(?im)^(week\s*(\d{1,2}))\b.*$", text))

    def slice_by(matches):
        sections = {}
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            try:
                idx = int(m.group(2))
            except Exception:
                continue
            sections[idx] = text[start:end].strip()
        return sections

    return slice_by(lesson_matches), slice_by(week_matches)

# Parse once on upload
if upload is not None and "parsed_text_blob" not in st.session_state:
    blob = parse_file(upload)
    st.session_state.parsed_text_blob = blob
    st.session_state.lessons, st.session_state.weeks = index_sections(blob)

# Lesson/Week selectors (show only when we have text)
if st.session_state.get("parsed_text_blob"):
    st.sidebar.subheader("Pick from eBook/Plan/PPT")
    lkeys = sorted(st.session_state.lessons.keys()) or list(range(1,15))
    wkeys = sorted(st.session_state.weeks.keys()) or list(range(1,15))
    sel_lesson = st.sidebar.selectbox("📖 Lesson", options=["—"]+[str(k) for k in lkeys], index=0)
    sel_week   = st.sidebar.selectbox("🗓️ Week",   options=["—"]+[str(k) for k in wkeys], index=0)
    c1, c2 = st.sidebar.columns(2)
    pull_mcq  = c1.button("Pull → MCQs")
    pull_acts = c2.button("Pull → Activities")

    def selected_text():
        parts = []
        if isinstance(sel_lesson,str) and sel_lesson.isdigit() and int(sel_lesson) in st.session_state.lessons:
            parts.append(st.session_state.lessons[int(sel_lesson)])
        if isinstance(sel_week,str) and sel_week.isdigit() and int(sel_week) in st.session_state.weeks:
            parts.append(st.session_state.weeks[int(sel_week)])
        return "\n\n".join(parts).strip()

    preview = selected_text()
    if preview:
        st.sidebar.caption("Preview of selection:")
        st.sidebar.text_area("", value=preview[:2000], height=140)
    else:
        st.sidebar.caption("No Lesson/Week headings detected — using generic 1–14 selectors.")

    if pull_mcq:
        st.session_state.mcq_seed = preview
    if pull_acts:
        st.session_state.act_seed = preview

# Activity parameters
st.sidebar.subheader("Activity Parameters")
col1, col2 = st.sidebar.columns(2)
num_activities = col1.number_input("Activities", 1, 10, 3)
duration       = col2.number_input("Duration (mins)", 5, 180, 45)

level = st.sidebar.selectbox("Bloom's Level", list(VERBS_CATALOG.keys()), index=2, key="level")
st.sidebar.info(f"**{level}**: {LEVEL_TIPS[level]}")

# Track selected verbs per level
if "verbs_by_level" not in st.session_state:
    st.session_state.verbs_by_level = {k: VERBS_DEFAULT[k][:] for k in VERBS_DEFAULT}

level_options = VERBS_CATALOG[level]
current_selected = st.session_state.verbs_by_level.get(level, VERBS_DEFAULT[level])

b1, b2 = st.sidebar.columns(2)
if b1.button("Select all verbs"):
    st.session_state.verbs_by_level[level] = level_options[:]
    st.rerun()
if b2.button("Auto‑select best"):
    st.session_state.verbs_by_level[level] = VERBS_DEFAULT[level][:]
    st.rerun()

valid_defaults = [v for v in current_selected if v in level_options]
# Ensure defaults are valid for the selected level
valid_defaults = [v for v in current_selected if v in level_options]
verbs = st.sidebar.multiselect(
    "Preferred verbs (per level)",
    options=level_options,
    default=valid_defaults if valid_defaults else VERBS_DEFAULT[level],
    key=f"verbs_{level}"
)
st.session_state.verbs_by_level[level] = verbs if verbs else VERBS_DEFAULT[level][:]

st.sidebar.markdown("**Selected verbs preview:**")
sel_preview = st.session_state.verbs_by_level[level]
st.sidebar.markdown(""+"<div class='chips'>"+"".join([f"<span class='chip'>{v}</span>" for v in sel_preview[:6]])+(f"<span class='chip more'>+{len(sel_preview)-6} more</span>" if len(sel_preview)>6 else "")+"</div>", unsafe_allow_html=True)

# === Main Tabs ===
kn_tab, skills_tab = st.tabs(["Knowledge MCQs", "Skills Activities"])

with kn_tab:
    st.subheader("Generate MCQs (from source or manual)")
    if st.session_state.get("mcq_seed"):
        st.success("Inserted Lesson/Week text into MCQ editor.")
    n_mcq = st.number_input("How many MCQs?", 1, 50, 5)
    topic = st.text_input("Topic (optional)", "Module description, knowledge & skills outcomes")
    base_text = st.text_area("Source text (editable)", value=st.session_state.get("mcq_seed", ""), key="mcq_source_box", height=220)

    if st.button("Generate MCQs"):
        import random
        # A mix of question patterns (definition, example, application, true/false, missing term, sequence)
        TEMPLATES = [
            lambda t: (f"Which of the following is the **best definition** of {t}?", ["A) A broad opinion","B) A precise explanation","C) An unrelated example","D) None of the above"], "B"),
            lambda t: (f"Which option **best illustrates** {t} in practice?", ["A) A generic list","B) A real‑world case that matches the concept","C) An opposite of the concept","D) None of the above"], "B"),
            lambda t: (f"You must apply {t} to a new situation. **What should you do first?**", ["A) Ignore the scenario","B) Identify the key variables and constraints","C) Memorize the definition","D) None of the above"], "B"),
            lambda t: (f"**Which statement is TRUE** about {t}?", ["A) It never varies","B) It always produces the same output","C) It depends on the given conditions","D) None of the above"], "C"),
            lambda t: (f"Fill the blank: **{t}** involves ____.", ["A) random guessing","B) structured analysis","C) ignoring evidence","D) None of the above"], "B"),
            lambda t: (f"Place the steps for **{t}** in the correct order (first to last). Which option is correct?", ["A) Decide → Evaluate → Define","B) Define → Apply → Evaluate","C) Apply → Define → Evaluate","D) None of the above"], "B"),
        ]
        mcqs = []
        for i in range(1, n_mcq+1):
            stem, opts, ans = random.choice(TEMPLATES)(topic)
            mcqs.append((stem, opts, ans))
        for i, (stem, opts, ans) in enumerate(mcqs, 1):
            options_html = "<br/>".join(opts)
            st.markdown(
                f"""
                <div class='card'>
                  <h4>📝 Question {i}</h4>
                  <div class='meta'>Single best answer</div>
                  <div>{stem}</div>
                  <div style='margin-top:6px;'>{options_html}</div>
                  <div style='margin-top:8px;'>Answer: <span class='answer-badge'>{ans}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        edited_mcq = st.text_area("✏️ Edit questions before export:", "
".join([q[0] for q in mcqs]), key="mcq_edit", height=220)
        st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
        st.download_button("📄 TXT", edited_mcq, file_name="mcqs.txt")
        st.download_button("📥 Moodle GIFT", edited_mcq, file_name="mcqs.gift")
        st.download_button("🗎 Word (.doc)", edited_mcq, file_name="mcqs.doc")
        st.markdown("</div>", unsafe_allow_html=True)

with skills_tab:
    st.subheader("Generate Skills Activities (from source or manual)")

    # Show selected verbs as chips
    st.markdown("**Verbs in use:**", unsafe_allow_html=True)
    st.markdown(""+"<div class='chips'>"+"".join([f"<span class='chip'>{v}</span>" for v in sel_preview[:6]])+(f"<span class='chip more'>+{len(sel_preview)-6} more</span>" if len(sel_preview)>6 else "")+"</div>", unsafe_allow_html=True)

    context_text = st.text_area("Context from eBook / notes (editable)", value=st.session_state.get("act_seed", ""), key="act_context_box", height=220)

    if st.button("Generate Activities", type="primary"):
        chosen_verbs = st.session_state.verbs_by_level[level]
        activities = []
        for i in range(1, num_activities+1):
            verb = chosen_verbs[(i-1) % max(1, len(chosen_verbs))]
            task = f"Using the provided context, work in pairs to {verb} a key concept relevant to the selected lesson/week."
            act = (
                f"Activity {i} — {duration} mins\n"
                f"Task: {task}\n"
                f"Output: Short presentation or diagram.\n"
                f"Evidence: Upload to LMS."
            )
            activities.append(act)
            st.markdown(f"""
            <div class='card'>
              <h4>📌 Activity {i} — {duration} mins</h4>
              <div class='meta'>Bloom's Level: {level} · Verb in use: <b>{verb}</b></div>
              <div class='chips'>{''.join([f"<span class='chip'>{v}</span>" for v in chosen_verbs[:6]])}{'<span class=\'chip more\'>+' + str(max(0,len(chosen_verbs)-6)) + ' more</span>' if len(chosen_verbs)>6 else ''}</div>
              <div><span class='label'>📝 Task:</span> {task}</div>
              <div><span class='label'>📊 Output:</span> Short presentation or diagram.</div>
              <div><span class='label'>📤 Evidence:</span> Upload to LMS.</div>
            </div>
            """, unsafe_allow_html=True)

        text_output = "\n\n".join(activities)
        edited_output = st.text_area("✏️ Review & edit before export:", text_output, key="act_edit", height=260)

        st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
        st.download_button("📄 TXT", edited_output, file_name="adi_activities.txt")
        st.download_button("📥 Moodle GIFT", edited_output, file_name="adi_activities.gift")
        st.download_button("🗎 Word (.doc)", edited_output, file_name="adi_activities.doc")
        if DOCX_AVAILABLE:
            doc = Document()
            s = doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Skills Activities', level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for block in activities:
                for line in block.split("\n"):
                    if line.startswith("Activity"):
                        doc.add_heading(line, level=2)
                    else:
                        doc.add_paragraph(line)
            bio = BytesIO(); doc.save(bio); bio.seek(0)
            st.download_button("📝 Word (.docx)", bio.getvalue(), file_name="adi_activities.docx")
        else:
            st.info("To enable Word (.docx) export, add `python-docx` to requirements.txt.")
        st.markdown("</div>", unsafe_allow_html=True)

# === Footer ===
st.markdown("<hr><div style='text-align:center; color:#666;'>© Academy of Defense Industries — ADI Builder</div>", unsafe_allow_html=True)

