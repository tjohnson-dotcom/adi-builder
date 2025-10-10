# app.py — clean & stable (no JS, no warnings)

import streamlit as st
from datetime import date

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")
# --- ADI brand system (colors, header, components) ---

from pathlib import Path
from PIL import Image

ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
STONE     = "#F5F4F2"
DARK_TEXT = "#1f2937"

# Global style (keeps Streamlit controls green; adds nicer cards/tabs/chips)
st.markdown(f"""
<style>
  .block-container {{ padding-top: 0.75rem; }}
  /* Header bar */
  .adi-topbar {{
    background:{ADI_GREEN}; color:white; padding:.75rem 1rem; border-radius: 0 0 12px 12px;
    display:flex; gap:14px; align-items:center; margin-bottom: 1rem;
  }}
  .adi-topbar img {{ height: 36px; }}
  .adi-topbar h1 {{ font-size: 1.25rem; margin:0; line-height:1.2; }}

  /* Cards / panels */
  .adi-card {{ background:{STONE}; border:1px solid #e7e5e4; border-radius:14px; padding:14px; }}

  /* Pills / chips */
  .adi-chip button {{
    width:100%; background:white; color:{DARK_TEXT}; border:1px solid #e7e5e4; border-radius:14px; padding:14px 10px;
  }}
  .adi-chip button:hover {{ border-color:{ADI_GREEN}; box-shadow:0 0 0 2px rgba(36,90,52,.08) inset; }}
  .adi-chip-selected {{ background:{ADI_GREEN}; color:white; border:1px solid {ADI_GREEN}; border-radius:14px; padding:14px 10px; text-align:center; }}
  .adi-chip-selected small {{ display:block; color:{ADI_GOLD}; opacity:.95; font-style:italic; }}

  /* Segmented control (tabs) */
  [data-baseweb="segmented-control"] div[role="tablist"] > div {{
    border-radius:999px !important;
    border:1px solid #e7e5e4 !important;
    background:white !important;
  }}
  [data-baseweb="segmented-control"] div[role="tab"] {{
    color:{DARK_TEXT} !important;
  }}
  [data-baseweb="segmented-control"] [aria-selected="true"] {{
    background:{ADI_GREEN} !important; color:white !important;
  }}

  /* Buttons pick up theme.primaryColor; keep slight rounding */
  .stButton > button {{ border-radius:10px; }}
</style>
""", unsafe_allow_html=True)

