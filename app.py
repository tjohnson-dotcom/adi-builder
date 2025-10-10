# -----------------------------
# ADI Builder — Lesson Activities & Questions
# A single-file, stable Streamlit app
# -----------------------------
import datetime
import io
import random
from typing import List, Dict

import streamlit as st

# Optional DOCX export (graceful fallback if not installed)
try:
    from docx import Document
    from docx.shared import Pt
    HAVE_DOCX = True
except Exception:
    HAVE_DOCX = False


# -----------------------------
# Page & modern query params
# -----------------------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="🧭",
                   layout="wide")

def qp_get() -> Dict[str, str]:
    """Modern query params (no deprecations)."""
    return dict(st.query_params)

def qp_set(**kwargs):
    st.query_params.clear()
    for k, v in kwargs.items():
        st.query_params[k] = str(v)


# -----------------------------
# Defaults & safe state init (no writes after widgets)
# -----------------------------
VERBS_LOW  = ["define", "identify", "list", "label", "describe", "recall"]
VERBS_MED  = ["apply", "demonstrate", "solve", "analyze", "compare", "summarize"]
VERBS_HIGH = ["evaluate", "synthesize", "design", "create", "critique", "justify"]

COURSES = [
    "GE4-IPM — Integrated Project & Materials Management",
    "GE4-ELM — Engineering Logistics Management",
    "GE4-QA  — Quality Assurance",
]
COHORTS = ["D1-C01", "D1-C02", "D1-C03", "D2-C01", "D2-C02"]
INSTRUCTORS = ["Daniel", "Fatima", "Hassan", "Layla", "Noura"]

def init_state_once():
    ss = st.session_state
    # Single-run defaults (do NOT write after widgets are built)
    ss.setdefault("topic", "")
    ss.setdefault("course", COURSES[0])
    ss.setdefault("cohort", COHORTS[0])
    ss.setdefault("instructor", INSTRUCTORS[0])
    ss.setdefault("date", datetime.date.today())
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)

    ss.setdefault("verbs_low",  ["define", "identify", "list"])
    ss.setdefault("verbs_med",  ["apply", "demonstrate", "solve"])
    ss.setdefault("verbs_high", ["evaluate", "synthesize", "design"])

    ss.setdefault("how_many", 10)
    ss.setdefault("answer_key", True)

    ss.setdefault("mcqs", [])           # list of dicts {"stem","A","B","C","D","answer"}
    ss.setdefault("activities", [])     # list of dicts
    ss.setdefault("revision", [])       # list of strings

    # Remember last selected tab across reruns
    ss.setdefault("tab_index", 0)

init_state_once()


