# app.py
import io
import datetime
from typing import List, Dict
import streamlit as st

# ========= BASIC PAGE CONFIG (must be first) =========
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="✅",
    layout="wide",
)

# ========= SAFE STATE DEFAULTS =========
def _get_query_params():
    # Compatible with older Streamlit
    try:
        return st.experimental_get_query_params()
    except Exception:
        return {}

def _set_query_params(**kwargs):
    try:
        st.experimental_set_query_params(**{k: str(v) for k, v in kwargs.items()})
    except Exception:
        pass

def _init_state():
    ss = st.session_state
    qp = _get_query_params()
    # text inputs
    ss.setdefault("topic_input", "")
    # numeric + booleans
    ss.setdefault("how_many", 10)
    ss.setdefault("answer_key", True)
    # sticky lesson/week
    try:
        lesson_q = int(qp.get("lesson", ["1"])[0])
        week_q   = int(qp.get("week", ["1"])[0])
    except Exception:
        lesson_q, week_q = 1, 1
    ss.setdefault("lesson", lesson_q)
    ss.setdefault("week", week_q)
    # tabs
    ss.setdefault("tab", "mcq")

_init_state()

def _push_query_params():
    _set_query_params(lesson=st.session_state.lesson, week=st.session_state.week, tab=st.session_state.tab)

