import streamlit as st
from datetime import date
from io import StringIO

# ---------- PAGE CONFIG (call once, at top) ----------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="🧩",
    layout="wide",
)

# ---------- SAFE SESSION DEFAULTS ----------
ss = st.session_state
def sdefault(key, value):
    if key not in ss:
        ss[key] = value
for k, v in {
    "topic": "",
    "course": "GE4-IPM — Integrated Project & Materials Management in Defense Technology",
    "cohort": "D1-C01",
    "instructor": "Daniel",
    "date": str(date.today()),
    "lesson": 1,
    "week": 1,
    "verbs_low": ["define", "identify", "list"],
    "verbs_med": ["apply", "demonstrate", "solve"],
    "verbs_high": ["evaluate", "synthesize", "design"],
    "how_many": 10,
    "answer_key": True,
    "mcqs": [],
    "skills_count": 1,
    "skills_mins": 10,
    "skills_group": "Solo (1)",
    "deep_scan": False,
} .items():
    sdefault(k, v)

# ---------- DATA ----------
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
COHORTS = ["D1-C01", "D1-E01", "D1-E02", "D1-M01", "D1-M02", "D1-M03", "D1-M04", "D1-M05",
           "D2-C01", "D2-M01", "D2-M02", "D2-M03", "D2-M04", "D2-M05", "D2-M06"]

INSTRUCTORS = [
    "Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen Tariq","Dari",
    "Ghamza Labeeb","Michail","Meshari","Mohammed Alwuthaylah","Myra","Meshal Algurabi",
    "Ibrahim Alrawaili","Khalil","Salem","Chetan","Yasser","Ahmed Albader","Muath","Sultan",
    "Dr. Mashael","Noura Aldossari","Daniel"
]

