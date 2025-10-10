# app.py — ADI Builder (stable baseline)
import datetime as dt
from io import BytesIO

import streamlit as st
from docx import Document

# ---------- Page config (must be first Streamlit call) ----------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="🎓",
                   layout="wide")

BUILD_TAG = "2025-10-10 • stable-baseline"

# ---------- Safe defaults for session_state ----------
def ss_default(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

# Single source of truth for keys
ss_default("topic", "")
ss_default("course", "GE4-IPM — Integrated Project & Materials Management")
ss_default("cohort", "D1-C01")
ss_default("instructor", "Daniel")
ss_default("date", dt.date.today().isoformat())
ss_default("lesson", 1)
ss_default("week", 1)

# Verb selections
ss_default("verbs_low", ["define", "identify", "list"])
ss_default("verbs_med", ["apply", "demonstrate", "solve"])
ss_default("verbs_high", ["evaluate", "synthesize", "design"])

# Generated content
ss_default("mcqs", [])
ss_default("skills", [])
ss_default("revision", [])

# ---------- Styling ----------
ADI_GREEN = "#153a27"
BAND_BORDER = "#245a34"
LOW_BG   = "#cfe8d9"  # light green
MED_BG   = "#f8e6c9"  # light sand
HIGH_BG  = "#dfe6ff"  # light blue

st.markdown(f"""
<style>
/* Title banner */
.adi-banner {{
  background:{ADI_GREEN};
  color:white;
  padding:10px 16px;
  border-radius:8px;
  font-weight:600;
  letter-spacing:.2px;
  margin-bottom:12px;
}}

/* Verb bands */
.band {{
  border:1px solid {BAND_BORDER};
  border-radius:8px;
  padding:10px;
  margin:8px 0 6px 0;
}}
.band.low.active   {{ background:{LOW_BG};  }}
.band.med.active   {{ background:{MED_BG};  }}
.band.high.active  {{ background:{HIGH_BG}; }}

/* Chips (multiselect pills) */
[data-baseweb="tag"] {{
  border-radius:10px !important;
  padding:2px 8px !important;
}}
/* Pointer & hover affordances */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button {{
  cursor: pointer !important;
}}
div[data-testid="stFileUploaderDropzone"] {{
  border:2px dashed {BAND_BORDER} !important;
  background:#f8faf9;
}}
div[data-testid="stFileUploaderDropzone"]:hover {{
  box-shadow: inset 0 0 0 3px {BAND_BORDER} !important;
}}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {{
  box-shadow: inset 0 0 0 2px {BAND_BORDER} !important;
}}
/* Sidebar cards */
.block-container {{
  padding-top: 12px;
}}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
cols = st.columns([1, 8, 1.5])
with cols[0]:
    try:
        st.image("adi_logo.png", width=120)
    except Exception:
        pass
with cols[1]:
    st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>',
                unsafe_allow_html=True)
with cols[2]:
    st.caption(f"Build: {BUILD_TAG}")

# ---------- Uploader + Course Details (left) ----------
left, right = st.columns([1.2, 2.4], gap="large")

with left:
    st.subheader("Upload (optional)")
    uploaded = st.file_uploader("Drag and drop file here",
                                type=["txt", "docx", "pptx", "pdf"],
                                help="Limit 200MB / file", label_visibility="collapsed")
    if uploaded is not None:
        st.success(f"Uploaded: **{uploaded.name}**")

    st.checkbox("Deep scan source (slower, better coverage)", value=False)

    st.subheader("Course details")
    st.selectbox("Course name", [
        "GE4-IPM — Integrated Project & Materials Management",
        "GE4-EPM — Defense Tech: Experiments/QM/Inspection",
        "GE4-MRO — Military Vehicle & Aircraft MRO",
    ], key="course")

    st.selectbox("Class / Cohort", ["D1-C01", "D1-M01", "D2-C01"], key="cohort")
    st.selectbox("Instructor name", [
        "Daniel", "Dr. Mashael", "Noura Aldossari", "Ahmed Albader", "Michail",
        "Myra", "Sultan", "Chetan"
    ], key="instructor")

    st.date_input("Date", value=dt.date.fromisoformat(st.session_state["date"]),
                  key="date")

    lc1, lc2 = st.columns(2)
    with lc1:
        st.number_input("Lesson", min_value=1, max_value=14, step=1, key="lesson")
    with lc2:
        st.number_input("Week", min_value=1, max_value=14, step=1, key="week")

# ---------- Topic + Verb bands (right) ----------
with right:
    st.subheader("Topic / Outcome (optional)")
    st.text_area("", key="topic",
                 placeholder="e.g., Integrated Project and …", height=80,
                 label_visibility="collapsed")

    # Helper: band renderer
    def verb_band(title, key, bg_class):
        selected = st.session_state[key]
        # Determine active class by current week
        wk = st.session_state["week"]
        active = (
            (bg_class == "low"  and 1 <= wk <= 4)  or
            (bg_class == "med"  and 5 <= wk <= 9)  or
            (bg_class == "high" and wk >= 10)
        )
        klass = f"band {bg_class}" + (" active" if active else "")
        st.markdown(f'<div class="{klass}"><strong>{title}</strong></div>', unsafe_allow_html=True)
        st.multiselect(" ", options=ALL_VERBS[key], default=selected, key=key, label_visibility="collapsed")

    # Verb dictionary for band rendering
    ALL_VERBS = {
        "verbs_low":  ["define", "identify", "list", "describe", "recall"],
        "verbs_med":  ["apply", "demonstrate", "solve", "analyze", "compare"],
        "verbs_high": ["evaluate", "synthesize", "design", "justify", "create"]
    }

    verb_band("Low (Weeks 1–4) — Remember / Understand", "verbs_low", "low")
    verb_band("Medium (Weeks 5–9) — Apply / Analyse", "verbs_med", "med")
    verb_band("High (Weeks 10–14) — Evaluate / Create", "verbs_high", "high")

    st.caption("ADI policy: 1–3 per lesson • 5–9 Medium • 10–14 High")

    # ---------- Tabs ----------
    tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

    # ----- MCQs tab -----
    with tabs[0]:
        # How many MCQs
        cols_mcq = st.columns([1, 2, 1])
        with cols_mcq[0]:
            n = st.selectbox("How many MCQs?", [5, 8, 10, 12, 15, 20], index=2, key="how_many")
        with cols_mcq[1]:
            st.toggle("Answer key", value=True, key="ak")

        if st.button("Generate from verbs/topic", key="btn_gen_mcq"):
            st.session_state["mcqs"] = generate_mcqs(n,
                                                     st.session_state["topic"],
                                                     st.session_state["verbs_low"],
                                                     st.session_state["verbs_med"],
                                                     st.session_state["verbs_high"])

        mcqs = st.session_state["mcqs"]
        if not mcqs:
            st.info("No questions yet. Click **Generate from verbs/topic**.")
        else:
            for i, q in enumerate(mcqs, start=1):
                st.write(f"**Q{i}**")
                q["stem"] = st.text_area(f"Question {i} stem",
                                         q["stem"], key=f"qstem_{i}", height=60)
                cols_qa = st.columns(2)
                with cols_qa[0]:
                    q["A"] = st.text_input("A", q["A"], key=f"qa_{i}")
                    q["B"] = st.text_input("B", q["B"], key=f"qb_{i}")
                with cols_qa[1]:
                    q["C"] = st.text_input("C", q["C"], key=f"qc_{i}")
                    q["D"] = st.text_input("D", q["D"], key=f"qd_{i}")
                if st.session_state["ak"]:
                    q["correct"] = st.radio("Correct answer", ["A","B","C","D"],
                                            index=["A","B","C","D"].index(q["correct"]),
                                            key=f"qr_{i}", horizontal=True)
                st.divider()

            # Downloads
            txt_bytes = mcqs_to_txt(mcqs).encode("utf-8")
            st.download_button("⬇️ Download TXT (All MCQs)", txt_bytes,
                               file_name="ADI_MCQ_All.txt", mime="text/plain",
                               key="dl_txt_all")

            docx_bytes = mcqs_to_docx_bytes(mcqs)
            st.download_button("⬇️ Download DOCX (All MCQs)", docx_bytes,
                               file_name="ADI_MCQ_All.docx",
                               mime=("application/vnd.openxmlformats-"
                                     "officedocument.wordprocessingml.document"),
                               key="dl_docx_all")

    # ----- Skills tab -----
    with tabs[1]:
        if st.button("Generate skills activities", key="btn_gen_skills"):
            st.session_state["skills"] = generate_skills(st.session_state["verbs_med"],
                                                         st.session_state["lesson"],
                                                         st.session_state["week"])
        if not st.session_state["skills"]:
            st.info("No activities yet. Click **Generate skills activities**.")
        else:
            for i, a in enumerate(st.session_state["skills"], start=1):
                st.markdown(f"**Activity {i}.** {a}")

    # ----- Revision tab -----
    with tabs[2]:
        if st.button("Generate revision prompts", key="btn_gen_rev"):
            st.session_state["revision"] = generate_revision(st.session_state["verbs_low"],
                                                             st.session_state["verbs_high"])
        if not st.session_state["revision"]:
            st.info("No revision prompts yet. Click **Generate revision prompts**.")
        else:
            for i, r in enumerate(st.session_state["revision"], start=1):
                st.markdown(f"**R{i}.** {r}")

    # ----- Print summary tab -----
    with tabs[3]:
        st.subheader("Print summary")
        st.write(f"**Course:** {st.session_state['course']}")
        st.write(f"**Cohort:** {st.session_state['cohort']}  •  **Instructor:** {st.session_state['instructor']}")
        st.write(f"**Date:** {st.session_state['date']}  •  **Lesson:** {st.session_state['lesson']}  •  **Week:** {st.session_state['week']}")
        st.write(f"**Topic:** {st.session_state['topic'] or '—'}")
        st.write("**Low verbs:**", ", ".join(st.session_state["verbs_low"]) or "—")
        st.write("**Medium verbs:**", ", ".join(st.session_state["verbs_med"]) or "—")
        st.write("**High verbs:**", ", ".join(st.session_state["verbs_high"]) or "—")

        if st.session_state["mcqs"]:
            st.markdown("### MCQs")
            for i, q in enumerate(st.session_state["mcqs"], start=1):
                st.write(f"**Q{i}.** {q['stem']}")
                st.write(f"A. {q['A']}  |  B. {q['B']}  |  C. {q['C']}  |  D. {q['D']}")
                st.caption(f"Answer: {q['correct']}")

# ---------- Generators ----------
def generate_mcqs(n, topic, low, med, high):
    """Simple, safe generator (no external calls)."""
    seeds = (high or med or low or ["analyze"])
    qs = []
    for i in range(n):
        v = seeds[i % len(seeds)]
        stem = topic.strip() or "Explain the role of inspection in quality management."
        stem = f"Using the verb **{v}**, {stem}"
        qs.append({
            "stem": stem,
            "A": "To verify conformance",   # keep placeholders clear & editable
            "B": "To set company policy",
            "C": "To hire staff",
            "D": "To control budgets",
            "correct": "A"
        })
    return qs

def mcqs_to_txt(mcqs):
    lines = []
    for i, q in enumerate(mcqs, start=1):
        lines.append(f"Q{i}. {q['stem']}")
        lines.append(f"A. {q['A']}")
        lines.append(f"B. {q['B']}")
        lines.append(f"C. {q['C']}")
        lines.append(f"D. {q['D']}")
        lines.append(f"Answer: {q['correct']}")
        lines.append("")
    return "\n".join(lines)

def mcqs_to_docx_bytes(mcqs):
    doc = Document()
    doc.add_heading("ADI MCQs", level=1)
    for i, q in enumerate(mcqs, start=1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        doc.add_paragraph(f"A. {q['A']}")
        doc.add_paragraph(f"B. {q['B']}")
        doc.add_paragraph(f"C. {q['C']}")
        doc.add_paragraph(f"D. {q['D']}")
        doc.add_paragraph(f"Answer: {q['correct']}")
        doc.add_paragraph("")
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

def generate_skills(verbs_med, lesson, week):
    if not verbs_med:
        verbs_med = ["apply"]
    prompts = []
    for i, v in enumerate(verbs_med, start=1):
        prompts.append(f"Week {week}, Lesson {lesson}: In teams of 3, **{v}** the method to a real part "
                       f"from your project; produce a 1-page evidence sheet.")
    return prompts

def generate_revision(verbs_low, verbs_high):
    prompts = []
    for v in (verbs_low or ["define"]):
        prompts.append(f"Flash-cards: **{v}** five key terms from this module.")
    for v in (verbs_high or ["evaluate"]):
        prompts.append(f"Exit ticket: **{v}** your process and justify improvements.")
    return prompts
