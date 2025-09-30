
# ADI Builder — Streamlit Pro v2
# Tabs UI, PDF/DOCX/PPTX ingest, MCQs + Activities, Render-friendly.
import os
from io import BytesIO
from typing import List, Dict, Tuple

import streamlit as st
from docx import Document
from pptx import Presentation
import fitz  # PyMuPDF

st.set_page_config(page_title="ADI Builder", page_icon="✅", layout="wide")

ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
BG = "#f6f5f2"

st.markdown(f"""
<style>
.stApp {{ background: {BG}; }}
section[data-testid="stSidebar"] > div {{ background: #f1efe9; }}
.badge {{ background:{ADI_GREEN}; color:#fff; padding:6px 10px; border-radius:999px; font-weight:600; display:inline-block }}
.soft {{ color:#666 }}
.gold {{ color:{ADI_GOLD} }}
.pill {{ border:1px solid {ADI_GREEN}; padding:6px 10px; border-radius:999px; display:inline-block; margin-right:6px }}
.divider {{ height:2px; background:{ADI_GREEN}; opacity:0.8; margin:8px 0 16px }}
</style>
""", unsafe_allow_html=True)

BLOOM = {
    "Understand": ["define", "list", "identify", "recall", "describe", "summarise"],
    "Apply": ["apply", "demonstrate", "solve", "illustrate", "use"],
    "Analyse": ["analyze", "compare", "contrast", "differentiate", "organize"],
    "Evaluate": ["evaluate", "justify", "critique", "argue", "assess"],
    "Create": ["design", "construct", "propose", "synthesize", "formulate"],
}

def bloom_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Understand"
    if 5 <= week <= 9: return "Apply/Analyse"
    return "Evaluate/Create"

def read_pdf(file) -> str:
    try:
        data = file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        texts = []
        for page in doc:  # limit to first 10 pages to keep it fast
            if page.number >= 10: break
            texts.append(page.get_text("text"))
        return "\n".join(texts).strip()
    except Exception as e:
        return ""

def read_docx(file) -> str:
    try:
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:
        return ""

def read_pptx(file) -> str:
    try:
        prs = Presentation(file)
        chunks = []
        for i, slide in enumerate(prs.slides):
            if i >= 20: break
            buf = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    t = shape.text.strip()
                    if t:
                        buf.append(t)
            if buf:
                chunks.append("\n".join(buf))
        return "\n\n".join(chunks)
    except Exception:
        return ""

def extract_text(upload) -> Tuple[str, str]:
    if upload is None: 
        return "", ""
    name = upload.name.lower()
    if name.endswith(".pdf"):
        return read_pdf(upload), "pdf"
    if name.endswith(".docx"):
        return read_docx(upload), "docx"
    if name.endswith(".pptx"):
        return read_pptx(upload), "pptx"
    return "", ""

def generate_mcqs(base_topic: str, verbs: List[str], blocks: int = 5) -> List[Dict]:
    topic = base_topic or "the lesson topic"
    out = []
    for i in range(blocks):
        v = verbs[i % max(1, len(verbs))] if verbs else "explain"
        q = {
            "question": f"{v.capitalize()} {topic}: Which option best fits?",
            "options": [
                f"Correct {v} response about {topic}",
                f"Irrelevant detail about {topic}",
                f"Common misconception about {topic}",
                f"Partially true but incomplete about {topic}",
            ],
            "answer_index": 0,
        }
        out.append(q)
    return out

def docx_from_mcqs(mcqs: List[Dict], title: str) -> bytes:
    doc = Document()
    doc.add_heading(title, level=1)
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"{i}. {q['question']}")
        letters = ["A","B","C","D"]
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"   {letters[j]}) {opt}")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

def docx_answer_key(mcqs: List[Dict]) -> bytes:
    doc = Document()
    doc.add_heading("Answer Key", level=1)
    letters = ["A","B","C","D"]
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{i}: {letters[q['answer_index']]}")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

def gift_from_mcqs(mcqs: List[Dict]) -> bytes:
    lines = []
    for i, q in enumerate(mcqs, 1):
        correct = q["options"][q["answer_index"]]
        distractors = [o for j, o in enumerate(q["options"]) if j != q["answer_index"]]
        body = f"::Q{i}:: {q['question']} {{ = {correct} ~ {distractors[0]} ~ {distractors[1]} ~ {distractors[2]} }}"
        lines.append(body)
    return ("\n\n".join(lines)).encode("utf-8")

def generate_activities(topic: str, verbs: List[str], n: int = 3, mins: int = 45) -> List[str]:
    t = topic or "the lesson topic"
    bank = [
        "Think-Pair-Share explaining {}.",
        "Create an infographic comparing aspects of {}.",
        "Solve a case applying {} to a real scenario.",
        "Critique a sample answer about {} and suggest improvements.",
        "Design a short quiz to assess {}.",
        "Construct a concept map of {}."
    ]
    out = []
    for i in range(n):
        base = bank[i % len(bank)].format(t)
        verb = (verbs[i % max(1, len(verbs))] if verbs else "explain")
        out.append(f"{base} (Use verb: {verb}; ~{mins} min)")
    return out

