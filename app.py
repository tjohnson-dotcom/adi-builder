# app.py — ADI Builder (Final: 3 modes, uploads, right-panel generate, branded Word exports)

import os, io, random
import streamlit as st
from docx import Document
from docx.shared import Inches

# ---------------------------
# Page / Theme
# ---------------------------
st.set_page_config(page_title="ADI Builder", page_icon="📚", layout="wide")
ADI_GREEN = "#245a34"; ADI_GOLD = "#C8A85A"; STONE_BG = "#f5f5f4"; INK = "#1f2937"

st.markdown(f"""
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
.hint {{ opacity:.85; font-size:.95rem; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Helpers
# ---------------------------
def bloom_band(week:int):
    if 1 <= week <= 4: return "LOW — Remember/Understand"
    if 5 <= week <= 9: return "MEDIUM — Apply/Analyse"
    return "HIGH — Evaluate/Create"

def ensure_state(key, default):
    if key not in st.session_state: st.session_state[key] = default
    return st.session_state[key]

def add_word_branding_header(doc: Document, mode: str, week: int, lesson: int):
    section = doc.sections[0]
    header = section.header
    p = header.paragraphs[0]
    run = p.add_run()
    if os.path.isfile("adi_logo.png"):
        try: run.add_picture("adi_logo.png", width=Inches(1.0))
        except Exception: pass
    doc.add_paragraph(f"ADI Builder — {mode}  •  Week {week}, Lesson {lesson}").runs[0].bold = True

def download_docx_button(filename: str, builder):
    bio = io.BytesIO(); doc = builder(); doc.save(bio); bio.seek(0)
    st.download_button(
        f"⬇️ Download {filename}",
        data=bio,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )

# Simple content generators (stable, no parsing risk)
def make_mcq(n:int, topic:str, week:int):
    t = (topic or "the topic").strip()
    band = "LOW" if week<=4 else ("MEDIUM" if week<=9 else "HIGH")
    pools = {
        "LOW":    [f"Select the best definition of {t}.",
                   f"Identify the correct statement about {t}.",
                   f"Recognise the main idea of {t}."],
        "MEDIUM": [f"Apply the concept of {t} to a scenario.",
                   f"Select the next correct step in {t}.",
                   f"Classify the example according to {t}."],
        "HIGH":   [f"Evaluate which option best justifies {t}.",
                   f"Decide which solution most improves {t}.",
                   f"Prioritise the factors for {t} and choose the top priority."],
    }
    stem = pools[band][(n-1) % len(pools[band])]
    options = [
        "Best, fully correct answer aligned to the stem",
        "Partly correct but incomplete",
        "Confuses two related concepts",
        "Irrelevant or unsupported detail",
    ]
    random.shuffle(options)
    correct = options.index("Best, fully correct answer aligned to the stem")
    return {"stem": stem, "options": options, "correct": correct}

def make_activity(n:int, mode:str, topic:str, minutes:int):
    t = (topic or "the topic").strip()
    titles = {
        "Activities": ["Think–Pair–Share","Jigsaw teach-back","Gallery walk","Case vignette","Concept map"],
        "Revision":   ["Cheat sheet","5 short-answer Qs","Flashcards","Past-paper drill","Exit ticket"],
    }
    title = titles[mode][(n-1) % len(titles[mode])]
    step_bank = {
        "Think–Pair–Share": ["Think: list 3 facts, 2 links, 1 question.",
                             "Pair: compare, agree top 3 points.",
                             "Share: pairs feedback; teacher synthesises."],
        "Jigsaw teach-back": ["Split subtopics to groups.",
                              "Prepare a 3-bullet explainer.",
                              "Teach-back; peers ask one question."],
        "Gallery walk": ["Poster draft on misconceptions.",
                         "Walk: add sticky-note corrections.",
                         "Debrief: highlight strongest corrections."],
        "Case vignette": ["Read the vignette; identify key issue.",
                          "Propose a solution with rationale.",
                          "Compare/ refine approaches."],
        "Concept map": ["List key terms for the topic.",
                        "Link with labelled connections.",
                        "Present and justify the map."],
        "Cheat sheet": ["Summarise key ideas on one page.",
                        "Add 2 examples and 1 diagram.",
                        "Swap and peer-review."],
        "5 short-answer Qs": ["Draft five focused questions.",
                              "Answer in 2–3 sentences each.",
                              "Swap and self/peer-mark."],
        "Flashcards": ["Create 10 term/definition cards.",
                       "Quiz a partner; track tricky cards.",
                       "Revisit tricky cards."],
        "Past-paper drill": ["Attempt one timed question.",
                             "Discuss model points.",
                             "Redraft weakest section."],
        "Exit ticket": ["Write 1 insight + 1 question.",
                        "Discuss with a partner.",
                        "Submit on exit."],
    }
    steps = step_bank.get(title, ["Brief", "Do", "Debrief"])
    return {
        "title": title,
        "minutes": minutes,
        "objective": f"Deepen understanding of {t} and demonstrate applied knowledge.",
        "grouping": "Pairs" if mode=="Activities" else "Individual",
        "materials": "Board, sticky notes" if mode=="Activities" else "Paper, pens",
        "steps": steps,
        "success": ["Accurate key points","Clear explanation","Evidence/example used"],
        "check": "Quick check: 1 insight + 1 question.",
    }

# ---------------------------
# Sidebar (inputs + uploads)
# ---------------------------
with st.sidebar:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_container_width=True)
    else:
        st.markdown("### **ADI Builder**")

    modes = ["Knowledge","Activities","Revision"]
    mode = st.radio("Workflow", modes, index=0)

    st.markdown("### Lesson setup")
    week   = st.selectbox("Week", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson", list(range(1,6)),  index=0)

    st.markdown("### Number of items")
    count = st.selectbox("How many?", [1,2,3,4,5,6,8,10,12,15,20], index=2)

    st.markdown("### Time per item (minutes)")
    minutes = st.selectbox("Time", [5,10,15,20,25,30,40,45,50,60], index=2)

    topic = st.text_input("Topic / Objective (short)")
    st.caption(f"Bloom: **{bloom_band(week)}**")

    # ---- Uploads (drag & drop) ----
    st.markdown("### Upload resources (drag & drop)")
    with st.expander("📥 Drag & drop files or click to browse", expanded=True):
        ebook_file = st.file_uploader("📖 eBook (PDF)", type=["pdf"], key="ebook")
        plan_file  = st.file_uploader("📄 Lesson Plan (DOCX/PDF)", type=["docx","pdf"], key="plan")
        ppt_file   = st.file_uploader("📊 Slides (PPTX)", type=["pptx"], key="ppt")
    uploaded = []
    if ebook_file: uploaded.append(f"📖 {ebook_file.name}")
    if plan_file:  uploaded.append(f"📄 {plan_file.name}")
    if ppt_file:   uploaded.append(f"📊 {ppt_file.name}")
    if uploaded: st.caption("✅ Uploaded: " + " • ".join(uploaded))

    # Sidebar generate
    run_side = st.button("✨ Generate for staff", use_container_width=True)

# ---------------------------
# Main layout
# ---------------------------
left, right = st.columns([1,1], gap="large")

with left:
    st.subheader(f"{mode} — Week {week}, Lesson {lesson}")
    st.caption("ADI-aligned prompts and activities. No sliders. Easy picks.")
    st.markdown("<div class='adi-card hint'>Uploads are optional in this stable build. Focus: clean outputs and branded Word downloads.</div>", unsafe_allow_html=True)

with right:
    st.subheader("Draft output")

    # Right-panel generate (hard to miss)
    rp_cols = st.columns([0.3, 0.7])
    with rp_cols[0]:
        run_right = st.button("✨ Generate for staff", use_container_width=True)
    run = run_side or run_right

    # (Optional) Auto-generate once after any change — toggle True/False
    AUTO_GENERATE = False
    def _cfg():
        return {"m":mode,"w":week,"l":lesson,"c":count,"t":minutes,"p":(topic or "").strip()}
    if "last_cfg" not in st.session_state: st.session_state["last_cfg"] = None
    if AUTO_GENERATE and st.session_state["last_cfg"] != _cfg():
        run = True
        st.session_state["last_cfg"] = _cfg()

    # Per-mode state
    knowledge = ensure_state("knowledge_items", [])
    activities = ensure_state("activity_items", [])
    revision = ensure_state("revision_items", [])

    # Generate
    if run:
        if mode == "Knowledge":
            st.session_state["knowledge_items"] = [make_mcq(i, topic, week) for i in range(1, count+1)]
        elif mode == "Activities":
            st.session_state["activity_items"] = [make_activity(i, "Activities", topic, minutes) for i in range(1, count+1)]
        else:
            templates = [
                f"Summarise key ideas of {topic or 'the topic'} in 5 bullet points.",
                f"Write 3 short-answer questions on {topic or 'the topic'} and answer them.",
                f"Create 10 flashcards on core terms for {topic or 'the topic'}."
            ]
            st.session_state["revision_items"] = [templates[(i-1) % len(templates)] for i in range(1, count+1)]
        st.rerun()

    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)

    # Render / Export
    if mode == "Knowledge":
        items = st.session_state["knowledge_items"]
        if not items:
            st.info("Click **Generate for staff** to create MCQs (A–D).")
        else:
            letters = ["A","B","C","D"]
            for i,q in enumerate(items, start=1):
                st.markdown(f"**Q{i}. {q['stem']}**")
                for j,opt in enumerate(q["options"]):
                    st.write(f"{letters[j]}. {opt}")
                st.caption(f"✅ Answer: {letters[q['correct']]}")
                st.divider()

            def build_doc():
                doc = Document()
                add_word_branding_header(doc, "Knowledge", week, lesson)
                if topic:
                    doc.add_paragraph(f"Topic: {topic}").runs[0].italic = True
                for i,q in enumerate(items, start=1):
                    letters = ["A","B","C","D"]
                    doc.add_paragraph(f"Q{i}. {q['stem']}")
                    for j,opt in enumerate(q["options"]):
                        doc.add_paragraph(f"   {letters[j]}. {opt}")
                    doc.add_paragraph(f"Answer: {letters[q['correct']]}")
                return doc
            download_docx_button(f"ADI_Knowledge_W{week}_L{lesson}.docx", build_doc)

    elif mode == "Activities":
        items = st.session_state["activity_items"]
        if not items:
            st.info("Click **Generate for staff** to create structured, timed activities.")
        else:
            for i,a in enumerate(items, start=1):
                st.markdown(f"**Activity {i} ({a['minutes']} min) — {a['title']}**")
                st.caption(a["objective"])
                st.write(f"**Grouping:** {a['grouping']}  |  **Materials:** {a['materials']}")
                st.write("**Procedure:**")
                for s in a["steps"]: st.write(f"- {s}")
                st.write("**Success criteria:** " + ", ".join(a["success"]))
                st.write(a["check"])
                st.divider()

            def build_doc():
                doc = Document()
                add_word_branding_header(doc, "Activities", week, lesson)
                if topic:
                    doc.add_paragraph(f"Topic: {topic}").runs[0].italic = True
                for i,a in enumerate(items, start=1):
                    doc.add_heading(f"Activity {i} ({a['minutes']} min) — {a['title']}", level=2)
                    doc.add_paragraph(f"Objective: {a['objective']}")
                    doc.add_paragraph(f"Grouping: {a['grouping']}  |  Materials: {a['materials']}")
                    doc.add_paragraph("Procedure:")
                    for s in a["steps"]: doc.add_paragraph(f" - {s}")
                    doc.add_paragraph("Success criteria: " + ", ".join(a["success"]))
                    doc.add_paragraph(a["check"])
                return doc
            download_docx_button(f"ADI_Activities_W{week}_L{lesson}.docx", build_doc)

    else:
        items = st.session_state["revision_items"]
        if not items:
            st.info("Click **Generate for staff** to create concise revision prompts.")
        else:
            for i,r in enumerate(items, start=1):
                st.markdown(f"**Task {i}:** {r}")
                st.divider()

            def build_doc():
                doc = Document()
                add_word_branding_header(doc, "Revision", week, lesson)
                if topic:
                    doc.add_paragraph(f"Topic: {topic}").runs[0].italic = True
                for i,r in enumerate(items, start=1):
                    doc.add_paragraph(f"Task {i}: {r}")
                return doc
            download_docx_button(f"ADI_Revision_W{week}_L{lesson}.docx", build_doc)

    st.markdown("</div>", unsafe_allow_html=True)
