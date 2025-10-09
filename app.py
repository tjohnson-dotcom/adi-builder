# ==============================  ADI Builder  ==============================
# Safe, self-contained Streamlit app.py — sticky header, hover/focus, dashed
# uploader, verb bands, local MCQ generation + editable + file downloads.
# ==========================================================================

import streamlit as st
from io import BytesIO
from datetime import date
import random
import textwrap

# Optional imports (defensive)
try:
    from docx import Document
    from docx.shared import Pt
    HAS_DOCX = True
except Exception:
    HAS_DOCX = False

# ========= 1) MUST be the first Streamlit call =========
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========= Build tag (safe AFTER page_config) =========
BUILD_TAG = "2025-10-10 • sticky+hover v2"
st.caption(f"Build: {BUILD_TAG}")
st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)
# --- Sticky top banner ---
st.markdown(
    '<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>',
    unsafe_allow_html=True
)

# ========= 2) Global CSS (pointer/hover/focus; dashed uploader; band) =========
CSS = """
<style>
:root { --adi: #245a34; --adi-dark:#153a27; --ring: #245a34; }

/* Container & spacing */
.block-container { padding-top: 0.6rem; }

/* Top sticky band look (use class .adi-band on any container heading if needed) */
.adi-banner{
  background: var(--adi-dark);
  color:#fff;
  padding:12px 16px;
  font-weight:600;
  border-radius: 0 0 10px 10px;
  position: sticky;
  top: 0;
  z-index: 1000;
  margin: -0.25rem -0.5rem 0.75rem;
}

.band { border: 1px solid #e6ece6; padding: 10px 12px; border-radius: 10px; }
.band + .band { margin-top: 10px; }
.band.active { border-color: var(--adi); box-shadow: 0 0 0 2px var(--adi) inset; }

/* Make interactive bits feel clickable */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button { cursor: pointer !important; }

/* Hover feedback */
div[data-testid="stFileUploaderDropzone"]:hover {
  box-shadow: 0 0 0 3px var(--ring) inset !important;
}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover,
[role="combobox"]:hover, 
[data-baseweb="select"]:hover {
  box-shadow: 0 0 0 2px var(--ring) inset !important;
  border-color: var(--ring) !important;
}

/* Keyboard focus ring for accessibility */
:focus-visible {
  outline: 2px solid var(--ring) !important;
  outline-offset: 2px;
}

/* Green dashed border around the drag-and-drop area */
div[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
  border: 2px dashed var(--adi) !important;
  border-radius: 10px !important;
}

/* Sidebar — keep same hover/focus behaviour */
[data-testid="stSidebar"] div[data-testid="stSelectbox"] button:hover,
[data-testid="stSidebar"] div[data-testid="stMultiSelect"] button:hover,
[data-testid="stSidebar"] [role="combobox"]:hover,
[data-testid="stSidebar"] [data-baseweb="select"]:hover {
  box-shadow: 0 0 0 2px var(--ring) inset !important;
  border-color: var(--ring) !important;
}
[data-testid="stSidebar"] input:focus-visible,
[data-testid="stSidebar"] .stNumberInput input:focus,
[data-testid="stSidebar"] .stDateInput input:focus,
[data-testid="stSidebar"] div[data-testid="stSelectbox"] button:focus-visible,
[data-testid="stSidebar"] div[data-testid="stMultiSelect"] button:focus-visible,
[data-testid="stSidebar"] [role="combobox"]:focus-visible {
  outline: 2px solid var(--ring) !important;
  outline-offset: 2px;
}

/* Tabs spacing aesthetic */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { padding: 6px 10px; border-radius: 8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ========= 3) Data (courses/cohorts/instructors) =========

COURSES = [
    "GE4-IPM — Integrated Project & Materials Management in Defense Technology",
    "GE4-EPM — Defense Technology Practices: Experimentation, Quality Management and Inspection",
    "GE4-MRO — Military Vehicle and Aircraft MRO: Principles & Applications",
    "CT4-COM — Computation for Chemical Technologists",
    "CT4-EMG — Explosives Manufacturing",
    "CT4-TFL — Thermofluids",
    "MT4-CMG — Composite Manufacturing",
    "MT4-CAD — Computer Aided Design",
    "MT4-MAE — Machine Elements",
    "EE4-MFC — Electrical Materials",
    "EE4-PMG — PCB Manufacturing",
    "EE4-PCT — Power Circuits & Transmission",
]
COHORTS = [
    "D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
    "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06",
]
INSTRUCTORS = [
    "Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen Tariq",
    "Dari","Ghamza Labeeb","Michail","Meshari","Mohammed Alwuthaylah","Myra",
    "Meshal Algurabi","Ibrahim Alrawaili","Khalil","Salem","Chetan","Yasser",
    "Ahmed Albader","Muath","Sultan","Dr. Mashael","Noura Aldossari","Daniel"
]

LOW_VERBS = ["define", "identify", "list", "describe", "label", "recall"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

def init_state():
    ss = st.session_state
    ss.setdefault("course_list", COURSES.copy())
    ss.setdefault("cohort_list", COHORTS.copy())
    ss.setdefault("instructor_list", INSTRUCTORS.copy())
    ss.setdefault("topic", "")
    ss.setdefault("low", ["define", "identify", "list"])
    ss.setdefault("med", ["apply", "demonstrate", "solve"])
    ss.setdefault("high", ["evaluate", "synthesize", "design"])
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("n_mcq", 10)
    ss.setdefault("answer_key", True)
    ss.setdefault("mcqs", [])  # list of dicts
    ss.setdefault("last_upload", None)

init_state()

# ========= 4) Sidebar — upload + course details =========

with st.sidebar:
    # Logo (no use_container_width — avoids older Streamlit error)
    try:
        st.image("adi_logo.png", width=160)
    except Exception:
        st.write("")

    st.subheader("Upload (optional)")
    up = st.file_uploader(
        "Drag and drop file here",
        type=["txt","docx","pptx","pdf"],
        accept_multiple_files=True,
        key="uploader"
    )
    if up:
        names = ", ".join(f.name for f in up)
        st.session_state["last_upload"] = names
        st.success(f"Uploaded: {names}")

    st.toggle("Deep scan source (slower, better coverage)", value=False, key="tog_deepscan")

    st.markdown("---")
    st.subheader("Course details")

    # Helper add/remove row
    def add_item(label, key_list):
        new = st.text_input(f"Add new {label}", key=f"add_{label}")
        if st.button(f"Add {label}", key=f"btn_add_{label}"):
            if new and new not in st.session_state[key_list]:
                st.session_state[key_list].append(new)
                st.success(f"Added {label}: {new}")

    def remove_item(label, key_list):
        opts = st.session_state[key_list]
        if opts:
            rem = st.selectbox(f"Remove {label}", opts, key=f"rem_{label}")
            if st.button(f"Remove {label}", key=f"btn_rem_{label}"):
                st.session_state[key_list] = [x for x in opts if x != rem]
                st.warning(f"Removed {label}: {rem}")

    course = st.selectbox("Course name", st.session_state["course_list"], key="sb_course")
    cols = st.columns(2)
    with cols[0]:
        add_item("course", "course_list")
    with cols[1]:
        remove_item("course", "course_list")

    cohort = st.selectbox("Class / Cohort", st.session_state["cohort_list"], key="sb_cohort")
    cols = st.columns(2)
    with cols[0]:
        add_item("cohort", "cohort_list")
    with cols[1]:
        remove_item("cohort", "cohort_list")

    instructor = st.selectbox("Instructor name", st.session_state["instructor_list"], key="sb_instructor")
    cols = st.columns(2)
    with cols[0]:
        add_item("instructor", "instructor_list")
    with cols[1]:
        remove_item("instructor", "instructor_list")

    st.date_input("Date", value=date.today(), key="sb_date")
    st.markdown("### Context")
    c1,c2 = st.columns(2)
    with c1:
        st.number_input("Lesson", min_value=1, value=st.session_state["lesson"], key="sb_lesson")
    with c2:
        st.number_input("Week", min_value=1, value=st.session_state["week"], key="sb_week")

# Persist context back
st.session_state["lesson"] = st.session_state.get("sb_lesson", 1)
st.session_state["week"] = st.session_state.get("sb_week", 1)

# ========= 5) Main — topic & verbs (bands) =========

st.subheader("Topic / Outcome (optional)")
st.session_state["topic"] = st.text_area(
    label="",
    placeholder="e.g., Integrated Project and …",
    value=st.session_state["topic"],
    height=90,
    label_visibility="collapsed",
    key="topic_box"
)

def band(title, verbs, key, help_txt):
    selected = st.session_state[key]
    klass = "band active" if selected else "band"
    with st.container():
        st.markdown(f'<div class="{klass}">**{title}**</div>', unsafe_allow_html=True)
        st.session_state[key] = st.multiselect(
            help_txt,
            options=verbs,
            default=selected,
            key=f"ms_{key}"
        )

band("Low (Weeks 1–4) — Remember / Understand", LOW_VERBS, "low", "Low verbs")
band("Medium (Weeks 5–9) — Apply / Analyse",     MED_VERBS, "med", "Medium verbs")
band("High (Weeks 10–14) — Evaluate / Create",   HIGH_VERBS, "high","High verbs")

st.markdown("---")

# ========= 6) Tabs =========
tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

# ---- MCQ helpers ----
def templated_question(topic: str, verbs: list[str], idx: int) -> dict:
    topic = (topic or "this lesson topic").strip()
    bank = [
        "Which of the following best {v} {t}?",
        "What is the most appropriate way to {v} {t}?",
        "Which statement correctly helps to {v} {t}?",
        "An instructor asks students to {v} {t}. Which option is best?",
    ]
    v = (verbs[idx % max(1, len(verbs))] if verbs else "address")
    stem = random.choice(bank).format(v=v, t=topic)
    opts = [
        "To verify conformance",
        "To set company policy",
        "To hire staff",
        "To control budgets",
    ]
    # simple shuffle
    random.shuffle(opts)
    correct = 0  # first option as correct (editable later)
    return {"stem": stem, "options": opts, "answer": correct}

def ensure_mcqs_count(n: int, topic: str, verbs: list[str]):
    """Ensure we have exactly n items in session mcqs, generating as needed."""
    cur = st.session_state["mcqs"]
    if len(cur) < n:
        for i in range(len(cur), n):
            cur.append(templated_question(topic, verbs, i))
    elif len(cur) > n:
        st.session_state["mcqs"] = cur[:n]

def docx_for_questions(qs: list[dict], title: str) -> bytes:
    if not HAS_DOCX:
        return b""
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.add_heading(title, level=1)
    for i, q in enumerate(qs, start=1):
        p = doc.add_paragraph()
        p.add_run(f"Q{i}. ").bold = True
        p.add_run(q["stem"])
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{chr(65+j)}. {opt}", style=None)
        if st.session_state.get("answer_key", False):
            doc.add_paragraph(f"Answer: {chr(65 + q['answer'])}")
        doc.add_paragraph("")  # spacer
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()

def txt_for_questions(qs: list[dict]) -> bytes:
    lines = []
    for i, q in enumerate(qs, start=1):
        lines.append(f"Q{i}. {q['stem']}")
        for j, opt in enumerate(q["options"]):
            lines.append(f"  {chr(65+j)}. {opt}")
        if st.session_state.get("answer_key", False):
            lines.append(f"  Answer: {chr(65 + q['answer'])}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")

# ---- Tab 1: Knowledge MCQs ----
with tabs[0]:
    c1, c2 = st.columns([1,1])
    with c1:
        st.selectbox(
            "How many?",
            options=[5,10,15,20],
            index=[5,10,15,20].index(st.session_state["n_mcq"]) if st.session_state["n_mcq"] in [5,10,15,20] else 1,
            key="sel_n_mcq",
        )
    with c2:
        st.checkbox("Answer key", value=st.session_state["answer_key"], key="ck_answer")

    st.session_state["n_mcq"] = st.session_state["sel_n_mcq"]
    st.session_state["answer_key"] = st.session_state["ck_answer"]

    # Generate/update bank deterministically on button
    if st.button("Generate from verbs/topic", key="btn_generate_mcq"):
        random.seed(42)  # stable order
        ensure_mcqs_count(st.session_state["n_mcq"], st.session_state["topic"], st.session_state["low"]+st.session_state["med"]+st.session_state["high"])
        st.success("MCQs generated / updated.")

    # If empty (first load), keep it quiet but show 1 editable shell so user sees structure
    if not st.session_state["mcqs"]:
        ensure_mcqs_count(1, st.session_state["topic"], st.session_state["low"])

    st.markdown("")

    # Editable block
    to_delete = None
    for i, q in enumerate(st.session_state["mcqs"]):
        with st.expander(f"Q{i+1}", expanded=(i == 0)):
            st.session_state["mcqs"][i]["stem"] = st.text_area(
                f"Question {i+1} stem",
                value=q["stem"], key=f"stem_{i}"
            )
            cols = st.columns(2)
            with cols[0]:
                st.session_state["mcqs"][i]["options"][0] = st.text_input("A", value=q["options"][0], key=f"opt_{i}_0")
                st.session_state["mcqs"][i]["options"][1] = st.text_input("B", value=q["options"][1], key=f"opt_{i}_1")
            with cols[1]:
                st.session_state["mcqs"][i]["options"][2] = st.text_input("C", value=q["options"][2], key=f"opt_{i}_2")
                st.session_state["mcqs"][i]["options"][3] = st.text_input("D", value=q["options"][3], key=f"opt_{i}_3")

            ans = st.radio("Correct answer", options=["A","B","C","D"], index=q["answer"], key=f"ans_{i}", horizontal=True)
            st.session_state["mcqs"][i]["answer"] = ["A","B","C","D"].index(ans)

            # Per-Q downloads
            cdl1, cdl2 = st.columns(2)
            with cdl1:
                txt_bytes = txt_for_questions([st.session_state["mcqs"][i]])
                st.download_button(
                    "📥 Download TXT (Q)",
                    data=txt_bytes, file_name=f"ADI_MCQ_Q{i+1}.txt",
                    mime="text/plain",
                    key=f"dl_txt_q_{i}",
                )
            with cdl2:
                if HAS_DOCX:
                    docx_bytes = docx_for_questions([st.session_state["mcqs"][i]], title=f"MCQ Q{i+1}")
                    st.download_button(
                        "📥 Download DOCX (Q)",
                        data=docx_bytes, file_name=f"ADI_MCQ_Q{i+1}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_docx_q_{i}",
                    )
                else:
                    st.info("Install python-docx to enable DOCX export.")

    st.markdown("---")
    cact, crem, cdl_all1, cdl_all2 = st.columns([1,1,1,1])
    with cact:
        if st.button("➕ Add blank question", key="btn_add_blank"):
            st.session_state["mcqs"].append(
                {"stem":"", "options":["","","",""], "answer":0}
            )
    with crem:
        if st.button("➖ Remove last", key="btn_remove_last") and st.session_state["mcqs"]:
            st.session_state["mcqs"].pop()

    with cdl_all1:
        txt_all = txt_for_questions(st.session_state["mcqs"])
        st.download_button(
            "📥 Download TXT (All MCQs)",
            data=txt_all, file_name="ADI_MCQ_All.txt",
            mime="text/plain",
            key="dl_txt_all"
        )
    with cdl_all2:
        if HAS_DOCX:
            docx_all = docx_for_questions(
                st.session_state["mcqs"],
                title=f"MCQs — {st.session_state.get('sb_course','Course')}"
            )
            st.download_button(
                "📥 Download DOCX (All MCQs)",
                data=docx_all, file_name="ADI_MCQ_All.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_docx_all"
            )
        else:
            st.info("Install python-docx to enable DOCX export.")

# ---- Tab 2: Skills Activities ----
with tabs[1]:
    st.subheader("Skills Activities")
    left, right = st.columns(2)
    with left:
        count = st.selectbox("How many activities?", [1,2,3], index=0, key="act_count")
    with right:
        mins = st.selectbox("Minutes per activity", [5,10,15,20,30,45,60], index=1, key="act_minutes")

    group_map = {"Solo (1)":1,"Pairs (2)":2,"Triads (3)":3,"Groups of 4":4}
    grp = st.selectbox("Group size", list(group_map.keys()), index=0, key="act_group")

    if st.button("Generate Activities", key="btn_gen_acts"):
        st.session_state["acts"] = []
        verbs = st.session_state["med"] or st.session_state["low"] or ["apply"]
        for i in range(count):
            v = verbs[i % len(verbs)]
            tmpl = f"Activity {i+1}: In groups of {group_map[grp]}, spend {mins} minutes to **{v}** the topic by creating a short example and sharing it."
            st.session_state["acts"].append(tmpl)
        st.success("Activities generated.")

    for i, a in enumerate(st.session_state.get("acts", [])):
        st.markdown(f"**{a}**")

# ---- Tab 3: Revision ----
with tabs[2]:
    st.subheader("Revision")
    st.write("Add revision guidance, spaced-repetition prompts, or links here.")

# ---- Tab 4: Print Summary ----
with tabs[3]:
    st.subheader("Print Summary")
    c = st.session_state.get("sb_course","Course")
    coh = st.session_state.get("sb_cohort","Cohort")
    ins = st.session_state.get("sb_instructor","Instructor")
    st.markdown(f"**Course:** {c}  \n**Cohort:** {coh}  \n**Instructor:** {ins}  \n**Lesson:** {st.session_state['lesson']}  \n**Week:** {st.session_state['week']}")
    if st.session_state["topic"]:
        st.markdown(f"**Topic/Outcome:** {st.session_state['topic']}")

    st.markdown("**Selected verbs**")
    st.write("Low:", ", ".join(st.session_state["low"]) or "—")
    st.write("Medium:", ", ".join(st.session_state["med"]) or "—")
    st.write("High:", ", ".join(st.session_state["high"]) or "—")

# ========= 7) Footer notice for uploaded file =========
if st.session_state.get("last_upload"):
    st.toast(f"Uploaded: {st.session_state['last_upload']}", icon="✅")
