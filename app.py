import streamlit as st
from pathlib import Path

# Set page config
st.set_page_config(page_title="ADI Learning Tracker", layout="centered")

# ADI branding colors
adi_blue = "#00AEEF"
adi_green = "#8DC63F"
adi_orange = "#F7941D"

# Header with branding
st.markdown(f"""
    <div style="text-align:center; padding:20px 0;">
        <h1 style="color:{adi_blue}; margin-bottom:0;">ADI Learning Tracker</h1>
        <h4 style="color:gray; margin-top:5px;">Transforming Lessons into Measurable Learning</h4>
    </div>
""", unsafe_allow_html=True)

# Tabs for navigation
tabs = st.tabs(["Upload", "Setup", "Generate", "Edit", "Export"])

# Upload tab content
with tabs[0]:
    st.markdown(f"""
        <div style="border:2px dashed {adi_blue}; padding:30px; border-radius:10px; background-color:#f9f9f9;">
            <h3 style="color:{adi_blue};">Upload Lesson Materials</h3>
            <p>Drag and drop your files below or click 'Browse files'.</p>
            <p><strong>Accepted formats:</strong> .pptx, .pdf, .epub, .docx</p>
            <p><strong>Max file size:</strong> 200MB</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a file", type=["pptx", "pdf", "epub", "docx"])

    if uploaded_file:
        file_details = {
            "filename": uploaded_file.name,
            "filetype": uploaded_file.type,
            "filesize": f"{uploaded_file.size / (1024*1024):.2f} MB"
        }
        st.success(f"Uploaded: {file_details['filename']} ({file_details['filesize']})")

# Placeholder content for other tabs
with tabs[1]:
    st.info("Setup tab content goes here.")

with tabs[2]:
    st.info("Generate tab content goes here.")

with tabs[3]:
    st.info("Edit tab content goes here.")

with tabs[4]:
    st.info("Export tab content goes here.")
