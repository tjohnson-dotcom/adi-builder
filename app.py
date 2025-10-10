# app.py — ADI Builder (clean)

import io
import random
from datetime import datetime
from typing import List, Dict

import streamlit as st

# ---------- Page ----------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🧰", layout="wide")

# ---------- Optional deps (fail-soft) ----------
try:
    from pptx import Presentation           # python-pptx
except Exception:
    Presentation = None

try:
    from docx import Document               # python-docx
    from docx.shared import Pt
except Exception:
    Document = None

# ---------- Hard data from your screenshots ----------
COURSES = [
    {"code": "GE4-EPM", "name": "Defense Technology Practices: Experimentation, Quality Management and Inspection", "color": "#bfe6c7"},
    {"code": "GE4-IPM", "name": "Integrated Project and Materials Management in Defense Technology", "color": "#bfe6c7"},
    {"code": "GE4-MRO", "name": "Military Vehicle and Aircraft MRO: Principles & Applications", "color": "#bfe6c7"},
    {"code": "CT4-COM", "name": "Computation for Chemical Technologists", "color": "#f5e5b3"},
    {"code": "CT4-EMG", "name": "Explosives Manufacturing", "color": "#f5e5b3"},
    {"code": "CT4-TFL", "name": "Thermofluids", "color": "#f5e5b3"},
]

COHORTS = [
    "D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
    "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"
]

INSTRUCTORS = [
    "Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen","Dari","Ghamza",
    "Michail","Meshari","Mohammed Alwuthaylah","Myra","Meshal","Ibrahim","Khalil","Salem",
    "Rana","Daniel","Ahmed Albader"
]

# ---------- Bloom policy ----------
LOW_VERBS  = ["remember", "list", "define", "identify", "state", "recognize"]
MED_VERBS  = ["apply", "analyze", "explain", "compare", "classify", "illustrate"]
HIGH_VERBS = ["evaluate", "create", "design", "critique", "synthesize", "hypothesize"]

def bloom_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    if 10 <= week <= 14: return "High"
    return "Medium"

def verbs(level: str) -> List[str]:
    return {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}.get(level, MED_VERBS)

