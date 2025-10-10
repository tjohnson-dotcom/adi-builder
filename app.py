# app.py
# ADI Builder — Lesson Activities & Questions
# Clean, stable build: sticky state + highlighted bands + dashed dropzone
# Requirements (your pins): streamlit==1.37.1, python-docx==1.1.2, python-pptx==1.0.2, pymupdf==1.24.9

import datetime as dt
from io import BytesIO
import streamlit as st

# -----------------------------
# Page config (call ONCE, first)
# -----------------------------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="📚",
    layout="wide",
)


# -----------------------------
# ADI constants / look & feel
# -----------------------------
ADI_GREEN = "#153a27"   # banner + accents
ADI_OUTLINE = "#245a34" # borders / hover ring

PALETTE = {
    "low_fill":   "#cfe8d9",  # low band bg
    "med_fill":   "#f8e6c9",  # medium band bg
    "high_fill":  "#dfe6ff",  # high band bg
    "chip":       "#245a34",  # chip green
}

LOW_VERBS  = ["define", "identify", "list"]
MED_VERBS  = ["apply", "demonstrate", "solve"]
HIGH_VERBS = ["evaluate", "synthesize", "design"]

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

INSTRUCTORS = [
    "Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen Tariq","Dari",
    "Ghamza Labeeb","Michail","Meshari","Mohammed Alwuthaylah","Myra","Meshal Algurabi",
    "Ibrahim Alrawaili","Khalil","Salem","Chetan","Yasser","Ahmed Albader","Muath",
    "Sultan","Dr. Mashael","Noura Aldossari","Daniel"
]
COHORTS = ["D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
           "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"]


# ------------------------------------
# One-shot state bootstrap (NO widgets)
# ------------------------------------
def init_state():
    ss = st.session_state
    defaults = {
        "course": COURSES[0],
        "cohort": COHORTS[0],
        "instructor": INSTRUCTORS[-1],  # Daniel (as per your screenshots)
        "date": dt.date.today().isoformat(),
        "lesson": 1,
        "week": 1,
        "topic": "",
        "how_many": 10,
        "include_key": True,
        "low_ms": LOW_VERBS.copy(),
        "med_ms": MED_VERBS.copy(),
        "high_ms": HIGH_VERBS.copy(),
        "active_tab": "mcq",   # "mcq" | "skills" | "revision" | "print"
        "upload_toast": False,
    }
    for k, v in defaults.items():
        if k not in ss:
            ss[k] = v

init_state()


# -----------------------------
# Helper: compute active level
# -----------------------------
def week_to_level(week: int) -> str:
    if week <= 4:
        return "low"
    if 5 <= week <= 9:
        return "med"
    return "high"


