# ---------------------------
# ADI Builder — Lesson Activities & Questions (stable)
# ---------------------------
import streamlit as st
from io import BytesIO
from datetime import date

# ---------- Page config (must be first) ----------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="📘",
    layout="wide",
)


# ---------- One-time state init ----------
def init_state():
    ss = st.session_state
    defaults = {
        # top form
        "topic": "",
        # selections
        "course": "GE4-IPM — Integrated Project & Materials Mgmt",
        "cohort": "D1-C01",
        "instructor": "Daniel",
        "lesson": 1,
        "week": 1,
        "how_many": 10,
        "answer_key": True,
        # verbs
        "verbs_low": ["define", "identify", "list"],
        "verbs_med": ["apply", "demonstrate", "solve"],
        "verbs_high": ["evaluate", "synthesize", "design"],
        # ui
        "active_tab": "mcq",
        "uploaded_files_count": 0,
    }
    for k, v in defaults.items():
        if k not in ss:
            ss[k] = v


init_state()

# ---------- Constants ----------
ADI_GREEN = "#245a34"       # brand green
ADI_GREEN_DARK = "#153a27"  # darker
LOW_BG = "#e6f3ec"          # pale green
MED_BG = "#f8f0db"          # pale sand
HIGH_BG = "#e6eefc"         # pale blue
BORDER = "#245a34"

