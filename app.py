
import streamlit as st

# ADI Branding
st.set_page_config(page_title="ADI Builder", layout="wide")

st.title("ADI Builder App")

# Course Dropdown
courses = {
    "CS101": "Introduction to Computer Science",
    "MATH201": "Advanced Mathematics",
    "ENG301": "English Literature",
    "BIO150": "Fundamentals of Biology"
}
course_tooltips = {
    "CS101": "Learn the basics of computer science.",
    "MATH201": "Explore advanced mathematical concepts.",
    "ENG301": "Study classic and modern literature.",
    "BIO150": "Understand biological systems and processes."
}
selected_course = st.selectbox("Select Course", options=list(courses.keys()), format_func=lambda x: f"{x} - {courses[x]}")
st.caption(course_tooltips[selected_course])

# Instructor Dropdown
instructors = ["Dr. Alice Smith", "Prof. John Doe", "Dr. Emily Zhang", "Mr. Robert Brown"]
selected_instructor = st.selectbox("Select Instructor", instructors)

# Class/Cohort Dropdown
class_groups = ["Cohort A", "Cohort B", "Cohort C", "Cohort D"]
selected_class = st.selectbox("Select Class/Cohort", class_groups)

# File Upload
uploaded_file = st.file_uploader("Upload Lesson File", type=["pdf", "docx", "pptx"])

# Bloom's Taxonomy Levels
st.subheader("Bloom’s Taxonomy Skill Levels")
skills = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
selected_skills = st.multiselect("Select Skills", skills)

# Weekly Timeline
st.subheader("Weekly Timeline")
timeline = {
    "Week 1": "Introduction",
    "Week 2": "Theory",
    "Week 3": "Practice",
    "Week 4": "Assessment"
}
for week, activity in timeline.items():
    st.markdown(f"**{week}**: {activity}")

# Generate & Export Buttons
col1, col2 = st.columns(2)
with col1:
    st.button("Generate", help="Generate lesson plan", type="primary")
with col2:
    st.button("Export", help="Export to Word & PowerPoint", type="primary")

# Preview Panel
st.subheader("Preview Panel")
st.text_area("MCQs and Activities Preview", height=200)

# Footer
st.markdown("---")
st.markdown("ADI Builder © 2024")
