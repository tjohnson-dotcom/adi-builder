# --- app.py (enhanced quick-pick chips + print-friendly summary) ---
import streamlit as st
from datetime import date
from textwrap import dedent

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

# ---------------- Session & theme helpers ----------------
if "selected_course" not in st.session_state:
    st.session_state.selected_course = None
if "topics" not in st.session_state:
    st.session_state.topics = []
if "generated_items" not in st.session_state:
    st.session_state.generated_items = []
if "mode" not in st.session_state:
    st.session_state.mode = "Knowledge"

ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
STONE = "#F5F4F2"

def pill(value, key=None):
    st.markdown(
        f"""
        <span style="border:1px solid {ADI_GREEN}; color:{ADI_GREEN};
                     padding:.35rem .7rem; border-radius:999px; display:inline-block; font-size:0.9rem;">
            {value}
        </span>
        """, unsafe_allow_html=True
    )

def bloom_badge(week:int):
    level = "Low" if week<=4 else ("Medium" if week<=9 else "High")
    st.markdown(
        f"""<span style="background:{ADI_GOLD}; color:black; padding:.1rem .5rem; 
                         border-radius:999px; font-weight:600;">{level}</span>""",
        unsafe_allow_html=True
    )
    return level

# ---------------- Side styles ----------------
st.markdown(
    f"""
    <style>
      .stApp {{ background: white; }}
      .block-container {{ padding-top: 2rem; }}
      .adi-card {{
        background:{STONE}; border:1px solid #e7e5e4; border-radius:14px; padding:14px;
      }}
      .adi-chip {{
        border-radius:14px; padding:12px; border:1px solid #e7e5e4; cursor:pointer;
        display:flex; align-items:center; justify-content:center; text-align:center;
      }}
      .adi-chip:hover {{ border-color:{ADI_GREEN}; box-shadow:0 0 0 2px rgba(36,90,52,.08) inset; }}
      .print-area {{ max-width: 900px; margin: 0 auto; }}
      @media print {{
        header, footer, .stApp [data-testid="stSidebar"], .stToolbar, .st-emotion-cache-12fmjuu, 
        .st-emotion-cache-ue6h4q, .stButton {{ display:none !important; }}
        .block-container {{ padding:0 !important; }}
        .print-area {{ margin:0; }}
        body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
      }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- Data ----------------
COURSE_OPTIONS = [
    ("GE4-EPM", "Defense Technology Practices: Experimentation, Quality Management and Inspection"),
    ("GE4-IPM", "Integrated Project & Materials Management in Defense Technology"),
    ("GE4-MRO", "Military Vehicle and Aircraft MRO: Principles & Applications"),
    ("CT4-COM", "Computation for Chemical Technologists"),
    ("CT4-EMG", "Explosives Manufacturing"),
    ("CT4-TFL", "Thermofluids"),
]

# ---------------- Header ----------------
left, right = st.columns([1.15, 1])
with left:
    st.markdown(f"<h1 style='color:{ADI_GREEN}'>ADI Builder — Lesson Activities & Questions</h1>", unsafe_allow_html=True)

with right:
    st.write("")

# ---------------- Layout ----------------
colL, colR = st.columns([1.15, 1])

# ============ RIGHT: Course quick-pick (now clickable) ============
with colR:
    st.markdown("### Course quick-pick")
    gp1 = st.columns(3)
    gp2 = st.columns(3)

    def chip(label, code, col):
        with col:
            clicked = st.button(
                f"{label}\n\n*{code}*",
                key=f"chip-{code}",
                help="Click to select this course",
                use_container_width=True
            )
            # convert to chip look
            st.markdown(
                f"""
                <script>
                const btn = window.parent.document.querySelector('button[k='{st.session_state._last_element_id}']');
                </script>
                """, unsafe_allow_html=True
            )
            if clicked:
                st.session_state.selected_course = code
                # jump user to the top-left authoring form
                st.sidebar.success(f"Selected course: {code}")
                st.experimental_rerun()

    chip("Defense Technology Practices", "GE4-EPM", gp1[0])
    chip("Integrated Project & Materials Mgmt", "GE4-IPM", gp1[1])
    chip("Military Vehicle & Aircraft MRO", "GE4-MRO", gp1[2])
    chip("Computation for Chemical Technologists", "CT4-COM", gp2[0])
    chip("Explosives Manufacturing", "CT4-EMG", gp2[1])
    chip("Thermofluids", "CT4-TFL", gp2[2])

    st.info("Tip: pick a chip or use the select box on the left.", icon="💡")

# ============ LEFT: Authoring =============
with colL:
    st.markdown("### Course details")

    # select box reflects chip click
    course_codes = [c[0] for c in COURSE_OPTIONS]
    default_idx = course_codes.index(st.session_state.selected_course) if st.session_state.selected_course in course_codes else 0
    course = st.selectbox("Course name", options=course_codes, index=default_idx, key="course_select")

    class_cohort = st.selectbox("Class / Cohort", options=["D1-C01", "D1-C02", "D2-C01"])
    instructor = st.text_input("Instructor name", value="Daniel")
    colA, colB = st.columns(2)
    with colA:
        lesson = st.number_input("Lesson", min_value=1, max_value=20, value=1, step=1)
    with colB:
        week = st.number_input("Week", min_value=1, max_value=14, value=1, step=1)

    st.markdown("---")
    st.markdown("### Authoring")

    topic_outcome = st.text_input("Topic / Outcome (optional)", placeholder="e.g., Integrated Project and …")

    st.caption("ADI policy: Weeks 1–4 Low • 5–9 Medium • 10–14 High  |  Recommended Bloom for Week:")
    bloom_level = bloom_badge(week)

    mode = st.segmented_control("Mode", options=["Knowledge", "Skills", "Revision", "Print Summary"], key="mode")

    # Progressive authoring
    if mode != "Print Summary":
        topics_text = st.text_area("Enter topics (one per line)", placeholder="Topic A\nTopic B\nTopic C", height=120)
        include_key = st.checkbox("Include answer key", value=True)

        count_col, _ = st.columns([2,1])
        with count_col:
            how_many = st.selectbox("How many MCQs?", options=[5, 10, 15, 20], index=1)

        # Generate button
        if st.button("Generate MCQs", type="primary", use_container_width=False):
            # --- placeholder generation (replace with your real generator) ---
            st.session_state.topics = [t.strip() for t in topics_text.splitlines() if t.strip()]
            items = []
            for i in range(how_many):
                items.append({
                    "stem": f"Sample question {i+1} on {st.session_state.topics[0] if st.session_state.topics else 'topic'}?",
                    "options": ["A) …", "B) …", "C) …", "D) …"],
                    "answer": "A"
                })
            st.session_state.generated_items = items
            st.success(f"Generated {len(items)} items.")
        # Inline editor
        if st.session_state.generated_items:
            st.markdown("#### Preview & quick edit")
            for idx, q in enumerate(st.session_state.generated_items):
                with st.expander(f"Q{idx+1}: {q['stem'][:80]}", expanded=False):
                    q["stem"] = st.text_input("Stem", value=q["stem"], key=f"stem-{idx}")
                    cols = st.columns(2)
                    q["options"][0] = cols[0].text_input("Option A", value=q["options"][0], key=f"oa-{idx}")
                    q["options"][1] = cols[1].text_input("Option B", value=q["options"][1], key=f"ob-{idx}")
                    cols2 = st.columns(2)
                    q["options"][2] = cols2[0].text_input("Option C", value=q["options"][2], key=f"oc-{idx}")
                    q["options"][3] = cols2[1].text_input("Option D", value=q["options"][3], key=f"od-{idx}")
                    q["answer"] = st.selectbox("Correct answer", options=["A","B","C","D"], index=["A","B","C","D"].index(q["answer"]), key=f"ans-{idx}")

            st.download_button("Export (TXT)", data="\n\n".join(
                [f"Q{n+1}. {q['stem']}\n" + "\n".join(q["options"]) + (f"\nAnswer: {q['answer']}" if include_key else "")
                 for n, q in enumerate(st.session_state.generated_items)]
            ), file_name=f"{course}_L{lesson}_W{week}_mcqs.txt")

    else:
        # ---------- PRINT-FRIENDLY MODE ----------
        st.markdown("#### Print Summary")
        st.markdown(
            f"""
            <div class="print-area">
                <h2 style="margin:0 0 .25rem 0; color:{ADI_GREEN}">{course} — Lesson {lesson} (Week {week})</h2>
                <div style="margin-bottom:.5rem;"><strong>Instructor:</strong> {instructor}</div>
                <div style="margin-bottom:.75rem;"><strong>Bloom focus:</strong> {bloom_level}</div>
                <h3 style="margin: 1rem 0 .5rem 0;">Topics</h3>
                <ol style="margin-top:0;">
                    {"".join(f"<li>{t}</li>" for t in (st.session_state.topics or ["(add topics in other modes)"]))}
                </ol>
                <h3 style="margin: 1rem 0 .5rem 0;">MCQs (summary)</h3>
                <ol>
                    {"".join(f"<li>{q['stem']}</li>" for q in (st.session_state.generated_items or []))}
                </ol>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <script>
              function doPrint(){ window.print(); }
            </script>
            """, unsafe_allow_html=True
        )
        st.button("Print", on_click=None, type="primary", use_container_width=False)

        # clickable JS for button
        st.markdown(
            """
            <script>
              const btns = parent.document.querySelectorAll('button');
              const printBtn = Array.from(btns).find(b => b.innerText.trim() === 'Print');
              if (printBtn) printBtn.addEventListener('click', () => window.print());
            </script>
            """, unsafe_allow_html=True
        )