LOW_VERBS = ["define", "identify", "list", "label", "recall", "state", "name"]
MED_VERBS = ["apply", "demonstrate", "solve", "analyse", "compare", "classify"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

MCQ_COUNT_OPTIONS = [5, 10, 12, 15, 20]

# ---------- Styles ----------
st.markdown(
    f"""
    <style>
      /* Header bar */
      .top-banner {{
        background:{ADI_GREEN_DARK};
        color:#fff;
        padding:10px 16px;
        border-radius:8px;
        font-weight:600;
        margin-bottom:12px;
      }}

      /* Drag & drop dashed */
      div[data-testid="stFileUploaderDropzone"] {{
        border: 2px dashed {ADI_GREEN} !important;
        border-radius: 10px !important;
        background: #f8faf9;
      }}
      div[data-testid="stFileUploaderDropzone"]:hover {{
        box-shadow: 0 0 0 3px {ADI_GREEN} inset !important;
      }}

      /* Make interactive bits feel clickable */
      div[data-testid="stFileUploaderDropzone"],
      div[data-testid="stSelectbox"] button,
      div[data-testid="stMultiSelect"] button,
      button[kind],
      button {{ cursor: pointer !important; }}

      /* Hover feedback for select buttons/chips */
      div[data-testid="stSelectbox"] button:hover,
      div[data-testid="stMultiSelect"] button:hover {{
        box-shadow: 0 0 0 2px {ADI_GREEN} inset !important;
      }}

      /* Chips */
      .chip-row {{
        border:1px solid {BORDER};
        border-radius:10px;
        padding:10px 10px 6px 10px;
        margin:6px 0 12px 0;
      }}
      .band-title {{
        font-weight:600; color:{ADI_GREEN_DARK};
        margin-bottom:6px;
      }}
      /* band colours */
      .low    {{ background:{LOW_BG}; }}
      .medium {{ background:{MED_BG}; }}
      .high   {{ background:{HIGH_BG}; }}

      /* multiselect pill accent (keeps Streamlit green, but we add depth) */
      div[data-baseweb="tag"] {{
        background: {ADI_GREEN} !important;
        color: #fff !important;
        border-radius: 999px !important;
        box-shadow: 0 0 0 1px {ADI_GREEN_DARK} inset;
      }}

      /* Focus ring for keyboard users */
      :focus-visible {{
        outline: 2px solid {ADI_GREEN} !important;
        outline-offset: 2px !important;
      }}

      /* Sidebar section headings spacing */
      section[data-testid="stSidebar"] .stMarkdown h3 {{
        margin-top: 0.25rem; margin-bottom: 0.25rem;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Layout ----------
st.markdown('<div class="top-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

left, right = st.columns([0.27, 0.73], gap="large")

# ---------- Sidebar-like left panel ----------
with left:
    st.subheader("Upload (optional)")
    up = st.file_uploader(
        "Drag and drop file here",
        type=["txt", "docx", "pptx", "pdf"],
        accept_multiple_files=True,
    )
    if up:
        st.session_state.uploaded_files_count = len(up)
        st.toast(f"Uploaded {len(up)} file(s).", icon="✅")

    st.checkbox("Deep scan source (slower, better coverage)", key="deep_scan")

    st.subheader("Course details")

    st.selectbox(
        "Course name",
        [
            "GE4-IPM — Integrated Project & Materials Mgmt",
            "GE4-EPM — Experimental Practices & Inspection",
            "GE4-MRO — Military Vehicle & Aircraft MRO",
            "CT4-COM — Computation for Chemical Technologists",
            "CT4-EMG — Explosives Manufacturing",
            "EE4-PMG — PCB Manufacturing",
        ],
        key="course",
    )
    st.selectbox(
        "Class / Cohort",
        ["D1-C01", "D1-M01", "D1-M02", "D2-C01", "D2-M01", "D2-M02", "D2-M03", "D2-M04"],
        key="cohort",
    )
    st.selectbox(
        "Instructor name",
        [
            "Daniel",
            "Ben", "Abdulmalik", "Gerhard", "Faiz Lazam", "Mohammed Alfarhan", "Nerdeen Tariq",
            "Dari", "Ghamza Labeeb", "Michail", "Meshari", "Mohammed Alwuthaylah", "Myra",
            "Meshal Algurabi", "Ibrahim Alrawaili", "Khalil", "Salem", "Chetan", "Yasser",
            "Ahmed Albader", "Muath", "Sultan", "Dr. Mashael", "Noura Aldossari",
        ],
        key="instructor",
    )

    st.date_input("Date", value=date.today(), key="the_date")

    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Lesson", min_value=1, max_value=20, step=1, key="lesson")
    with c2:
        st.number_input("Week", min_value=1, max_value=14, step=1, key="week")

# ---------- Main panel ----------
with right:
    st.text_area(
        "Topic / Outcome (optional)",
        key="topic",
        placeholder="e.g., Integrated Project and …",
        label_visibility="visible",
    )

    # Helper to render a verb band with colored box
    def verb_band(title: str, key: str, options, css_class: str):
        st.markdown(f'<div class="chip-row {css_class}">', unsafe_allow_html=True)
        st.markdown(f'<div class="band-title">{title}</div>', unsafe_allow_html=True)
        st.multiselect(
            " ",
            options=options,
            default=st.session_state.get(key, []),
            key=key,
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Bands
    verb_band("Low (Weeks 1–4) — Remember / Understand", "verbs_low", LOW_VERBS, "low")
    verb_band("Medium (Weeks 5–9) — Apply / Analyse", "verbs_med", MED_VERBS, "medium")
    verb_band("High (Weeks 10–14) — Evaluate / Create", "verbs_high", HIGH_VERBS, "high")

    # Tabs
    tab_mcq, tab_skills, tab_rev, tab_print = st.tabs(
        ["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"]
    )

    with tab_mcq:
        st.caption("ADI policy: 1–3 per lesson • 5–9 Medium • 10–14 High")
        mcq_controls = st.container()
        with mcq_controls:
            c1, c2 = st.columns([0.55, 0.45])
            with c1:
                st.selectbox(
                    "How many MCQs?",
                    MCQ_COUNT_OPTIONS,
                    index=MCQ_COUNT_OPTIONS.index(
                        st.session_state.get("how_many", 10)
                    ),
                    key="how_many",
                )
            with c2:
                st.checkbox("Answer key", key="answer_key")

            # Generate MCQs
            if st.button("Generate from verbs/topic", use_container_width=False):
                # ---- plug your real generator here if you have one ----
                qcount = st.session_state.how_many
                verbs = (
                    st.session_state.verbs_low
                    + st.session_state.verbs_med
                    + st.session_state.verbs_high
                )
                topic = st.session_state.topic.strip() or "the lesson topic"
                if not verbs:
                    st.warning("Please choose at least one verb.")
                else:
                    st.session_state["mcqs"] = [
                        {
                            "q": f"({i+1}) Based on {topic}, using '{verbs[i % len(verbs)]}', choose the best answer.",
                            "A": "Option A",
                            "B": "Option B",
                            "C": "Option C",
                            "D": "Option D",
                            "ans": "A",
                        }
                        for i in range(qcount)
                    ]
                    st.success(f"Generated {qcount} MCQs.")

        # Render MCQs (editable text inputs)
        mcqs = st.session_state.get("mcqs", [])
        if mcqs:
            for i, q in enumerate(mcqs):
                st.markdown(f"**Q{i+1}**")
                q["q"] = st.text_area(f"Question {i+1}", value=q["q"], key=f"q_{i}")
                cols = st.columns(2)
                with cols[0]:
                    q["A"] = st.text_input("A", value=q["A"], key=f"A_{i}")
                    q["B"] = st.text_input("B", value=q["B"], key=f"B_{i}")
                with cols[1]:
                    q["C"] = st.text_input("C", value=q["C"], key=f"C_{i}")
                    q["D"] = st.text_input("D", value=q["D"], key=f"D_{i}")
                st.radio("Correct answer", ["A", "B", "C", "D"], index=["A","B","C","D"].index(q["ans"]), key=f"ans_{i}")
                st.divider()
        else:
            st.info("No questions yet. Click **Generate from verbs/topic**.")

    with tab_skills:
        st.caption("Quick activity ideas based on your selected verbs.")
        if st.button("Generate Skills", key="gen_skills"):
            verbs = (
                st.session_state.verbs_low
                + st.session_state.verbs_med
                + st.session_state.verbs_high
            )
            topic = st.session_state.topic.strip() or "the lesson topic"
            st.session_state["skills"] = [
                f"Pair discussion: Using **{v}** for **{topic}** (10 min)."
                for v in verbs[:6] or ["apply", "evaluate"]
            ]
            st.success("Skills activities drafted.")
        for i, s in enumerate(st.session_state.get("skills", [])):
            st.text_area(f"Activity {i+1}", value=s, key=f"skill_{i}")

    with tab_rev:
        st.caption("A quick end-of-lesson review prompt.")
        st.text_area(
            "Exit ticket",
            value="One thing I learned …\nOne question I still have …",
            key="exit_ticket",
            height=120,
        )

    with tab_print:
        st.caption("Compact summary for printing/export (stub).")
        st.write("• **Course**:", st.session_state.course)
        st.write("• **Cohort**:", st.session_state.cohort)
        st.write("• **Instructor**:", st.session_state.instructor)
        st.write("• **Lesson/Week**:", st.session_state.lesson, "/", st.session_state.week)
        st.write("• **Topic**:", st.session_state.topic or "—")
        st.write("• **Low**:", ", ".join(st.session_state.verbs_low) or "—")
        st.write("• **Medium**:", ", ".join(st.session_state.verbs_med) or "—")
        st.write("• **High**:", ", ".join(st.session_state.verbs_high) or "—")
        st.caption("Export to DOCX/PDF can be wired here when ready.")
