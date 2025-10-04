
# app.py — ADI Builder (clean nav: radio pages; unique widget keys; no key mutation)

import io
import base64
import random
from datetime import date
import streamlit as st

# Optional parsers
try:
    from docx import Document
except Exception:
    Document = None
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
except Exception:
    Presentation = None
    Inches = Pt = None
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None


# ---------- helpers ----------

def _b64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""

def week_focus(w: int) -> str:
    if 1 <= w <= 4: return "Low"
    if 5 <= w <= 9: return "Medium"
    return "High"

def parse_upload(file, deep=False) -> str:
    if not file: return ""
    name = file.name.lower()
    try:
        if name.endswith(".txt"):
            data = file.getvalue() if hasattr(file,"getvalue") else file.read()
            return data.decode("utf-8","ignore")
        if name.endswith(".docx") and Document:
            d = Document(file); return "\n".join(p.text for p in d.paragraphs)
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(file); lines=[]
            for slide in prs.slides:
                for sh in slide.shapes:
                    if hasattr(sh,"text") and sh.text: lines.append(sh.text)
            return "\n".join(lines)
        if name.endswith(".pdf") and fitz:
            data = file.read(); doc = fitz.open(stream=data, filetype="pdf"); out=[]
            for pg in doc:
                try: t = pg.get_text("blocks" if deep else "text") or ""
                except Exception: t = ""
                out.append(t)
            return "\n".join(out)
    except Exception as e:
        st.warning(f"Could not parse file: {e}")
    return ""

def docx_download(lines: list[str]) -> io.BytesIO:
    if not Document:
        buf = io.BytesIO(); buf.write("\n".join(lines).encode("utf-8")); buf.seek(0); return buf
    doc = Document()
    for line in lines: doc.add_paragraph(line)
    buf = io.BytesIO(); doc.save(buf); buf.seek(0); return buf

def build_mcqs(topic: str, verbs: list[str], n: int):
    out = []
    verbs = list(verbs) or ["identify"]
    for i in range(n):
        v = verbs[(i) % len(verbs)]
        stem = f"{v.title()} — {topic or 'Topic'} — Q{i+1}"
        opts = ["Option A","Option B","Option C","Correct answer","Option D"]
        random.shuffle(opts)
        out.append({"stem":stem,"options":opts,"answer":"Correct answer"})
    return out

def build_activities(topic: str, n: int, minutes: int, verbs: list[str]):
    verbs = list(verbs) or ["apply","demonstrate","solve"]
    return [f"Activity {i} ({minutes} min): {verbs[(i-1)%len(verbs)]} on {topic or 'today’s concept'} via example / mini-lab." for i in range(1,n+1)]

def build_revision(topic: str, verbs: list[str], qty: int = 5):
    verbs = list(verbs) or ["recall","classify","compare","justify","design"]
    return [f"Rev {i}: {verbs[(i-1)%len(verbs)]}. Connect this week to prior learning for {topic or 'the module'} (3–4 sentences)." for i in range(1,qty+1)]


# ---------- page setup ----------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")
LOGO64 = _b64("adi_logo.png")

st.markdown("""
<style>
.block-container { padding-top: 1.0rem; }
.adi-hero {background: linear-gradient(180deg,#245a34 0%, #214d2f 100%);
  color:#fff;border-radius:14px;padding:14px 16px;box-shadow:0 6px 18px rgba(0,0,0,.06);margin-bottom:10px;}
.adi-hero * {color:#fff !important;}
.adi-hero h1 {font-size:1.0rem;margin:0 0 4px 0;font-weight:700;}
.adi-hero p  {font-size:.85rem;margin:0;opacity:.96;}
.adi-logo { width: 180px; max-width: 100%; height:auto; display:block; }
.hr-soft { height:1px; border:0; background:#e5e7eb; margin:.4rem 0 1rem 0; }
.bloom-group {border:1px solid #e5e7eb;border-radius:12px;padding:12px 12px 8px 12px;margin:10px 0;}
.bloom-low  { background: linear-gradient(180deg,#f1f8f1, #ffffff); }
.bloom-med  { background: linear-gradient(180deg,#fff7e8, #ffffff); }
.bloom-high { background: linear-gradient(180deg,#eef2ff, #ffffff); }
.bloom-focus { box-shadow: 0 0 0 2px rgba(36,90,52,.12) inset; border-color:#245a34; }
.bloom-active { box-shadow: 0 0 0 2px rgba(36,90,52,.18) inset; border-color:#245a34; }
.bloom-caption {font-size:.80rem;color:#6b7280;margin-left:6px;}
.bloom-pill {display:inline-block;background:#edf2ee;color:#245a34;border-radius:999px;padding:4px 10px;font-weight:600;font-size:.75rem;}
/* Cards */
.card {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#fff;}
</style>
""", unsafe_allow_html=True)

