import streamlit as st
import base64

# Set page configuration
st.set_page_config(page_title="ADI Learning Tracker", layout="wide")

# Custom CSS for branding and layout
st.markdown("""
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
        }
        .adi-header {
            background-color: #f0f2f6;
            padding: 20px 40px;
            border-bottom: 2px solid #00AEEF;
        }
        .adi-header h1 {
            color: #00AEEF;
            margin-bottom: 5px;
        }
        .adi-header p {
            font-size: 18px;
            color: #333;
        }
        .nav-tabs {
            display: flex;
            gap: 20px;
            padding: 10px 40px;
            background-color: #ffffff;
            border-bottom: 1px solid #ccc;
        }
        .nav-tabs a {
            text-decoration: none;
            font-weight: bold;
            color: #333;
        }
        .nav-tabs a:hover {
            color: #00AEEF;
        }
        .upload-box {
            border: 2px dashed #00AEEF;
            padding: 40px;
            text-align: center;
            background-color: #f9f9f9;
            margin: 40px;
            border-radius: 10px;
        }
        .upload-box p {
            font-size: 16px;
            color: #555;
        }
    </style>
""", unsafe_allow_html=True)

# Header section
st.markdown("""
    <div class="adi-header">
        <h1>ADI Learning Tracker</h1>
        <p>Transforming Lessons into Measurable Learning</p>
    </div>
""", unsafe_allow_html=True)

# Navigation tabs
st.markdown("""
    <div class="nav-tabs">
        <a href="#">Upload</a>
        <a href="#">Setup</a>
        <a href="#">Generate</a>
        <a href="#">Edit</a>
        <a href="#">Export</a>
    </div>
""", unsafe_allow_html=True)

# Upload section
st.markdown("""
    <div class="upload-box">
        <h3>Upload Lesson Materials</h3>
        <p>Drag and drop files (.pptx, .pdf, .epub, .docx) or browse to upload</p>
        <p><em>Max file size: 200MB</em></p>
    </div>
""", unsafe_allow_html=True)

# File uploader widget
uploaded_file = st.file_uploader("Choose a file", type=["pptx", "pdf", "epub", "docx"])

if uploaded_file:
    st.success(f"Uploaded file: {uploaded_file.name}")