# ========= STYLES =========
st.markdown("""
<style>
/* ADI top banner look */
.adi-banner {
  background:#153a2c;
  color:#fff;
  padding:10px 16px;
  border-radius:8px;
  font-weight:600;
  letter-spacing:.3px;
}

/* ADI dashed uploader */
div[data-testid="stFileUploaderDropzone"]{
  border:2px dashed #245a34 !important;
  background:#f7faf7 !important;
  border-radius:10px !important;
}
div[data-testid="stFileUploaderDropzone"]:hover{
  box-shadow:0 0 0 3px rgba(36,90,52,.2) inset !important;
}

/* Make interactive bits feel clickable */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button {
  cursor:pointer !important;
}

/* Hover feedback on selects/multiselects */
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {
  box-shadow:0 0 0 2px #245a34 inset !important;
}

/* Focus ring */
:focus-visible { outline:2px solid #245a34 !important; outline-offset:2px !important; }

/* Verb “bands” */
.band{padding:.6rem .8rem;border:1px solid #1f3b2f;border-radius:8px;margin:.4rem 0}
.band.low{background:#e6f0e9}
.band.med{background:#f7ecd4}
.band.high{background:#e6eefc}
.band.active{box-shadow:0 0 0 2px #245a34 inset}

/* Side panel cards look */
.sidebar-card {
  background:#ffffff;
  border:1px solid #e9ecef;
  border-radius:10px;
  padding:10px;
  margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# ========= HEADER =========
st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)
st.write("")

# ========= LAYOUT: left sidebar (controls) + main body =========
left, main = st.columns([0.28, 0.72], gap="large")

# ---------------- LEFT SIDEBAR ----------------
with left:
    st.subheader("Upload (optional)")
    uploaded = st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"])
    if uploaded is not None:
        st.success(f"Uploaded **{uploaded.name}** ({uploaded.size/1024:.1f} KB)")

    st.checkbox("Deep scan source (slower, better coverage)", key="deep_scan")

    st.subheader("Course details")
    with st.container():
        # Course / Cohort / Instructor / Date / Lesson / Week
        st.selectbox("Course name", [
            "GE4-IPM — Integrated Project & Materials Management",
            "GE4-ELM — Engineering Logistics Management",
            "GE4-QA  — Quality Assurance"
        ], key="course_name")

        st.selectbox("Class / Cohort", [
            "D1-C01", "D1-C02", "D1-C03", "D2-C01", "D2-C02"
        ], key="cohort")

        st.selectbox("Instructor name", [
            "Daniel", "Fatima", "Hassan", "Layla"
        ], key="instructor")

        st.date_input("Date", value=datetime.date.today(), key="date")

        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Lesson", 1, 99, key="lesson", on_change=_push_query_params)
        with c2:
            st.number_input("Week", 1, 14, key="week", on_change=_push_query_params)

# ---------------- MAIN ----------------
with main:
    topic = st.text_area("Topic / Outcome (optional)", key="topic_input", placeholder="e.g., Integrated Project and …")

    # Active band
    def _active_band(week:int)->str:
        if week <= 4:  return "low"
        if week <= 9:  return "med"
        return "high"

    active = _active_band(st.session_state.week)

    # Band helper
    def band(title:str, band_key:str, verbs:List[str], state_key:str)->List[str]:
        klass = f"band {band_key}" + (" active" if band_key == active else "")
        st.markdown(f'<div class="{klass}"><strong>{title}</strong></div>', unsafe_allow_html=True)
        return st.multiselect("", options=verbs, default=st.session_state.get(state_key, []), key=state_key)

    low_verbs  = band("Low (Weeks 1–4) — Remember / Understand", "low",
                      ["define","identify","list"], "verbs_low")
    med_verbs  = band("Medium (Weeks 5–9) — Apply / Analyse", "med",
                      ["apply","demonstrate","solve"], "verbs_med")
    high_verbs = band("High (Weeks 10–14) — Evaluate / Create", "high",
                      ["evaluate","synthesize","design"], "verbs_high")

    st.caption("ADI policy: 1–3 per lesson • 5–9 Medium • 10–14 High")

    tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

    # ---- SIMPLE DEMO GENERATORS ----
    def gen_mcqs(n:int, topic_text:str, verbs:List[str], include_key:bool=True) -> List[Dict]:
        base = topic_text.strip() if topic_text.strip() else "the topic"
        out = []
        for i in range(1, n+1):
            prompt = f"Q{i}. With reference to {base}, which option best matches the learning intent"
            if verbs:
                prompt += f" (**{', '.join(verbs)}**)?"
            else:
                prompt += "?"
            opts = [("A", "To verify conformance"),
                    ("B", "To set company policy"),
                    ("C", "To hire staff"),
                    ("D", "To control budgets")]
            correct = "A"
            out.append({"q":prompt, "opts":opts, "ans":correct})
        return out

    def gen_skills(n:int, topic_text:str, verbs:List[str]) -> List[str]:
        base = topic_text.strip() if topic_text.strip() else "the topic"
        verbs_s = ", ".join(verbs) if verbs else "apply"
        out = []
        for i in range(1, n+1):
            out.append(f"Activity {i}: In teams, {verbs_s} concepts to {base}; present findings in 3–5 min.")
        return out

    # MCQs TAB
    with tabs[0]:
        cA, cB = st.columns([1, 1])
        with cA:
            st.selectbox("How many MCQs?", [5, 10, 12, 15, 20], key="how_many")
        with cB:
            st.checkbox("Answer key", key="answer_key")

        if st.button("Generate from verbs/topic", key="gen_mcq"):
            chosen_verbs = (low_verbs or []) + (med_verbs or []) + (high_verbs or [])
            st.session_state["mcqs"] = gen_mcqs(st.session_state.how_many, topic, chosen_verbs, st.session_state.answer_key)

        mcqs = st.session_state.get("mcqs", [])
        if mcqs:
            for q in mcqs:
                st.write(q["q"])
                cols = st.columns(2)
                with cols[0]:
                    st.write(f"A. {q['opts'][0][1]}")
                    st.write(f"B. {q['opts'][1][1]}")
                with cols[1]:
                    st.write(f"C. {q['opts'][2][1]}")
                    st.write(f"D. {q['opts'][3][1]}")
                if st.session_state.answer_key:
                    st.caption(f"**Correct answer:** {q['ans']}")
                st.divider()

            # Download as TXT (demo)
            txt_io = io.StringIO()
            for q in mcqs:
                txt_io.write(q["q"] + "\n")
                for code, opt in q["opts"]:
                    txt_io.write(f"{code}. {opt}\n")
                if st.session_state.answer_key:
                    txt_io.write(f"Answer: {q['ans']}\n")
                txt_io.write("\n")
            st.download_button("Download TXT (All MCQs)", data=txt_io.getvalue().encode("utf-8"),
                               file_name="ADI_MCQ_All.txt", mime="text/plain", key="dl_mcq_txt")

    # SKILLS TAB
    with tabs[1]:
        if st.button("Generate Skills", key="gen_skills"):
            chosen_verbs = (low_verbs or []) + (med_verbs or []) + (high_verbs or [])
            st.session_state["skills"] = gen_skills(3, topic, chosen_verbs)

        skills = st.session_state.get("skills", [])
        if skills:
            for s in skills:
                st.write("• " + s)

            txt_io2 = io.StringIO("\n".join(skills))
            st.download_button("Download TXT (Skills)", data=txt_io2.getvalue().encode("utf-8"),
                               file_name="ADI_Skills.txt", mime="text/plain", key="dl_skills_txt")

    # REVISION TAB (placeholder)
    with tabs[2]:
        st.info("Revision toolkit coming soon (flash cards, recall prompts, quick quizzes).")

    # PRINT SUMMARY TAB
    with tabs[3]:
        st.write("**Print Summary**")
        st.write(f"- Course: {st.session_state.course_name}")
        st.write(f"- Cohort: {st.session_state.cohort}")
        st.write(f"- Instructor: {st.session_state.instructor}")
        st.write(f"- Date: {st.session_state.date}")
        st.write(f"- Lesson: {st.session_state.lesson} • Week: {st.session_state.week}")
        st.write(f"- Topic: {topic if topic.strip() else '—'}")
        st.write(f"- Low verbs: {', '.join(low_verbs) if low_verbs else '—'}")
        st.write(f"- Medium verbs: {', '.join(med_verbs) if med_verbs else '—'}")
        st.write(f"- High verbs: {', '.join(high_verbs) if high_verbs else '—'}")

