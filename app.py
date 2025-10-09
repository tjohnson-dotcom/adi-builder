# app.py
# ADI Builder — Lesson Activities & Questions (safe build)

import io
import random
import itertools
import re
from datetime import date

import streamlit as st

# --------------------------- THEME & STYLE ---------------------------

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

BASE_GREEN = "#245a34"
DARK_GREEN = "#153a27"

STYLE = f"""
<style>
/* App banner */
.block-container {{
  padding-top: 0.5rem;
  padding-bottom: 3rem;
}}
h1, h2, h3, h4 {{ color: {DARK_GREEN}; }}

/* Pointer + hover affordances */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button {{
  cursor: pointer !important;
}}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {{
  box-shadow: 0 0 0 2px {BASE_GREEN} inset !important;
}}

/* Keyboard focus ring */
:focus-visible {{
  outline: 2px solid {BASE_GREEN} !important;
  outline-offset: 2px;
}}

/* Dashed dropzone */
div[data-testid="stFileUploaderDropzone"] {{
  border: 2px dashed {BASE_GREEN} !important;
  border-radius: 10px !important;
}}

/* Active band frames */
.band {{
  border: 1px solid #dfe5df;
  border-radius: 10px;
  padding: 6px 8px 2px 8px;
  margin-bottom: 10px;
}}
.band.active {{
  border: 2px solid {BASE_GREEN};
  box-shadow: 0 0 0 2px rgba(36,90,52,0.10);
}}
.band-title {{
  font-weight: 600;
  color: {DARK_GREEN};
  margin-bottom: 6px;
}}

hr.thin {{
  border: none;
  border-top: 1px solid #e7ece7;
  margin: 0.6rem 0 0.8rem 0;
}}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)


# --------------------------- SESSION DEFAULTS ---------------------------

def ss_default(name, value):
    if name not in st.session_state:
        st.session_state[name] = value

ss_default("lowverbs", ["define", "identify", "list"])
ss_default("medverbs", ["apply", "demonstrate", "solve"])
ss_default("highverbs", ["evaluate", "synthesize", "design"])
ss_default("mcqs", [])
ss_default("activities", [])
ss_default("source_text", "")
ss_default("lesson", 1)
ss_default("week", 1)


# --------------------------- HELPERS ---------------------------

def ctx_filename(prefix: str) -> str:
    """Simple context-based filename base, always safe."""
    course = st.session_state.get("course", "Course")
    cohort = st.session_state.get("cohort", "Cohort")
    instr = st.session_state.get("instructor", "Instructor")
    wk = st.session_state.get("week", 1)
    return f"{prefix}__{course}__{cohort}__W{wk}"

def harvest_keywords(text: str, k=6):
    """Super-light keyword grabber (safe, optional)."""
    if not text:
        return []
    stop = set("""
        the a an and or of in on at by for to from with into over after before
        is are was were be being been this that those these there here as it its
        we you they he she him her them i me my our your their not no yes
    """.split())
    words = re.findall(r"[A-Za-z]{5,}", text.lower())
    words = [w for w in words if w not in stop]
    scored = {}
    for w in words:
        scored[w] = scored.get(w, 0) + 1 + len(w)/20.0
    return [w.capitalize() for w, _ in sorted(scored.items(), key=lambda x: -x[1])[:k]]


# --------------------------- MCQ GENERATOR ---------------------------

def generate_mcqs(n, topic, low_verbs, med_verbs, high_verbs):
    """
    Generate n varied MCQs using Bloom-aligned stems, rotating option banks,
    shuffling correct-answer positions, and preventing duplicates.
    """
    topic_text = (topic or "").strip() or "this lesson"

    # Band by week
    band = "low"
    try:
        wk = int(st.session_state.week)
        if 5 <= wk <= 9:
            band = "med"
        elif wk >= 10:
            band = "high"
    except Exception:
        pass

    # Verbs by band with safe fallback
    if band == "low":
        verbs = (low_verbs or []) or ["define", "identify", "list"]
    elif band == "med":
        verbs = (med_verbs or []) or ["apply", "demonstrate", "solve"]
    else:
        verbs = (high_verbs or []) or ["evaluate", "synthesize", "design"]

    STEMS = {
        "low": [
            "Which statement best **{verb}s** the idea related to **{topic}**?",
            "What does the term connected to **{topic}** primarily mean?",
            "Identify the choice that correctly **{verb}s** **{topic}**.",
        ],
        "med": [
            "Which action would you take to **{verb}** **{topic}**?",
            "Choose the example that correctly **{verb}s** **{topic}**.",
            "What is a sensible next step to **{verb}** **{topic}**?",
        ],
        "high": [
            "Which option best allows you to **{verb}** **{topic}**?",
            "Evaluate the approach that would **{verb}** **{topic}** most effectively.",
            "Which design would best **{verb}** **{topic}**?",
        ],
    }

    OPTION_SETS = {
        "low": [
            {"correct": "A clear, accurate statement of the key idea",
             "distractors": ["An unrelated fact", "A vague claim", "A contradictory statement"]},
            {"correct": "The definition that matches the concept",
             "distractors": ["A narrow example only", "A personal opinion", "An off-topic description"]},
            {"correct": "A concise identification of the concept",
             "distractors": ["A procedural step", "A tool choice", "A result from a different topic"]},
        ],
        "med": [
            {"correct": "An applied example that successfully uses the concept",
             "distractors": ["A restated definition", "A trivial detail", "An unrelated policy"]},
            {"correct": "A reasonable step that progresses the task",
             "distractors": ["A step from a different process", "A redundant action", "A goal with no action"]},
            {"correct": "A practical choice that would work in practice",
             "distractors": ["A purely theoretical note", "A historical aside", "A conflicting requirement"]},
        ],
        "high": [
            {"correct": "A justified option with clear criteria and trade-offs",
             "distractors": ["A superficial claim", "A one-line summary", "A choice without rationale"]},
            {"correct": "A design that optimizes constraints and objectives",
             "distractors": ["A workaround that ignores constraints", "A non-comparable option", "An anecdotal preference"]},
            {"correct": "An evaluation that weighs evidence and impact",
             "distractors": ["An assertion with no evidence", "A definition only", "An unrelated measurement"]},
        ],
    }

    kw = harvest_keywords(st.session_state.get("source_text", ""), k=6)

    def add_keywords(distractors):
        if not kw:
            return distractors
        extra = []
        for kword in kw[:3]:
            extra.append(f"A detail focusing on {kword}")
        return (distractors + extra)[:max(3, len(distractors))]

    out = []
    used = set()
    stems = itertools.cycle(STEMS[band])
    banks = itertools.cycle(OPTION_SETS[band])

    for i in range(n):
        verb = verbs[i % len(verbs)]
        stem_tpl = next(stems)
        stem = stem_tpl.format(verb=verb, topic=topic_text)
        bank = next(banks).copy()
        bank["distractors"] = add_keywords(bank["distractors"])

        options = [bank["correct"], *bank["distractors"][:3]]
        random.shuffle(options)
        correct_idx = options.index(bank["correct"])

        sig = (stem, bank["correct"])
        if sig in used:
            random.shuffle(options)
            correct_idx = options.index(bank["correct"])
        used.add(sig)

        out.append({"stem": stem, "options": options, "correct": correct_idx})

    st.session_state.mcqs = out


def export_mcqs_docx(mcqs):
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.add_heading("Knowledge MCQs", level=0)
    for i, q in enumerate(mcqs, 1):
        doc.add_heading(f"Q{i}", level=1)
        doc.add_paragraph(q["stem"])
        labels = ["A", "B", "C", "D"]
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{labels[j]}. {opt}")
        ans = labels[q["correct"]]
        p = doc.add_paragraph(f"Answer: {ans}")
        p.style.font.size = Pt(10)
    buf = io.BytesIO()
    doc.save(buf); buf.seek(0)
    return buf.getvalue()


def export_mcqs_txt(mcqs):
    labels = ["A", "B", "C", "D"]
    lines = []
    for i, q in enumerate(mcqs, 1):
        lines.append(f"Q{i}: {q['stem']}")
        for j, opt in enumerate(q["options"]):
            lines.append(f"  {labels[j]}. {opt}")
        lines.append(f"Answer: {labels[q['correct']]}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")


# --------------------------- ACTIVITIES GENERATOR ---------------------------

def generate_activities(n, minutes, group_label, topic, low_verbs, med_verbs, high_verbs):
    verbs = [*(low_verbs or []), *(med_verbs or []), *(high_verbs or [])]
    if not verbs:
        verbs = ["discuss", "apply", "evaluate"]
    t = (topic or "").strip() or "today’s content"

    templates = [
        lambda v: [
            f"In your {group_label.lower()}, {v} the key idea in {t}.",
            "Identify two examples from the uploaded material or your notes.",
            "Prepare a 1-minute share-out."
        ],
        lambda v: [
            f"Create a quick diagram/flow of how you would {v} {t}.",
            "Annotate with 3–4 keywords.",
            "Trade with another group and give one piece of feedback."
        ],
        lambda v: [
            f"Write two quiz questions that require learners to {v} {t}.",
            "Swap with neighbours and answer each other’s questions.",
            "As a class, discuss common answer patterns."
        ],
    ]

    acts = []
    for i in range(n):
        v = verbs[i % len(verbs)]
        steps = templates[i % len(templates)](v)
        acts.append({
            "title": f"{v.capitalize()} — {t}",
            "minutes": minutes,
            "group": group_label,
            "steps": steps
        })
    st.session_state.activities = acts


def export_activities_docx(acts):
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.add_heading("Skills Activities", level=0)
    for i, a in enumerate(acts, 1):
        doc.add_heading(f"Activity {i}: {a['title']}", level=1)
        p = doc.add_paragraph(f"Time: {a['minutes']} min  |  Group: {a['group']}")
        p.style.font.size = Pt(11)
        for j, step in enumerate(a["steps"], 1):
            doc.add_paragraph(f"{j}. {step}")
    buf = io.BytesIO(); doc.save(buf); buf.seek(0)
    return buf.getvalue()


def export_activities_txt(acts):
    lines = ["Skills Activities", ""]
    for i, a in enumerate(acts, 1):
        lines.append(f"Activity {i}: {a['title']}")
        lines.append(f"Time: {a['minutes']} min  |  Group: {a['group']}")
        for j, step in enumerate(a["steps"], 1):
            lines.append(f"{j}. {step}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")


# --------------------------- SIDEBAR (UPLOAD & CONTEXT) ---------------------------

with st.sidebar:
    st.image("adi_logo.png", width=160, caption=None, use_container_width=False)
    st.markdown("### Upload (optional)")
    f = st.file_uploader("Drag and drop file here", type=["txt", "docx", "pptx", "pdf"])

    if f is not None:
        with st.spinner("Scanning file…"):
            text = ""
            try:
                if f.type == "text/plain":
                    text = f.read().decode("utf-8", errors="ignore")
                elif f.name.lower().endswith(".docx"):
                    from docx import Document
                    d = Document(f)
                    text = "\n".join(p.text for p in d.paragraphs)
                elif f.name.lower().endswith(".pptx"):
                    from pptx import Presentation
                    p = Presentation(f)
                    parts = []
                    for s in p.slides:
                        for shp in s.shapes:
                            if hasattr(shp, "text"): parts.append(shp.text)
                    text = "\n".join(parts)
                elif f.name.lower().endswith(".pdf"):
                    import fitz  # PyMuPDF
                    pdf = fitz.open(stream=f.read(), filetype="pdf")
                    parts = [page.get_text() for page in pdf]
                    text = "\n".join(parts)
            except Exception:
                text = ""
            st.session_state.source_text = text
        try:
            st.toast(f"Uploaded: {f.name}", icon="✅")
        except Exception:
            st.success(f"Uploaded: {f.name}")

    st.markdown("### Course details")
    st.session_state.course = st.selectbox("Course name", [
        "GE4-IPM — Integrated Project & Materials Mgmt in Defense Technology",
        "CT4-COM — Computation for Chemical Technologists",
        "CT4-EMG — Explosives Manufacturing",
        "MT4-CMG — Composite Manufacturing",
    ], index=0)

    st.session_state.cohort = st.selectbox("Class / Cohort", [
        "D1-C01", "D1-M01", "D1-M02", "D2-C01", "D2-M01"
    ], index=0)

    st.session_state.instructor = st.selectbox("Instructor name", [
        "Daniel", "Ghamza Labeeb", "Abdulmalik", "Gerhard", "Nerdeen Tariq", "Dari"
    ], index=0)

    st.markdown("### Date")
    st.date_input("Date", value=date.today(), format="YYYY/MM/DD")

    st.markdown("### Context")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.lesson = st.number_input("Lesson", min_value=1, max_value=14, value=int(st.session_state.lesson), step=1)
    with c2:
        st.session_state.week = st.number_input("Week", min_value=1, max_value=14, value=int(st.session_state.week), step=1)


# --------------------------- MAIN LAYOUT ---------------------------

st.markdown(f"### ADI Builder — Lesson Activities & Questions")

topic = st.text_area("Topic / Outcome (optional)", placeholder="e.g., Integrated Project and ...", height=80)

# Active band by week (visual highlight)
wk = int(st.session_state.week)
active = "low"
if 5 <= wk <= 9: active = "med"
elif wk >= 10:  active = "high"

def band_container(title, key_band, verbs_key, default):
    css_class = "band active" if active == key_band else "band"
    st.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
    st.markdown(f"<div class='band-title'>{title}</div>", unsafe_allow_html=True)
    st.session_state[verbs_key] = st.multiselect(
        label="", options=default, default=st.session_state.get(verbs_key, default),
        key=f"{verbs_key}_ms"
    )
    st.markdown("</div>", unsafe_allow_html=True)

band_container("Low (Weeks 1–4) — Remember / Understand", "low", "lowverbs",
               ["define", "identify", "list", "recall", "describe", "label"])
band_container("Medium (Weeks 5–9) — Apply / Analyse", "med", "medverbs",
               ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"])
band_container("High (Weeks 10–14) — Evaluate / Create", "high", "highverbs",
               ["evaluate", "synthesize", "design", "justify", "critique", "create"])

tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])


# --------------------------- TAB: MCQs ---------------------------

with tabs[0]:
    st.query_params["tab"] = "mcqs"

    left, right = st.columns([1, 1])
    with left:
        how_many = st.selectbox("How many MCQs?", [5, 10, 15, 20], index=1, key="mcq_count_sb")
    with right:
        answer_key = st.checkbox("Include answer key in export", value=True, key="include_ans_key")

    if st.button("Generate from verbs/topic", key="gen_mcq_btn"):
        generate_mcqs(
            how_many, topic,
            st.session_state.lowverbs, st.session_state.medverbs, st.session_state.highverbs
        )
        try:
            st.toast(f"Generated {how_many} MCQs", icon="🧪")
        except Exception:
            pass

    # Render MCQs (editable)
    labels = ["A", "B", "C", "D"]
    if st.session_state.mcqs:
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        for i, q in enumerate(st.session_state.mcqs, 1):
            with st.container(border=True):
                st.markdown(f"**Q{i}**")
                q["stem"] = st.text_area("Question", value=q["stem"], key=f"stem_{i}")
                cols = st.columns(2)
                for j in range(4):
                    with cols[j % 2]:
                        q["options"][j] = st.text_input(f"{labels[j]}", value=q["options"][j], key=f"opt_{i}_{j}")
                q["correct"] = st.radio("Correct answer", labels, index=q["correct"], horizontal=True, key=f"ans_{i}")

        # Exports
        colx, coly = st.columns(2)
        with colx:
            st.download_button(
                "⬇️ Download DOCX (All MCQs)",
                data=export_mcqs_docx(st.session_state.mcqs),
                file_name=ctx_filename("ADI_Knowledge_MCQs") + ".docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_mcq_docx"
            )
        with coly:
            st.download_button(
                "⬇️ Download TXT (All MCQs)",
                data=export_mcqs_txt(st.session_state.mcqs),
                file_name=ctx_filename("ADI_Knowledge_MCQs") + ".txt",
                mime="text/plain",
                key="dl_mcq_txt"
            )
    else:
        st.info("Use **Generate from verbs/topic** to create MCQs.")


# --------------------------- TAB: SKILLS ACTIVITIES ---------------------------

with tabs[1]:
    st.query_params["tab"] = "skills"
    st.subheader("Skills Activities")

    a1, a2, a3, a4 = st.columns([1,1,1,1.2])
    with a1:
        acts_count = st.selectbox("How many activities?", [1, 2, 3], index=0, key="acts_count")
    with a2:
        minutes = st.selectbox("Minutes per activity", list(range(5, 61, 5)), index=1, key="acts_minutes")
    with a3:
        group_label = st.selectbox("Group size", ["Solo (1)", "Pairs (2)", "Triads (3)", "Groups of 4"], index=0, key="acts_group")

    with a4:
        if st.button("Generate from verbs/topic", key="gen_skills_btn"):
            generate_activities(
                acts_count, minutes, group_label, topic,
                st.session_state.lowverbs, st.session_state.medverbs, st.session_state.highverbs
            )
            try:
                st.toast(f"Generated {acts_count} activities", icon="🧩")
            except Exception:
                pass

    if st.session_state.activities:
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        for i, a in enumerate(st.session_state.activities, 1):
            with st.container(border=True):
                st.markdown(f"**Activity {i}: {a['title']}**")
                st.caption(f"Time: {a['minutes']} min  |  Group: {a['group']}")
                for j, step in enumerate(a["steps"], 1):
                    st.write(f"{j}. {step}")

        colx, coly = st.columns(2)
        with colx:
            st.download_button(
                "⬇️ Download DOCX (All Activities)",
                data=export_activities_docx(st.session_state.activities),
                file_name=ctx_filename("ADI_Skills_Activities") + ".docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_acts_docx"
            )
        with coly:
            st.download_button(
                "⬇️ Download TXT (All Activities)",
                data=export_activities_txt(st.session_state.activities),
                file_name=ctx_filename("ADI_Skills_Activities") + ".txt",
                mime="text/plain",
                key="dl_acts_txt"
            )
    else:
        st.info("Use **Generate from verbs/topic** to create activities.")


# --------------------------- TABS: PLACEHOLDERS ---------------------------

with tabs[2]:
    st.write("Revision — coming soon.")
with tabs[3]:
    st.write("Print summary — coming soon.")
