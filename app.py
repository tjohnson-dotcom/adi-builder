# ------------------------------
# ADI Builder — Lesson Activities & Questions
# "palette-chips + sticky-tab" build
# ------------------------------
import streamlit as st
from datetime import date
from urllib.parse import urlencode

# ---------- 1) PAGE CONFIG (ONLY ONCE) ----------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- 2) CONSTANTS ----------
LOW_WEEKS = range(1, 5)        # 1..4
MED_WEEKS = range(5, 10)       # 5..9
HIGH_WEEKS = range(10, 15)     # 10..14

LOW_VERBS = ["define", "identify", "list"]
MED_VERBS = ["apply", "demonstrate", "solve"]
HIGH_VERBS = ["evaluate", "synthesize", "design"]

# Your known data
COURSES = [
    "GE4-IPM — Integrated Project & Materials Management in Defense Technology",
    "GE4-EPM — Defense Technology Practices: Experimental, Quality & Inspection",
    "GE4-MRO — Military Vehicle & Aircraft MRO: Principles & Applications",
    "CT4-COM — Computation for Chemical Technologists",
    "CT4-EMG — Explosives Manufacturing",
    "CT4-TFL — Thermofluids",
    "MT4-CMG — Composite Manufacturing",
    "MT4-CAD — Computer-Aided Design",
    "MT4-MAE — Machine Elements",
    "EE4-MFC — Electrical Materials",
    "EE4-PMG — PCB Manufacturing",
    "EE4-PCT — Power Circuits & Transmission",
]
COHORTS = [
    "D1-C01", "D1-E01", "D1-E02",
    "D1-M01", "D1-M02", "D1-M03", "D1-M04", "D1-M05",
    "D2-C01", "D2-M01", "D2-M02", "D2-M03", "D2-M04", "D2-M05", "D2-M06"
]
INSTRUCTORS = [
    "Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen Tariq","Dari",
    "Ghamza Labeeb","Michail","Meshari","Mohammed Alwuthaylah","Myra","Meshal Algurabi",
    "Ibrahim Alrawaili","Khalil","Salem","Chetan","Yasser","Ahmed Albader","Muath","Sultan",
    "Dr. Mashael","Noura Aldossari","Daniel"
]

# ---------- 3) STATE INIT (NO ASSIGNMENTS AFTER WIDGET CREATION) ----------
ss = st.session_state
def init_state():
    ss.setdefault("course", COURSES[0])
    ss.setdefault("cohort", COHORTS[0])
    ss.setdefault("instructor", "Daniel")
    ss.setdefault("date", date.today().isoformat())
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("topic", "")
    ss.setdefault("low_verbs", LOW_VERBS.copy())
    ss.setdefault("med_verbs", MED_VERBS.copy())
    ss.setdefault("high_verbs", HIGH_VERBS.copy())
    ss.setdefault("how_many", 10)
    ss.setdefault("include_answer_key", True)
    ss.setdefault("active_tab", "mcq")
    ss.setdefault("mcqs", [])   # holds generated MCQs for preview
init_state()

# ---------- 4) HELPERS ----------
def set_query_params_from_state():
    st.query_params.update({
        "course": ss.course,
        "cohort": ss.cohort,
        "inst": ss.instructor,
        "d": ss.date,
        "lesson": str(ss.lesson),
        "week": str(ss.week),
        "tab": ss.active_tab
    })

def restore_state_from_query():
    qp = st.query_params
    if "course" in qp and qp["course"] in COURSES:
        ss.course = qp["course"]
    if "cohort" in qp and qp["cohort"] in COHORTS:
        ss.cohort = qp["cohort"]
    if "inst" in qp and qp["inst"] in INSTRUCTORS:
        ss.instructor = qp["inst"]
    if "d" in qp:
        ss.date = qp["d"]
    if "lesson" in qp and qp["lesson"].isdigit():
        ss.lesson = int(qp["lesson"])
    if "week" in qp and qp["week"].isdigit():
        ss.week = int(qp["week"])
    if "tab" in qp:
        ss.active_tab = qp["tab"]

restore_state_from_query()

def band_class():
    """Return which band should be 'active' based on week selection."""
    w = ss.week
    if w in LOW_WEEKS:   return "low"
    if w in MED_WEEKS:   return "med"
    return "high"