# ---------- CSS (theme polish, dashed uploader, pointer/hover) ----------
st.markdown("""
<style>
/* Header bar */
.adibar {
  background:#153a27;
  color:#fff;
  padding:12px 16px;
  border-radius:8px;
  margin:8px 0 16px 0;
  font-weight:600;
}

/* Verb bands */
.band { border:1.5px solid #245a34; border-radius:8px; padding:10px 12px; margin:8px 0; }
.band.low  { background:#cfe8d9; }   /* soft green */
.band.med  { background:#f8e6c9; }   /* soft amber */
.band.high { background:#dfe6ff; }   /* soft blue  */

/* MultiSelect chip tidy (keeps Streamlit default green chips) */
[data-baseweb="tag"] {
  font-weight:600;
}
[data-baseweb="tag"] span {
  margin-right:2px;
}

/* Dashed uploader + pointer */
div[data-testid="stFileUploaderDropzone"] {
  border:2px dashed #245a34 !important;
  border-radius:10px !important;
  background:#f7faf8 !important;
  transition: box-shadow .15s ease;
}
div[data-testid="stFileUploaderDropzone"]:hover {
  box-shadow:0 0 0 3px #245a34 inset !important;
  cursor:pointer !important;
}

/* Pointer + subtle hover ring for select-like widgets */
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button {
  cursor:pointer !important;
}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {
  box-shadow:0 0 0 2px #245a34 inset !important;
}

/* Keyboard focus ring */
:focus-visible { outline:2px solid #245a34 !important; outline-offset: 2px; }
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.image("adi_logo.png", width=120)
    st.markdown("### Upload (optional)")
    st.file_uploader(
        "Drag and drop file here",
        type=["txt","docx","pptx","pdf"],
        key="uploader"
    )
    st.checkbox("Deep scan source (slower, better coverage)", key="deep_scan")

    st.markdown("### Course details")
    # helper to find index safely
    def _idx(lst, val, fallback=0):
        return lst.index(val) if val in lst else fallback

    st.selectbox("Course name", COURSES, index=_idx(COURSES, ss.course), key="course")
    st.selectbox("Class / Cohort", COHORTS, index=_idx(COHORTS, ss.cohort), key="cohort")
    st.selectbox("Instructor name", INSTRUCTORS, index=_idx(INSTRUCTORS, ss.instructor), key="instructor")

    st.text_input("Date", ss.date, key="date")

    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Lesson", min_value=1, max_value=14, step=1, value=int(ss.lesson), key="lesson")
    with c2:
        st.number_input("Week", min_value=1, max_value=14, step=1, value=int(ss.week), key="week")

# ---------- MAIN ----------
st.markdown('<div class="adibar">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

# Topic
ss.topic = st.text_area(
    "Topic / Outcome (optional)",
    value=ss.topic,
    placeholder="e.g., Integrated Project and …",
    key="topic"
)

# Verb bands (static palette; chips stay Streamlit green)
st.markdown('<div class="band low"><strong>Low (Weeks 1–4) — Remember / Understand</strong></div>', unsafe_allow_html=True)
ss.verbs_low = st.multiselect(
    "Low verbs", options=["define","identify","list","name","recall","describe"],
    default=ss.verbs_low, key="verbs_low_ms", label_visibility="collapsed"
)

st.markdown('<div class="band med"><strong>Medium (Weeks 5–9) — Apply / Analyse</strong></div>', unsafe_allow_html=True)
ss.verbs_med = st.multiselect(
    "Medium verbs", options=["apply","demonstrate","solve","analyse","compare","organize"],
    default=ss.verbs_med, key="verbs_med_ms", label_visibility="collapsed"
)

st.markdown('<div class="band high"><strong>High (Weeks 10–14) — Evaluate / Create</strong></div>', unsafe_allow_html=True)
ss.verbs_high = st.multiselect(
    "High verbs", options=["evaluate","synthesize","design","justify","critique","compose"],
    default=ss.verbs_high, key="verbs_high_ms", label_visibility="collapsed"
)

st.caption("ADI policy: 1–3 per lesson (Weeks 1–4 Low, 5–9 Medium, 10–14 High)")

# ---------- TABS ----------
tab_mcq, tab_skills, tab_rev, tab_print = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

# ---------- HELPERS ----------
def generate_mcqs(topic, low, med, high, n):
    """Simple stable generator: creates n editable MCQs based on any available verbs/topic."""
    verbs = (low or []) + (med or []) + (high or [])
    if not verbs: verbs = ["define","apply","evaluate"]
    qs = []
    for i in range(n):
        v = verbs[i % len(verbs)]
        stem = f"Using the verb '{v}', write one question about: {topic or 'this lesson'}."
        qs.append({
            "stem": stem,
            "A": "Option A",
            "B": "Option B",
            "C": "Option C",
            "D": "Option D",
            "correct": "A"
        })
    return qs

def mcqs_to_txt(mcqs, include_key=True):
    buf = StringIO()
    for i, q in enumerate(mcqs, start=1):
        buf.write(f"Q{i}. {q['stem']}\n")
        buf.write(f"  A) {q['A']}\n")
        buf.write(f"  B) {q['B']}\n")
        buf.write(f"  C) {q['C']}\n")
        buf.write(f"  D) {q['D']}\n")
        if include_key:
            buf.write(f"  Answer: {q['correct']}\n")
        buf.write("\n")
    return buf.getvalue()

# ---------- MCQ TAB ----------
with tab_mcq:
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        ss.how_many = st.selectbox(
            "How many MCQs?",
            [5,10,12,15,20],
            index=[5,10,12,15,20].index(ss.how_many) if ss.how_many in [5,10,12,15,20] else 1,
            key="how_many"
        )
    with col2:
        st.checkbox("Answer key", key="answer_key")

    if st.button("Generate from verbs/topic", key="btn_gen_mcq"):
        ss.mcqs = generate_mcqs(ss.topic, ss.verbs_low, ss.verbs_med, ss.verbs_high, ss.how_many)

    # Editor
    if not ss.mcqs:
        st.info("No questions yet. Click **Generate from verbs/topic**.")
    else:
        for i, q in enumerate(ss.mcqs, start=1):
            st.markdown(f"**Q{i}**")
            q["stem"] = st.text_area(f"Question", q["stem"], key=f"q_stem_{i}")
            cA, cB = st.columns(2)
            with cA:
                q["A"] = st.text_input("A", q["A"], key=f"qA_{i}")
                q["C"] = st.text_input("C", q["C"], key=f"qC_{i}")
            with cB:
                q["B"] = st.text_input("B", q["B"], key=f"qB_{i}")
                q["D"] = st.text_input("D", q["D"], key=f"qD_{i}")
            q["correct"] = st.radio("Correct answer", ["A","B","C","D"], horizontal=True, index=["A","B","C","D"].index(q["correct"]), key=f"q_correct_{i}")
            st.divider()

        txt = mcqs_to_txt(ss.mcqs, include_key=ss.answer_key)
        st.download_button(
            "⬇️ Download TXT (All MCQs)",
            data=txt.encode("utf-8"),
            file_name=f"ADI_MCQ__{ss.course.split('—')[0].strip()}__{ss.cohort}__W{ss.week}__Q{len(ss.mcqs)}.txt",
            mime="text/plain",
            key="dl_mcq_txt_all"
        )

# ---------- SKILLS TAB ----------
with tab_skills:
    c1, c2, c3 = st.columns(3)
    ss.skills_count = c1.selectbox("How many activities?", [1,2,3], index=[1,2,3].index(ss.skills_count), key="skills_count")
    ss.skills_mins  = c2.selectbox("Minutes per activity", list(range(5,65,5)), index=list(range(5,65,5)).index(ss.skills_mins), key="skills_mins")
    ss.skills_group = c3.selectbox("Group size", ["Solo (1)","Pairs (2)","Triads (3)","Teams of 4"], index=["Solo (1)","Pairs (2)","Triads (3)","Teams of 4"].index(ss.skills_group), key="skills_group")

    if st.button("Generate activities", key="btn_gen_skills"):
        acts = []
        verbs = (ss.verbs_med or []) + (ss.verbs_high or []) + (ss.verbs_low or [])
        if not verbs: verbs = ["apply","evaluate","design"]
        for i in range(ss.skills_count):
            v = verbs[i % len(verbs)]
            acts.append({
                "title": f"Activity {i+1}: {v.title()} task",
                "brief": f"Students will {v} in groups: {ss.skills_group.lower()}, for {ss.skills_mins} minutes.",
            })
        ss["skills"] = acts

    if "skills" in ss and ss.skills_count:
        for i, a in enumerate(ss.skills, start=1):
            st.markdown(f"**{a['title']}**  \n{a['brief']}")
            st.divider()
    else:
        st.info("No activities yet. Click **Generate activities**.")

# ---------- REVISION TAB ----------
with tab_rev:
    st.write("Quick revision prompts (coming next). For now, reuse the MCQs or create a short recap.")

# ---------- PRINT SUMMARY TAB ----------
with tab_print:
    st.write("Printable summary (coming next). For now, use the TXT download from MCQs.")
