import streamlit as st

# Optional: Show logo (only works if you upload logo.png to the repo)
try:
    st.image("logo.png", width=140)
except Exception:
    st.write("")

st.title("ADI Builder - Question Generator")

st.write("Welcome to ADI Builder! Upload your PPTX or DOCX files, pick Bloom’s levels, and generate practice questions.")

# Example input
topic = st.text_input("Enter a topic or lesson content:")

if st.button("Generate Example Question"):
    if topic:
        st.success(f"Example: What are the key ideas of **{topic}**?")
    else:
        st.warning("Please enter a topic first.")
