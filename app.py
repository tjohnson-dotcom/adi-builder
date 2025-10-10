
import streamlit as st

# Custom CSS for advanced styling
st.markdown("""
    <style>
        .gradient-header {
            background: linear-gradient(to right, #004d40, #00796b);
            color: white;
            padding: 1rem;
            font-size: 1.5rem;
            font-weight: bold;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .card {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("ADI Builder")
page = st.sidebar.radio("Navigate", ["Home", "Activities", "Revision"])

# Home Page
if page == "Home":
    st.markdown('<div class="gradient-header">Home: Lesson Setup</div>', unsafe_allow_html=True)

    with st.expander("📁 Upload Lesson File"):
        uploaded_file = st.file_uploader("Upload a lesson file (PDF, DOCX, PPTX)", type=["pdf", "docx", "pptx"])
        if uploaded_file:
            st.success(f"Uploaded: {uploaded_file.name}")

    with st.expander("📘 Course Details"):
        col1, col2 = st.columns(2)
        with col1:
            course_name = st.text_input("Course Name")
            instructor = st.selectbox("Instructor", ["Ben", "Daniel", "Sarah"])
        with col2:
            lesson_number = st.number_input("Lesson Number", min_value=1, max_value=20, step=1)
            date = st.date_input("Date")
        answer_key = st.checkbox("Include Answer Key")

    with st.expander("🧠 Bloom's Taxonomy Verbs"):
        st.markdown('<div class="section-title">Low-Level Cognitive Skills</div>', unsafe_allow_html=True)
        low_verbs = st.multiselect("Select Low-Level Verbs", ["define", "identify", "list", "describe"])

        st.markdown('<div class="section-title">Medium-Level Cognitive Skills</div>', unsafe_allow_html=True)
        medium_verbs = st.multiselect("Select Medium-Level Verbs", ["apply", "demonstrate", "interpret", "compare"])

        st.markdown('<div class="section-title">High-Level Cognitive Skills</div>', unsafe_allow_html=True)
        high_verbs = st.multiselect("Select High-Level Verbs", ["analyze", "evaluate", "design", "formulate"])

    st.button("Generate Questions")
    st.button("Export to Word")

# Activities Page
elif page == "Activities":
    st.markdown('<div class="gradient-header">Activities</div>', unsafe_allow_html=True)

    with st.expander("🎯 Activity Setup"):
        num_activities = st.slider("Number of Activities", 1, 5, 3)
        time_per_activity = st.slider("Time per Activity (minutes)", 5, 60, 20)

    with st.expander("📄 Upload Activity Worksheet"):
        activity_file = st.file_uploader("Upload activity worksheet (DOCX)", type=["docx"])
        if activity_file:
            st.success(f"Uploaded: {activity_file.name}")

    st.button("Generate Activities")
    st.button("Export Activities to Word")

# Revision Page
elif page == "Revision":
    st.markdown('<div class="gradient-header">Revision</div>', unsafe_allow_html=True)

    with st.expander("📘 Upload Revision Guide"):
        revision_file = st.file_uploader("Upload revision guide (PDF)", type=["pdf"])
        if revision_file:
            st.success(f"Uploaded: {revision_file.name}")

    with st.expander("📝 Reflection Prompts"):
        prompt1 = st.text_area("Reflection Prompt 1")
        prompt2 = st.text_area("Reflection Prompt 2")
        prompt3 = st.text_area("Reflection Prompt 3")

    st.button("Generate Revision Sheet")
    st.button("Export Revision to Word")
