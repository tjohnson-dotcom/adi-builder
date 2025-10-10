# app.py — ADI Builder (palette chips + week highlight + skills & MCQs)
# Build: 2025-10-10

from __future__ import annotations
import io
from typing import List, Dict, Tuple
from datetime import date

import streamlit as st

# Optional DOCX export
try:
    from docx import Document  # type: ignore
    HAVE_DOCX = True
except Exception:
    HAVE_DOCX = False

# ── 1) Page config (must be first Streamlit call)
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🧩", layout="wide")

# ── 2) Query param helper (sticky tab bookmark)
def get_qp():
    try:
        return st.query_params
    except Exception:
        # Fallback for older Streamlit
        return st.experimental_get_query_params()

def set_qp(**kwargs):
    try:
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**kwargs)

qp = get_qp()
if "tab" not in qp:
    set_qp(tab="mcq")

# ── 3) Theme & CSS (ADI palette + chips per band + dashed uploader + hover)
st.markdown("""
<style>
:root{
  --adi:#245a34;        /* deep green */
  --adi-dark:#153a27;   /* banner */
  --low-bg:#cfe8d9;  --low-text:#0e3e2a;
  --med-bg:#f8e6c9;  --med-text:#5a3b00;
  --high-bg:#dfe6ff; --high-text:#0e2a73;
  --ring:#245a34;
}

.block-container{ padding-top: 0.6rem; }

/* Sticky banner */
.adi-banner{
  background: var(--adi-dark);
  color: #fff;
  padding: 10px 14px;
  border-radius: 8px;
  font-weight: 600;
  margin: 4px 0 12px 0;
  position: sticky; top:0; z-index: 10;
}

/* Band frame */
.band{ border: 2px solid var(--adi); border-radius: 10px; padding: 8px 12px; margin: 10px 0 6px 0; }
.band.active{ box-shadow: 0 0 0 3px rgba(36,90,52,.18) inset; }

/* Palette chips per band */
.low-band   div[data-baseweb="tag"]{   background: var(--low-bg)  !important; color: var(--low-text)  !important; }
.med-band   div[data-baseweb="tag"]{   background: var(--med-bg)  !important; color: var(--med-text)  !important; }
.high-band  div[data-baseweb="tag"]{   background: var(--high-bg) !important; color: var(--high-text) !important; }

/* Drag-and-drop dashed */
div[data-testid="stFileUploaderDropzone"]{
  border: 2px dashed var(--adi) !important; border-radius: 10px !important; background: #fff;
}
div[data-testid="stFileUploaderDropzone"]:hover{ box-shadow: 0 0 0 3px var(--adi) inset !important; }

/* Pointer+hover */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button { cursor: pointer !important; }
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover,
button[kind]:hover, button:hover { box-shadow: 0 0 0 2px var(--ring) inset !important; }

/* Focus ring */
:focus-visible{ outline: 2px solid var(--ring) !important; outline-offset: 2px; }

/* Tabs accent */
.stTabs [data-baseweb="tab-list"]{ gap: 6px; }
.stTabs [data-baseweb="tab"]{ padding: 6px 10px; border-radius: 8px; }
button[role="tab"][aria-selected="true"]{ border-bottom: 3px solid var(--adi) !important; }

/* Card look for generated items */
.gen-card{ padding: 10px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; }
.hint { color:#6b7280; font-size: 12px; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

# ── 4) Static data
LOW_VERBS  = ["define","identify","list","describe","label","recall"]
MED_VERBS  = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","critique","create"]

COURSES = [
    "GE4-IPM — Integrated Project & Materials Mgmt in Defense Technology",
    "GE4-EPM — Defense Technology Practices",
    "GE4-MRO — Military Vehicle & Aircraft MRO",
    "CT4-COM — Computation for Chemical Technologists",
    "CT4-EMG — Explosives Manufacturing",
    "MT4-CMG — Composite Manufacturing",
    "MT4-CAD — Computer Aided Design",
    "MT4-MAE — Machine Elements",
    "EE4-MFC — Electrical Materials",
    "EE4-PMG — PCB Manufacturing",
    "EE4-PCT — Power Circuits & Transmission",
]
COHORTS = ["D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05","D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"]
INSTRUCTORS = ["Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen Tariq",
               "Dari","Ghamza Labeeb","Michail","Meshari","Mohammed Alwuthaylah","Myra",
               "Meshal Algurabi","Ibrahim Alrawaili","Khalil","Salem","Chetan","Yasser",
               "Ahmed Albader","Muath","Sultan","Dr. Mashael","Noura Aldossari","Daniel"]

# ── 5) Session defaults
ss = st.session_state
ss.setdefault("course", COURSES[0])
ss.setdefault("cohort", COHORTS[0])
ss.setdefault("instructor", "Daniel")
ss.setdefault("lesson", 1)
ss.setdefault("week", 1)
ss.setdefault("topic", "")
ss.setdefault("verbs_low",  ["define","identify","list"])
ss.setdefault("verbs_med",  ["apply","demonstrate","solve"])
ss.setdefault("verbs_high", ["evaluate","synthesize","design"])
ss.setdefault("mcqs", [])
ss.setdefault("skills", [])
ss.setdefault("active_tab", qp.get("tab", ["mcq"])[0] if isinstance(qp.get("tab"), list) else qp.get("tab", "mcq"))

# ── 6) Sidebar (logo safe, upload toast, course controls)
with st.sidebar:
    try:
        st.image("adi_logo.png", width=96)
    except Exception:
        st.caption("ADI")

    st.subheader("Upload (optional)")
    up = st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"])
    if up is not None:
        try:
            st.toast(f"Uploaded: {up.name}", icon="✅")
        except Exception:
            st.success(f"Uploaded: {up.name}")

    st.toggle("Deep scan source (slower, better coverage)", value=False, key="deep_scan")

    st.markdown("---")
    st.subheader("Course details")
    ss.course = st.selectbox("Course name", COURSES, index=COURSES.index(ss.course) if ss.course in COURSES else 0, key="sb_course")
    ss.cohort = st.selectbox("Class / Cohort", COHORTS, index=COHORTS.index(ss.cohort) if ss.cohort in COHORTS else 0, key="sb_cohort")
    ss.instructor = st.selectbox("Instructor name", INSTRUCTORS, index=INSTRUCTORS.index(ss.instructor) if ss.instructor in INSTRUCTORS else INSTRUCTORS.index("Daniel"), key="sb_instr")

    st.date_input("Date", value=date.today(), key="the_date")
    c1, c2 = st.columns(2)
    with c1:
        ss.lesson = st.number_input("Lesson", min_value=1, max_value=30, value=int(ss.lesson), step=1, key="sb_lesson")
    with c2:
        ss.week = st.number_input("Week", min_value=1, max_value=14, value=int(ss.week), step=1, key="sb_week")

# ── 7) Top banner
st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

# ── 8) Topic
ss.topic = st.text_area("Topic / Outcome (optional)", value=ss.topic, placeholder="e.g., Integrated Project and …")

# ── 9) Band helper (palette chips + auto-highlight by week/selection)
def band(title: str, verbs: List[str], state_key: str, help_txt: str, week_range: Tuple[int, int], wrap_class: str):
    selected = ss.get(state_key, [])
    in_window = week_range[0] <= int(ss.week) <= week_range[1]
    klass = "band active" if (selected or in_window) else "band"
    st.markdown(f'<div class="{klass}"><strong>{title}</strong></div>', unsafe_allow_html=True)
    # palette chip wrapper
    st.markdown(f'<div class="{wrap_class}">', unsafe_allow_html=True)
    ss[state_key] = st.multiselect(help_txt, options=verbs, default=selected, key=f"ms_{state_key}")
    st.markdown('</div>', unsafe_allow_html=True)

# ── 10) Render bands
band("Low (Weeks 1–4) — Remember / Understand", LOW_VERBS,  "verbs_low",  "Low verbs",  (1,4),  "low-band")
band("Medium (Weeks 5–9) — Apply / Analyse",     MED_VERBS,  "verbs_med",  "Medium verbs",(5,9), "med-band")
band("High (Weeks 10–14) — Evaluate / Create",   HIGH_VERBS, "verbs_high", "High verbs", (10,14),"high-band")

# Empty-state hint
if not (ss.verbs_low or ss.verbs_med or ss.verbs_high):
    st.markdown('<div class="hint">Tip: pick at least one verb from any band to enable better generation.</div>', unsafe_allow_html=True)

st.markdown("---")

# ── 11) Tabs with light bookmark
labels = ["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"]
tab_key_map = {"mcq":0, "skills":1, "rev":2, "print":3}
active_idx = tab_key_map.get(ss.active_tab, 0)
tabs = st.tabs(labels)

def set_active_tab(key: str):
    ss.active_tab = key
    set_qp(tab=key)

# ── 12) MCQs TAB
with tabs[0]:
    if active_idx == 0: set_active_tab("mcq")
    cA, cB = st.columns([1,1])
    with cA:
        mcq_qty = st.selectbox("How many MCQs?", [5,10,15,20], index=1, key="mcq_qty")
    with cB:
        with_key = st.checkbox("Answer key", value=True, key="mcq_key")

    if st.button("Generate from verbs/topic", key="btn_generate_mcq"):
        topic = ss.topic.strip() or "today’s topic"
        # simple, safe MCQ bank using selected verbs (stem mentions topic)
        ss.mcqs = []
        for i in range(int(mcq_qty)):
            stem = f"Which option best relates to {topic}?"
            opts = ["To verify conformance", "To set company policy", "To hire staff", "To control budgets"]
            ss.mcqs.append({"stem": stem, "options": opts[:], "correct": 0 if with_key else None})
        try:
            st.toast("MCQs generated.", icon="✅")
        except Exception:
            st.success("MCQs generated.")

    for i, q in enumerate(ss.mcqs, start=1):
        with st.container():
            st.markdown(f"**Q{i}**")
            q["stem"] = st.text_area("Question", value=q["stem"], key=f"stem_{i}")
            cols = st.columns(2)
            for j in range(4):
                label = chr(65+j)
                with cols[j%2]:
                    q["options"][j] = st.text_input(f"{label}", value=q["options"][j], key=f"opt_{i}_{j}")
            if with_key:
                q["correct"] = st.radio("Correct", options=[0,1,2,3], format_func=lambda x: chr(65+x), index=q.get("correct") or 0, horizontal=True, key=f"ans_{i}")

    # Downloads
    def export_txt(qs: List[Dict]) -> bytes:
        out = []
        for i, q in enumerate(qs, start=1):
            out.append(f"Q{i}. {q['stem']}")
            for j, opt in enumerate(q["options"]):
                out.append(f"  {chr(65+j)}. {opt}")
            if q.get("correct") is not None:
                out.append(f"  Answer: {chr(65+q['correct'])}")
            out.append("")
        return "\n".join(out).encode("utf-8")

    def export_docx(qs: List[Dict]) -> bytes | None:
        if not HAVE_DOCX: return None
        doc = Document()
        doc.add_heading("Knowledge MCQs", level=1)
        for i, q in enumerate(qs, start=1):
            doc.add_paragraph(f"Q{i}. {q['stem']}")
            for j, opt in enumerate(q["options"]):
                doc.add_paragraph(f"{chr(65+j)}. {opt}")
            if q.get("correct") is not None:
                doc.add_paragraph(f"Answer: {chr(65+q['correct'])}")
            doc.add_paragraph("")
        bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

    if ss.mcqs:
        c1,c2,c3 = st.columns(3)
        with c1:
            txt_q1 = export_txt([ss.mcqs[0]])
            st.download_button("📥 Download TXT (Q1)", data=txt_q1, file_name="ADI_MCQ_Q1.txt", key="dl_txt_q1")
        with c2:
            txt_all = export_txt(ss.mcqs)
            st.download_button("📥 Download TXT (All MCQs)", data=txt_all, file_name="ADI_MCQ_All.txt", key="dl_txt_all")
        with c3:
            if HAVE_DOCX:
                docx_all = export_docx(ss.mcqs)
                st.download_button("📥 Download DOCX (All MCQs)", data=docx_all, file_name="ADI_MCQ_All.docx", key="dl_docx_all")
            else:
                st.info("Install python-docx for DOCX export. TXT ready above.")

# ── 13) SKILLS TAB
with tabs[1]:
    if active_idx == 1: set_active_tab("skills")
    st.subheader("Skills Activities")
    c1,c2,c3 = st.columns(3)
    with c1:
        n_skills = st.selectbox("How many activities?", [1,2,3], index=0, key="skills_count")
    with c2:
        minutes = st.selectbox("Minutes per activity", list(range(5,65,5)), index=1, key="skills_minutes")
    with c3:
        group = st.selectbox("Group size", ["Solo (1)","Pairs (2)","Triads (3)","Groups of 4"], index=0, key="skills_group")

    if st.button("Generate Skills", key="btn_generate_skills"):
        verbs_all = ss.verbs_low + ss.verbs_med + ss.verbs_high
        hint = f" using verbs: {', '.join(verbs_all)}" if verbs_all else ""
        topic = ss.topic.strip() or "today’s topic"
        ss.skills = [
            f"Activity {i+1}: In {group}, spend {minutes} minutes to **apply** to {topic}{hint}. Capture outcomes and share."
            for i in range(int(n_skills))
        ]
        try:
            st.toast("Skills generated.", icon="✅")
        except Exception:
            st.success("Skills generated.")

    if not (ss.verbs_low or ss.verbs_med or ss.verbs_high):
        st.markdown('<div class="hint">Tip: selecting verbs will make the activities more specific.</div>', unsafe_allow_html=True)

    for i, line in enumerate(ss.skills, start=1):
        st.text_input(f"Skill {i}", value=line, key=f"skill_{i}")

    if ss.skills:
        skills_txt = ("\n".join(ss.skills)).encode("utf-8")
        st.download_button("📥 Download Skills (TXT)", data=skills_txt, file_name="ADI_Skills.txt", key="dl_skills_txt")

# ── 14) REVISION TAB (placeholder)
with tabs[2]:
    if active_idx == 2: set_active_tab("rev")
    st.info("Revision area: quick checkpoints & mini quizzes (coming soon).")

# ── 15) PRINT SUMMARY TAB (placeholder)
with tabs[3]:
    if active_idx == 3: set_active_tab("print")
    st.markdown("**Print Summary** (preview)")
    st.write(f"**Course:** {ss.course}  \n**Cohort:** {ss.cohort}  \n**Instructor:** {ss.instructor}")
    st.write(f"**Week/Lesson:** W{ss.week} / L{ss.lesson}")
    st.write(f"**Topic:** {ss.topic or '—'}")
    st.write("**Selected verbs**")
    st.write("- Low:", ", ".join(ss.verbs_low) or "—")
    st.write("- Medium:", ", ".join(ss.verbs_med) or "—")
    st.write("- High:", ", ".join(ss.verbs_high) or "—")
    st.write(f"**MCQs generated:** {len(ss.mcqs)}")
    st.write(f"**Skills generated:** {len(ss.skills)}")

# ── 16) Build tag
st.caption("Build: 2025-10-10 • palette-chips + sticky-tab")
