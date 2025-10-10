import streamlit as st
from ui import render_sidebar, render_course_details, render_bloom_panels
from generators import generate_questions
from export import export_to_word

st.set_page_config(page_title="ADI Builder", layout="wide")

# Sidebar with ADI branding
render_sidebar()

# Main header
st.markdown("<h1 style='color:#004225;'>ADI Builder — Lesson Activities & Questions</h1>", unsafe_allow_html=True)

# File upload with dashed border
uploaded_file = st.file_uploader("Upload lesson file", type=["pdf", "docx", "pptx"], label_visibility="collapsed")
if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")

# Course details section
course_info = render_course_details()

# Bloom's Taxonomy panels
selected_verbs = render_bloom_panels()

# Generate questions
if st.button("Generate Questions", use_container_width=True):
    if selected_verbs:
        questions = generate_questions(selected_verbs)
        for q in questions:
            st.markdown(f"- {q}")
    else:
        st.warning("Please select at least one verb.")

# Export section
st.markdown("### Export")
col1, col2 = st.columns(2)
with col1:
    if st.button("Export to Word"):
        export_to_word(course_info, selected_verbs)
with col2:
    st.button("Export to Google Docs (Coming Soon)")
