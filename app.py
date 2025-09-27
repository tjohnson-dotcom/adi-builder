import streamlit as st
import fitz  # PyMuPDF
from pptx import Presentation
import docx
import os

# ADI Branding Colors
ADI_BLUE = "#00AEEF"
ADI_GREEN = "#8DC63F"
ADI_ORANGE = "#F7941D"
ADI_GRAY = "#F2F2F2"

# Set page config
st.set_page_config(page_title="ADI Learning Tracker", layout="wide")

# Logo and Tagline
st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background-color: {ADI_GRAY}; padding: 10px 20px;">
        <div>
            <h1 style="color: {ADI_BLUE}; margin-bottom: 0;">ADI Learning Tracker</h1>
            <p style="font-size: 18px; margin-top: 0;">Transforming Lessons into Measurable Learning</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Navigation Bar
nav_options = ["Upload", "Setup", "Generate", "Edit", "Export"]
selected_nav = st.radio("Navigation", nav_options, horizontal=True)

# Upload Step
if selected_nav == "Upload":
    st.subheader("Upload Lesson Materials")
    uploaded_file = st.file_uploader("Drag and drop or browse files (.pptx, .pdf, .epub, .docx)", type=["pptx", "pdf", "epub", "docx"])
    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")
        with open(os.path.join("uploaded_" + uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())

# Setup Step
elif selected_nav == "Setup":
    st.subheader("Setup Lesson Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        lesson = st.selectbox("Select Lesson", [f"Lesson {i}" for i in range(1, 5)])
    with col2:
        week = st.selectbox("Select Week", [f"Week {i}" for i in range(1, 15)])
    with col3:
        duration = st.selectbox("Activity Duration", [f"{i} mins" for i in range(10, 61, 10)])

    st.markdown("### Bloom’s Verbs")
    col_low, col_med, col_high = st.columns(3)
    with col_low:
        low_verbs = st.multiselect("Low (Blue)", ["Remember", "Understand"], key="low", default=[], help="Basic cognitive skills")
    with col_med:
        med_verbs = st.multiselect("Medium (Green)", ["Apply", "Analyze"], key="med", default=[], help="Intermediate cognitive skills")
    with col_high:
        high_verbs = st.multiselect("High (Orange)", ["Evaluate", "Create"], key="high", default=[], help="Advanced cognitive skills")

# Generate Step
elif selected_nav == "Generate":
    st.subheader("Generate Questions and Activities")
    preview_text = ""
    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1]
        if file_type == "pdf":
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            preview_text = "\n".join([page.get_text() for page in doc])
        elif file_type == "pptx":
            prs = Presentation(uploaded_file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        preview_text += shape.text + "\n"
        elif file_type == "docx":
            doc = docx.Document(uploaded_file)
            preview_text = "\n".join([para.text for para in doc.paragraphs])
        else:
            preview_text = "Preview not available for this file type."

        st.text_area("Preview of Uploaded Content", preview_text, height=300)

    st.text_area("Generated Questions / Activities", "", height=300)

# Edit Step
elif selected_nav == "Edit":
    st.subheader("Edit Generated Content")
    edited_text = st.text_area("Edit your questions and activities here", "", height=300)
    st.button("Save Changes")

# Export Step
elif selected_nav == "Export":
    st.subheader("Export Your Work")
    st.text_input("Enter filename for export", value="ADI_Questions")
    st.button("Export to PDF")
    st.button("Copy Shareable Link")
