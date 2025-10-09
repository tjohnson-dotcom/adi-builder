# ADI Builder — Lesson Activities & Questions (classic-v3.9)
import streamlit as st
import json, io, datetime, re
from docx import Document
from docx.shared import Pt

APP_TITLE = "ADI Builder — Lesson Activities & Questions"
PREFS_FILE = "adi_prefs.json"

# ---------- THEME & STYLES ----------
STYLES = """
<style>
:root{
  --adi-green:#245a34; --adi-green-50:#eaf6ef;
  --low:#cfe8d9;  --low-b:#96d1b4;  --low-t:#0c3a23;
  --med:#f8e6c9;  --med-b:#efc989;  --med-t:#4a3514;
  --high:#dfe6ff; --high-b:#9db4ff; --high-t:#101a3d;
}
/* Banner */
[data-testid="stHeader"] { background: transparent; }
.stApp header { background: transparent; }
div.block-container{padding-top:1rem;}
/* Logo sizing */
.adi-logo{width:160px;margin:6px 0 12px 0}

/* Drag & drop dashed box */
div[data-testid="stFileUploaderDropzone"]{
  border:2px dashed var(--adi-green)!important;
  border-radius:12px!important;
  background:#fff;
}
div[data-testid="stFileUploaderDropzone"]:hover{
  box-shadow:0 0 0 3px var(--adi-green) inset!important;
}

/* Make interactive bits feel clickable */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind], button { cursor:pointer!important; }
:focus-visible{ outline:2px solid var(--adi-green)!important; outline-offset:2px; }

/* Verb band containers + colored chips */
.band{
  border:1px solid rgba(36,90,52,.18)!important;
  border-radius:10px!important;
  padding:10px!important;
  background:#f8f9fa!important;
  transition: box-shadow .12s, background-color .12s, opacity .12s
}
.band:not(.active){opacity:.92}
.band:not(.active):hover{opacity:1}
.band.low  [data-baseweb="tag"]{
  background:var(--low)!important;border:1px solid var(--low-b)!important;
  color:var(--low-t)!important;border-radius:9999px!important;font-weight:700!important
}
.band.med  [data-baseweb="tag"]{
  background:var(--med)!important;border:1px solid var(--med-b)!important;
  color:var(--med-t)!important;border-radius:9999px!important;font-weight:700!important
}
.band.high [data-baseweb="tag"]{
  background:var(--high)!important;border:1px solid var(--high-b)!important;
  color:var(--high-t)!important;border-radius:9999px!important;font-weight:700!important
}
/* Stronger active ring (4px) for projectors */
.band.low.active  {box-shadow:0 0 0 4px var(--low-b) inset!important;background:#eaf6ef!important}
.band.med.active  {box-shadow:0 0 0 4px var(--med-b) inset!important;background:#fcf2e3!important}
.band.high.active {box-shadow:0 0 0 4px var(--high-b) inset!important;background:#eef1ff!important}

/* Cards */
.mcq-card{margin:6px 0}
/* Secondary (outline) buttons for per-question downloads — robust selector */
.secondary .stDownloadButton > button,
.secondary button{
  background:transparent!important;color:var(--adi-green)!important;
  border:2px solid var(--adi-green)!important;border-radius:10px!important;font-weight:700!important
}
.secondary .stDownloadButton > button:hover,
.secondary button:hover{background:rgba(36,90,52,.06)!important}
/* Action rows + radio spacing */
.mcq-actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:6px 0 0 0}
.mcq-card .stRadio{margin:0 0 6px 0;padding:2px 0}

/* Thin rule & compact header row */
hr.thin{border:none;border-top:1px solid #e5e7eb;margin:8px 0}
.mcq-top-row{margin-bottom:6px}

/* Tabs hover/active cues */
.stTabs [role="tab"][aria-selected="true"]{border-bottom:2px solid var(--adi-green);font-weight:700}
.stTabs [role="tab"]:hover{ text-decoration: underline; }
</style>
"""

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")
st.markdown(STYLES, unsafe_allow_html=True)

# ---------- DATA ----------
LOW  = ["define","identify","list","recall","describe","label"]
MED  = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH = ["evaluate","synthesize","design","justify","critique","create"]

