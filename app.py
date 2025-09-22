import streamlit as st

# Optional logo
st.image("logo.png", width=120)

st.title("ADI Builder - Question Generator")
st.write("Upload your PPTX or DOCX files, pick Bloom’s levels, and generate practice questions.")

# User input
topic = st.text_input("Enter a topic or lesson content:")

# Bloom’s levels
levels = {
    "Remember": ["define", "list", "recall"],
    "Understand": ["explain", "summarize", "classify"],
    "Apply": ["demonstrate", "use", "implement"],
    "Analyze": ["differentiate", "compare", "contrast"],
    "Evaluate": ["justify", "critique", "assess"],
    "Create": ["design", "construct", "produce"],
}

level = st.selectbox("Choose Bloom’s level:", list(levels.keys()))
verb = st.selectbox("Choose a Bloom’s verb:", levels[level])

# Generate
if st.button("Generate Example Question"):
    if topic.strip():
        st.success(f"**Example Question:** {verb.capitalize()} {topic} ({level} level).")
    else:
        st.warning("Please enter a topic first.")
