# app.py  — ADI Builder (stable UI, highlighted bands, sticky banner)
# Build: 2025-10-10 • sticky+hover v3

import streamlit as st
from datetime import date

# ---------------------------------------------------------------
# 1) Page config (must be the first Streamlit call)
# ---------------------------------------------------------------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    layout="wide"
)

# ---------------------------------------------------------------
# 2) Styles (keeps your look; pointer+hover; dashed uploader)
# ---------------------------------------------------------------
ADI_GREEN = "#245a34"
ADI_GREEN_DARK = "#153a27"
ADI_PILL = ADI_GREEN

st.markdown(
    f"""
    <style>
      /* Top sticky banner */
      .adi-banner {{
        position: sticky;
        top: 0;
        z-index: 999;
        background: {ADI_GREEN_DARK};
        color: white;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 600;
        margin: 8px 0 16px 0;
      }}

      /* Bands for Low / Medium / High */
      .band {{
        border: 2px solid {ADI_GREEN};
        border-radius: 10px;
        padding: 8px 12px;
        color: {ADI_GREEN_DARK};
        margin: 10px 0 6px 0;
      }}
      .band.active {{
        box-shadow: 0 0 0 3px rgba(36,90,52,.2) inset;
      }}

      /* Chip (multiselect) look keeps your scheme */
      div[data-baseweb="tag"] {{
        background: {ADI_PILL} !important;
        color: #fff !important;
        border-radius: 12px !important;
      }}

      /* Dashed drag & drop */
      div[data-testid="stFileUploader"] > section {{
        border: 2px dashed {ADI_GREEN} !important;
        border-radius: 12px !important;
      }}

      /* Pointer + hover rings on interactive things */
      div[data-testid="stFileUploaderDropzone"],
      div[data-testid="stSelectbox"] button,
      div[data-testid="stMultiSelect"] button,
      button[kind], button {{
        cursor: pointer !important;
      }}
      div[data-testid="stFileUploaderDropzone"]:hover {{
        box-shadow: 0 0 0 3px {ADI_GREEN} inset !important;
      }}
      div[data-testid="stSelectbox"] button:hover,
      div[data-testid="stMultiSelect"] button:hover {{
        box-shadow: 0 0 0 2px {ADI_GREEN} inset !important;
      }}

      /* Focus ring (keyboard) */
      :focus-visible {{
        outline: 2px solid {ADI_GREEN} !important;
        outline-offset: 2px;
      }}

      /* Tabs underline accent */
      button[role="tab"][aria-selected="true"] {{
        border-bottom: 3px solid {ADI_GREEN} !important;
      }}

      /* Compact “How many?” row */
      .small-note {{
        font-size: 12px; color: #6b7280; margin-top: 6px;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# 3) Sticky banner (same wording/green as your current look)
# ---------------------------------------------------------------
st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------
# 4) Data / defaults
# ---------------------------------------------------------------
LOW_VERBS    = ["define", "identify", "list", "describe", "label", "recall"]
MEDIUM_VERBS = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH_VERBS   = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

DEFAULT_COURSES = [
    "GE4-IPM — Integrated Project & Materials Management in Defense Technology",
    "GE4-EPM — Defense Technology Practices",
    "GE4-MRO — Military Vehicle & Aircraft MRO"
]
DEFAULT_COHORTS = ["D1-C01", "D1-E01", "D1-E02"]
DEFAULT_INSTRUCTORS = [
    "Daniel", "Ghamza Labeeb", "Abdulmalik", "Gerhard", "Faiz Lazam",
    "Mohammed Alfarhan", "Nerdeen Tariq", "Dari", "Michail", "Meshari",
    "Mohammed Alwuthaylah", "Myra", "Meshal Algurabi", "Ibrahim Alrawaili",
    "Khalil", "Salem", "Chetan", "Yasser", "Ahmed Albader", "Muath",
    "Sultan", "Dr. Mashael", "Noura Aldossari", "Ben"
]

# ---------------------------------------------------------------
# 5) Session defaults
# ---------------------------------------------------------------
ss = st.session_state
ss.setdefault("low_verbs", [])
ss.setdefault("medium_verbs", [])
ss.setdefault("high_verbs", [])
ss.setdefault("courses", DEFAULT_COURSES.copy())
ss.setdefault("cohorts", DEFAULT_COHORTS.copy())
ss.setdefault("instructors", DEFAULT_INSTRUCTORS.copy())

# ---------------------------------------------------------------
# 6) Small helper to render a verb band with highlight
# ---------------------------------------------------------------
def band(title: str, verbs: list[str], key: str, help_txt: str):
    """
    Renders a header band + multiselect. Band gets a subtle green glow
    when at least one verb is selected.
    """
    selected = ss.get(key, [])
    klass = "band active" if selected else "band"
    st.markdown(f'<div class="{klass}"><strong>{title}</strong></div>', unsafe_allow_html=True)
    ss[key] = st.multiselect(
        help_txt,
        options=verbs,
        default=selected,
        key=f"ms_{key}",
    )

# ---------------------------------------------------------------
# 7) Sidebar (keeps your look/controls exactly)
# ---------------------------------------------------------------
with st.sidebar:
    st.image("adi_logo.png", width=100)  # no use_container_width to avoid old crash
    st.subheader("Upload (optional)")
    up_file = st.file_uploader(
        "Drag and drop file here",
        type=["txt", "docx", "pptx", "pdf"]
    )
    if up_file is not None:
        st.success(f"Uploaded: {up_file.name}")

    st.toggle("Deep scan source (slower, better coverage)", value=False)

    st.subheader("Course details")

    # Course select with + / -
    c1, c2, c3 = st.columns([1, 0.18, 0.18])
    with c1:
        course = st.selectbox("Course name", ss["courses"], index=0, key="course_select")
    with c2:
        if st.button("+", key="add_course"):
            with st.popover("Add course"):
                new = st.text_input("New course name")
                if st.button("Save", key="save_course_pop"):
                    if new and new not in ss["courses"]:
                        ss["courses"].append(new)
                        st.toast("Course added", icon="✅")
    with c3:
        if st.button("—", key="remove_course"):
            with st.popover("Remove course"):
                rem = st.selectbox("Pick course", ss["courses"])
                if st.button("Confirm remove", key="confirm_remove_course"):
                    ss["courses"] = [x for x in ss["courses"] if x != rem]
                    st.toast("Course removed", icon="🗑️")

    # Cohort select with + / -
    c1, c2, c3 = st.columns([1, 0.18, 0.18])
    with c1:
        cohort = st.selectbox("Class / Cohort", ss["cohorts"], index=0, key="cohort_select")
    with c2:
        if st.button("+", key="add_cohort"):
            with st.popover("Add cohort"):
                new = st.text_input("New cohort (e.g., D1-C02)")
                if st.button("Save", key="save_cohort_pop"):
                    if new and new not in ss["cohorts"]:
                        ss["cohorts"].append(new)
                        st.toast("Cohort added", icon="✅")
    with c3:
        if st.button("—", key="remove_cohort"):
            with st.popover("Remove cohort"):
                rem = st.selectbox("Pick cohort", ss["cohorts"])
                if st.button("Confirm remove", key="confirm_remove_cohort"):
                    ss["cohorts"] = [x for x in ss["cohorts"] if x != rem]
                    st.toast("Cohort removed", icon="🗑️")

    # Instructor select with + / -
    c1, c2, c3 = st.columns([1, 0.18, 0.18])
    with c1:
        instructor = st.selectbox("Instructor name", ss["instructors"], index=0, key="instr_select")
    with c2:
        if st.button("+", key="add_instr"):
            with st.popover("Add instructor"):
                new = st.text_input("New instructor")
                if st.button("Save", key="save_instr_pop"):
                    if new and new not in ss["instructors"]:
                        ss["instructors"].append(new)
                        st.toast("Instructor added", icon="✅")
    with c3:
        if st.button("—", key="remove_instr"):
            with st.popover("Remove instructor"):
                rem = st.selectbox("Pick instructor", ss["instructors"])
                if st.button("Confirm remove", key="confirm_remove_instr"):
                    ss["instructors"] = [x for x in ss["instructors"] if x != rem]
                    st.toast("Instructor removed", icon="🗑️")

    # Date + context
    st.date_input("Date", value=date.today())
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Lesson", min_value=1, max_value=14, value=1, step=1, key="lesson_no")
    with c2:
        st.number_input("Week", min_value=1, max_value=14, value=1, step=1, key="week_no")

# ---------------------------------------------------------------
# 8) Main content — Topic + Bands + MCQ controls
# ---------------------------------------------------------------
st.subheader("Topic / Outcome (optional)")
st.text_area(
    "e.g., Integrated Project and …",
    label_visibility="collapsed",
    height=120,
    key="topic_text"
)

# Bands (highlight when selected)
band("Low (Weeks 1–4) — Remember / Understand", LOW_VERBS, "low_verbs", "Low verbs")
band("Medium (Weeks 5–9) — Apply / Analyse",     MEDIUM_VERBS, "medium_verbs", "Medium verbs")
band("High (Weeks 10–14) — Evaluate / Create",   HIGH_VERBS, "high_verbs", "High verbs")

# Tabs shell (content editable / generation etc.)
tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

with tabs[0]:
    c1, c2 = st.columns([3, 1])
    with c1:
        count = st.selectbox("How many?", [5, 10, 15, 20], index=1, key="mcq_count")
        st.caption('<div class="small-note">ADI policy: 10 is standard</div>', unsafe_allow_html=True)
    with c2:
        answer_key = st.checkbox("Answer key", value=True, key="mcq_anskey")

    # Simple skeleton (keeps your look; you can wire real generation here)
    st.button("Generate from verbs/topic", key="btn_generate_mcqs")
    st.divider()
    st.write("Q1")
    st.text_area("Question", value="Explain the role of inspection in quality management.", key="q1_text")
    cols = st.columns(2)
    with cols[0]:
        st.text_input("A", value="To verify conformance", key="q1_a")
        st.text_input("B", value="To set company policy", key="q1_b")
    with cols[1]:
        st.text_input("C", value="To hire staff", key="q1_c")
        st.text_input("D", value="To control budgets", key="q1_d")
    st.radio("Correct answer", options=["A","B","C","D"], index=0, key="q1_correct")

with tabs[1]:
    st.info("Skills activities designer coming here (unchanged).")

with tabs[2]:
    st.info("Revision content (unchanged).")

with tabs[3]:
    st.info("Print summary layout (unchanged).")

# ---------------------------------------------------------------
# 9) Build tag (tiny, unobtrusive)
# ---------------------------------------------------------------
st.caption("Build: 2025-10-10 • sticky+hover v3")