# -----------------------------
# CSS (banner, dashed dropzone,
# chips, hover ring, pointer)
# -----------------------------
st.markdown(f"""
<style>
/* Banner spacing (we keep Streamlit's top bar visible) */
.block-container {{
  padding-top: 1rem !important;
}}

/* Dark banner look */
h1, .adi-banner {{
  background: {ADI_GREEN};
  color: white;
  padding: .60rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  letter-spacing: .2px;
}}

/* Dashed file drop */
[data-testid="stFileUploaderDropzone"] {{
  border: 2px dashed {ADI_OUTLINE} !important;
  border-radius: 10px !important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
  box-shadow: 0 0 0 3px {ADI_OUTLINE} inset !important;
}}

/* Make interactive bits obviously clickable */
[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button, [role="button"] {{
  cursor: pointer !important;
}}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {{
  box-shadow: 0 0 0 2px {ADI_OUTLINE} inset !important;
}}
:focus-visible {{
  outline: 2px solid {ADI_OUTLINE} !important;
  outline-offset: 2px;
}}

/* Verb bands */
.band {{
  border: 1.5px solid {ADI_OUTLINE};
  border-radius: 10px;
  padding: .35rem .55rem .25rem .55rem;
  margin: .25rem 0 .35rem 0;
}}
.band.low  {{ background: {PALETTE["low_fill"]};  }}
.band.med  {{ background: {PALETTE["med_fill"]};  }}
.band.high {{ background: {PALETTE["high_fill"]}; }}

.band.active {{
  box-shadow: 0 0 0 3px {ADI_OUTLINE} inset;
}}

/* Chips */
.stMultiSelect [data-baseweb="tag"] {{
  background: {PALETTE["chip"]} !important;
  color: white !important;
  font-weight: 600;
  border-radius: 8px !important;
}}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Sidebar (upload + course info)
# -----------------------------
with st.sidebar:
    st.image("adi_logo.png", width=160, use_container_width=False)
    st.write("### Upload (optional)")
    upload = st.file_uploader(
        "Drag and drop file here",
        type=["txt","docx","pptx","pdf"],
        label_visibility="collapsed",
        key="uploader_main"
    )
    deep_scan = st.toggle(
        "Deep scan source (slower, better coverage)",
        value=False
    )

    if upload and not st.session_state.upload_toast:
        st.toast(f"Uploaded: {upload.name}", icon="✅")
        st.session_state.upload_toast = True

    st.write("### Course details")
    st.session_state.course = st.selectbox(
        "Course name", COURSES, index=COURSES.index(st.session_state.course)
    )
    st.session_state.cohort = st.selectbox(
        "Class / Cohort", COHORTS, index=COHORTS.index(st.session_state.cohort)
    )
    st.session_state.instructor = st.selectbox(
        "Instructor name", INSTRUCTORS, index=INSTRUCTORS.index(st.session_state.instructor)
    )
    st.session_state.date = st.date_input(
        "Date", value=dt.datetime.strptime(st.session_state.date, "%Y-%m-%d").date()
    ).isoformat()

    # Lesson/Week steppers (sticky)
    col_l, col_w = st.columns(2)
    with col_l:
        st.session_state.lesson = st.number_input(
            "Lesson", min_value=1, max_value=14, step=1, value=int(st.session_state.lesson)
        )
    with col_w:
        st.session_state.week = st.number_input(
            "Week", min_value=1, max_value=14, step=1, value=int(st.session_state.week)
        )


# -----------------------------
# Title bar (kept inside main)
# -----------------------------
st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

# -----------------------------
# Topic / Outcome (NO state set after widget is created)
# -----------------------------
topic_val = st.text_area(
    "Topic / Outcome (optional)",
    placeholder="e.g., Integrated Project and …",
    key="topic",  # safe: we never change st.session_state.topic later in the same run
    height=120
)


# -----------------------------
# Verb bands (with highlight)
# -----------------------------
def verb_band(title: str, level_key: str, verbs: list, multiselect_key: str):
    """Renders a coloured band with a multiselect inside."""
    active_lvl = week_to_level(st.session_state.week)
    is_active = "active" if level_key == active_lvl else ""
    st.markdown(f'<div class="band {level_key} {is_active}">', unsafe_allow_html=True)
    st.caption(title)
    st.session_state[multiselect_key] = st.multiselect(
        label=f"{level_key.capitalize()} verbs",
        options=verbs,
        default=st.session_state.get(multiselect_key, verbs),
        key=f"ms_{multiselect_key}"
    )
    st.markdown("</div>", unsafe_allow_html=True)


verb_band("Low (Weeks 1–4) — Remember / Understand", "low", LOW_VERBS,  "low_ms")
verb_band("Medium (Weeks 5–9) — Apply / Analyse",   "med", MED_VERBS,  "med_ms")
verb_band("High (Weeks 10–14) — Evaluate / Create", "high", HIGH_VERBS, "high_ms")


# -----------------------------
# Tabs
# -----------------------------
tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

# Common “how many” control
HOW_MANY_CHOICES = [5, 10, 12, 15, 20]

with tabs[0]:
    st.caption("ADI policy: 1–3 per lesson = Low, 5–9 = Medium, 10–14 = High")
    st.session_state.how_many = st.selectbox(
        "How many MCQs?",
        HOW_MANY_CHOICES,
        index=HOW_MANY_CHOICES.index(st.session_state.how_many)
    )
    st.session_state.include_key = st.checkbox("Answer key", value=bool(st.session_state.include_key))

    # Unique key for the button to avoid duplicate-widget errors
    if st.button("Generate from verbs/topic", key="btn_gen_mcq"):
        with st.spinner("Generating MCQs…"):
            # Placeholder: you can replace this with your real generator
            if "mcq_items" not in st.session_state:
                st.session_state.mcq_items = []
            st.session_state.mcq_items = []
            N = st.session_state.how_many
            for i in range(1, N+1):
                st.session_state.mcq_items.append({
                    "stem": f"Q{i}. Draft question based on topic: {st.session_state.topic or '—'}",
                    "a": "Option A", "b": "Option B", "c": "Option C", "d": "Option D",
                    "correct": "A" if i % 4 == 1 else ("B" if i % 4 == 2 else ("C" if i % 4 == 3 else "D"))
                })
        st.success(f"Prepared {len(st.session_state.mcq_items)} draft MCQs. Edit below or export.")

    # Render any prepared MCQs
    mcqs = st.session_state.get("mcq_items", [])
    if not mcqs:
        st.info("No questions yet. Click **Generate from verbs/topic**.")
    else:
        for i, q in enumerate(mcqs, start=1):
            with st.expander(f"Q{i}"):
                q["stem"] = st.text_area("Question", value=q["stem"], key=f"q_stem_{i}")
                cols = st.columns(2)
                with cols[0]:
                    q["a"] = st.text_input("A", value=q["a"], key=f"q_a_{i}")
                    q["c"] = st.text_input("C", value=q["c"], key=f"q_c_{i}")
                with cols[1]:
                    q["b"] = st.text_input("B", value=q["b"], key=f"q_b_{i}")
                    q["d"] = st.text_input("D", value=q["d"], key=f"q_d_{i}")
                q["correct"] = st.radio("Correct answer", ["A","B","C","D"], horizontal=True, index=["A","B","C","D"].index(q["correct"]), key=f"q_corr_{i}")

        # Simple TXT export (so you can verify quickly)
        if mcqs:
            lines = []
            hdr = f"ADI_MCQ__{st.session_state.course.split(' — ')[0]}__{st.session_state.course.split(' — ')[1].split(' in ')[0].replace(' ','_')}__{st.session_state.cohort}__W{st.session_state.week}__Q{len(mcqs)}"
            lines.append(hdr)
            lines.append(f"Instructor: {st.session_state.instructor}")
            lines.append(f"Date: {st.session_state.date}")
            lines.append(f"Topic: {st.session_state.topic or '—'}")
            lines.append("")
            for i, q in enumerate(mcqs, start=1):
                lines.append(q["stem"])
                lines.append(f"A) {q['a']}")
                lines.append(f"B) {q['b']}")
                lines.append(f"C) {q['c']}")
                lines.append(f"D) {q['d']}")
                if st.session_state.include_key:
                    lines.append(f"[Answer: {q['correct']}]")
                lines.append("")
            buf = BytesIO("\n".join(lines).encode("utf-8"))
            st.download_button("⬇️ Download TXT (All MCQs)", data=buf.getvalue(), file_name=f"{hdr}.txt", mime="text/plain", key="dl_all_txt")


with tabs[1]:
    st.subheader("Skills Activities")
    act_cols = st.columns(3)
    with act_cols[0]:
        acts = st.selectbox("How many activities?", [1,2,3], index=0, key="skills_n")
    with act_cols[1]:
        mins = st.selectbox("Minutes per activity", list(range(5, 61, 5)), index=1, key="skills_mins")
    with act_cols[2]:
        group = st.selectbox("Group size", ["Solo (1)","Pairs (2)","Triads (3)","Teams (4)"], index=0, key="skills_group")

    if st.button("Generate Skills", key="btn_gen_skills"):
        with st.spinner("Generating activities…"):
            st.session_state.skills = []
            for i in range(1, st.session_state.skills_n+1):
                st.session_state.skills.append({
                    "title": f"Activity {i} — {st.session_state.skills_mins} min",
                    "brief": f"Design a short task using verbs {st.session_state.low_ms + st.session_state.med_ms + st.session_state.high_ms} related to: {st.session_state.topic or '—'}.",
                    "group": st.session_state.skills_group
                })
        st.success(f"Prepared {len(st.session_state.skills)} activity drafts.")

    for i, a in enumerate(st.session_state.get("skills", []), start=1):
        with st.expander(a["title"]):
            a["brief"] = st.text_area("Brief", value=a["brief"], key=f"sk_brief_{i}")
            a["group"] = st.text_input("Group", value=a["group"], key=f"sk_group_{i}")


with tabs[2]:
    st.subheader("Revision")
    st.info("(Optional) Add revision prompts or reflection questions here.")


with tabs[3]:
    st.subheader("Print Summary")
    st.write(f"**Course:** {st.session_state.course}")
    st.write(f"**Cohort:** {st.session_state.cohort}  |  **Instructor:** {st.session_state.instructor}")
    st.write(f"**Date:** {st.session_state.date}  |  **Lesson:** {st.session_state.lesson}  |  **Week:** {st.session_state.week}")
    st.write(f"**Topic/Outcome:** {st.session_state.topic or '—'}")
    st.write("**Low verbs:**", ", ".join(st.session_state.low_ms) or "—")
    st.write("**Medium verbs:**", ", ".join(st.session_state.med_ms) or "—")
    st.write("**High verbs:**", ", ".join(st.session_state.high_ms) or "—")
    st.divider()
    st.write("**MCQs prepared:**", len(st.session_state.get("mcq_items", [])))
    st.write("**Activities prepared:**", len(st.session_state.get("skills", [])))