def render_band(title, verbs, state_key, band_name, help_txt):
    """Title strip + chips for a Bloom band. Adds 'active' tint by week."""
    active = (band_class() == band_name)
    band_css = f"band {'active' if active else ''}"
    st.markdown(f'<div class="{band_css}"><strong>{title}</strong></div>', unsafe_allow_html=True)
    # default only matters first render; afterwards Streamlit controls the value
    default_list = ss.get(state_key, verbs)
    st.multiselect(
        help_txt,
        options=verbs,
        default=default_list,
        key=state_key
    )

def generate_mcqs_stub():
    """Lightweight local stub so UI proves end-to-end without backend calls."""
    ss.mcqs = []
    for i in range(ss.how_many):
        qn = f"Q{i+1}"
        stem = f"Explain the role of inspection in quality management. (Generated {i+1})"
        options = ["To verify conformance", "To set company policy", "To hire staff", "To control budgets"]
        ans_idx = 0  # A
        ss.mcqs.append({"id": qn, "stem": stem, "options": options, "answer": ans_idx})

# ---------- 5) STYLES ----------
st.markdown("""
<style>
/* overall spacing so banner isn't covered */
section[data-testid="stSidebar"] { z-index: 100; }
.block-container { padding-top: 0.8rem !important; }

/* top banner bar */
.header-bar {
  background:#153a27; color:#ffffff; padding:10px 14px; border-radius:8px;
  margin-bottom:10px; font-weight:600; letter-spacing:.2px;
}
/* dashed uploader */
div[data-testid="stFileUploaderDropzone"] {
  border:2px dashed #245a34 !important;
  border-radius:10px !important;
  background: #f7fbf8 !important;
}
div[data-testid="stFileUploaderDropzone"]:hover {
  box-shadow: 0 0 0 3px #245a34 inset !important;
}

/* bands */
.band {
  border:1px solid #245a34;
  border-radius:8px; padding:8px 10px; margin:6px 0 4px 0;
  background:#ffffff;
  color:#153a27;
}
.band.active { background:#e8f3ed; }

/* chips */
span[data-baseweb="tag"] {
  background:#245a34 !important;
  color:#fff !important;
  border-radius:999px !important;
  padding:2px 10px !important;
}

/* Make interactive bits feel clickable */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind],
button { cursor: pointer !important; }

/* hover feedback */
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {
  box-shadow: 0 0 0 2px #245a34 inset !important;
}

/* keyboard focus ring */
:focus-visible { outline: 2px solid #245a34 !important; outline-offset: 2px; }

/* tabs (our simulated tab buttons) */
.tabbar { display:flex; gap:12px; margin:14px 0 6px 0; }
.tabbtn {
  background:#fff; border:1px solid #c9d5ce; color:#153a27;
  padding:6px 10px; border-radius:10px;
}
.tabbtn.active { background:#245a34; color:#fff; border-color:#245a34; }

/* small build tag */
.buildtag { color:#6b7a73; font-size:12px; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

# ---------- 6) HEADER ----------
st.markdown('<div class="header-bar">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

# ---------- 7) SIDEBAR: Upload + Course controls ----------
with st.sidebar:
    st.image("adi_logo.png", width=160)  # no use_container_width to avoid older Streamlit error

    up = st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"])
    if up is not None:
        st.success(f"✅ Uploaded: **{up.name}**")

    st.toggle("Deep scan source (slower, better coverage)", value=False)

    st.markdown("### Course details")
    ss.course = st.selectbox("Course name", COURSES, index=COURSES.index(ss.course))
    ss.cohort = st.selectbox("Class / Cohort", COHORTS, index=COHORTS.index(ss.cohort))
    ss.instructor = st.selectbox("Instructor name", INSTRUCTORS, index=INSTRUCTORS.index(ss.instructor))
    ss.date = st.text_input("Date", ss.date)

    colL, colW = st.columns(2)
    with colL:
        ss.lesson = st.number_input("Lesson", min_value=1, max_value=14, step=1, value=int(ss.lesson))
    with colW:
        ss.week = st.number_input("Week", min_value=1, max_value=14, step=1, value=int(ss.week))

# Reflect sidebar choices to query params (keeps Week persistent across reload)
set_query_params_from_state()

# ---------- 8) MAIN LAYOUT ----------
st.text_area(
    "Topic / Outcome (optional)",
    placeholder="e.g., Integrated Project and …",
    key="topic"
)

# Bands
render_band("Low (Weeks 1–4) — Remember / Understand", LOW_VERBS, "low_verbs", "low", "Low verbs")
render_band("Medium (Weeks 5–9) — Apply / Analyse", MED_VERBS, "med_verbs", "med", "Medium verbs")
render_band("High (Weeks 10–14) — Evaluate / Create", HIGH_VERBS, "high_verbs", "high", "High verbs")

# ---------- 9) TABS (MCQs / Skills / Revision / Print) ----------
st.markdown('<div class="tabbar">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([1,1,1,1])
with c1:
    if st.button("Knowledge MCQs (Editable)", key="tab_m", use_container_width=True):
        ss.active_tab = "mcq"; set_query_params_from_state()
with c2:
    if st.button("Skills Activities", key="tab_s", use_container_width=True):
        ss.active_tab = "skills"; set_query_params_from_state()
with c3:
    if st.button("Revision", key="tab_r", use_container_width=True):
        ss.active_tab = "revision"; set_query_params_from_state()
with c4:
    if st.button("Print Summary", key="tab_p", use_container_width=True):
        ss.active_tab = "print"; set_query_params_from_state()
st.markdown('</div>', unsafe_allow_html=True)

# paint which tab is active
tab_map = {"mcq":"tab_m","skills":"tab_s","revision":"tab_r","print":"tab_p"}
st.markdown(f"""
<script>
for (const id of ["tab_m","tab_s","tab_r","tab_p"]) {{
  const btn = window.parent.document.querySelector('button[data-testid="baseButton-secondary"][aria-label="{id}"]');
}}
</script>
""", unsafe_allow_html=True)
# (In Streamlit, toggling “active” class on buttons from Python is awkward;
# the visual ‘active’ is handled by the build tag below to indicate current tab.)

st.caption(f"Active tab: **{ss.active_tab}**")

# ---------- 10) TAB CONTENT ----------
if ss.active_tab == "mcq":
    st.subheader("Knowledge MCQs (ADI Policy)")

    cc1, cc2 = st.columns([3,1])
    with cc1:
        ss.how_many = st.selectbox("How many MCQs?", [5,10,12,15,20], index=[5,10,12,15,20].index(ss.how_many) if ss.how_many in [5,10,12,15,20] else 1, key="how_many")
    with cc2:
        ss.include_answer_key = st.checkbox("Answer key", value=ss.include_answer_key, key="include_answer_key")

    if st.button("Generate from verbs/topic", key="gen_mcq_btn"):
        generate_mcqs_stub()
        st.success(f"Generated {len(ss.mcqs)} MCQs.")

    # Preview first question (if any) to prove flow works
    if ss.mcqs:
        q = ss.mcqs[0]
        st.write("### Q1")
        st.text_area("Question", value=q["stem"], key="q1_stem")
        cols = st.columns(2)
        with cols[0]:
            st.text_input("A", value=q["options"][0], key="q1_A")
            st.text_input("B", value=q["options"][1], key="q1_B")
        with cols[1]:
            st.text_input("C", value=q["options"][2], key="q1_C")
            st.text_input("D", value=q["options"][3], key="q1_D")
        st.radio("Correct answer", ["A","B","C","D"], index=q["answer"], key="q1_correct")

elif ss.active_tab == "skills":
    st.subheader("Skills Activities")
    c1, c2, c3 = st.columns(3)
    n_acts = c1.selectbox("How many activities?", [1,2,3], index=2)
    mins   = c2.selectbox("Minutes per activity", [5,10,15,20,25,30,40,45,50,60], index=1)
    gsize  = c3.selectbox("Group size", ["Solo (1)","Pairs (2)","Triads (3)","Teams (4)"], index=0)
    st.info("This tab will use your selected verbs + topic to create classroom activities. (Hook your real generator here.)")

elif ss.active_tab == "revision":
    st.subheader("Revision")
    st.info("Revision materials builder coming next. (Safe placeholder.)")

else:  # print
    st.subheader("Print Summary")
    st.write("**Course:**", ss.course)
    st.write("**Cohort:**", ss.cohort, " • **Instructor:**", ss.instructor)
    st.write("**Lesson/Week:**", ss.lesson, "/", ss.week)
    st.write("**Topic:**", ss.topic if ss.topic.strip() else "—")
    st.write("**Low verbs:**", ", ".join(ss.low_verbs))
    st.write("**Medium verbs:**", ", ".join(ss.med_verbs))
    st.write("**High verbs:**", ", ".join(ss.high_verbs))

st.markdown('<div class="buildtag">Build: 2025-10-10 • palette-chips + sticky-tab</div>', unsafe_allow_html=True)
