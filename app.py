import streamlit as st
import base64
import re

# ADI Branding Colors
COLOR_LOW = "#bbbbbd"       # Light gray for Low Bloom's verbs
COLOR_MEDIUM = "#8592a0"    # Steel blue for Medium Bloom's verbs
COLOR_HIGH = "#1b49a0"      # Deep navy for High Bloom's verbs

# Bloom's taxonomy verb lists
BLOOMS_LOW = ["define", "list", "recall", "identify", "name", "recognize"]
BLOOMS_MEDIUM = ["apply", "demonstrate", "interpret", "analyze", "compare"]
BLOOMS_HIGH = ["evaluate", "create", "design", "formulate", "construct"]

# Highlight Bloom's verbs in text
def highlight_blooms(text):
    def replace(match):
        word = match.group(0)
        word_lower = word.lower()
        if word_lower in BLOOMS_LOW:
            return f'<span style="background-color:{COLOR_LOW}; padding:2px 4px; border-radius:4px;">{word}</span>'
        elif word_lower in BLOOMS_MEDIUM:
            return f'<span style="background-color:{COLOR_MEDIUM}; color:white; padding:2px 4px; border-radius:4px;">{word}</span>'
        elif word_lower in BLOOMS_HIGH:
            return f'<span style="background-color:{COLOR_HIGH}; color:white; padding:2px 4px; border-radius:4px;">{word}</span>'
        else:
            return word

    pattern = re.compile(r'\\b(' + '|'.join(BLOOMS_LOW + BLOOMS_MEDIUM + BLOOMS_HIGH) + r')\\b', re.IGNORECASE)
    return pattern.sub(replace, text)

# App layout
st.set_page_config(page_title="ADI Builder", layout="wide")

st.markdown(f"<h1 style='color:{COLOR_HIGH};'>ADI Builder</h1>", unsafe_allow_html=True)
st.markdown("Build learning objectives and questions with Bloom's taxonomy highlighting.")

# Sidebar
st.sidebar.header("Upload & Settings")
uploaded_file = st.sidebar.file_uploader("Upload PowerPoint", type=["pptx"])
learning_objectives = st.sidebar.text_area("Learning Objectives", height=150)

# Main content
st.subheader("Generated Questions")

sample_questions = [
    "Define the key components of the ADI framework.",
    "Apply the ADI model to a real-world scenario.",
    "Evaluate the effectiveness of ADI in your institution."
]

for q in sample_questions:
    highlighted = highlight_blooms(q)
    st.markdown(f"<p style='font-size:18px;'>{highlighted}</p>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("© ADI Builder | Streamlit App")

