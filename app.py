import streamlit as st
import time
from io import BytesIO

# --- ADI Colors ---
ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
STONE = "#f5f3ef"

# --- Page config ---
st.set_page_config(page_title="ADI Builder - Lesson Activities & Questions", layout="wide")

# --- Global Styles ---
st.markdown(f"""
<style>
  .stApp {{ background: {STONE}; }}
  .adi-header h1 {{ color: {ADI_GREEN}; margin-bottom: .25rem; }}
  .adi-sub {{ color: {ADI_GOLD}; margin-top: 0; }}
  .adi-card {{
      background: white;
      border: 1px solid #e7e5e4;
      border-radius: 1rem;
      padding: 1rem 1.5rem;
      margin-bottom: 1.5rem;
  }}
  .adi-help {{ color: #5f6368; font-size: 0.9rem; }}

  /* Lesson & Week box */
  .adi-box {{
      border: 2px solid {ADI_GREEN};
      border-radius: 12px;
      padding: 1rem 1.5rem;
      margin-bottom: 1.5rem;
      background: white;
  }}
  .adi-box h4 {{
      color: {ADI_GREEN};
      font-weight: 700;
      margin-top: 0;
      margin-bottom: .75rem;
  }}
  .adi-radio label span {{
      font-weight: 600;
      color: {ADI_GREEN};
  }}

  /* Bloom highlight pills (left column) */
  .bloom-pill {{
      display: inline-block;
      padding: 0.35rem 0.75rem;
      margin: 0.25rem;
      border-radius: 999px;
      border: 1px solid {ADI_GREEN};
      font-weight: 600;
      color: {ADI_GREEN};
      background: white;
  }}
  .bloom-pill.active {{
      background: {ADI_GREEN};
      color: white;
  }}

  /* Section headers (right tabs) */
  .adi-section-header {{
      font-size: 1.6rem;
      font-weight: 700;
      color: {ADI_GREEN};
      margin-top: .5rem;
      margin-bottom: 1rem;
  }}

  /* Multiselect labels */
  .adi-subhead {{
      font-weight: 700;
      color: {ADI_GREEN};
      margin: .25rem 0 .5rem 0;
  }}

  /* Tidy the multiselects so they look like chips rows */
  div[data-baseweb="select"] > div {{}}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown(
    '<div class="adi-header"><h1>ADI Builder - Lesson Activities & Questions</h1>'
    '<p class="adi-sub">Professional, branded, editable and export-ready.</p></div>',
    unsafe_allow_html=True
)

# Bloom taxonomy (verbs) master lists
BLOOM_VERBS = {
    "Low": [
        "define","identify","list","recall","describe","label","locate","match",
        "name","outline","recognize","state"
    ],
    "Medium": [
        "apply","demonstrate","solve","use","classify","illustrate","interpret",
        "summarize","compare","explain"
    ],
    "High": [
        "evaluate","synthesize","design","justify","create","critique","argue",
        "defend","compose","plan"
    ],
}

def default_verbs_for_week(week: int):
    """Return sensible defaults matching ADI policy mapping."""
    if 1 <= week <= 4:
        return ("Low", BLOOM_VERBS["Low"][:5])      # a handful of low verbs
    if 5 <= week <= 9:
        return ("Medium", BLOOM_VERBS["Medium"][:5])
    return ("High", BLOOM_VERBS["High"][:5])

# --- Layout ---
left, right = st.columns([1, 1], gap="large")

# ======================================================
# LEFT SIDE
# ======================================================
with left:
    # Upload Box
    st.markdown('<div class="adi-card"><h3>Upload eBook / Lesson Plan / PPT</h3>', unsafe_allow_html=True)

    up = st.file_uploader(
        "Drop your file here (PDF, DOCX, PPTX)",
        type=["pdf", "docx", "pptx"],
        accept_multiple_files=False,
        help="Native Streamlit uploader with drag-and-drop (max 200MB).",
        key="adi_uploader"
    )

    if up is not None:
        file_bytes = up.read()

        with st.status("Processing file…", expanded=True) as status:
            prog = st.progress(0)
            total = max(len(file_bytes), 1)
            chunk = max(total // 20, 1)

            buf = BytesIO()
            for i in range(0, total, chunk):
                end = min(i + chunk, total)
                buf.write(file_bytes[i:end])
                pct = int(end / total * 100)
                prog.progress(min(pct, 100))
                time.sleep(0.02)

            status.update(label="Upload complete ✅", state="complete")

        st.success(f"Loaded: {up.name} ({len(file_bytes)/1024:.1f} KB)")
    else:
        st.markdown('<p class="adi-help">Tip: If drag-and-drop doesn’t work, click the box to browse.</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Lesson & Week box
    st.markdown('<div class="adi-box"><h4>Lesson & Week</h4>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        lesson = st.radio(
            "Pick a Lesson",
            [1, 2, 3, 4, 5],
            horizontal=True,
            label_visibility="collapsed",
            key="lesson_radio"
        )

    with col2:
        week = st.radio(
            "Pick a Week",
            list(range(1, 15)),
            horizontal=True,
            label_visibility="collapsed",
            key="week_radio"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Bloom Policy Highlight (auto)
    st.markdown('<div class="adi-card"><h3>Bloom Policy (Auto)</h3>', unsafe_allow_html=True)

    if 1 <= week <= 4:
        bloom_level = "Low"
    elif 5 <= week <= 9:
        bloom_level = "Medium"
    else:
        bloom_level = "High"

    col_low, col_med, col_high = st.columns(3)
    with col_low:
        st.markdown(f'<span class="bloom-pill {"active" if bloom_level=="Low" else ""}">Low Tier</span>', unsafe_allow_html=True)
    with col_med:
        st.markdown(f'<span class="bloom-pill {"active" if bloom_level=="Medium" else ""}">Medium Tier</span>', unsafe_allow_html=True)
    with col_high:
        st.markdown(f'<span class="bloom-pill {"active" if bloom_level=="High" else ""}">High Tier</span>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================
# RIGHT SIDE
# ======================================================
with right:
    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

    # --- Tab 1: Knowledge MCQs ---
    with tabs[0]:
        st.markdown('<div class="adi-section-header">Knowledge MCQs (ADI Policy)</div>', unsafe_allow_html=True)

        # Context inputs
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source_text = st.text_area("Source text (optional, editable)", placeholder="Paste or edit source text here…")

        # Bloom taxonomy (full) with verb selectors
        st.markdown('<div class="adi-subhead">Bloom Taxonomy — Pick verbs to emphasise</div>', unsafe_allow_html=True)

        # Set defaults for multiselects based on current week
        default_level, default_list = default_verbs_for_week(week)

        c1, c2, c3 = st.columns(3)
        with c1:
            low_defaults = default_list if default_level == "Low" else []
            low_selected = st.multiselect(
                "Low tier verbs",
                options=BLOOM_VERBS["Low"],
                default=low_defaults,
                help="Weeks 1–4 focus here.",
                key="bloom_low"
            )
        with c2:
            med_defaults = default_list if default_level == "Medium" else []
            med_selected = st.multiselect(
                "Medium tier verbs",
                options=BLOOM_VERBS["Medium"],
                default=med_defaults,
                help="Weeks 5–9 focus here.",
                key="bloom_medium"
            )
        with c3:
            high_defaults = default_list if default_level == "High" else []
            high_selected = st.multiselect(
                "High tier verbs",
                options=BLOOM_VERBS["High"],
                default=high_defaults,
                help="Weeks 10–14 focus here.",
                key="bloom_high"
            )

        # How many MCQ blocks?
        mcq_blocks = st.slider("How many MCQ blocks? (≥3 questions each)", 1, 10, 1)

        if st.button("Generate MCQ Blocks", type="primary"):
            chosen_verbs = {
                "Low": low_selected,
                "Medium": med_selected,
                "High": high_selected,
            }
            st.success(
                f"✅ Generating {mcq_blocks} MCQ block(s) "
                f"for {topic if topic else 'selected content'} using Bloom emphasis: {default_level}"
            )
            st.write("Selected verbs:", chosen_verbs)

    # --- Tab 2: Skills Activities ---
    with tabs[1]:
        st.markdown('<div class="adi-section-header">Skills Activities</div>', unsafe_allow_html=True)

        st.text_area("Activity Instructions", placeholder="Write or paste skills-based activity here…")
        if st.button("Generate Activity", type="primary"):
            st.success("✅ Skills activity generated")