# ---------- session defaults ----------
s = st.session_state
if "_ok" not in s:
    s._ok = True
    s.courses = ["Defense Technology Practices (GE4-EPM)","Integrated Project & Materials Mgmt (GE4-IPM)"]
    s.cohorts = ["D1-C01","D1-E01","D1-M01"]
    s.instructors = ["GHAMZA LABEEB KHADER","DANIEL JOSEPH LAMB"]
    s.lesson = 1; s.week = 1; s.date_str = date.today().isoformat()
    s.source_text = ""; s.deep_scan=False; s.bloom_picks=set(); s.last_generated = {}

# ---------- hero ----------
st.markdown("""
<div class="adi-hero">
  <h1>ADI Builder — Lesson Activities &amp; Questions</h1>
  <p>Sleek, professional and engaging. Print-ready handouts for your instructors.</p>
</div>
""", unsafe_allow_html=True)

# ---------- sidebar ----------
with st.sidebar:
    if LOGO64:
        st.markdown(f'<img class="adi-logo" src="data:image/png;base64,{LOGO64}" alt="ADI logo"/>', unsafe_allow_html=True)
    st.caption("ADI")

    st.write("### Upload (optional)")
    st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"], key="uploader")
    if s.get("uploader"):
        f = s.uploader
        size_kb = (getattr(f,"size",0) or 0)/1024
        st.success(f"✅ File selected: **{f.name}** ({size_kb:.1f} KB)")
    if st.button("Process source"):
        with st.spinner("Processing upload…"):
            parsed = parse_upload(s.get("uploader"), s.get("deep_scan", False))
            if parsed:
                s.source_text = parsed
                st.success("✅ Upload processed.")
            else:
                st.warning("No readable text found.")

    st.write("### Course details")
    st.selectbox("Course name", s.courses, index=0, key="course_sel")
    st.selectbox("Class / Cohort", s.cohorts, index=0, key="coh_sel")
    st.selectbox("Instructor name", s.instructors, index=0, key="ins_sel")
    st.text_input("Date", s.date_str, key="date_str")

    st.write("### Context")
    c1,c2 = st.columns(2)
    with c1: st.number_input("Lesson", min_value=1, key="lesson")
    with c2: st.number_input("Week", min_value=1, key="week")
    st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

# ---------- main top inputs ----------
st.write("**Topic / Outcome (optional)**")
st.text_area("Module description, knowledge & skills outcomes",
             value=s.get("source_text",""), height=110, label_visibility="collapsed", key="source_text")
st.toggle("Deep scan source (slower, better coverage)", value=s.get("deep_scan", False), key="deep_scan")

# ---------- Bloom ----------
LOW = ["define","identify","list","recall","describe","label"]
MED = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH= ["evaluate","synthesize","design","justify","critique","create"]

def verb_row(verbs):
    cols = st.columns(len(verbs))
    picks = s.setdefault("bloom_picks", set())
    for i,v in enumerate(verbs):
        with cols[i]:
            k=f"verb-{v}"
            val = st.checkbox(v, value=s.get(k, False), key=k)
            if val: picks.add(v)
            else: picks.discard(v)

focus = week_focus(int(s.get("week",1)))
st.markdown(f"<div style='text-align:right'><span class='bloom-pill'>Week {int(s.get('week',1))}: {focus}</span></div>", unsafe_allow_html=True)
def bloom_group(title, subtitle, verbs, css):
    st.markdown(f'<div class="bloom-group {css}">', unsafe_allow_html=True)
    st.markdown(f"**{title}**  <span class='bloom-caption'>{subtitle}</span>", unsafe_allow_html=True)
    verb_row(verbs); st.markdown("</div>", unsafe_allow_html=True)

bloom_group("Low (Weeks 1–4)","Remember / Understand", LOW,"bloom-low")
bloom_group("Medium (Weeks 5–9)","Apply / Analyse", MED,"bloom-med")
bloom_group("High (Weeks 10–14)","Evaluate / Create", HIGH,"bloom-high")

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

