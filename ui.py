# ui.py — UI components and styling
import datetime as dt
import streamlit as st

def initialize_session_state():
    defaults = {
        "topic": "",
        "course": "GE4-IPM — Integrated Project & Materials Management",
        "cohort": "D1-C01",
        "instructor": "Daniel",
        "date": dt.date.today().isoformat(),
        "lesson": 1,
        "week": 1,
        "verbs_low": ["define", "identify", "list"],
        "verbs_med": ["apply", "demonstrate", "solve"],
        "verbs_high": ["evaluate", "synthesize", "design"],
        "mcqs": [],
        "skills": [],
        "revision": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def apply_custom_styles():
    st.markdown(f"""
    <style>
    .adi-banner {{
        background:#153a27; color:white; padding:10px 16px; border-radius:8px;
        font-weight:600; letter-spacing:.2px; margin-bottom:12px;
    }}
    .band {{ border:1px solid #153a27; border-radius:8px; padding:10px; margin:8px 0; }}
    .band.low.active   {{ background:#d6e8df; }}
    .band.med.active   {{ background:#f3e9d2; }}
    .band.high.active  {{ background:#dbe6e1; }}
    div[data-testid="stFileUploaderDropzone"] {{
        border:2px dashed #153a27 !important; background:#f8faf9;
    }}
    div[data-testid="stFileUploaderDropzone"]:hover {{
        box-shadow: inset 0 0 0 3px #153a27 !important;
    }}
    input:hover, select:hover {{
        box-shadow: 0 0 0 2px #153a27 !important; border-color:#153a27 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def render_header(build_tag):
    cols = st.columns([1, 8, 1.5])
    with cols[0]:
        try:
            st.image("adi_logo.png", width=120)
        except Exception:
            pass
    with cols[1]:
        st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)
    with cols[2]:
        st.caption(f"Build: {build_tag}")

def render_course_inputs():
    st.subheader("Upload (optional)")
    uploaded = st.file_uploader("Drag and drop file here",
        type=["txt", "docx", "pptx", "pdf"],
        help="Limit 200MB / file", label_visibility="collapsed")
    if uploaded is not None:
        st.success(f"Uploaded: **{uploaded.name}**")
    st.checkbox("Deep scan source (slower, better coverage)", value=False)

    st.subheader("Course details")
    st.selectbox("Course name", [
        "GE4-IPM — Integrated Project & Materials Management",
        "GE4-EPM — Defense Tech: Experiments/QM/Inspection",
        "GE4-MRO — Military Vehicle & Aircraft MRO",
    ], key="course")
    st.selectbox("Class / Cohort", ["D1-C01", "D1-M01", "D2-C01"], key="cohort")
    st.selectbox("Instructor name", [
        "Daniel", "Dr. Mashael", "Noura Aldossari", "Ahmed Albader", "Michail",
        "Myra", "Sultan", "Chetan"
    ], key="instructor")
    st.date_input("Date", value=dt.date.fromisoformat(st.session_state["date"]), key="date")
    lc1, lc2 = st.columns(2)
    with lc1:
        st.number_input("Lesson", min_value=1, max_value=14, step=1, key="lesson")
    with lc2:
        st.number_input("Week", min_value=1, max_value=14, step=1, key="week")
    return uploaded

def render_topic_and_verbs():
    st.subheader("Topic / Outcome (optional)")
    st.text_area("", key="topic", placeholder="e.g., Integrated Project and …", height=80, label_visibility="collapsed")

    ALL_VERBS = {
        "verbs_low":  ["define", "identify", "list", "describe", "recall"],
        "verbs_med":  ["apply", "demonstrate", "solve", "analyze", "compare"],
        "verbs_high": ["evaluate", "synthesize", "design", "justify", "create"]
    }

    def verb_band(title, key, bg_class):
        selected = st.session_state[key]
        wk = st.session_state["week"]
        active = (
            (bg_class == "low"  and 1 <= wk <= 4)  or
            (bg_class == "med"  and 5 <= wk <= 9)  or
            (bg_class == "high" and wk >= 10)
        )
        klass = f"band {bg_class}" + (" active" if active else "")
        st.markdown(f'<div class="{klass}"><strong>{title}</strong></div>', unsafe_allow_html=True)
        st.multiselect(" ", options=ALL_VERBS[key], default=selected, key=key, label_visibility="collapsed")

    verb_band("Low (Weeks 1–4) — Remember / Understand", "verbs_low", "low")
    verb_band("Medium (Weeks 5–9) — Apply / Analyse", "verbs_med", "med")
    verb_band("High (Weeks 10–14) — Evaluate / Create", "verbs_high", "high")
    st.caption("ADI policy: 1–3 per lesson • 5–9 Medium • 10–14 High")
