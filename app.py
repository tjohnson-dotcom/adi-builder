
import streamlit as st
from pptx import Presentation

# Set page config
st.set_page_config(page_title="ADI Lesson Designer", layout="centered")

# ADI Branding
st.markdown("<h1 style='color:#2E86C1;'>ADI Lesson Designer</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#5D6D7E;'>Transforming Lessons into Measurable Learning</h4>", unsafe_allow_html=True)
st.markdown("---")

# Dropdowns
lesson = st.selectbox("Select Lesson", ["Lesson 1", "Lesson 2", "Lesson 3", "Lesson 4"])
activity = st.selectbox("Select Activity", ["Discussion", "Experiment", "Presentation", "Assessment"])
week = st.selectbox("Select Week", [f"Week {i}" for i in range(1, 15)])
bloom = st.selectbox("Select Bloom’s Verb", ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"])
time = st.selectbox("Select Time (minutes)", [str(i) for i in range(10, 61, 10)])

st.markdown("---")

# Drag-and-drop file uploader
uploaded_file = st.file_uploader("Upload a PowerPoint file (.pptx)", type=["pptx"])

# Function to extract text from slides
def extract_text_from_ppt(file):
    prs = Presentation(file)
    text_runs = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text = shape.text.strip()
                if text:
                    text_runs.append(text)
    return text_runs

# Function to generate questions
def generate_questions(text_list):
    return [f"What is the meaning of: '{text}'?" for text in text_list][:10]

# Process uploaded file
if uploaded_file:
    text_list = extract_text_from_ppt(uploaded_file)
    questions = generate_questions(text_list)

    st.markdown("### Generated Questions")
    for i, q in enumerate(questions, 1):
        st.write(f"{i}. {q}")