COURSES    = [
    "GE4-IPM — Integrated Project & Materials Mgmt",
    "GE4-EPM — Defense Technology Practices",
    "CT4-COM — Computation for Chemical Technologists"
]
COHORTS    = ["D1-C01","D1-M01","D1-M02","D2-C01"]
INSTRUCTORS= ["Daniel","Ghamza Labeeb","Abdulmalik","Nerdeen Tariq"]

# ---------- PREFS ----------
def load_prefs():
    try:
        with open(PREFS_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def save_prefs(d:dict):
    try:
        with open(PREFS_FILE,"w",encoding="utf-8") as f: json.dump(d,f)
    except Exception: pass

prefs = load_prefs()

def init_state():
    ss = st.session_state
    ss.setdefault("week", prefs.get("week", 1))
    ss.setdefault("lesson", prefs.get("lesson", 1))
    ss.setdefault("deep_scan", prefs.get("deep_scan", False))
    ss.setdefault("sel_courses", prefs.get("sel_courses", ""))
    ss.setdefault("sel_cohorts", prefs.get("sel_cohorts", ""))
    ss.setdefault("sel_instructors", prefs.get("sel_instructors", ""))
    ss.setdefault("mcqs", [
        {"stem":"Explain the role of inspection in quality management.",
         "options":["To verify conformance","To set company policy","To hire staff","To control budgets"],
         "correct":0}
    ])
    ss.setdefault("include_key", True)

init_state()

def persist_state():
    save_prefs({
        "week": st.session_state.week,
        "lesson": st.session_state.lesson,
        "deep_scan": st.session_state.deep_scan,
        "sel_courses": st.session_state.sel_courses,
        "sel_cohorts": st.session_state.sel_cohorts,
        "sel_instructors": st.session_state.sel_instructors,
    })

# ---------- HELPERS ----------
def _slug(s:str)->str:
    if not s: return "NA"
    s = re.sub(r"\s+","_", str(s))
    s = re.sub(r"[^A-Za-z0-9_\-]","", s)
    return s[:60]

def ctx_filename(base:str, qnum=None):
    c  = _slug(st.session_state.get('sel_courses',''))
    coh= _slug(st.session_state.get('sel_cohorts',''))
    wk = _slug(st.session_state.get('week',''))
    if qnum is None:
        return f"{base}__{c}__{coh}__W{wk}"
    return f"{base}__{c}__{coh}__W{wk}__Q{qnum}"

def export_docx_one(item, idx=1)->bytes:
    doc = Document()
    doc.add_heading(f"Question {idx}", level=1)
    p = doc.add_paragraph(item["stem"])
    p.style.font.size = Pt(12)
    letters = ["A","B","C","D"]
    for i,opt in enumerate(item["options"]):
        doc.add_paragraph(f"{letters[i]}. {opt}")
    doc.add_paragraph("")
    doc.add_paragraph(f"Answer: {letters[item['correct']]}")
    buf = io.BytesIO(); doc.save(buf); buf.seek(0)
    return buf.getvalue()

def export_txt_one(item, idx=1)->bytes:
    letters = ["A","B","C","D"]
    lines = [f"Q{idx}: {item['stem']}"]
    for i,opt in enumerate(item["options"]):
        lines.append(f"{letters[i]}. {opt}")
    lines.append(f"Answer: {letters[item['correct']]}")
    return ("\n".join(lines)).encode("utf-8")

def export_docx_all(items, include_key=True)->bytes:
    doc = Document()
    doc.add_heading("ADI Knowledge MCQs", level=0)
    letters = ["A","B","C","D"]
    for i,it in enumerate(items, start=1):
        doc.add_heading(f"Q{i}", level=1)
        doc.add_paragraph(it["stem"])
        for j,opt in enumerate(it["options"]):
            doc.add_paragraph(f"{letters[j]}. {opt}")
        if include_key: doc.add_paragraph(f"Answer: {letters[it['correct']]}")
    buf = io.BytesIO(); doc.save(buf); buf.seek(0)
    return buf.getvalue()

def export_txt_all(items, include_key=True)->bytes:
    letters = ["A","B","C","D"]
    out=[]
    for i,it in enumerate(items, start=1):
        out.append(f"Q{i}: {it['stem']}")
        for j,opt in enumerate(it["options"]):
            out.append(f"{letters[j]}. {opt}")
        if include_key: out.append(f"Answer: {letters[it['correct']]}")
        out.append("")
    return ("\n".join(out)).encode("utf-8")

# ---------- SIDEBAR ----------
with st.sidebar:
    try:
        st.image("adi_logo.png", use_column_width=False, output_format="PNG",
                 caption=None, clamp=False, channels="RGB", width=160)
    except Exception:
        st.markdown("<div class='adi-logo'></div>", unsafe_allow_html=True)

    st.write("**Upload (optional)**")
    f = st.file_uploader("Drag and drop file here",
                         type=["txt","docx","pptx","pdf"],
                         label_visibility="collapsed")
    if f is not None:
        with st.spinner("Scanning file…"):
            # (Hook for future parsing.)
            pass
        st.success(f"✅ Uploaded: **{f.name}**")
        try: st.toast(f"File '{f.name}' uploaded", icon="📄")
        except Exception: pass

    st.checkbox("Deep scan source (slower, better coverage)", key="deep_scan")
    st.markdown("---")
    st.subheader("Course details")
    st.selectbox("Course name", COURSES,
                 index=0 if st.session_state.sel_courses=="" else
                 max(0, COURSES.index(st.session_state.sel_courses))
                 if st.session_state.sel_courses in COURSES else 0,
                 key="sel_courses")
    st.selectbox("Class / Cohort", COHORTS,
                 index=0 if st.session_state.sel_cohorts=="" else
                 max(0, COHORTS.index(st.session_state.sel_cohorts))
                 if st.session_state.sel_cohorts in COHORTS else 0,
                 key="sel_cohorts")
    st.selectbox("Instructor name", INSTRUCTORS,
                 index=0 if st.session_state.sel_instructors=="" else
                 max(0, INSTRUCTORS.index(st.session_state.sel_instructors))
                 if st.session_state.sel_instructors in INSTRUCTORS else 0,
                 key="sel_instructors")

    st.write("**Date**")
    st.date_input("", value=datetime.date.today(), label_visibility="collapsed")
    st.write("**Context**")
    cols = st.columns(2)
    with cols[0]:
        st.number_input("Lesson", min_value=1, max_value=20, step=1, key="lesson")
    with cols[1]:
        st.number_input("Week", min_value=1, max_value=14, step=1, key="week")
    # persist
    save_prefs({
        "week": st.session_state.week,
        "lesson": st.session_state.lesson,
        "deep_scan": st.session_state.deep_scan,
        "sel_courses": st.session_state.sel_courses,
        "sel_cohorts": st.session_state.sel_cohorts,
        "sel_instructors": st.session_state.sel_instructors,
    })

# ---------- MAIN ----------
st.markdown(f"### {APP_TITLE}")
topic = st.text_area("Topic / Outcome (optional)",
                     placeholder="e.g., Integrated Project and …")

# Active band from week
active_band = 'low'
try:
    wk = int(st.session_state.week)
    if 5 <= wk <= 9: active_band='med'
    elif wk >= 10:   active_band='high'
except Exception: pass

# Verb sections
with st.expander("Low (Weeks 1–4) — Remember / Understand", True):
    st.markdown(f'<div class="band low {"active" if active_band=="low" else ""}">', unsafe_allow_html=True)
    low = st.multiselect("Low verbs", LOW, default=LOW[:3], key="lowverbs")
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Medium (Weeks 5–9) — Apply / Analyse", True):
    st.markdown(f'<div class="band med {"active" if active_band=="med" else ""}">', unsafe_allow_html=True)
    med = st.multiselect("Medium verbs", MED, default=MED[:3], key="medverbs")
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("High (Weeks 10–14) — Evaluate / Create", True):
    st.markdown(f'<div class="band high {"active" if active_band=="high" else ""}">', unsafe_allow_html=True)
    high = st.multiselect("High verbs", HIGH, default=HIGH[:3], key="highverbs")
    st.markdown('</div>', unsafe_allow_html=True)

# Tabs with URL bookmark (keeps URL updated)
tab_names = ["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"]
tabs = st.tabs(tab_names)

# ----- MCQs TAB -----
with tabs[0]:
    st.query_params["tab"] = "mcq"
    st.subheader("Knowledge MCQs (ADI Policy)")

    st.markdown('<div class="mcq-top-row">', unsafe_allow_html=True)
    cols = st.columns([1,1,1,2])
    with cols[0]:
        how_many = st.selectbox("How many?", [5,10,15,20], index=1)
    with cols[1]:
        st.checkbox("Answer key", key="include_key")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr class="thin">', unsafe_allow_html=True)

    letters = ["A","B","C","D"]
    for i,item in enumerate(st.session_state.mcqs):
        with st.container(border=True):
            st.markdown(f"**Q{i+1}**")
            item["stem"] = st.text_area("Question", value=item["stem"], key=f"stem_{i}")
            c1,c2 = st.columns(2)
            with c1:
                item["options"][0] = st.text_input("A", value=item["options"][0], key=f"a_{i}")
                item["options"][1] = st.text_input("B", value=item["options"][1], key=f"b_{i}")
            with c2:
                item["options"][2] = st.text_input("C", value=item["options"][2], key=f"c_{i}")
                item["options"][3] = st.text_input("D", value=item["options"][3], key=f"d_{i}")
            item["correct"] = letters.index(st.radio("Correct answer", letters, index=item["correct"], horizontal=True, key=f"corr_{i}"))
            st.caption("Answer key above controls the correct option.")

            st.markdown('<div class="mcq-actions">', unsafe_allow_html=True)
            st.markdown('<div class="secondary">', unsafe_allow_html=True)
            clicked_docx = st.download_button(
                f"⬇️ Download DOCX (Q{i+1})",
                data=export_docx_one(item, idx=i+1),
                file_name=ctx_filename("ADI_MCQ", qnum=i+1)+".docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"dl_docx_q{i}",
                disabled=not bool(item["stem"].strip()),
                help="Download DOCX for this specific question"
            )
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="secondary">', unsafe_allow_html=True)
            clicked_txt = st.download_button(
                f"⬇️ Download TXT (Q{i+1})",
                data=export_txt_one(item, idx=i+1),
                file_name=ctx_filename("ADI_MCQ", qnum=i+1)+".txt",
                mime="text/plain",
                key=f"dl_txt_q{i}",
                disabled=not bool(item["stem"].strip()),
                help="Download plain-text version for this question"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if clicked_docx or clicked_txt:
                try: st.toast("Export started", icon="⬇️")
                except Exception: pass

    st.markdown("")
    col1,col2,col3 = st.columns([1,1,2])
    with col1:
        if st.button("➕ Add blank question"):
            st.session_state.mcqs.append(
                {"stem":"New question...", "options":["Option A","Option B","Option C","Option D"], "correct":0}
            )
    with col2:
        if st.button("➖ Remove last"):
            if st.session_state.mcqs:
                st.session_state.mcqs.pop()

    with col3:
        clicked_all_docx = st.download_button(
            "⬇️ Download DOCX (All MCQs)",
            data=export_docx_all(st.session_state.mcqs, st.session_state.include_key),
            file_name=ctx_filename("ADI_Knowledge_MCQs")+".docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=not bool(st.session_state.mcqs),
            help="Download a DOCX with all questions"
        )

    clicked_all_txt = st.download_button(
        "⬇️ Download TXT (All MCQs)",
        data=export_txt_all(st.session_state.mcqs, st.session_state.include_key),
        file_name=ctx_filename("ADI_Knowledge_MCQs")+".txt",
        mime="text/plain",
        disabled=not bool(st.session_state.mcqs),
        help="Download a TXT with all questions"
    )

    if clicked_all_docx or clicked_all_txt:
        try: st.toast("Export started", icon="⬇️")
        except Exception: pass

# ----- Skills Activities -----
with tabs[1]:
    st.query_params["tab"] = "skills"
    st.subheader("Skills Activities")
    a1,a2,a3 = st.columns(3)
    with a1:
        acts = st.selectbox("How many activities?", [1,2,3], index=0)
    with a2:
        mins = st.selectbox("Minutes per activity", list(range(5,61,5)), index=1)
    with a3:
        group = st.selectbox("Group size", ["Solo (1)","Pairs (2)","Triads (3)","Groups of 4"], index=0)
    st.button("Generate from verbs/topic")

# ----- Revision -----
with tabs[2]:
    st.query_params["tab"] = "revision"
    st.subheader("Revision")
    st.info("Revision worksheet generator coming next.")

# ----- Print Summary -----
with tabs[3]:
    st.query_params["tab"] = "summary"
    st.subheader("Print Summary")
    st.write("Course:", st.session_state.sel_courses)
    st.write("Cohort:", st.session_state.sel_cohorts)
    st.write("Instructor:", st.session_state.sel_instructors)
    st.write("Week/Lesson:", st.session_state.week, "/", st.session_state.lesson)