# --- Sidebar ---
with st.sidebar:
    st.markdown('<span class="badge">ADI Builder</span>', unsafe_allow_html=True)
    st.write("")
    up = st.file_uploader("Upload PDF / DOCX / PPTX", type=["pdf","docx","pptx"])
    week = st.selectbox("Week", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson", [1,2,3,4,5], index=0)
    st.caption(f"Policy: <span class='gold'>{bloom_for_week(week)}</span>", unsafe_allow_html=True)

st.title("Knowledge MCQs & Skills Activities")
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

extracted, kind = extract_text(up)

tab1, tab2 = st.tabs(["🧠 Knowledge MCQs", "🛠️ Skills Activities"])

with tab1:
    st.subheader("Knowledge MCQs")
    cols = st.columns(2)
    with cols[0]:
        levels = st.multiselect("Bloom’s levels", ["Understand","Apply","Analyse","Evaluate","Create"], default=["Understand","Apply","Analyse"])
    with cols[1]:
        auto = st.checkbox("Auto-select verbs (balanced)", value=False)
    verbs = []
    if auto:
        for lvl in levels:
            verbs.extend(BLOOM[lvl][:2])
    else:
        with st.expander("Verbs per level", expanded=True):
            for lvl in levels:
                verbs.extend(st.multiselect(f"Verbs for {lvl}", BLOOM[lvl], default=BLOOM[lvl][:2], key=f"verbs_{lvl}"))
    topic_hint = (extracted.split("\n")[0][:120] if extracted else "")
    topic = st.text_input("Topic (optional)", value=topic_hint)
    blocks_col1, blocks_col2 = st.columns([1,3])
    with blocks_col1:
        quick = st.radio("Quick pick", [5,10,20,30], index=1, horizontal=True)
    with blocks_col2:
        blocks = st.number_input("Or custom number of MCQ blocks", min_value=1, max_value=100, value=int(quick), step=1, key="mcq_blocks")
        st.caption("The widget with key 'mcq_blocks' was created with a default value but also had its value set via the Session State API.")
    if st.button("Generate MCQ Blocks", type="primary"):
        mcqs = generate_mcqs(topic or topic_hint, verbs, blocks=blocks)
        st.session_state["mcqs"] = mcqs
    mcqs = st.session_state.get("mcqs", [])
    if mcqs:
        st.success(f"Generated {len(mcqs)} MCQs.")
        for i, q in enumerate(mcqs[:10], 1):
            st.markdown(f"**Q{i}.** {q['question']}")
            letters = ["A","B","C","D"]
            for j, opt in enumerate(q["options"]):
                st.write(f"- {letters[j]}) {opt}")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("⬇️ MCQ Paper (.docx)", data=docx_from_mcqs(mcqs, "MCQ Paper"), file_name="mcq_paper.docx")
        with c2:
            st.download_button("⬇️ Answer Key (.docx)", data=docx_answer_key(mcqs), file_name="answer_key.docx")
        with c3:
            st.download_button("⬇️ Moodle GIFT (.gift)", data=gift_from_mcqs(mcqs), file_name="mcq_questions.gift")
    else:
        st.info("Upload a file (optional), pick Bloom levels/verbs, then click **Generate MCQ Blocks**.")

with tab2:
    st.subheader("Skills Activities")
    a1, a2 = st.columns(2)
    with a1:
        n_acts = st.number_input("Activities", min_value=1, max_value=10, value=3, step=1)
    with a2:
        mins = st.number_input("Duration per activity (mins)", min_value=10, max_value=120, value=45, step=5)
    verbs_for_acts = st.multiselect("Preferred action verbs", BLOOM["Apply"] + BLOOM["Analyse"] + BLOOM["Evaluate"] + BLOOM["Create"], default=["apply","demonstrate","evaluate","design"])
    if st.button("Generate Activities"):
        acts = generate_activities(extracted.split("\n")[0] if extracted else "", verbs_for_acts, n=int(n_acts), mins=int(mins))
        st.session_state["acts"] = acts
    acts = st.session_state.get("acts", [])
    if acts:
        for i, a in enumerate(acts, 1):
            st.write(f"{i}. {a}")
        doc = Document(); doc.add_heading("Activity Sheet", 1)
        for i, a in enumerate(acts, 1): doc.add_paragraph(f"{i}. {a}")
        bio = BytesIO(); doc.save(bio)
        st.download_button("⬇️ Activity Sheet (.docx)", data=bio.getvalue(), file_name="activity_sheet.docx")
    else:
        st.info("Pick count/duration and verbs, then click **Generate Activities**.")

# Bind to Render $PORT if running there
if __name__ == "__main__":
    # Running under 'streamlit run app.py' so nothing to do here.
    pass