def adi_header(title="ADI Builder — Lesson Activities & Questions", logo_path="assets/adi-logo.png"):
    logo_html = ""
    p = Path(logo_path)
    if p.exists():
        try:
            img = Image.open(p)
            st.image(img, width=44)
            # When an image is rendered by st.image, we can’t place it inline with HTML easily;
            # Instead, render a single HTML header bar:
        except Exception:
            pass
    # Build a clean HTML bar (renders whether or not the image exists)
    img_tag = f"<img src='file://{p.resolve()}' alt='ADI'/>" if p.exists() else ""
    st.markdown(
        f"""
        <div class="adi-topbar">
            {img_tag}
            <h1>{title}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------ Theme constants ------------
ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
STONE = "#F5F4F2"

# ------------ One-time session init ------------
def init_state():
    ss = st.session_state
    ss.setdefault("selected_course", "GE4-EPM")
    ss.setdefault("topics", [])
    ss.setdefault("generated_items", [])
    ss.setdefault("mode", "Knowledge")
    ss.setdefault("class_cohort", "D1-C01")
    ss.setdefault("instructor", "Daniel")          # set once here
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("topic_outcome", "")
init_state()

# ------------ Styles (simple, no JS) ------------
st.markdown(f"""
<style>
  .block-container {{ padding-top: 1.5rem; }}
  .adi-chip button {{
    border:1px solid #e7e5e4; border-radius:14px; padding:12px; width:100%;
    background:white;
  }}
  .adi-chip button:hover {{ border-color:{ADI_GREEN}; box-shadow:0 0 0 2px rgba(36,90,52,.08) inset; }}
  .adi-card {{ background:{STONE}; border:1px solid #e7e5e4; border-radius:14px; padding:14px; }}
  @media print {{
    header, footer, [data-testid="stSidebar"], .stToolbar, .stDownloadButton, .stButton {{ display:none !important; }}
    .block-container {{ padding:0 !important; }}
  }}
</style>
""", unsafe_allow_html=True)

# ------------ Data ------------
COURSES = [
    ("GE4-EPM", "Defense Technology Practices"),
    ("GE4-IPM", "Integrated Project & Materials Mgmt"),
    ("GE4-MRO", "Military Vehicle & Aircraft MRO"),
    ("CT4-COM", "Computation for Chemical Technologists"),
    ("CT4-EMG", "Explosives Manufacturing"),
    ("CT4-TFL", "Thermofluids"),
]

def bloom_level(week:int)->str:
    return "Low" if week<=4 else ("Medium" if week<=9 else "High")

# ------------ Header ------------
st.markdown(f"<h1 style='color:{ADI_GREEN}'>ADI Builder — Lesson Activities & Questions</h1>", unsafe_allow_html=True)

# ------------ Layout ------------
colL, colR = st.columns([1.15, 1])

# ===== RIGHT: quick-pick chips (pure Streamlit) =====
with colR:
    st.markdown("### Course quick-pick")
    rows = [COURSES[:3], COURSES[3:]]
    for row in rows:
        cols = st.columns(3)
        for (code, label), c in zip(row, cols):
            with c:
                if st.container().button(f"{label}\n\n*{code}*", key=f"chip-{code}", help="Select this course", use_container_width=True):
                    st.session_state.selected_course = code
                    st.rerun()

# ===== LEFT: authoring =====
with colL:
    st.markdown("### Course details")

    # widgets read/write session_state keys directly → no yellow warnings
    course_codes = [c[0] for c in COURSES]
    st.selectbox("Course name", options=course_codes,
                 index=course_codes.index(st.session_state.selected_course),
                 key="selected_course")

    st.selectbox("Class / Cohort", options=["D1-C01", "D1-C02", "D2-C01"], key="class_cohort")
    st.text_input("Instructor name", key="instructor")
    d1, d2 = st.columns(2)
    with d1:
        st.number_input("Lesson", min_value=1, max_value=20, step=1, key="lesson")
    with d2:
        st.number_input("Week", min_value=1, max_value=14, step=1, key="week")

    st.markdown("---")
    st.markdown("### Authoring")

    st.text_input("Topic / Outcome (optional)", key="topic_outcome",
                  placeholder="e.g., Integrated Project and …")
    st.caption(f"ADI policy: Weeks 1–4 Low • 5–9 Medium • 10–14 High  |  Recommended Bloom: **{bloom_level(st.session_state.week)}**")

    mode = st.segmented_control("Mode", options=["Knowledge", "Skills", "Revision", "Print Summary"], key="mode")

    if mode != "Print Summary":
        topics_text = st.text_area("Enter topics (one per line)",
                                   placeholder="Topic A\nTopic B\nTopic C", height=120, key="topics_text")
        include_key = st.checkbox("Include answer key", value=True, key="include_key")
        how_many = st.selectbox("How many MCQs?", options=[5, 10, 15, 20], index=1, key="mcq_count")

        if st.button("Generate MCQs", type="primary"):
            st.session_state.topics = [t.strip() for t in topics_text.splitlines() if t.strip()]
            items = []
            for i in range(st.session_state.mcq_count):
                items.append({
                    "stem": f"Sample question {i+1} on {st.session_state.topics[0] if st.session_state.topics else 'topic'}?",
                    "options": ["A) …", "B) …", "C) …", "D) …"],
                    "answer": "A"
                })
            st.session_state.generated_items = items
            st.success(f"Generated {len(items)} items.")

        if st.session_state.generated_items:
            st.markdown("#### Preview & quick edit")
            for idx, q in enumerate(st.session_state.generated_items):
                with st.expander(f"Q{idx+1}: {q['stem'][:80]}"):
                    q["stem"] = st.text_input("Stem", value=q["stem"], key=f"stem-{idx}")
                    c1, c2 = st.columns(2)
                    q["options"][0] = c1.text_input("Option A", value=q["options"][0], key=f"oa-{idx}")
                    q["options"][1] = c2.text_input("Option B", value=q["options"][1], key=f"ob-{idx}")
                    c3, c4 = st.columns(2)
                    q["options"][2] = c3.text_input("Option C", value=q["options"][2], key=f"oc-{idx}")
                    q["options"][3] = c4.text_input("Option D", value=q["options"][3], key=f"od-{idx}")
                    q["answer"] = st.selectbox("Correct answer", ["A","B","C","D"],
                                               index=["A","B","C","D"].index(q["answer"]),
                                               key=f"ans-{idx}")

            txt = "\n\n".join(
                [f"Q{n+1}. {q['stem']}\n" + "\n".join(q["options"]) + (f"\nAnswer: {q['answer']}" if include_key else "")
                 for n, q in enumerate(st.session_state.generated_items)]
            )
            st.download_button("Export (TXT)", data=txt,
                               file_name=f"{st.session_state.selected_course}_L{st.session_state.lesson}_W{st.session_state.week}_mcqs.txt")

    else:
        st.markdown("#### Print Summary")
        ss = st.session_state
        st.markdown(
            f"""
            <div class="adi-card" style="max-width:900px;">
                <h2 style="margin:0 0 .25rem 0; color:{ADI_GREEN}">{ss.selected_course} — Lesson {ss.lesson} (Week {ss.week})</h2>
                <div style="margin-bottom:.5rem;"><strong>Instructor:</strong> {ss.instructor}</div>
                <div style="margin-bottom:.75rem;"><strong>Bloom focus:</strong> {bloom_level(ss.week)}</div>
                <h3 style="margin: 1rem 0 .5rem 0;">Topics</h3>
                <ol style="margin-top:0;">
                    {"".join(f"<li>{t}</li>" for t in (ss.topics or ["(add topics in other modes)"]))}
                </ol>
                <h3 style="margin: 1rem 0 .5rem 0;">MCQs (summary)</h3>
                <ol>
                    {"".join(f"<li>{q['stem']}</li>" for q in (ss.generated_items or []))}
                </ol>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.button("Print (use browser)", type="primary")
        st.markdown("<small>Use your browser’s “Print to PDF” to save.</small>", unsafe_allow_html=True)


