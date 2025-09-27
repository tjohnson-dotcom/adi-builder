import streamlit as st
from pptx import Presentation
import fitz  # PyMuPDF
from io import BytesIO

# ADI logo colors for Bloom's taxonomy levels
adi_colors = {
    "Low": "#00AEEF",     # Blue
    "Medium": "#8DC63F",  # Green
    "High": "#F7941D"     # Orange
}

# Bloom's verbs categorized by level
blooms_verbs = {
    "Low": ["Define", "List", "Recall", "Identify"],
    "Medium": ["Explain", "Summarize", "Interpret", "Apply"],
    "High": ["Evaluate", "Create", "Design", "Analyze"]
}

# Streamlit UI setup
st.set_page_config(page_title="ADI Learning Tracker Question Generator", layout="wide")

st.title("ADI Learning Tracker Question Generator")

# Sidebar for selections
st.sidebar.header("Configuration")
lesson = st.sidebar.selectbox("Select Lesson", ["Lesson 1", "Lesson 2", "Lesson 3", "Lesson 4"])
activity = st.sidebar.text_input("Activity Name")
week = st.sidebar.selectbox("Select Week", [f"Week {i}" for i in range(1, 15)])
time = st.sidebar.slider("Time (minutes)", 10, 60, 30)

# Bloom's verbs selection with color-coded tags
st.sidebar.markdown("### Bloom's Verbs")
selected_verbs = []
for level, verbs in blooms_verbs.items():
    st.sidebar.markdown(f"**{level} Level**")
    for verb in verbs:
        if st.sidebar.checkbox(verb, key=verb):
            selected_verbs.append((verb, adi_colors[level]))

# File upload section
st.subheader("Upload Learning Materials")
uploaded_files = st.file_uploader("Drag and drop PowerPoint or e-book files", type=["pdf", "pptx"], accept_multiple_files=True)

# Display uploaded content
for uploaded_file in uploaded_files or []:
    st.markdown(f"**Uploaded File:** {uploaded_file.name}")
    if uploaded_file.name.endswith(".pdf"):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        st.text_area(f"Extracted Text from {uploaded_file.name}", value=text, height=200)
    elif uploaded_file.name.endswith(".pptx"):
        prs = Presentation(uploaded_file)
        ppt_text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    ppt_text.append(shape.text)
        st.text_area(f"Extracted Text from {uploaded_file.name}", value="\n".join(ppt_text), height=200)

# Editable section for generated questions and activities
st.subheader("Generated Questions and Activities")
default_text = "Edit your questions and activities here..."
st.text_area("Editable Section", value=default_text, height=300)

# Display selected Bloom's verbs with color highlights
st.subheader("Selected Bloom's Verbs")
for verb, color in selected_verbs:
    st.markdown(f"<span style='color:{color}; font-weight:bold'>{verb}</span>", unsafe_allow_html=True)
