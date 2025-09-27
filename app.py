streamlit run app.py

import streamlit as st
import base64
import io
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation
import fitz  # PyMuPDF

# ADI Branding Colors (no red)
ADI_COLORS = {
    "Low": "#0072C6",     # Blue
    "Medium": "#F6A623",  # Orange
    "High": "#7ED321"     # Green
}

# Page config
st.set_page_config(page_title="ADI Builder", layout="wide")

# Branding
st.markdown("<h1 style='text-align: center; color: #0072C6;'>Academy of Defense Industries</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Transforming Lessons into Measurable Learning</h3>", unsafe_allow_html=True)

# Welcome screen
if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    if st.button("Begin Tracking Learning", use_container_width=True):
        st.session_state.started = True
    st.stop()

# Tabs
tabs = st.tabs(["Upload", "Setup", "Generate", "Edit", "Export"])

# Upload Tab
with tabs[0]:
    st.header("Upload Learning Material")
    uploaded_file = st.file_uploader("Upload a file (pptx, pdf, epub, docx)", type=["pptx", "pdf", "epub", "docx"])
    file_text = ""

    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower()
        if file_type == "pdf":
            reader = PdfReader(uploaded_file)
            file_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif file_type == "docx":
            doc = Document(uploaded_file)
            file_text = "\n".join([para.text for para in doc.paragraphs])
        elif file_type == "pptx":
            prs = Presentation(uploaded_file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        file_text += shape.text + "\n"
        elif file_type == "epub":
            file_text = "EPUB parsing not supported in this version."
        st.success("File uploaded and processed.")

# Setup Tab
with tabs[1]:
    st.header("Setup Lesson Parameters")
    lesson = st.selectbox("Select Lesson", ["Lesson 1", "Lesson 2", "Lesson 3", "Lesson 4"])
    activity = st.selectbox("Select Activity", [f"Week {i}" for i in range(1, 15)])
    bloom_level = st.selectbox("Select Bloom’s Verb Level", ["Low", "Medium", "High"])
    time_allocated = st.slider("Time Allocation (minutes)", 10, 60, 30)
    learning_objective = st.text_input("Learning Objective", "Identify key-themes and arguments in the text.")

# Generate Tab
with tabs[2]:
    st.header("Generate Questions")
    if file_text:
        if st.button("Create Questions"):
            questions = []
            if bloom_level == "Low":
                questions = [
                    "What are the main arguments presented in the text?",
                    "List the key themes discussed.",
                    "Define the central concept of the lesson."
                ]
            elif bloom_level == "Medium":
                questions = [
                    "Explain the significance of the key themes in the text.",
                    "Summarize the author's perspective.",
                    "Interpret the meaning of the main argument."
                ]
            elif bloom_level == "High":
                questions = [
                    "Analyze the relationship between themes and arguments.",
                    "Evaluate strengths and weaknesses of the author’s arguments.",
                    "Propose an alternative viewpoint based on the text."
                ]
            st.session_state.generated_questions = questions
            st.success("Questions generated successfully.")
    else:
        st.warning("Please upload a file in the Upload tab.")

    if "generated_questions" in st.session_state:
        st.markdown(f"### Learning Objective: *{learning_objective}*")
        for i, q in enumerate(st.session_state.generated_questions, 1):
            color = ADI_COLORS[bloom_level]
            st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:5px; margin-bottom:5px;'>Q{i}: {q}</div>", unsafe_allow_html=True)

# Edit Tab
with tabs[3]:
    st.header("Edit Questions")
    if "generated_questions" in st.session_state:
        edited_questions = []
        for i, q in enumerate(st.session_state.generated_questions, 1):
            edited = st.text_area(f"Edit Question {i}", value=q)
            edited_questions.append(edited)
        st.session_state.edited_questions = edited_questions
    else:
        st.info("No questions to edit. Generate them first.")

# Export Tab
with tabs[4]:
    st.header("Export Options")
    if "edited_questions" in st.session_state:
        export_text = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(st.session_state.edited_questions)])

        # Export as Word
        docx_buffer = io.BytesIO()
        doc = Document()
        doc.add_heading("ADI Builder - Generated Questions", 0)
        doc.add_paragraph(f"Lesson: {lesson}, Activity: {activity}, Time: {time_allocated} mins")
        doc.add_paragraph(f"Learning Objective: {learning_objective}")
        for i, q in enumerate(st.session_state.edited_questions, 1):
            doc.add_paragraph(f"Q{i}: {q}")
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        st.download_button("Download as Word", docx_buffer, file_name="ADI_Questions.docx")

        # Export as PDF
        pdf_buffer = io.BytesIO()
        pdf_doc = fitz.open()
        page = pdf_doc.new_page()
        text = f"ADI Builder - Generated Questions\nLesson: {lesson}, Activity: {activity}, Time: {time_allocated} mins\nLearning Objective: {learning_objective}\n\n"
        for i, q in enumerate(st.session_state.edited_questions, 1):
            text += f"Q{i}: {q}\n"
        page.insert_text((72, 72), text, fontsize=12)
        pdf_doc.save(pdf_buffer)
        pdf_doc.close()
        pdf_buffer.seek(0)
        st.download_button("Download as PDF", pdf_buffer, file_name="ADI_Questions.pdf")

        # Copy Link (simulated)
        st.code(export_text, language="markdown")
        st.success("Copy the questions above or download as needed.")
    else:
        st.info("No questions to export.")
