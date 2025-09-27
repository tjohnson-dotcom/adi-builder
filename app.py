
import streamlit as st
import fitz  # PyMuPDF
from pptx import Presentation
from docx import Document

# ADI brand colors for Bloom's verbs
ADI_COLORS = {
    "Low": "#00AEEF",     # Blue
    "Medium": "#8DC63F",  # Green
    "High": "#F7941D"     # Orange
}

# Bloom's verbs categorized
BLOOMS_VERBS = {
    "Low": ["Define", "List", "Recall", "Identify", "Name"],
    "Medium": ["Explain", "Summarize", "Compare", "Interpret", "Classify"],
    "High": ["Evaluate", "Create", "Design", "Analyze", "Justify"]
}

# Function to extract text from uploaded files
def extract_text(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    elif file.name.endswith(".pptx"):
        prs = Presentation(file)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text
    elif file.name.endswith(".docx"):
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return "Unsupported file format."

# Function to highlight Bloom's verbs
def highlight_verbs(text):
    for level, verbs in BLOOMS_VERBS.items():
        for verb in verbs:
            text = text.replace(
                verb,
                f"<span style='color:{ADI_COLORS[level]}; font-weight:bold'>{verb}</span>"
            )
    return text

# Streamlit UI
st.set_page_config(page_title="ADI Learning Tracker Question Generator", layout="centered")

st.markdown("<h1 style='color:#002855;'>ADI Learning Tracker Question Generator</h1>", unsafe_allow_html=True)

# Sidebar for file upload
st.sidebar.header("Upload Lesson Materials")
uploaded_file = st.sidebar.file_uploader("Upload pptx, pdf, or docx", type=["pdf", "pptx", "docx"])

# Dropdowns
lesson = st.selectbox("Select Lesson", ["Lesson 1", "Lesson 2", "Lesson 3", "Lesson 4"])
activity = st.selectbox("Select Activity", ["Activity A", "Activity B", "Activity C"])
week = st.selectbox("Select Week", [f"Week {i}" for i in range(1, 15)])
time = st.selectbox("Select Time (mins)", list(range(10, 65, 10)))
bloom_level = st.selectbox("Select Bloom's Level", list(BLOOMS_VERBS.keys()))
verb = st.selectbox("Select Bloom's Verb", BLOOMS_VERBS[bloom_level])

# Learning Objective input
learning_objective = st.text_area("Learning Objective", placeholder="e.g. Identify key themes and arguments in the text")

# Display extracted text
if uploaded_file:
    st.subheader("Extracted Lesson Text")
    extracted = extract_text(uploaded_file)
    st.text_area("Lesson Content", value=extracted, height=200)

# Generate questions
if st.button("Generate Questions"):
    st.subheader("Generated Questions")
    questions = [
        f"What are the main arguments presented in the text?",
        f"Explain the significance of the key themes in the text.",
        f"How would you compare the author's perspective to other views?",
        f"Analyze the relationship between themes and arguments, evaluating strengths and weaknesses."
    ]
    for i, q in enumerate(questions, 1):
        highlighted = highlight_verbs(q)
        st.markdown(f"**{i}.** {highlighted}", unsafe_allow_html=True)

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<small style='color:gray;'>ADI Learning Tracker © 2025</small>", unsafe_allow_html=True)
