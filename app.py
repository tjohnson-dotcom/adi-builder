import streamlit as st
from pptx import Presentation
import os

# Set page configuration
st.set_page_config(page_title="ADI Lesson Designer", layout="wide")

# ADI Branding
st.markdown("""
    <div style='display: flex; justify-content: space-between; align-items: center; background-color: #f0f4f8; padding: 10px 20px; border-radius: 8px;'>
        <div>
            <h1 style='color: #2a4d69;'>ADI Lesson Designer</h1>
            <p style='color: #4b6584;'>Transforming Lessons into Measurable Learning</p>
        </div>
        <div style='font-size: 24px; color: #2a4d69;'>🌟</div>
    </div>
""", unsafe_allow_html=True)

# Sidebar dropdowns
st.sidebar.header("Lesson Metadata")
lesson = st.sidebar.selectbox("Lesson", ["Lesson 1", "Lesson 2", "Lesson 3", "Lesson 4"])
activity = st.sidebar.selectbox("Activity", ["Discussion", "Experiment", "Presentation", "Assessment"])
week = st.sidebar.selectbox("Week", [f"Week {i}" for i in range(1, 15)])
bloom = st.sidebar.selectbox("Bloom’s Verb", ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"])
time = st.sidebar.selectbox("Time (minutes)", [str(i) for i in range(10, 61, 10)])

# Drag-and-drop uploader
st.subheader("Upload PowerPoint File")
ppt_file = st.file_uploader("Drag and drop your .pptx file here", type=["pptx"])

# Function to extract text from slides
def extract_text_from_ppt(file_path):
    prs = Presentation(file_path)
    text_runs = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                text_runs.append(shape.text.strip())
    return text_runs

# Function to generate questions
def generate_questions(text_list):
    return [f"What is the meaning of: '{text}'?" for text in text_list][:10]

# Process uploaded file
if ppt_file:
    temp_path = os.path.join("/tmp", ppt_file.name)
    with open(temp_path, "wb") as f:
        f.write(ppt_file.read())

    text_list = extract_text_from_ppt(temp_path)
    questions = generate_questions(text_list)

    st.subheader("Generated Questions")
    for i, q in enumerate(questions, 1):
        st.markdown(f"<div style='background-color:#eaf2f8; padding:10px; border-radius:5px; margin-bottom:5px;'>{i}. {q}</div>", unsafe_allow_html=True)
