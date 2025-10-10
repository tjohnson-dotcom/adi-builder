import streamlit as st
from ui import render_sidebar, render_bloom_panels
from generators import generate_questions_from_topic, generate_questions_from_file
from export import export_to_word, export_to_pdf, export_to_google_docs

# Initialize session state
if "course_details" not in st.session_state:
    st.session_state.course_details = {
        "Course Name": "",
        "Class/Cohort": "",
        "Instructor Name": "",
        "Date": "",
        "Lesson Number": "",
        "Week": ""
    }

if "questions" not in st.session_state:
    st.session_state.questions = []

# Sidebar
render_sidebar()

# Main UI
st.title("ADI Builder — Lesson Activities & Questions")

# File upload
uploaded_file = st.file_uploader("Upload source file (.PPTX, .DOCX, .PDF)", type=["pptx", "docx", "pdf"])
deep_scan = st.checkbox("Deep scan source: slower, better coverage")

# Course details
st.subheader("Course Details")
for key in st.session_state.course_details:
    st.session_state.course_details[key] = st.text_input(key, st.session_state.course_details[key])

# Bloom panels
st.subheader("Bloom’s Taxonomy Levels by Week")
selected_week = st.selectbox("Select Week", ["1–4 (Low)", "5–9 (Medium)", "10–14 (High)"])
verbs = render_bloom_panels(selected_week)

# Topic input
st.subheader("Generate Questions")
topic = st.text_input("Enter topic or concept")
if st.button("Generate from Topic"):
    st.session_state.questions = generate_questions_from_topic(topic, verbs)

if uploaded_file and st.button("Generate from Uploaded File"):
    st.session_state.questions = generate_questions_from_file(uploaded_file, verbs, deep_scan)

# Display questions
if st.session_state.questions:
    st.subheader("Generated Questions")
    for i, q in enumerate(st.session_state.questions, 1):
        st.markdown(f"**Q{i}:** {q}")

# Export options
st.subheader("Export")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Export to Word"):
        export_to_word(st.session_state.questions)
with col2:
    if st.button("Export to PDF"):
        export_to_pdf(st.session_state.questions)
with col3:
    if st.button("Export to Google Docs"):
        export_to_google_docs(st.session_state.questions)
