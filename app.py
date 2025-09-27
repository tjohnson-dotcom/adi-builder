import streamlit as st
import fitz  # PyMuPDF
import docx
import pptx
import io
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

# ADI Branding
st.set_page_config(page_title="ADI Learning Tracker", layout="wide")
st.title("ADI Learning Tracker Question Generator")
st.markdown("##### *Transforming Lessons into Measurable Learning*")

# Sidebar Inputs
st.sidebar.header("Setup")
lesson = st.sidebar.selectbox("Lesson", ["Lesson 1", "Lesson 2", "Lesson 3", "Lesson 4"])
activity = st.sidebar.selectbox("Activity", ["Activity A", "Activity B", "Activity C"])
week = st.sidebar.selectbox("Week", [f"Week {i}" for i in range(1, 15)])
bloom_level = st.sidebar.selectbox("Bloom’s Verb Level", ["Low", "Medium", "High"])
time_allocated = st.sidebar.slider("Time (minutes)", 10, 60, 30)

# Upload Section
st.subheader("Upload Lesson Material")
uploaded_file = st.file_uploader("Upload PPTX, PDF, EPUB, or DOCX", type=["pptx", "pdf", "epub", "docx"])

# Editable Learning Objectives
st.subheader("Learning Objectives")
learning_objectives = st.text_area("Enter or edit learning objectives here:", height=150)

# Bloom’s Verbs Dictionary
blooms_verbs = {
    "Low": ["define", "list", "recall", "identify"],
    "Medium": ["explain", "summarize", "compare", "interpret"],
    "High": ["evaluate", "design", "create", "formulate"]
}

# Function to extract text from uploaded file
def extract_text(file, file_type):
    text = ""
    if file_type == "pdf":
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
    elif file_type == "docx":
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file_type == "pptx":
        prs = pptx.Presentation(file)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
    elif file_type == "epub":
        text = "EPUB parsing not supported in this version."
    return text

# Question Generation
def generate_questions(text, bloom_level):
    questions = []
    verbs = blooms_verbs[bloom_level]
    sentences = text.split(".")
    for i, sentence in enumerate(sentences):
        if len(sentence.strip()) > 20:
            verb = verbs[i % len(verbs)]
            question = f"**{verb.capitalize()}**: Based on the content, {verb} {sentence.strip()}?"
            questions.append(question)
    return questions

# Display and Generate Questions
if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    content = extract_text(uploaded_file, file_type)
    st.subheader("Generated Questions")
    questions = generate_questions(content, bloom_level)
    for q in questions:
        st.markdown(f"- {q}")

    # Export Options
    st.subheader("Export Options")

    # Export to Word
    def export_to_word(questions):
        doc = Document()
        doc.add_heading("ADI Learning Tracker Questions", 0)
        doc.add_paragraph(f"{lesson} | {activity} | {week} | {bloom_level} | {time_allocated} mins")
        doc.add_paragraph("Learning Objectives:")
        doc.add_paragraph(learning_objectives)
        doc.add_paragraph("Generated Questions:")
        for q in questions:
            doc.add_paragraph(q, style='List Bullet')
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    word_buffer = export_to_word(questions)
    st.download_button("Download as Word", data=word_buffer.getvalue(), file_name="ADI_Questions.docx")

    # Export to PDF using fitz
    def export_to_pdf(questions):
        pdf_doc = fitz.open()
        page = pdf_doc.new_page()
        text = f"{lesson} | {activity} | {week} | {bloom_level} | {time_allocated} mins\n\n"
        text += "Learning Objectives:\n" + learning_objectives + "\n\nGenerated Questions:\n"
        for q in questions:
            text += q + "\n"
        rect = fitz.Rect(50, 50, 550, 800)
        page.insert_textbox(rect, text, fontsize=12)
        buffer = io.BytesIO()
        pdf_doc.save(buffer)
        buffer.seek(0)
        return buffer

    pdf_buffer = export_to_pdf(questions)
    st.download_button("Download as PDF", data=pdf_buffer.getvalue(), file_name="ADI_Questions.pdf")

    # Copy to Clipboard (simulated)
    st.text_area("Copy Questions", value="\n".join(questions), height=200)

else:
    st.info("Please upload a lesson file to begin generating questions.")
