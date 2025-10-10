import streamlit as st

# Inject custom CSS with hover effects and tooltips
st.markdown("""
<style>
.adi-header { background: #004d40; color: #fff; padding: 15px; font-size: 24px; font-weight: bold; }
.upload-box, .bloom-panels, .export, .course-details { background: #fff; margin-bottom: 20px; padding: 20px; border-radius: 8px; }
.drag-drop { border: 2px dashed #004d40; padding: 20px; text-align: center; border-radius: 8px; }
.panel.low { background: #e8f5e9; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
.panel.medium { background: #fffde7; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
.panel.high { background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
.tag { display: inline-block; background: #004d40; color: #fff; padding: 5px 10px; border-radius: 4px; margin: 5px; cursor: pointer; transition: background 0.3s; }
.tag:hover { background: #00695c; }
.export-btn, .generate-btn { padding: 10px 20px; background: #004d40; color: #fff; border: none; border-radius: 4px; cursor: pointer; transition: background 0.3s; }
.export-btn:hover, .generate-btn:hover { background: #00695c; }
.tooltip { font-size: 12px; color: #555; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='adi-header'>ADI Builder — Lesson Activities & Questions</div>", unsafe_allow_html=True)

# Upload section with tooltip
st.markdown("<div class='upload-box'><h3>Upload (optional)</h3></div>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Drag and drop or browse files", type=["txt", "docx", "pptx", "pdf"])
st.markdown("<div class='tooltip'>Upload lesson files (TXT, DOCX, PPTX, PDF) for question generation.</div>", unsafe_allow_html=True)
if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")

# Course details
st.markdown("<div class='course-details'><h3>Course Details</h3></div>", unsafe_allow_html=True)
course_name = st.text_input("Course Name")
instructor = st.selectbox("Instructor", ["Ben", "Daniel", "Sarah"])
date = st.date_input("Date")
lesson_number = st.number_input("Lesson", min_value=1, max_value=20, step=1)
answer_key = st.checkbox("Answer Key")

# Bloom panels with tooltip
st.markdown("<div class='bloom-panels'><h3>Bloom's Taxonomy Levels</h3></div>", unsafe_allow_html=True)
st.markdown("<div class='tooltip'>Select verbs to guide question complexity.</div>", unsafe_allow_html=True)

# Initialize session state for verbs
if "low_verbs" not in st.session_state:
    st.session_state["low_verbs"] = ["define", "identify", "list", "describe"]
if "medium_verbs" not in st.session_state:
    st.session_state["medium_verbs"] = ["apply", "demonstrate", "interpret", "compare"]
if "high_verbs" not in st.session_state:
    st.session_state["high_verbs"] = ["analyze", "evaluate", "design", "formulate"]

def render_tags(level):
    verbs = st.session_state[level]
    cols = st.columns(len(verbs))
    for i, verb in enumerate(verbs):
        if cols[i].button(f"{verb} ✕", key=f"{level}_{verb}"):
            st.session_state[level].remove(verb)

st.subheader("Low (Weeks 1–4)")
render_tags("low_verbs")
st.subheader("Medium (Weeks 5–9)")
render_tags("medium_verbs")
st.subheader("High (Weeks 10–14)")
render_tags("high_verbs")

# Add new verb
new_verb = st.text_input("Add a new verb")
level_choice = st.selectbox("Select Level", ["Low", "Medium", "High"])
if st.button("Add Verb"):
    if new_verb.strip():
        key = f"{level_choice.lower()}_verbs"
        st.session_state[key].append(new_verb.strip())

# Generate Questions button with tooltip
if st.button("Generate Questions"):
    all_verbs = st.session_state["low_verbs"] + st.session_state["medium_verbs"] + st.session_state["high_verbs"]
    st.info(f"Generating questions for verbs: {', '.join(all_verbs)}")
st.markdown("<div class='tooltip'>Click to generate questions from selected verbs.</div>", unsafe_allow_html=True)

# Export section with tooltip
if st.button("Export to Word"):
    st.success("Exported to Word (placeholder)")
st.markdown("<div class='tooltip'>Download generated questions in Word format.</div>", unsafe_allow_html=True)
