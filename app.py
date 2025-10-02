# app.py — ADI Builder (Clean, Branded, Staff-friendly)

import os
import io
import random
import streamlit as st
from docx import Document
from docx.shared import Inches, Pt

# ---------------------------
# Page / Theme
# ---------------------------
st.set_page_config(page_title="ADI Builder", page_icon="📚", layout="wide")

ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
STONE_BG  = "#f5f5f4"
INK       = "#1f2937"

st.markdown(
    f"""
    <style>
      html, body, [data-testid="stAppViewContainer"] {{
        background:{STONE_BG}; color:{INK};
        font-family: ui-sans-serif, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial;
      }}
      .main .block-container {{ max-width: 1280px; }}
      .adi-card {{ background:#fff; border-radius:16px; padding:1rem; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
      .stButton>button {{
        background:{ADI_GREEN} !important; color:#fff !important; border:0; border-radius:14px;
        padding:.6rem 1rem; font-weight:700;
      }}
      .stButton>button:hover {{ filter:brightness(1.05); }}
      .hint {{ opacity:.8; font-size:.95rem; }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Helpers
# ---------------------------
def bloom_band(week:int):
    if 1 <= week <= 4:   return "LOW — Remember/Understand"
    if 5 <= week <= 9:   return "MEDIUM — Apply/Analyse"
    return "HIGH — Evaluate/Create"

def ensure_list_state(key:str):
    if key not in st.session_state:
        st.session_state[key] = []

def make_mcq(n:int, topic:str, week:int):
    # Simple, stable MCQ generator (no external parsing)
    t = topic.strip() or "the topic"
    band = bloom_band(week).split(" — ")[0]
    stems_by_band = {
        "LOW":    [f"Identify the correct statement about {t}.",
                   f"Select the best definition of {t}.",
                   f"Recognize the main idea of {t}."],
        "MEDIUM": [f"Apply the concept of {t} to a scenario.",
                   f"Select the step that should occur next in {t}.",
                   f"Classify the example according to {t}."],
        "HIGH":   [f"Evaluate which option best justifies {t}.",
                   f"Decide which solution most improves {t}.",
                   f"Prioritize the factors for {t} and pick the top priority."]
    }
    stem = stems_by_band[band][(n-1) % len(stems_by_band[band])]
    options = [
        "Best, fully correct answer aligned to the stem",
        "Partly correct but incomplete",
        "Confuses two related concepts",
        "Irrelevant or unsupported detail"
    ]
    random.shuffle(options)
    correct_idx = options.index("Best, fully correct answer aligned to the stem")
    return {"stem": stem, "options": options, "correct": correct_idx}

def make_activity(n:int, mode:str, topic:str, minutes:int):
    t = topic.strip() or "the topic"
    title_bank = {
        "Activities": ["Think–Pair–Share", "Jigsaw teach-back", "Gallery walk", "Case vignette", "Concept map"],
        "Revision":   ["Cheat sheet", "5 short-answer Qs", "Flashcards", "Past-paper drill", "Exit ticket"]
    }
    title = title_bank[mode][(n-1) % len(title_bank[mode])]
    steps = {
        "Think–Pair–Share": [
            "Think: list 3 facts, 2 links, 1 question.",
            "Pair: compare notes, agree top 3 points.",
            "Share: selected pairs feed back to whole class."
        ],
        "Jigsaw teach-back": [
            "Split subtopics to groups.",
            "Each group prepares a 3-bullet explainer.",
            "Teach-back to peers; each peer asks one question."
        ],
        "Gallery walk": [
            "Groups create posters addressing misconceptions.",
            "Walk: add sticky-note corrections to others’ posters.",
            "Debrief: highlight strong corrections and next steps."
        ],
        "Case vignette": [
            "Read the vignette and identify the key issue.",
            "Propose a solution with rationale.",
            "Compare approaches and refine the plan."
        ],
        "Concept map": [
            "List key terms for the topic.",
            "Connect terms with labelled links.",
            "Present and justify the connections."
        ],
        "Cheat sheet": [
            "Summarise key ideas on one page.",
            "Add two examples and one diagram.",
            "Swap sheets and peer-review."
        ],
        "5 short-answer Qs": [
            "Draft five focused questions on key ideas.",
            "Answer in 2–3 sentences each.",
            "Swap and self/peer-mark with criteria."
        ],
        "Flashcards": [
            "Make 10 term/definition cards.",
            "Quiz a partner and track tricky cards.",
            "Revise tricky cards again."
        ],
        "Past-paper drill": [
            "Attempt one past-paper style question (timed).",
            "Swap and discuss model points.",
            "Redraft the weakest section."
        ],
        "Exit ticket": [
            "Write 1 insight and 1 question from today.",
            "Turn to a partner and discuss.",
            "Submit to teacher on exit."
        ],
    }
    plan = steps.get(title, ["Brief", "Do", "Debrief"])
    return {
        "title": f"{title}",
        "minutes": minutes,
        "objective": f"To deepen understanding of {t} and demonstrate applied knowledge.",
        "grouping": "Pairs" if mode == "Activities" else "Individual",
        "materials": "Board, sticky notes" if mode == "Activities" else "Paper, pens",
        "steps": plan,
        "success": ["Accurate key points", "Clear explanation", "Evidence/example used"],
        "check": "Quick check: 1 insight + 1 question."
    }

def add_word_branding_header(doc: Document, mode: str, week: int, lesson: int):
    """Adds ADI logo in header (if available) and a branding line."""
    section = doc.sections[0]
    header = section.header
    p = header.paragraphs[0]
    run = p.add_run()
    logo_path = "adi_logo.png"
    # If logo exists in repo, add it to the header
    if os.path.isfile(logo_path):
        try:
            run.add_picture(logo_path, width=Inches(1.0))
        except Exception:
            pass  # if image fails, just skip it
    # Branding line below header
    doc.add_paragraph(f"ADI Builder — {mode}  •  Week {week}, Lesson {lesson}").runs[0].bold = True

def download_docx_button(filename: str, build_fn):
    """Build docx in memory and offer a single download button."""
    bio = io.BytesIO()
    doc = build_fn()
    doc.save(bio)
    bio.seek(0)
    st.download_button(
        label=f"⬇️ Download {filename}",
        data=bio,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

# ---------------------------
# Sidebar (inputs)
# ---------------------------
with st.sidebar:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_container_width=True)  # fixed deprecation
    else:
        st.markdown("### **ADI Builder**")

    modes = ["Knowledge", "Activities", "Revision"]
    mode = st.radio("Workflow", modes, index=0, label_visibility="visible")

    st.markdown("### Lesson setup")
    week = st.selectbox("Week", list(range(1, 15)), index=0)
    lesson = st.selectbox("Lesson", list(range(1, 6)), index=0)

    st.markdown("### Number of items")
    num_items = st.selectbox("How many?", [1,2,3,4,5,6,8,10,12,15,20], index=2)

    st.markdown("### Time per item (minutes)")
    time_per_item = st.selectbox("Time", [5,10,15,20,25,30,40,45,50,60], index=2)

    topic = st.text_input("Topic / Objective (short)", value="")
    st.caption(f"Bloom: **{bloom_band(week)}**")

    st.markdown("---")
    run = st.button("✨ Generate for staff", use_container_width=True)

# ---------------------------
# Main layout
# ---------------------------
left, right = st.columns([1,1], gap="large")

with left:
    st.subheader(f"{mode} — Week {week}, Lesson {lesson}")
    st.caption("ADI-aligned prompts and activities. No sliders. Easy picks.")
    st.markdown("<div class='adi-card hint'>Upload eBooks/Plans/Slides are optional in this clean build. This version focuses on stable outputs and branded Word downloads.</div>", unsafe_allow_html=True)

with right:
    st.subheader("Draft output")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)

    # Keep separate state per mode
    ensure_list_state("knowledge_items")
    ensure_list_state("activity_items")
    ensure_list_state("revision_items")

    # Generate
    if run:
        if mode == "Knowledge":
            st.session_state["knowledge_items"] = [make_mcq(i, topic, week) for i in range(1, num_items+1)]
        elif mode == "Activities":
            st.session_state["activity_items"] = [make_activity(i, "Activities", topic, time_per_item) for i in range(1, num_items+1)]
        else:
            # Revision prompts — concise, focused
            rev_templates = [
                f"Summarise the key ideas of {topic or 'the topic'} in 5 bullet points.",
                f"Write 3 short-answer questions on {topic or 'the topic'} and answer them.",
                f"Create 10 flashcards covering terms for {topic or 'the topic'}."
            ]
            st.session_state["revision_items"] = [rev_templates[(i-1) % len(rev_templates)] for i in range(1, num_items+1)]
        st.rerun()

    # Render per mode
    if mode == "Knowledge":
        items = st.session_state["knowledge_items"]
        if not items:
            st.info("Click **Generate for staff** to create MCQs (A–D) based on your topic and week.")
        else:
            letters = ["A", "B", "C", "D"]
            for i, q in enumerate(items, start=1):
                st.markdown(f"**Q{i}. {q['stem']}**")
                for j, opt in enumerate(q["options"]):
                    st.write(f"{letters[j]}. {opt}")
                st.caption(f"✅ Answer: {letters[q['correct']]}")
                st.divider()

            # Word export (with logo + banner)
            def build_doc():
                doc = Document()
                add_word_branding_header(doc, "Knowledge", week, lesson)
                if topic:
                    p = doc.add_paragraph(f"Topic: {topic}")
                    p.runs[0].italic = True
                for i, q in enumerate(items, start=1):
                    doc.add_paragraph(f"Q{i}. {q['stem']}")
                    for j, opt in enumerate(q["options"]):
                        doc.add_paragraph(f"   {letters[j]}. {opt}")
                    doc.add_paragraph(f"Answer: {letters[q['correct']]}")
                return doc

            download_docx_button(f"ADI_Knowledge_W{week}_L{lesson}.docx", build_doc)

    elif mode == "Activities":
        items = st.session_state["activity_items"]
        if not items:
            st.info("Click **Generate for staff** to create structured, timed activities.")
        else:
            for i, a in enumerate(items, start=1):
                st.markdown(f"**Activity {i} ({a['minutes']} min) — {a['title']}**")
                st.caption(a["objective"])
                st.write(f"**Grouping:** {a['grouping']}  |  **Materials:** {a['materials']}")
                st.write("**Procedure:**")
                for s in a["steps"]:
                    st.write(f"- {s}")
                st.write("**Success criteria:** " + ", ".join(a["success"]))
                st.write(a["check"])
                st.divider()

            # Word export (with logo + banner)
            def build_doc():
                doc = Document()
                add_word_branding_header(doc, "Activities", week, lesson)
                if topic:
                    p = doc.add_paragraph(f"Topic: {topic}")
                    p.runs[0].italic = True
                for i, a in enumerate(items, start=1):
                    doc.add_heading(f"Activity {i} ({a['minutes']} min) — {a['title']}", level=2)
                    doc.add_paragraph(f"Objective: {a['objective']}")
                    doc.add_paragraph(f"Grouping: {a['grouping']}  |  Materials: {a['materials']}")
                    doc.add_paragraph("Procedure:")
                    for s in a["steps"]:
                        doc.add_paragraph(f" - {s}")
                    doc.add_paragraph("Success criteria: " + ", ".join(a["success"]))
                    doc.add_paragraph(a["check"])
                return doc

            download_docx_button(f"ADI_Activities_W{week}_L{lesson}.docx", build_doc)

    else:  # Revision
        items = st.session_state["revision_items"]
        if not items:
            st.info("Click **Generate for staff** to create concise revision prompts.")
        else:
            for i, r in enumerate(items, start=1):
                st.markdown(f"**Task {i}:** {r}")
                st.divider()

            # Word export (with logo + banner)
            def build_doc():
                doc = Document()
                add_word_branding_header(doc, "Revision", week, lesson)
                if topic:
                    p = doc.add_paragraph(f"Topic: {topic}")
                    p.runs[0].italic = True
                for i, r in enumerate(items, start=1):
                    doc.add_paragraph(f"Task {i}: {r}")
                return doc

            download_docx_button(f"ADI_Revision_W{week}_L{lesson}.docx", build_doc)

    st.markdown("</div>", unsafe_allow_html=True)