# ---------- Page switch (radio) ----------
page = st.radio("Mode", ["Activities","MCQs","Revision","Print Summary"], horizontal=True, key="mode_radio")

picked = sorted(list(s.get("bloom_picks", set())))
topic = s.get("source_text","").strip()

# ---------- Activities ----------
if page == "Activities":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Activities")
    st.selectbox("Number of activities", [1,2,3,4], index=1, key="acts_count_sel")
    st.number_input("Minutes per activity", min_value=5, max_value=60, step=5, value=20, key="acts_minutes_input")
    if st.button("Generate Activities", type="primary"):
        s.last_generated["activities"] = build_activities(topic, s.get("acts_count_sel",2), s.get("acts_minutes_input",20), picked)
        st.success(f"Generated {len(s.last_generated['activities'])} activities.")
    acts = s.last_generated.get("activities") or build_activities(topic, 2, 15, picked)
    for a in acts: st.write("• " + a)
    buf = docx_download([f"{i+1}. {a}" for i,a in enumerate(acts)])
    st.download_button("Download Activities (DOCX)", data=buf, file_name="ADI_Activities.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- MCQs ----------
elif page == "MCQs":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Knowledge MCQs")
    st.selectbox("How many MCQs?", [5,10,15,20,25,30], index=1, key="mcq_count_sel")
    st.checkbox("Include answer key in export", value=True, key="include_answer_chk")
    if st.button("Generate MCQs", type="primary"):
        s.last_generated["mcqs"] = build_mcqs(topic, picked, s.get("mcq_count_sel",10))
        st.success(f"Generated {len(s.last_generated['mcqs'])} MCQs.")
    mcqs = s.last_generated.get("mcqs") or build_mcqs(topic, picked, 5)
    for i,q in enumerate(mcqs,1):
        st.markdown(f"**Q{i}. {q['stem']}**")
        for opt in q["options"]: st.write(f"- {opt}")
        if s.get("include_answer_chk", True): st.caption(f"Answer: {q['answer']}")
        st.divider()
    lines = []
    for i,q in enumerate(mcqs,1):
        lines.append(f"Q{i}. {q['stem']}"); lines.extend([f"- {o}" for o in q["options"]])
        if s.get("include_answer_chk", True): lines.append(f"Answer: {q['answer']}")
        lines.append("")
    buf = docx_download(lines)
    st.download_button("Download MCQs (DOCX)", data=buf, file_name="ADI_MCQs.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Revision ----------
elif page == "Revision":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Revision")
    st.selectbox("How many revision prompts?", list(range(3,13)), index=2, key="rev_qty_sel")
    if st.button("Generate Revision", type="primary"):
        s.last_generated["revision"] = build_revision(topic, picked, s.get("rev_qty_sel",5))
        st.success(f"Generated {len(s.last_generated['revision'])} revision prompts.")
    rev = s.last_generated.get("revision") or build_revision(topic, picked, 5)
    for r in rev: st.write("• " + r)
    buf = docx_download([f"{i+1}. {r}" for i,r in enumerate(rev)])
    st.download_button("Download Revision (DOCX)", data=buf, file_name="ADI_Revision.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Print Summary ----------
else:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Print Summary")
    st.write(
        f"**Course**: {s.get('course_sel', s.courses[0])}  \n"
        f"**Cohort**: {s.get('coh_sel', s.cohorts[0])}  \n"
        f"**Instructor**: {s.get('ins_sel', s.instructors[0])}  \n"
        f"**Week**: {s.get('week',1)}  \n"
        f"**Lesson**: {s.get('lesson',1)}  \n"
        f"**Date**: {s.get('date_str','')}"
    )
    if topic:
        st.subheader("Module notes / outcomes"); st.write(topic)
    g = s.last_generated
    if g.get("mcqs"):
        st.subheader("Latest MCQs")
        for i,q in enumerate(g["mcqs"][:5],1): st.write(f"{i}. {q['stem']}")
    if g.get("activities"):
        st.subheader("Latest Activities")
        for a in g["activities"]: st.write("• " + a)
    if g.get("revision"):
        st.subheader("Latest Revision")
        for r in g["revision"]: st.write("• " + r)
    st.markdown('</div>', unsafe_allow_html=True)
