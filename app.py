import streamlit as st
import pandas as pd

# ---------- Bloom Policy ----------
BLOOM_POLICY = {
    "Low": ["define", "identify", "list", "describe", "recall", "label"],
    "Medium": ["apply", "demonstrate", "solve", "illustrate", "analyze", "interpret", "compare"],
    "High": ["evaluate", "synthesize", "design", "justify", "formulate", "critique"]
}

def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    elif 5 <= week <= 9:
        return "Medium"
    else:
        return "High"

# ---------- Page Setup ----------
st.set_page_config(page_title="Learning Tracker Question Generator", layout="wide")

# ---------- Inject CSS ----------
st.markdown("""
<style>
/* Base */
body { background:#f6f8f7; }
section.main > div { padding-top:1rem; }

/* Tabs */
.stTabs [role="tablist"] { justify-content:space-evenly; border-bottom:1px solid #e0e4e2; }
.stTabs [role="tab"] { font-weight:700; padding:10px 18px; border-radius:10px 10px 0 0; }
.stTabs [aria-selected="true"] { color:#245a34 !important; border-bottom:3px solid #C8A85A; }

/* Inputs */
:root{
  --field-bg:#ffffff;
  --field-bd:#e2e9e5;
  --field-bd-hover:#cfe1d7;
  --field-shadow:0 6px 16px rgba(36,90,52,0.06), inset 0 1px 0 rgba(255,255,255,0.5);
  --field-shadow-focus:0 10px 24px rgba(36,90,52,0.18);
}
.stTextInput > div > div,
.stTextArea  > div > div,
.stSelectbox > div > div{
  background: var(--field-bg) !important;
  border:1.8px solid var(--field-bd) !important;
  border-radius:14px !important;
  box-shadow: var(--field-shadow) !important;
  transition: box-shadow .18s ease, border-color .18s ease, transform .05s ease;
}
.stTextInput > div > div:hover,
.stTextArea  > div > div:hover,
.stSelectbox > div > div:hover{
  border-color: var(--field-bd-hover) !important;
  transform: translateY(-1px);
}
.stTextInput > div > div:focus-within,
.stTextArea  > div > div:focus-within,
.stSelectbox > div > div:focus-within{
  border-color:#245a34 !important;
  box-shadow: var(--field-shadow-focus) !important;
  outline:3px solid rgba(36,90,52,0.28);
}

/* File uploader */
[data-testid="stFileUploaderDropzone"]{
  border:2.5px dashed #b9cfc4 !important;
  border-radius:18px !important;
  background:#ffffff !important;
  box-shadow:0 10px 26px rgba(36,90,52,0.08);
  transition:all .2s ease;
}
[data-testid="stFileUploaderDropzone"]:hover{
  border-color:#8fb8a3 !important;
  background:#fcfefd !important;
  outline:3px solid rgba(36,90,52,0.25);
}

/* Bloom chips */
.bloom-chip{
  display:inline-block; padding:6px 14px; margin:4px; border-radius:999px;
  font-weight:700; font-size:.9rem; color:#fff;
}
.low   { background:#245a34; }
.med   { background:#C8A85A; color:#111; }
.high  { background:#333; }
.active{ outline:3px solid #245a34; }

/* Export reminders */
.note-green{
  padding:12px 14px; border-radius:12px; border:1px solid #b5d1c0;
  background:linear-gradient(180deg,#f9fefb,#f3fbf6);
  color:#133c23; font-weight:600;
}
.note-amber{
  padding:12px 14px; border-radius:12px; border:1px solid #e4d3a7;
  background:linear-gradient(180deg,#fffdf7,#fffaf0);
  color:#4a3d14; font-weight:600;
}

/* Toolbar summary */
.toolbar{
  display:flex; gap:.6rem; flex-wrap:wrap;
  background:#fff; border:1px solid #e0e4e2; border-radius:16px;
  padding:10px 12px; box-shadow:0 10px 28px rgba(36,90,52,0.10);
  margin:.6rem 0 1rem;
}
.pill{
  display:inline-flex; align-items:center; gap:.5rem;
  padding:8px 12px; border-radius:999px; font-weight:800;
  border:1px solid rgba(0,0,0,0.08); box-shadow:0 6px 16px rgba(0,0,0,0.08);
}
.pill.lesson{ background:#f3fbf6; border-color:#cfe1d7; }
.pill.week{ background:#f8faf9; border-color:#dfe7e3; }
.pill.focus.low   { background:#245a34; color:#fff; border-color:#1a4628; }
.pill.focus.med   { background:#C8A85A; color:#111; border-color:#9c874b; }
.pill.focus.high  { background:#333;    color:#fff; border-color:#222; }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
logo = "Logo.png"  # place your ADI logo file in same folder
col1, col2 = st.columns([1,5])
with col1:
    st.image(logo, width=80)
with col2:
    st.markdown("## Learning Tracker Question Generator\nTransform lessons into measurable learning")

# ---------- Tabs ----------
tabs = st.tabs(["① Upload", "② Setup", "③ Generate", "④ Export"])

# ---------- Upload ----------
with tabs[0]:
    st.header("Upload your lesson")
    st.file_uploader("Drag a .pptx, .pdf, or .docx file here, or click to browse.", type=["pptx","pdf","docx"])

# ---------- Setup ----------
with tabs[1]:
    st.header("Setup")
    c1, c2, c3 = st.columns(3)
    with c1:
        lesson = st.selectbox("Lesson", [1,2,3,4])
    with c2:
        week = st.selectbox("Week", list(range(1,15)))
    with c3:
        focus = bloom_focus_for_week(week)
        st.text_input("Bloom focus (auto)", value=f"Week {week}: {focus}", disabled=True)

    # summary bar
    focus_cls = "low" if focus=="Low" else ("med" if focus=="Medium" else "high")
    st.markdown(f"""
    <div class="toolbar">
      <div class="pill lesson">📘 Lesson {lesson}</div>
      <div class="pill week">📅 Week {week}</div>
      <div class="pill focus {focus_cls}">🎯 Focus {focus}</div>
    </div>
    """, unsafe_allow_html=True)

    st.text_input("Learning Objective / Topic (optional)")
    st.text_area("Source (editable)", placeholder="Paste or edit full sentences here…")

    st.subheader("MCQ Setup")
    mcq = st.radio("Number of MCQs", [5,10,20,30], horizontal=True)

    st.subheader("Activity Setup")
    c4, c5 = st.columns([1,2])
    with c4:
        activities = st.radio("Activities", [1,2,3], horizontal=True)
    with c5:
        duration = st.slider("Duration per Activity (mins)", 10, 60, 30, 5)

    st.subheader("Bloom’s Verbs (ADI Policy)")
    for tier, verbs in BLOOM_POLICY.items():
        css_class = "low" if tier=="Low" else "med" if tier=="Medium" else "high"
        highlight = (tier==focus)
        st.write(f"**{tier} (Weeks {'1–4' if tier=='Low' else '5–9' if tier=='Medium' else '10–14'})**")
        st.markdown(" ".join([f"<span class='bloom-chip {css_class}{' active' if highlight else ''}'>{v}</span>" for v in verbs]), unsafe_allow_html=True)

# ---------- Generate ----------
with tabs[2]:
    st.header("Generate")
    st.write("This is where MCQs and activities will be generated. (placeholder for now)")
    if st.button("Create MCQs"):
        st.success(f"Generated {mcq} MCQs.")
    if st.button("Create Activities"):
        st.success(f"Generated {activities} activities of {duration} mins each.")

# ---------- Export ----------
with tabs[3]:
    st.header("Export")
    st.subheader("MCQs")
    st.markdown("<div class='note-green'>Generate MCQs in ③ Generate to enable downloads.</div>", unsafe_allow_html=True)
    st.subheader("Activities")
    st.markdown("<div class='note-amber'>Generate Activities in ③ Generate to enable downloads.</div>", unsafe_allow_html=True)
