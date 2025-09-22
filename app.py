# app.py — ADI Builder (Streamlit, Branded UI)
# Sleek + professional look with ADI brand colors from logo

from __future__ import annotations
import streamlit as st
from io import BytesIO
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")

# Extracted palette from ADI logo
ADI_GREEN = "#006C35"
ADI_BEIGE = "#C8B697"
ADI_SAND = "#D9CFC2"
ADI_BROWN = "#6B4E3D"
ADI_GRAY = "#F5F5F5"

CUSTOM_CSS = f"""
<style>
/* Background gradient */
.stApp {{
  background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%);
}}

/* Typography */
html, body, [class*="css"] {{
  font-family: 'Segoe UI', Roboto, Inter, sans-serif;
}}

/* Headings */
h1, h2, h3 {{ font-weight: 700; color: {ADI_GREEN}; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  border-bottom: 4px solid {ADI_GREEN};
  font-weight: 600;
  color: {ADI_GREEN};
}}

/* Card container */
.card {{
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 6px 14px rgba(0,0,0,0.08);
  padding: 20px;
  margin: 14px 0;
  border-left: 6px solid {ADI_GREEN};
}}
.card h4 {{ margin: 0 0 10px 0; color: {ADI_GREEN}; }}
.card .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 8px; }}
.card .label {{ font-weight: 600; color: {ADI_BROWN}; }}

/* Toolbar */
.toolbar {{
  display: flex; justify-content: flex-end; gap: 12px;
  margin: 16px 0;
}}

/* Buttons */
.stButton>button {{
  background: {ADI_GREEN};
  color: white;
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-weight: 600;
  transition: background 0.2s;
}}
.stButton>button:hover {{
  background: {ADI_BROWN};
}}

/* Sidebar */
.css-1d391kg {{ background-color: {ADI_GRAY} !important; }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Sidebar branding
st.sidebar.image("https://i.imgur.com/F4P6o5D.png", use_column_width=True)  # Replace with ADI logo hosted link
st.sidebar.header("Upload Source (Optional)")
upload = st.sidebar.file_uploader("PDF / DOCX / PPTX (≤200MB)", type=["pdf", "docx", "pptx"])

col1, col2 = st.sidebar.columns(2)
num_activities = col1.number_input("Activities", 1, 10, 3)
duration = col2.number_input("Duration (mins)", 5, 180, 45)

level = st.sidebar.selectbox("Bloom's Level", ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"], index=2)
verbs = st.sidebar.multiselect("Preferred verbs", ["demonstrate", "solve", "use"], default=["demonstrate", "solve"])

st.sidebar.caption("Export buttons appear after generating content.")

# Main Title
st.markdown(f"<h1>ADI Builder — Lesson Activities & Questions</h1>", unsafe_allow_html=True)
st.caption("Professional, branded, and export‑ready.")

# Tabs
kn_tab, skills_tab = st.tabs(["Knowledge MCQs", "Skills Activities"])

with kn_tab:
    st.subheader("Generate MCQs (placeholder)")
    n_mcq = st.number_input("How many MCQs?", 1, 20, 5)
    topic = st.text_input("Topic (optional)", "Module description, knowledge & skills outcomes")
    if st.button("Generate MCQs"):
        for i in range(1, n_mcq+1):
            st.markdown(f"<div class='card'><h4>Q{i}</h4><div class='meta'>Topic: {topic}</div><div>Placeholder question stem...</div></div>", unsafe_allow_html=True)

with skills_tab:
    st.subheader("Generate Skills Activities")
    if st.button("Generate Activities", type="primary"):
        for i in range(1, num_activities+1):
            st.markdown(f"""
            <div class='card'>
            <h4>Activity {i} — {duration} mins</h4>
            <div class='meta'>Bloom's Level: {level}</div>
            <div><span class='label'>Task:</span> Work in pairs using verb <b>{verbs[(i-1)%len(verbs)]}</b>.</div>
            <div><span class='label'>Output:</span> Short presentation or diagram.</div>
            <div><span class='label'>Evidence:</span> Upload photo to LMS.</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Toolbar with export buttons
        st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
        st.download_button("⬇️ TXT", "Example text export", file_name="adi.txt")
        st.download_button("⬇️ Moodle GIFT", "Example GIFT export", file_name="adi.gift")
        st.download_button("⬇️ Word (.doc)", "Example doc export", file_name="adi.doc")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr><div style='text-align:center; color:#666;'>© Academy of Defense Industries — ADI Builder</div>", unsafe_allow_html=True)