# -----------------------------
# Styles (palette + chips + dashed uploader + hover)
# -----------------------------
st.markdown("""
<style>
:root{
  --adi-green:#173E2C;      /* top banner */
  --low:#cfe8d9;            /* light green */
  --med:#f8e6c9;            /* sand */
  --high:#dfe6ff;           /* light blue */
  --chip:#1f513a;           /* chip text bg */
}

/* Make the real sidebar a tad wider */
section[data-testid="stSidebar"]{ width:340px !important; }
section[data-testid="stSidebar"] > div{ padding-right:8px; }

/* Top banner */
.adi-banner{
  background:var(--adi-green);
  color:#fff; padding:10px 18px; border-radius:8px;
  font-weight:600; letter-spacing:.2px; margin-bottom:8px;
}

/* Verb bands */
.band{ border:2px solid #1f513a33; border-radius:8px; padding:8px 10px; margin:6px 0;}
.band.low     {background:var(--low);}
.band.med     {background:var(--med);}
.band.high    {background:var(--high);}
.band.active  {box-shadow:0 0 0 3px #1f513a55 inset;}

/* Multiselect chips look clickable */
div[data-testid="stMultiSelect"] button{ cursor:pointer !important; }
div[data-testid="stMultiSelect"] button:hover{
  box-shadow:0 0 0 2px #1f513a inset !important;
}

/* dashed drop zone */
div[data-testid="stFileUploaderDropzone"]{
  border:2px dashed #1f513a99 !important;
  background: #f9faf9;
}
div[data-testid="stFileUploaderDropzone"]:hover{
  box-shadow:0 0 0 3px #1f513a55 inset !important;
}

/* Buttons */
button[kind], .stButton>button{
  background: var(--adi-green) !important;
  color:#fff !important; border:0; border-radius:8px !important;
}
.stDownloadButton>button{
  background: var(--adi-green) !important;
  color:#fff !important; border-radius:8px !important;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Helpers
# -----------------------------
def week_band(week:int)->str:
    """Which band is 'active' given week."""
    if 1 <= week <= 4:  return "low"
    if 5 <= week <= 9:  return "med"
    return "high"

def safe_logo():
    col_logo = st.sidebar.container()
    try:
        # Provide your local logo path if available
        col_logo.image("adi_logo.png", width=140)
    except Exception:
        col_logo.markdown("**Academy of Defense Industries**")

def make_mcq_stem(verb:str, topic:str)->str:
    topic = topic.strip() or "the lesson topic"
    patterns = [
        f"Using the verb **{verb}**, which statement best relates to {topic}?",
        f"Which option correctly uses **{verb}** in the context of {topic}?",
        f"For {topic}, select the best example of **{verb}**.",
    ]
    return random.choice(patterns)

def generate_mcqs(how_many:int, topic:str, verbs:List[str], answer_key:bool=True)->List[Dict]:
    out=[]
    bank = [
        ("To verify conformance","To hire staff","To set company policy","To control budgets","A"),
        ("A reduction in scrap rate","A new paint color","An office plant","A brand slogan","A"),
        ("Record defects per batch","Paint the building","Order coffee","Organize a party","A"),
        ("Measure mean time between failures","Buy new uniforms","Add a company holiday","Update the logo","A"),
    ]
    for i in range(how_many):
        verb = random.choice(verbs or ["apply","analyze","design"])
        stem = make_mcq_stem(verb, topic)
        A,B,C,D,ans = random.choice(bank)
        out.append({"stem":stem,"A":A,"B":B,"C":C,"D":D,"answer":ans if answer_key else ""})
    return out

def generate_activities(n:int, minutes:int, group:str, topic:str)->List[Dict]:
    topic = topic.strip() or "today’s topic"
    templates = [
        "In small groups, **{group}**, create a quick sketch / flow showing {topic}.",
        "Pair up and **role-play** a scenario applying {topic} for {min} minutes.",
        "Individually, list five risks about {topic}, then share in **{group}**.",
        "Teams prepare a one-slide summary to **present** in {min} minutes on {topic}.",
    ]
    groups = {"Solo (1)":"solo","Pairs (2)":"pairs","Triads (3)":"triads","Group of 4":"groups of four"}
    gtxt = groups.get(group, group)
    out=[]
    for _ in range(n):
        t = random.choice(templates).format(group=gtxt, min=minutes, topic=topic)
        out.append({"task":t,"minutes":minutes,"group":group})
    return out

def generate_revision(topic:str, verbs:List[str])->List[str]:
    topic = topic.strip() or "the lesson"
    prompts = [
        f"Write a 3-sentence summary of {topic}.",
        f"Explain {topic} to a first-year student.",
        f"Create a quick checklist to **{random.choice(verbs or ['apply'])}** {topic}.",
    ]
    return prompts

def txt_download(label:str, filename:str, content:str):
    st.download_button(label, data=content.encode("utf-8"),
                       file_name=filename, mime="text/plain")

def mcqs_to_txt(mcqs:List[Dict])->str:
    lines=[]
    for i,q in enumerate(mcqs,1):
        lines += [f"Q{i}. {q['stem']}",
                  f"A. {q['A']}",
                  f"B. {q['B']}",
                  f"C. {q['C']}",
                  f"D. {q['D']}"]
        if q.get("answer"):
            lines.append(f"Answer: {q['answer']}")
        lines.append("")
    return "\n".join(lines)

def mcqs_to_docx(mcqs:List[Dict], title:str="MCQs"):
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.add_heading(title, level=1)
    for i,q in enumerate(mcqs,1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        doc.add_paragraph(f"A. {q['A']}")
        doc.add_paragraph(f"B. {q['B']}")
        doc.add_paragraph(f"C. {q['C']}")
        doc.add_paragraph(f"D. {q['D']}")
        if q.get("answer"):
            doc.add_paragraph(f"Answer: {q['answer']}")
        doc.add_paragraph("")
    buf = io.BytesIO()
    doc.save(buf); buf.seek(0)
    return buf


# -----------------------------
# Sidebar (sticky)
# -----------------------------
safe_logo()

st.sidebar.subheader("Upload (optional)")
uploaded = st.sidebar.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"], key="file_up")
if uploaded:
    st.sidebar.success(f"Uploaded **{uploaded.name}** ({uploaded.size/1024:.1f} KB)")
st.sidebar.checkbox("Deep scan source (slower, better coverage)", key="deep_scan")

st.sidebar.subheader("Course details")
st.session_state.course = st.sidebar.selectbox("Course name", COURSES, index=COURSES.index(st.session_state.course))
st.session_state.cohort = st.sidebar.selectbox("Class / Cohort", COHORTS, index=COHORTS.index(st.session_state.cohort))
st.session_state.instructor = st.sidebar.selectbox("Instructor name", INSTRUCTORS, index=INSTRUCTORS.index(st.session_state.instructor))
st.session_state.date = st.sidebar.date_input("Date", value=st.session_state.date)

c1, c2 = st.sidebar.columns(2)
with c1:
    st.session_state.lesson = st.number_input("Lesson", 1, 99, value=int(st.session_state.lesson), step=1, key="lesson_num")
with c2:
    st.session_state.week = st.number_input("Week", 1, 14, value=int(st.session_state.week), step=1, key="week_num")

# keep URL sticky
qp_set(week=st.session_state.week, lesson=st.session_state.lesson)


# -----------------------------
# Main banner + topic
# -----------------------------
st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

st.text_area("Topic / Outcome (optional)", key="topic",
             placeholder="e.g., Integrated Project and …")

# -----------------------------
# Verb bands (+ color highlight by week)
# -----------------------------
active = week_band(st.session_state.week)

def band(title:str, verbs:List[str], key:str, css_class:str):
    cls = f"band {css_class}" + (" active" if active == css_class else "")
    st.markdown(f'<div class="{cls}"><strong>{title}</strong></div>', unsafe_allow_html=True)
    return st.multiselect(f"{css_class.capitalize()} verbs", options=verbs,
                          default=st.session_state.get(key, []), key=key)

st.session_state.verbs_low  = band("Low (Weeks 1–4) — Remember / Understand", VERBS_LOW,  "verbs_low",  "low")
st.session_state.verbs_med  = band("Medium (Weeks 5–9) — Apply / Analyse",   VERBS_MED,  "verbs_med",  "med")
st.session_state.verbs_high = band("High (Weeks 10–14) — Evaluate / Create", VERBS_HIGH, "verbs_high", "high")

# -----------------------------
# Tabs
# -----------------------------
tab_names = ["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"]
tabs = st.tabs(tab_names)
# keep index stable
for i, t in enumerate(tabs):
    if i == st.session_state.tab_index:
        pass
st.session_state.tab_index = 0  # default to first on build

# ---------- Tab 0: MCQs ----------
with tabs[0]:
    st.caption("ADI policy: 1–3 per lesson • 5–9 Medium • 10–14 High")
    left, right = st.columns([0.35, 0.65])

    with left:
        st.session_state.how_many = st.selectbox("How many MCQs?",
                                                 [5, 10, 12, 15, 20],
                                                 index=[5,10,12,15,20].index(st.session_state.how_many),
                                                 key="how_many_sel")
        st.session_state.answer_key = st.checkbox("Answer key", value=st.session_state.answer_key, key="ans_key")

        if st.button("Generate from verbs/topic", key="btn_gen_mcq"):
            # pick pool: if week selects band, bias that band
            if   active == "low":  pool = st.session_state.verbs_low
            elif active == "med":  pool = st.session_state.verbs_med
            else:                  pool = st.session_state.verbs_high
            verbs = pool or (st.session_state.verbs_low + st.session_state.verbs_med + st.session_state.verbs_high)
            st.session_state.mcqs = generate_mcqs(
                st.session_state.how_many, st.session_state.topic, verbs, st.session_state.answer_key
            )

        if st.session_state.mcqs:
            # Downloads
            txt_content = mcqs_to_txt(st.session_state.mcqs)
            txt_download("⬇️ Download TXT (All MCQs)",
                         f"ADI_MCQ__{st.session_state.course.split(' — ')[0]}__W{st.session_state.week:02d}.txt",
                         txt_content)
            if HAVE_DOCX:
                buf = mcqs_to_docx(st.session_state.mcqs,
                                   title=f"MCQs — {st.session_state.course} — W{st.session_state.week:02d}")
                st.download_button("⬇️ Download DOCX (All MCQs)", data=buf.getvalue(),
                                   file_name=f"ADI_MCQ__{st.session_state.course.split(' — ')[0]}__W{st.session_state.week:02d}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            else:
                st.info("DOCX export unavailable (python-docx not installed). TXT download works.")

    with right:
        if not st.session_state.mcqs:
            st.info("No questions yet. Click **Generate from verbs/topic**.")
        else:
            # Editable MCQs
            for i, q in enumerate(st.session_state.mcqs):
                box = st.expander(f"Q{i+1}", expanded=(i==0))
                with box:
                    q["stem"]   = st.text_input("Question", q["stem"], key=f"stem_{i}")
                    q["A"]      = st.text_input("A", q["A"], key=f"A_{i}")
                    q["B"]      = st.text_input("B", q["B"], key=f"B_{i}")
                    q["C"]      = st.text_input("C", q["C"], key=f"C_{i}")
                    q["D"]      = st.text_input("D", q["D"], key=f"D_{i}")
                    q["answer"] = st.radio("Correct answer", ["","A","B","C","D"], index=["","A","B","C","D"].index(q.get("answer","")),
                                           horizontal=True, key=f"ans_{i}")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("➕ Add blank question", key="add_q"):
                    st.session_state.mcqs.append({"stem":"", "A":"","B":"","C":"","D":"","answer":""})
            with c2:
                if st.session_state.mcqs and st.button("➖ Remove last", key="rem_q"):
                    st.session_state.mcqs.pop()

# ---------- Tab 1: Skills ----------
with tabs[1]:
    st.session_state.tab_index = 1
    c1, c2, c3 = st.columns([0.3, 0.3, 0.4])
    with c1:
        n_acts = st.selectbox("How many activities?", [1,2,3], index=1, key="acts_n")
    with c2:
        minutes = st.selectbox("Minutes per activity", [5,10,15,20,30,45,60], index=1, key="acts_min")
    with c3:
        group = st.selectbox("Group size", ["Solo (1)", "Pairs (2)", "Triads (3)", "Group of 4"], index=1, key="acts_group")

    if st.button("Generate Activities", key="btn_gen_acts"):
        # choose verbs from active band to flavor text a bit
        if   active == "low":  pool = st.session_state.verbs_low
        elif active == "med":  pool = st.session_state.verbs_med
        else:                  pool = st.session_state.verbs_high
        st.session_state.activities = generate_activities(n_acts, minutes, group, st.session_state.topic)

    if st.session_state.activities:
        st.subheader("Activities")
        for i, a in enumerate(st.session_state.activities, 1):
            st.markdown(f"**A{i}.** {a['task']}  \n*({a['minutes']} min, {a['group']})*")
        txt = "\n\n".join([f"A{i}. {a['task']} ({a['minutes']} min, {a['group']})" for i,a in enumerate(st.session_state.activities,1)])
        txt_download("⬇️ Download TXT (Activities)",
                     f"ADI_Activities__{st.session_state.course.split(' — ')[0]}__W{st.session_state.week:02d}.txt",
                     txt)

# ---------- Tab 2: Revision ----------
with tabs[2]:
    st.session_state.tab_index = 2
    if st.button("Generate revision prompts", key="btn_rev"):
        pool = (st.session_state.verbs_low + st.session_state.verbs_med + st.session_state.verbs_high)
        st.session_state.revision = generate_revision(st.session_state.topic, pool)
    if st.session_state.revision:
        st.subheader("Revision")
        for i, line in enumerate(st.session_state.revision, 1):
            st.markdown(f"**R{i}.** {line}")
        txt = "\n".join([f"R{i}. {line}" for i,line in enumerate(st.session_state.revision,1)])
        txt_download("⬇️ Download TXT (Revision)",
                     f"ADI_Revision__{st.session_state.course.split(' — ')[0]}__W{st.session_state.week:02d}.txt",
                     txt)
    else:
        st.info("Click **Generate revision prompts**.")

# ---------- Tab 3: Print Summary ----------
with tabs[3]:
    st.session_state.tab_index = 3
    st.subheader("Print summary")
    st.markdown(f"**Course:** {st.session_state.course}  \n"
                f"**Cohort:** {st.session_state.cohort}  \n"
                f"**Instructor:** {st.session_state.instructor}  \n"
                f"**Date:** {st.session_state.date}  \n"
                f"**Lesson:** {st.session_state.lesson}  \n"
                f"**Week:** {st.session_state.week}")
    st.markdown("---")
    st.markdown(f"**Topic / Outcome**  \n{st.session_state.topic or '_(not provided)_'}")
    st.markdown("---")
    st.markdown("**Verbs selected**")
    st.write({"Low": st.session_state.verbs_low,
              "Medium": st.session_state.verbs_med,
              "High": st.session_state.verbs_high})
    st.markdown("---")
    st.markdown("**Question count requested:** " + str(st.session_state.how_many))
    if st.session_state.mcqs:
        st.markdown(f"*MCQs generated:* **{len(st.session_state.mcqs)}**")
    if st.session_state.activities:
        st.markdown(f"*Activities generated:* **{len(st.session_state.activities)}**")
    if st.session_state.revision:
        st.markdown(f"*Revision prompts generated:* **{len(st.session_state.revision)}**")