# ---------- Styling (NO f-strings; no brace escaping problems) ----------
def inject_css():
    css = """
    <style>
    :root { --adi: #245a34; --gold: #C8A85A; --stone: #F3F3F0; }
    .block-container { padding-top: .8rem; max-width: 1480px; }
    h1,h2,h3,h4 { color: var(--adi) !important; }
    .stTabs [data-baseweb=tab-list] { gap:.35rem; }
    .stTabs [data-baseweb=tab] { border:1px solid var(--adi); border-radius:999px; padding:.35rem .9rem; }
    .stTabs [aria-selected=true] { background:var(--adi); color:#fff; }
    .badge { display:inline-block; padding:.2rem .55rem; border:1px solid var(--adi); color:var(--adi);
             border-radius:.5rem; font-weight:700; }
    .course-chip { border:1px solid #999; border-radius:.4rem; padding:.4rem; font-size:.85rem;
                   font-weight:700; text-align:center; margin-bottom:.5rem; }
    .thin-hr { border:0; height:1px; background:#ececec; margin:.8rem 0; }
    .stButton>button { border-radius:.6rem; font-weight:700; }
    .stButton>button[kind=primary] { background:var(--adi); color:#fff; border-color:var(--adi); }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_css()

# ---------- PPTX topic extraction ----------
def extract_topics(upload) -> List[str]:
    if not upload or Presentation is None:
        return []
    prs = Presentation(upload)
    rough = []
    for slide in prs.slides:
        if slide.shapes.title and slide.shapes.title.text:
            t = slide.shapes.title.text.strip()
            if t and t not in rough: rough.append(t)
        for shp in slide.shapes:
            if hasattr(shp, "text_frame") and shp.text_frame:
                for p in shp.text_frame.paragraphs:
                    txt = (p.text or "").strip()
                    if 3 <= len(txt) <= 80 and txt not in rough:
                        rough.append(txt)
        if len(rough) > 50:
            break
    cleaned = []
    for s in rough:
        s = " ".join(s.split()).strip("•-–—: ")
        if s and s not in cleaned:
            cleaned.append(s)
    return cleaned[:30]

# ---------- MCQ generation ----------
def make_mcq(topic: str, level: str) -> Dict:
    verb = random.choice(verbs(level)).capitalize()
    stem = f"{verb} the key idea related to: {topic}"
    correct = f"{topic} — core concept"
    distractors = [
        f"{topic} — unrelated detail",
        f"{topic} — misconception",
        f"{topic} — peripheral fact",
    ]
    options = [correct] + distractors
    random.shuffle(options)
    return {"stem": stem, "options": options, "answer": correct}

# ---------- Export (Word if available; else TXT) ----------
def export_word(mcqs: List[Dict], meta: Dict) -> bytes:
    if not mcqs:
        return b""

    if Document is None:
        buf = io.StringIO()
        course = meta.get("course", "")
        cohort = meta.get("cohort", "")
        week_s = meta.get("week", "")
        header_line = f"ADI Lesson — {course} — {cohort} — Week {week_s}\n\n"
        buf.write(header_line)
        for i, q in enumerate(mcqs, 1):
            buf.write(f"Q{i}. {q['stem']}\n")
            for j, o in enumerate(q["options"], 1):
                buf.write(f"   {chr(64+j)}. {o}\n")
            if meta.get("answer_key", True):
                buf.write(f"Answer: {q['answer']}\n")
            buf.write("\n")
        return buf.getvalue().encode("utf-8")

    # DOCX path
    doc = Document()
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(11)

    doc.add_heading("ADI Lesson Activities & Questions", level=1)
    doc.add_paragraph(f"Course: {meta.get('course','')}  |  Cohort: {meta.get('cohort','')}  |  Instructor: {meta.get('instructor','')}")
    doc.add_paragraph(f"Date: {meta.get('date','')}  |  Lesson: {meta.get('lesson','')}  |  Week: {meta.get('week','')}")
    doc.add_paragraph("")

    doc.add_heading("Knowledge MCQs", level=2)
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        for j, o in enumerate(q["options"], 1):
            doc.add_paragraph(f"{chr(64+j)}. {o}", style="List Bullet")
        if meta.get("answer_key", True):
            doc.add_paragraph(f"Answer: {q['answer']}")
        doc.add_paragraph("")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ---------- State ----------
if "topics" not in st.session_state: st.session_state.topics = []
if "mcqs" not in st.session_state: st.session_state.mcqs = []

# ---------- Sidebar ----------
with st.sidebar:
    st.subheader("Upload (optional)")
    uploaded = st.file_uploader("Drag and drop file here", type=["txt", "docx", "pptx", "pdf"], help="We can scan titles & bullets from PPTX.")
    st.caption(" ")

    st.subheader("Course details")
    course_ix = st.selectbox("Course name", list(range(len(COURSES))),
                             format_func=lambda i: f"{COURSES[i]['code']} — {COURSES[i]['name']}")
    cohort = st.selectbox("Class / Cohort", COHORTS, index=0)
    instructor = st.selectbox("Instructor name", INSTRUCTORS, index=INSTRUCTORS.index("Daniel") if "Daniel" in INSTRUCTORS else 0)
    date = st.date_input("Date", value=datetime.now())
    c1, c2 = st.columns(2)
    with c1:
        lesson = st.number_input("Lesson", min_value=1, max_value=5, value=1, step=1)
    with c2:
        week = st.number_input("Week", min_value=1, max_value=14, value=1, step=1)

# ---------- Main ----------
st.markdown("## ADI Builder — Lesson Activities & Questions")
st.markdown("<div class='thin-hr'></div>", unsafe_allow_html=True)

left, right = st.columns([1, 1])

with left:
    topic = st.text_area("Topic / Outcome (optional)", placeholder="e.g., Integrated Project and …")

    st.caption("ADI policy: Weeks 1–4 Low • 5–9 Medium • 10–14 High")
    recommended = bloom_for_week(int(week))
    st.write(f"**Recommended Bloom for Week {int(week)}:**  "
             f"<span class='badge'>{recommended}</span>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

    with tab1:
        # Get topics (from PPTX or manual)
        if uploaded and Presentation is not None and st.button("Extract topics from uploaded PPTX"):
            topics = extract_topics(uploaded)
            st.session_state.topics = topics
            if topics:
                st.success(f"Extracted {len(topics)} topics.")
            else:
                st.warning("No topics detected in the PPTX.")

        topics = st.session_state.get("topics", [])
        picked: List[str]
        if topics:
            picked = st.multiselect("Pick topics (5–10)", topics, default=topics[:8], max_selections=10)
        else:
            manual = st.text_area("Enter topics (one per line)", placeholder="Topic A\nTopic B\nTopic C")
            picked = [t.strip() for t in manual.splitlines() if t.strip()]

        n_q = st.selectbox("How many MCQs?", [5, 10, 12, 15, 20], index=1)
        answer_key = st.checkbox("Include answer key", value=True)

        if st.button("Generate MCQs", type="primary"):
            base = picked if picked else ([topic] if topic.strip() else [])
            if not base:
                st.error("Provide at least one topic (or extract from upload).")
            else:
                pool = []
                while len(pool) < n_q:
                    for t in base:
                        pool.append(t)
                        if len(pool) >= n_q:
                            break
                random.shuffle(pool)
                st.session_state.mcqs = [make_mcq(t, recommended) for t in pool]
                st.success(f"Generated {len(st.session_state.mcqs)} MCQs at {recommended} level.")

        if st.session_state.mcqs:
            with st.expander("Preview / quick edit"):
                for i, q in enumerate(st.session_state.mcqs, 1):
                    q["stem"] = st.text_input(f"Q{i}", value=q["stem"], key=f"stem_{i}")
                    for j, o in enumerate(q["options"], 1):
                        q["options"][j-1] = st.text_input(f"Option {chr(64+j)}", value=o, key=f"opt_{i}_{j}")
                    q["answer"] = st.selectbox("Correct answer", q["options"],
                                               index=q["options"].index(q["answer"]), key=f"ans_{i}")
                    st.divider()

            meta = {
                "course": f"{COURSES[course_ix]['code']} — {COURSES[course_ix]['name']}",
                "cohort": cohort,
                "instructor": instructor,
                "date": date.strftime("%Y/%m/%d"),
                "lesson": int(lesson),
                "week": int(week),
                "answer_key": answer_key,
            }
            data = export_word(st.session_state.mcqs, meta)
            fname = f"ADI_Lesson_{COURSES[course_ix]['code']}_W{int(week)}_{datetime.now().strftime('%Y%m%d_%H%M')}.{('docx' if Document else 'txt')}"
            st.download_button("Download Word" if Document else "Download TXT", data=data, file_name=fname,
                               mime=("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if Document else "text/plain"))

    with tab2:
        st.caption("Skills activities templates coming soon (rubrics & scenarios).")

    with tab3:
        st.caption("Revision pack builder coming soon (printable).")

    with tab4:
        st.caption("Print-friendly summary coming soon.")

with right:
    st.subheader("Course quick-pick")
    cols = st.columns(3)
    for i, c in enumerate(COURSES):
        with cols[i % 3]:
            st.markdown(
                f"<div class='course-chip' style='background:{c['color']}'>{c['name']}<br><b>{c['code']}</b></div>",
                unsafe_allow_html=True
            )

    st.markdown("<div class='thin-hr'></div>", unsafe_allow_html=True)
    if st.session_state.mcqs:
        st.success(f"{len(st.session_state.mcqs)} MCQs ready to export.")
    else:
        st.info("No questions yet — add a topic or extract from upload, then Generate.")

# ---------- Requirements (for Render) ----------
# requirements.txt:
# streamlit
# python-pptx
# python-docx
