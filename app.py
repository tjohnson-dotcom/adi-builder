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
  /* Bloom highlight pills */
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
  /* Section headers */
  .adi-section-header {{
      font-size: 1.5rem;
      font-weight: 700;
      color: {ADI_GREEN};
      margin-top: 1rem;
      margin-bottom: 1rem;
  }}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<div class="adi-header"><h1>ADI Builder - Lesson Activities & Questions</h1>'
            '<p class="adi-sub">Professional, branded, editable and export-ready.</p></div>',
            unsafe_allow_html=True)

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

    # Bloom Policy Highlight
    st.markdown('<div class="adi-card"><h3>Bloom Policy (Auto)</h3>', unsafe_allow_html=True)

    if 1 <= week <= 4:
        bloom = "Low"
    elif 5 <= week <= 9:
        bloom = "Medium"
    else:
        bloom = "High"

    col_low, col_med, col_high = st.columns(3)
    with col_low:
        st.markdown(f'<span class="bloom-pill {"active" if bloom=="Low" else ""}">Low Tier</span>', unsafe_allow_html=True)
    with col_med:
        st.markdown(f'<span class="bloom-pill {"active" if bloom=="Medium" else ""}">Medium Tier</span>', unsafe_allow_html=True)
    with col_high:
        st.markdown(f'<span class="bloom-pill {"active" if bloom=="High" else ""}">High Tier</span>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================
# RIGHT SIDE
# ======================================================
with right:
    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

    # --- Tab 1 ---
    with tabs[0]:
        st.markdown('<div class="adi-section-header">Knowledge MCQs (ADI Policy)</div>', unsafe_allow_html=True)

        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source_text = st.text_area("Source text (optional, editable)", placeholder="Paste or edit source text here…")

        mcq_blocks = st.slider("How many MCQ blocks? (≥3 questions each)", 1, 10, 1)
        if st.button("Generate MCQ Blocks", type="primary"):
            st.success(f"✅ Generated {mcq_blocks} MCQ block(s) for {topic if topic else 'selected content'}")

    # --- Tab 2 ---
    with tabs[1]:
        st.markdown('<div class="adi-section-header">Skills Activities</div>', unsafe_allow_html=True)

        st.text_area("Activity Instructions", placeholder="Write or paste skills-based activity here…")
        if st.button("Generate Activity", type="primary"):
            st.success("✅ Skills activity generated")
