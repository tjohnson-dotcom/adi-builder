# streamlit_app.py — ADI Builder (Pedagogical, Fixed)
import os
import streamlit as st
from docx import Document
import random

# ---------------------------
# Page & Theme
# ---------------------------
st.set_page_config(
    page_title="ADI Builder — Staff Friendly",
    page_icon="📚",
    layout="wide",
)

ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
STONE_BG  = "#f5f5f4"
INK       = "#1f2937"

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_column_width=True)
    else:
        st.markdown("### ADI Builder")

    st.markdown("### Modes")
    modes = ["Knowledge", "Activities", "Revision"]
    mode = st.radio("Pick a workflow", modes, index=0)

    st.markdown("### Lesson setup")
    week = st.selectbox("Week", options=list(range(1, 15)), index=0)
    lesson = st.selectbox("Lesson", options=list(range(1, 6)), index=0)

    st.markdown("### Number of items")
    num_items = st.selectbox("How many?", options=[1,2,3,4,5,6,8,10,12,15,20], index=2)

    st.markdown("### Time per item (minutes)")
    time_per_item = st.selectbox("Time", options=list(range(5,65,5)), index=1)

    st.markdown("### Upload resources")
    ebook_file = st.file_uploader("📖 eBook (PDF)", type=["pdf"], key="ebook")
    plan_file = st.file_uploader("📄 Lesson Plan (DOCX/PDF)", type=["docx","pdf"], key="plan")
    ppt_file  = st.file_uploader("📊 Slides (PPTX)", type=["pptx"], key="ppt")

    run = st.button("✨ Generate for staff")

# ---------------------------
# Main Layout
# ---------------------------
st.header(f"{mode} — Week {week}, Lesson {lesson}")
st.caption("ADI-aligned prompts and activities. Easy picks.")

def make_mcq(n:int):
    stem = f"Q{n}: Apply the concept of the topic to a scenario."
    options = [
        "Confuses two concepts",
        "Irrelevant detail",
        "Best answer aligned to the topic",
        "Partly correct but incomplete"
    ]
    random.shuffle(options)
    correct = options.index("Best answer aligned to the topic")
    return {"stem": stem, "options": options, "correct": correct}

# State
if "items" not in st.session_state:
    st.session_state["items"] = []

# Generate
if run:
    st.session_state["items"] = []
    if mode == "Knowledge":
        for i in range(1, num_items+1):
            st.session_state["items"].append(make_mcq(i))
    else:
        for i in range(1, num_items+1):
            st.session_state["items"].append({
                "title": f"{mode} {i} ({time_per_item} min)",
                "steps": [
                    "Step 1: Introduce task",
                    "Step 2: Group discussion",
                    "Step 3: Share back"
                ]
            })
    st.rerun()

# Display items
if st.session_state["items"]:
    for idx, item in enumerate(st.session_state["items"]):
        with st.container():
            if mode == "Knowledge":
                st.markdown(f"**{item['stem']}**")
                letters = ["A","B","C","D"]
                for i,opt in enumerate(item['options']):
                    st.markdown(f"{letters[i]}. {opt}")
                st.caption(f"✅ Correct: {letters[item['correct']]}")
            else:
                st.markdown(f"### {item['title']}")
                for s in item['steps']:
                    st.write(s)

            cols = st.columns([1,1])
            with cols[0]:
                if st.button("🔄 Regenerate", key=f"regen{idx}"):
                    if mode == "Knowledge":
                        st.session_state["items"][idx] = make_mcq(idx+1)
                    else:
                        st.session_state["items"][idx] = {
                            "title": f"{mode} {idx+1} ({time_per_item} min)",
                            "steps": ["Step 1: New task","Step 2: Work","Step 3: Review"]
                        }
                    st.rerun()
            with cols[1]:
                st.text_area("📋 Copy", value=str(item), height=80, key=f"copy{idx}")

# ---------------------------
# Export
# ---------------------------
def export_docx(items, mode):
    doc = Document()
    doc.add_heading(f"{mode} — Week {week}, Lesson {lesson}", 0)
    for i,item in enumerate(items,1):
        if mode=="Knowledge":
            doc.add_paragraph(item["stem"])
            letters = ["A","B","C","D"]
            for j,opt in enumerate(item["options"]):
                doc.add_paragraph(f"{letters[j]}. {opt}", style="List Bullet")
            doc.add_paragraph(f"Answer: {letters[item['correct']]}")
        else:
            doc.add_heading(item["title"], level=1)
            for s in item["steps"]:
                doc.add_paragraph(s, style="List Bullet")
    return doc

if st.session_state["items"]:
    if st.button("⬇️ Export to DOCX"):
        doc = export_docx(st.session_state["items"], mode)
        filename = f"ADI_{mode}_W{week}_L{lesson}.docx"
        doc.save(filename)
        with open(filename,"rb") as f:
            st.download_button("Download DOCX", f, file_name=filename)
