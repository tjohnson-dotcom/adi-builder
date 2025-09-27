import streamlit as st
from PIL import Image
import base64

# Set page config
st.set_page_config(page_title="ADI Learning Tracker", layout="centered")

# Load ADI logo if available
logo_path = "jpeg (1).jpg"
try:
    logo = Image.open(logo_path)
    st.image(logo, width=120)
except:
    st.write("")

# Title and tagline
st.markdown("<h1 style='text-align: center; color: #00AEEF;'>ADI Learning Tracker</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #555;'>Transforming Lessons into Measurable Learning</h4>", unsafe_allow_html=True)
st.markdown("---")

# Tabs
tabs = st.tabs(["Upload", "Setup", "Generate", "Edit", "Export"])

with tabs[0]:
    st.markdown("### Upload your learning materials")
    st.markdown("Accepted formats: `.pptx`, `.pdf`, `.epub`, `.docx`  &nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp; Max size: 200MB")

    # Drag and drop file uploader
    uploaded_file = st.file_uploader("Drag and drop a PowerPoint or e-book file here, or click to browse", type=["pptx", "pdf", "epub", "docx"])

    if uploaded_file:
        st.success(f"Uploaded file: {uploaded_file.name}")

    # Begin Tracking Learning button
    st.markdown("<div style='text-align: center; margin-top: 30px;'>", unsafe_allow_html=True)
    st.button("Begin Tracking Learning")
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[1]:
    st.markdown("### Setup")
    st.info("Setup options will appear here.")

with tabs[2]:
    st.markdown("### Generate")
    st.info("Question generation interface will appear here.")

with tabs[3]:
    st.markdown("### Edit")
    st.info("Edit generated questions and activities here.")

with tabs[4]:
    st.markdown("### Export")
    st.info("Export options will appear here.")
