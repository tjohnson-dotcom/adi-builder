import streamlit as st
import random

st.title("ADI Builder - Question Generator")
st.write("Upload your PPTX or DOCX files, pick Bloom’s levels, and generate practice questions.")

# --- Bloom's Levels + Verbs ---
BLOOM_VERBS = {
    "Remember": ["define", "list", "recall", "state"],
    "Understand": ["explain", "summarize", "describe", "classify"],
    "Apply": ["demonstrate", "use", "illustrate", "solve"],
    "Analyze": ["differentiate", "compare", "contrast", "categorize"],
    "Evaluate": ["judge", "critique", "assess", "recommend"],
    "Create": ["design", "construct", "formulate", "develop"]
}

# --- Inputs ---
topic = st.text_input("Enter a topic or lesson content:")

level = st.selectbox("Choose Bloom’s level:", list(BLOOM_VERBS.keys()))
verb = st.selectbox("Choose a Bloom’s verb:", BLOOM_VERBS[level])

# --- Generate Button ---
if st.button("Generate Example Question"):
    if topic:
        question = f"Using the verb **{verb}**, create a question about: {topic}"
        st.success(question)
    else:
        st.warning("Please enter a topic or lesson content first.")
