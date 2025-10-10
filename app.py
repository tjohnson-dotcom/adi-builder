import streamlit as st
from ui import render_ui
from generators import generate_questions, generate_activities
from export import export_to_word, export_to_gdocs

def main():
    st.set_page_config(page_title="ADI Builder", layout="wide")
    render_ui()

    topic = st.text_input("Enter your topic:")
    level = st.selectbox("Select Bloom's Taxonomy Level:", ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"])

    if st.button("Generate"):
        questions = generate_questions(topic, level)
        activities = generate_activities(topic, level)
        st.subheader("Generated Questions")
        st.write(questions)
        st.subheader("Suggested Activities")
        st.write(activities)

        if st.button("Export to Word"):
            export_to_word(topic, questions, activities)
        if st.button("Export to Google Docs"):
            export_to_gdocs(topic, questions, activities)

if __name__ == "__main__":
    main()
