# app.py — ADI Builder (Sept-24 polished UI: tabs, Bloom chips, quick-picks, branded exports)

import os, io, random
import streamlit as st
from docx import Document
from docx.shared import Inches

# ---------------------------
# Page / Theme
# ---------------------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="📚", layout="wide")

ADI_GREEN = "#245a34"; ADI_GOLD = "#C8A85A"; STONE_BG = "#f5f5f4"; INK = "#1f2937"

st.markdown(f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{
  background:{STONE_BG}; color:{INK};
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial;
}}
.main .block-container {{ max-width: 1320px; }}

/* Banner */
.adi-banner {{
  background:{ADI_GREEN}; color:#fff; border-radius:16px;
  padding:1rem 1.25rem; display:flex; align-items:center; gap:.75rem;
  box-shadow:0 2px 8px rgba(0,0,0,.08); margin:.25rem 0 1rem 0;
}}
.adi-chip {{ background:rgba(255,255,255,.12); color:#fff; padding:.25rem .6rem; border-radius:999px; font-weight:700; font-size:.8rem; }}
.adi-title {{ font-weight:900; letter-spacing:.2px; }}

.adi-card {{ background:#fff; border-radius:14px; padding:1rem; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
.stButton>button {{
  background:{ADI_GREEN} !important; color:#fff !important; border:0; border-radius:12px;
  padding:.55rem 1rem; font-weight:800; box-shadow:0 2px 6px rgba(0,0,0,.10);
}}
.stButton>button:hover {{ filter:brightness(1.06); }}

/* Pills + verbs */
.bloom-row {{ display:flex; gap:.5rem; align-items:center; margin:.25rem 0 .75rem 0; flex-wrap:wrap; }}
.bloom-pill {{
  padding:.28rem .65rem; border-radius:999px; font-weight:800; font-size:.82rem;
  background:#e5e7eb; color:#374151; border:1px solid rgba(0,0,0,.06);
}}
.bloom-pill.active--LOW    {{ background:#E0F2E9; color:#14532d; border-color:#b7e2cc; }}
.bloom-pill.active--MEDIUM {{ background:#FFF1CC; color:#7a5a00; border-color:#f4dc8a; }}
.bloom-pill.active--HIGH   {{ background:#FCE2E2; color:#7a1d1d; border-color:#f3bcbc; }}

.verb-chip {{
  display:inline-block; margin:.2rem .35rem 0 0; padding:.22rem .55rem; border-radius:999px;
  background:#f3f4f6; color:#374151; border:1px solid rgba(0,0,0,.05); font-weight:700; font-size:.8rem;
}}
.verb-chip.active {{ background:#e8fff0; color:#14532d; border-color:#b7e2cc; }}

/* Inputs */
.stTextInput>div>div>input, .stTextArea textarea {{
  background:white; border-radius:12px !important; box-shadow: inset 0 0 0 1px rgba(0,0,0,.08);
}}
.stTextInput>div>div>input:focus, .stTextArea textarea:focus {{
  outline: 2px solid {ADI_GREEN}; box-shadow: 0 0 0 3px rgba(36,90,52,.20);
}}

/* Quick-picks */
.qp {{ display:flex; gap:.75rem; align-items:center; }}
.qp .dot {{
  width:28px; height:28px; border-radius:999px; display:flex; align-items:center; justify-content:center;
  background:#fff; border:2px solid #e5e7eb; cursor:pointer; font-weight:800; color:#6b7280;
}}
.qp .dot.active {{ border-color:{ADI_GREEN}; color:{ADI_GREEN}; }}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# Helpers
# ---------------------------
LOW_VERBS    = ["define","identify","list","recall","describe","label"]
MED_VERBS    = ["apply","demonstrate","solve","illustrate"]
HIGH_VERBS   = ["evaluate","synthesise","design","justify"]

def bloom_from_week(w:int)->str:
    return "LOW" if w<=4 else ("MEDIUM" if w<=9 else "HIGH")

def bloom_pills_html(level:str)->str:
    pills=[]
    for n in ["LOW","MEDIUM","HIGH"]:
        cls = "bloom-pill" + (f" active--{n}" if n==level else "")
        pills.append(f"<span class='{cls}'>{n}</span>")
    return "<div class='bloom-row'>" + "".join(pills) + "</div>"

def verbs_block_html(title:str, verbs:list, selected:set)->str:
    chips=[]
    for v in verbs:
        cls = "verb-chip" + (" active" if v in selected else "")
        chips.append(f"<span class='{cls}'>{v}</span>")
    return f"""
    <div class='adi-card' style='margin:.5rem 0 0 0'>
      <div style='font-weight:800; opacity:.8; margin-bottom:.35rem'>{title}</div>
      {''.join(chips)}
    </div>
    """

def add_word_header(doc: Document, mode: str, week: int, lesson: int, bloom: str, topic: str):
    section = doc.sections[0]
    p = section.header.paragraphs[0]
    run = p.add_run()
    if os.path.isfile("adi_logo.png"):
        try: run.add_picture("adi_logo.png", width=Inches(1.0))
        except Exception: pass
    title = doc.add_paragraph(f"ADI Builder — {mode}  •  Week {week}, Lesson {lesson}")
    title.runs[0].bold = True
    doc.add_paragraph(f"Bloom level: {bloom}")
    if topic:
        t = doc.add_paragraph(f"Topic: {topic}")
        t.runs[0].italic = True

def download_docx(filename: str, builder):
    bio = io.BytesIO(); doc = builder(); doc.save(bio); bio.seek(0)
    st.download_button(
        f"⬇️ Download {filename}",
        data=bio, file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

# MCQ/Activity generators (stable)
def make_mcq(n:int, topic:str, bloom:str, verbs:list):
    t = (topic or "the topic").strip()
    # Prefer verb in stem if available
    verb = verbs[(n-1) % len(verbs)] if verbs else None
    stem_templates = {
        "LOW":    [f"{verb.capitalize() if verb else 'Identify'} the correct statement about {t}.",
                   f"{verb.capitalize() if verb else 'Select'} the best definition of {t}.",
                   f"{verb.capitalize() if verb else 'Recognise'} the main idea of {t}."],
        "MEDIUM": [f"{verb.capitalize() if verb else 'Apply'} the concept of {t} to the scenario.",
                   f"{verb.capitalize() if verb else 'Select'} the next correct step in {t}.",
                   f"{verb.capitalize() if verb else 'Classify'} the example according to {t}."],
        "HIGH":   [f"{verb.capitalize() if verb else 'Evaluate'} which option best justifies {t}.",
                   f"{verb.capitalize() if verb else 'Decide'} which solution most improves {t}.",
                   f"{verb.capitalize() if verb else 'Prioritise'} factors for {t} and choose the top priority."]
    }
    stems = stem_templates[bloom]
    stem = stems[(n-1) % len(stems)]
    options = [
        "Best, fully correct answer aligned to the stem",
        "Partly correct but incomplete",
        "Confuses two related concepts",
        "Irrelevant or unsupported detail",
    ]
    random.shuffle(options)
    correct = options.index("Best, fully correct answer aligned to the stem")
    return {"stem": stem, "options": options, "correct": correct}

def make_activity(n:int, topic:str, minutes:int, verbs:list, tier:str):
    t = (topic or "the topic").strip()
    titles_by_tier = {
        "LOW":    ["Label & list","Describe then recall","Identify & match"],
        "MEDIUM": ["Apply & demo","Solve a case","Illustrate a process"],
        "HIGH":   ["Evaluate options","Design & justify","Synthesis map"]
    }
    title = titles_by_tier[tier][(n-1) % len(titles_by_tier[tier])]
    vtxt  = ", ".join(verbs[:2]) if verbs else ("apply" if tier!="LOW" else "identify")
    steps = [
        f"Brief: Using the verb(s) **{vtxt}**, work with {t}.",
        "Work: follow the task steps and capture evidence.",
        "Debrief: pairs share, then whole-group synthesis."
    ]
    return {
        "title": title, "minutes": minutes,
        "objective": f"To deepen understanding of {t} using Bloom-{tier.lower()} tasks.",
        "grouping": "Pairs", "materials": "Board, sticky notes",
        "steps": steps,
        "success": ["Accurate key points","Clear explanation","Evidence/example used"],
        "check": "Quick exit ticket: 1 insight + 1 question."
    }

# ---------------------------
# Sidebar (uploads + context)
# ---------------------------
with st.sidebar:
    st.markdown("#### UPLOAD (OPTIONAL)")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    up = st.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"], accept_multiple_files=True)
    if up:
        st.caption("✅ " + " • ".join([f.name for f in up]))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### COURSE CONTEXT")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    lesson = st.selectbox("Lesson", list(range(1, 6)), index=0)
    week   = st.selectbox("Week",   list(range(1, 15)), index=6)  # showing 7 in screenshot
    st.markdown("</div>", unsafe_allow_html=True)

    # Quick-pick blocks
    st.markdown("#### QUICK PICK BLOCKS")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    qp_cols = st.columns(4)
    qp_map = {0:5, 1:10, 2:20, 3:30}
    qp_pick = st.session_state.get("qp_pick", 1)
    for i,c in enumerate(qp_cols):
        with c:
            if st.button(f"{qp_map[i]}", key=f"qp{i}"):
                st.session_state["qp_pick"] = i
                st.session_state["count"] = qp_map[i]
                st.rerun()
    # current count
    count = st.session_state.get("count", qp_map.get(qp_pick, 10))
    st.caption(f"Items selected: **{count}**")
    st.markdown("</div>", unsafe_allow_html=True)

# Auto Bloom from week
bloom_level = bloom_from_week(week)

# ---------------------------
# Banner
# ---------------------------
banner_cols = st.columns([0.07, 0.93])
with banner_cols[0]:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_container_width=True)
with banner_cols[1]:
    st.markdown(
        f"<div class='adi-banner'><span class='adi-title'>ADI Builder — Lesson Activities & Questions</span>"
        f"<span class='adi-chip'>Sleek, professional and engaging. Print-ready handouts for your instructors.</span>"
        f"</div>",
        unsafe_allow_html=True
    )

# ---------------------------
# Tabs (Knowledge / Activities / Revision)
# ---------------------------
tab_k, tab_a, tab_r = st.tabs(["KNOWLEDGE MCQs (ADI POLICY)", "SKILLS ACTIVITIES", "REVISION"])

# keep simple state
for key in ["mcqs","acts","revs"]: st.session_state.setdefault(key, [])

# ---------- KNOWLEDGE TAB ----------
with tab_k:
    st.markdown("### MCQ GENERATOR")
    c1, c2 = st.columns([0.62, 0.38])
    with c1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with c2:
        st.text_input("Bloom focus (auto)", value=f"Week {week}: {bloom_level.title()}", disabled=True)

    src = st.text_area("Source text (editable)", height=140, placeholder="Paste or jot key notes, vocab, facts here...")

    # Bloom policy (verbs visible)
    st.markdown("#### Bloom’s verbs (ADI Policy)")
    st.caption("Grouped by policy tiers and week ranges")
    # Allow verb selection per tier (click = toggle via multiselect UI)
    low_sel = st.multiselect("LOW (Weeks 1–4): Remember / Understand", LOW_VERBS, default=LOW_VERBS[:3], key="low_sel")
    med_sel = st.multiselect("MEDIUM (Weeks 5–9): Apply / Analyse", MED_VERBS, default=MED_VERBS[:2], key="med_sel")
    high_sel= st.multiselect("HIGH (Weeks 10–14): Evaluate / Create", HIGH_VERBS, default=HIGH_VERBS[:2], key="high_sel")

    st.markdown(bloom_pills_html(bloom_level), unsafe_allow_html=True)

    # Generate + Export
    g1, g2 = st.columns([0.2, 0.8])
    with g1:
        run_k = st.button("✨ Generate MCQs", use_container_width=True)
    if run_k:
        # pick verbs from the active tier
        verbs = low_sel if bloom_level=="LOW" else (med_sel if bloom_level=="MEDIUM" else high_sel)
        st.session_state["mcqs"] = [make_mcq(i, topic, bloom_level, verbs) for i in range(1, int(count)+1)]
        st.rerun()

    # Render MCQs
    if st.session_state["mcqs"]:
        letters = ["A","B","C","D"]
        for i,q in enumerate(st.session_state["mcqs"], start=1):
            st.markdown(f"**Q{i}. {q['stem']}**")
            for j,opt in enumerate(q["options"]):
                st.write(f"{letters[j]}. {opt}")
            st.caption(f"✅ Answer: {letters[q['correct']]}")
            st.divider()

        def build_doc():
            doc = Document()
            add_word_header(doc, "Knowledge", week, lesson, bloom_level, topic)
            letters = ["A","B","C","D"]
            for i,q in enumerate(st.session_state["mcqs"], start=1):
                doc.add_paragraph(f"Q{i}. {q['stem']}")
                for j,opt in enumerate(q["options"]):
                    doc.add_paragraph(f"   {letters[j]}. {opt}")
                doc.add_paragraph(f"Answer: {letters[q['correct']]}")
            return doc
        download_docx(f"ADI_Knowledge_W{week}_L{lesson}.docx", build_doc)
    else:
        st.info("Set Week (auto-Bloom), choose verbs if you like, then **Generate MCQs**.")

# ---------- ACTIVITIES TAB ----------
with tab_a:
    st.markdown("### ACTIVITY PLANNER")
    c1, c2 = st.columns([0.62, 0.38])
    with c1:
        a_topic = st.text_input("Topic / Outcome (optional)", value=topic or "", key="a_topic")
    with c2:
        minutes = st.selectbox("Time per activity (minutes)", [5,10,15,20,25,30,40,45,50,60], index=2)
    st.markdown(bloom_pills_html(bloom_level), unsafe_allow_html=True)

    a_low  = st.multiselect("LOW verbs you want to emphasise", LOW_VERBS, default=LOW_VERBS[:2], key="a_low")
    a_med  = st.multiselect("MEDIUM verbs", MED_VERBS, default=MED_VERBS[:2], key="a_med")
    a_high = st.multiselect("HIGH verbs", HIGH_VERBS, default=HIGH_VERBS[:1], key="a_high")
    verbs_active = a_low if bloom_level=="LOW" else (a_med if bloom_level=="MEDIUM" else a_high)

    g1, g2 = st.columns([0.2, 0.8])
    with g1:
        run_a = st.button("✨ Generate activities", use_container_width=True)
    if run_a:
        st.session_state["acts"] = [make_activity(i, a_topic, minutes, verbs_active, bloom_level)
                                    for i in range(1, int(count)+1)]
        st.rerun()

    if st.session_state["acts"]:
        for i,a in enumerate(st.session_state["acts"], start=1):
            st.markdown(f"**Activity {i} — {a['title']} ({a['minutes']} min)**")
            st.caption(a["objective"])
            st.write(f"**Grouping:** {a['grouping']}  |  **Materials:** {a['materials']}")
            st.write("**Procedure:**")
            for s in a["steps"]: st.write(f"- {s}")
            st.write("**Success criteria:** " + ", ".join(a["success"]))
            st.write(a["check"])
            st.divider()

        def build_doc():
            doc = Document()
            add_word_header(doc, "Activities", week, lesson, bloom_level, a_topic)
            for i,a in enumerate(st.session_state["acts"], start=1):
                doc.add_heading(f"Activity {i} — {a['title']} ({a['minutes']} min)", level=2)
                doc.add_paragraph(f"Objective: {a['objective']}")
                doc.add_paragraph(f"Grouping: {a['grouping']}  |  Materials: {a['materials']}")
                doc.add_paragraph("Procedure:")
                for s in a["steps"]: doc.add_paragraph(f" - {s}")
                doc.add_paragraph("Success criteria: " + ", ".join(a["success"]))
                doc.add_paragraph(a["check"])
            return doc
        download_docx(f"ADI_Activities_W{week}_L{lesson}.docx", build_doc)
    else:
        st.info("Pick time per activity and verbs (optional), then **Generate activities**.")

# ---------- REVISION TAB ----------
with tab_r:
    st.markdown("### QUICK REVISION TASKS")
    r_topic = st.text_input("Topic / Outcome (optional)", value=topic or "", key="r_topic")
    st.markdown(bloom_pills_html(bloom_level), unsafe_allow_html=True)

    g1, g2 = st.columns([0.2, 0.8])
    with g1:
        run_r = st.button("✨ Generate revision", use_container_width=True)
    if run_r:
        templates = [
            f"Summarise key ideas of {r_topic or 'the topic'} in 5 bullet points.",
            f"Write 3 short-answer questions on {r_topic or 'the topic'} and answer them.",
            f"Create 10 flashcards on core terms for {r_topic or 'the topic'}."
        ]
        st.session_state["revs"] = [templates[(i-1) % len(templates)] for i in range(1, int(count)+1)]
        st.rerun()

    if st.session_state["revs"]:
        for i,r in enumerate(st.session_state["revs"], start=1):
            st.markdown(f"**Task {i}:** {r}")
            st.divider()

        def build_doc():
            doc = Document()
            add_word_header(doc, "Revision", week, lesson, bloom_level, r_topic)
            for i,r in enumerate(st.session_state["revs"], start=1):
                doc.add_paragraph(f"Task {i}: {r}")
            return doc
        download_docx(f"ADI_Revision_W{week}_L{lesson}.docx", build_doc)
    else:
        st.info("Enter a topic (optional), then **Generate revision**.")

