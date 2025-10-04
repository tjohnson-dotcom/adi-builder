
# app.py — ADI Builder (Week-4 polished, function-order fix)
# Layout: Left = Activities, Right = MCQs (top) + Revision (bottom). No tabs.

import io
import base64
import random
from datetime import date
from uuid import uuid4

import streamlit as st

# Optional parsers (guarded)
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


# --------------------------- helpers ---------------------------

def _b64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""  # repo includes adi_logo.png


def week_focus(w: int) -> str:
    if 1 <= w <= 4: return "Low"
    if 5 <= w <= 9: return "Medium"
    return "High"


# --------------------------- page setup ---------------------------

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")
LOGO64 = _b64("adi_logo.png")

st.markdown("""
<style>
.block-container { padding-top: 1.0rem; }
.adi-hero {background: linear-gradient(180deg,#245a34 0%, #214d2f 100%);
  color:#fff;border-radius:14px;padding:16px 18px;box-shadow:0 6px 18px rgba(0,0,0,.06);margin-bottom:12px;}
.adi-hero * {color:#fff !important;}
.adi-hero h1 {font-size:1.06rem;margin:0 0 4px 0;font-weight:700;}
.adi-hero p  {font-size:.86rem;margin:0;opacity:.96;}
.adi-logo { width: 180px; max-width: 100%; height:auto; display:block; }
.hr-soft { height:1px; border:0; background:#e5e7eb; margin:.4rem 0 1rem 0; }
.bloom-group {border:1px solid #e5e7eb;border-radius:12px;padding:12px 12px 8px 12px;margin:10px 0;}
.bloom-low  { background: linear-gradient(180deg,#f1f8f1, #ffffff); }
.bloom-med  { background: linear-gradient(180deg,#fff7e8, #ffffff); }
.bloom-high { background: linear-gradient(180deg,#eef2ff, #ffffff); }
.bloom-focus { box-shadow: 0 0 0 2px rgba(36,90,52,.12) inset; border-color:#245a34; }
.bloom-active { box-shadow: 0 0 0 2px rgba(36,90,52,.18) inset; border-color:#245a34; }
.bloom-group [data-testid="stCheckbox"] > div > label,
.bloom-group [data-testid="stCheckbox"] > label{
  display:inline-block;border:1px solid #d1d5db;border-radius:999px;padding:6px 12px;background:#fff;
  transition: box-shadow .15s ease, border-color .15s ease, background .15s ease; white-space:nowrap;}
.bloom-group [data-testid="stCheckbox"] > div > label:hover,
.bloom-group [data-testid="stCheckbox"] > label:hover { box-shadow:0 2px 10px rgba(0,0,0,.06); }
.bloom-group [data-testid="stCheckbox"] input:checked + div,
.bloom-group [data-testid="stCheckbox"] input:checked + label{
  background:#def7e3;border-color:#245a34;box-shadow:0 0 0 2px rgba(36,90,52,.15);}
.bloom-caption {font-size:.80rem;color:#6b7280;margin-left:6px;}
.bloom-pill {display:inline-block;background:#edf2ee;color:#245a34;border-radius:999px;padding:4px 10px;font-weight:600;font-size:.75rem;}

/* Section cards */
.card {border:1px solid #e5e7eb; border-radius:14px; padding:16px; margin-bottom:16px; background:#fff;}
.card h3 {margin:0 0 8px 0; font-size:1.0rem; font-weight:700;}
.card small {color:#6b7280;}
.card-green { box-shadow:0 0 0 2px rgba(36,90,52,.15) inset; border-color:#245a34; }
.card-gold  { box-shadow:0 0 0 2px rgba(200,168,90,.25) inset; border-color:#C8A85A; }
.card-blue  { box-shadow:0 0 0 2px rgba(59,130,246,.18) inset; border-color:#93B4F4; }
</style>
""", unsafe_allow_html=True)


# --------------------------- session defaults ---------------------------

def init_state():
    s = st.session_state
    if s.get("_ok"): return
    s._ok = True

    s.courses = [
        "Defense Technology Practices: Experimentation, Quality Management and Inspection (GE4-EPM)",
        "Integrated Project and Materials Management in Defense Technology (GE4-IPM)",
        "Military Vehicle and Aircraft MRO: Principles & Applications (GE4-MRO)",
        "Computation for Chemical Technologists (CT4-COM)",
        "Explosives Manufacturing (CT4-EMG)",
        "Thermofluids (CT4-TFL)",
        "Composite Manufacturing (MT4-CMG)",
        "Computer Aided Design (MT4-CAD)",
        "Machine Elements (MT4-MAE)",
        "Electrical Materials (EE4-MFC)",
        "PCB Manufacturing (EE4-PMG)",
        "Power Circuits & Transmission (EE4-PCT)",
        "Mechanical Product Dissection (MT5-MPD)",
        "Assembly Technology (MT5-AST)",
        "Aviation Maintenance (MT5-AVM)",
        "Hydraulics and Pneumatics (MT5-HYP)",
        "Computer Aided Design and Additive Manufacturing (MT5-CAD)",
        "Industrial Machining (MT5-CNC)",
        "Thermochemistry of Explosives (CT5-TCE)",
        "Separation Technologies 1 (CT5-SET)",
        "Explosives Plant Operations and Troubleshooting (CT5-POT)",
        "Coating Technologies (CT5-COT)",
        "Chemical Technology Laboratory Techniques (CT5-LAB)",
        "Chemical Process Technology (CT5-CPT)",
    ]
    s.cohorts = ["D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
                 "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"]
    s.instructors = [
        "GHAMZA LABEEB KHADER","DANIEL JOSEPH LAMB","NARDEEN TARIQ",
        "FAIZ LAZAM ALSHAMMARI","DR. MASHAEL ALSHAMMARI","AHMED ALBADER",
        "Noura Aldossari","Ahmed Gasem Alharbi","Mohammed Saeed Alfarhan",
        "Abdulmalik Halawani","Dari AlMutairi","Meshari AlMutrafi","Myra Crawford",
        "Meshal Alghurabi","Ibrahim Alrawili","Michail Mavroftas","Gerhard Van der Poel",
        "Khalil Razak","Mohammed Alwuthylah","Rana Ramadan","Salem Saleh Subaih",
        "Barend Daniel Esterhuizen",
    ]

    s.course = s.courses[0]
    s.cohort = s.cohorts[0]
    s.instructor = s.instructors[0]

    s.lesson = 1
    s.week = 1
    s.date_str = date.today().isoformat()

    s.uploaded_file = None
    s.deep_scan = False
    s.source_text = ""

    s.bloom_picks = set()

    s.mcq_count = 10
    s.include_answer_key = True
    s.activities_count = 2
    s.activity_minutes = 20

    s.last_generated = {}

init_state()


# --------------------------- parsing + export helpers (defined BEFORE use) ---------------------------

def parse_upload(file, deep=False) -> str:
    if not file: 
        return ""
    name = file.name.lower()
    try:
        if name.endswith(".txt"):
            data = file.getvalue() if hasattr(file, "getvalue") else file.read()
            return data.decode("utf-8", errors="ignore")
        if name.endswith(".docx") and Document:
            d = Document(file)
            return "\n".join(p.text for p in d.paragraphs)
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(file)
            lines = []
            for slide in prs.slides:
                for sh in slide.shapes:
                    if hasattr(sh, "text") and sh.text:
                        lines.append(sh.text)
            return "\n".join(lines)
        if name.endswith(".pdf") and fitz:
            data = file.read()
            doc = fitz.open(stream=data, filetype="pdf")
            texts = []
            for pg in doc:
                try:
                    t = pg.get_text("blocks" if deep else "text") or ""
                except Exception:
                    t = ""
                texts.append(t)
            return "\n".join([t if isinstance(t, str) else str(t) for t in texts])
    except Exception as e:
        st.warning(f"Could not parse file: {e}")
    return ""

def docx_download(filename: str, lines: list[str]) -> io.BytesIO:
    if not Document:
        buf = io.BytesIO(); buf.write("\n".join(lines).encode("utf-8")); buf.seek(0); return buf
    doc = Document()
    for line in lines: doc.add_paragraph(line)
    buf = io.BytesIO(); doc.save(buf); buf.seek(0); return buf

def pptx_download(title: str, bullets: list[str]) -> io.BytesIO:
    if not Presentation:
        buf = io.BytesIO(); buf.write((title + "\n" + "\n".join(bullets)).encode("utf-8")); buf.seek(0); return buf
    prs = Presentation(); slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = title
    left, top, width, height = Inches(1), Inches(1.8), Inches(8), Inches(4.5)
    tb = slide.shapes.add_textbox(left, top, width, height); tf = tb.text_frame; tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.add_paragraph() if i else tf.paragraphs[0]; p.text = b; p.level = 0
        if Pt: p.font.size = Pt(18)
    buf = io.BytesIO(); prs.save(buf); buf.seek(0); return buf


# --------------------------- hero banner ---------------------------

st.markdown("""
<div class="adi-hero">
  <h1>ADI Builder — Lesson Activities &amp; Questions</h1>
  <p>Sleek, professional and engaging. Print-ready handouts for your instructors.</p>
</div>
""", unsafe_allow_html=True)


# --------------------------- sidebar ---------------------------

with st.sidebar:
    if LOGO64:
        st.markdown(f'<img class="adi-logo" src="data:image/png;base64,{LOGO64}" alt="ADI logo"/>',
                    unsafe_allow_html=True)
    st.caption("ADI")

    st.write("### Upload (optional)")
    st.session_state.uploaded_file = st.file_uploader(
        "Drag and drop file here",
        type=["txt","docx","pptx","pdf"],
        help="Limit 200MB per file • TXT, DOCX, PPTX, PDF",
        key="uploader"
    )
    if st.session_state.uploaded_file is not None:
        f = st.session_state.uploaded_file
        size_kb = (f.size or 0) / 1024 if hasattr(f, "size") else 0
        st.success(f"✅ File selected: **{f.name}** ({size_kb:.1f} KB)")

    st.write("### Course details")
    c1, c2, c3 = st.columns([6,1,1])
    with c1:
        st.session_state.course = st.selectbox("Course name", st.session_state.courses, index=0, key="course_sel")
    with c2:
        if st.button("＋", help="Add Course", key="add_course"):
            if "New Course" not in st.session_state.courses:
                st.session_state.courses.insert(0, "New Course")
            st.session_state.course = "New Course"
    with c3:
        if st.button("－", help="Remove Course", key="del_course"):
            lst = st.session_state.courses
            if st.session_state.course in lst and len(lst) > 1:
                idx = lst.index(st.session_state.course)
                lst.remove(st.session_state.course)
                st.session_state.course = lst[max(0, idx-1)]

    coh1, coh2, coh3 = st.columns([6,1,1])
    with coh1:
        st.session_state.cohort = st.selectbox("Class / Cohort", st.session_state.cohorts, index=0, key="coh_sel")
    with coh2:
        if st.button("＋ ", key="add_coh", help="Add Cohort"):
            if "New Cohort" not in st.session_state.cohorts:
                st.session_state.cohorts.insert(0, "New Cohort")
            st.session_state.cohort = "New Cohort"
    with coh3:
        if st.button("－ ", key="del_coh", help="Remove Cohort"):
            lst = st.session_state.cohorts
            if st.session_state.cohort in lst and len(lst) > 1:
                idx = lst.index(st.session_state.cohort)
                lst.remove(st.session_state.cohort)
                st.session_state.cohort = lst[max(0, idx-1)]

    ins1, ins2, ins3 = st.columns([6,1,1])
    with ins1:
        st.session_state.instructor = st.selectbox("Instructor name", st.session_state.instructors, index=0, key="ins_sel")
    with ins2:
        if st.button("＋  ", key="add_ins", help="Add Instructor"):
            if "New Instructor" not in st.session_state.instructors:
                st.session_state.instructors.insert(0, "New Instructor")
            st.session_state.instructor = "New Instructor"
    with ins3:
        if st.button("－  ", key="del_ins", help="Remove Instructor"):
            lst = st.session_state.instructors
            if st.session_state.instructor in lst and len(lst) > 1:
                idx = lst.index(st.session_state.instructor)
                lst.remove(st.session_state.instructor)
                st.session_state.instructor = lst[max(0, idx-1)]

    st.write("### Date")
    st.session_state.date_str = st.text_input("Date", st.session_state.date_str)

    st.write("### Context")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.number_input("Lesson", min_value=1, key="lesson")
    with cc2:
        st.number_input("Week", min_value=1, key="week")
    if "lesson" not in st.session_state: st.session_state.lesson = 1
    if "week" not in st.session_state: st.session_state.week = 1

    st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

    if st.button("Process source", key="process_src"):
        try:
            with st.spinner("Processing upload…"):
                parsed = parse_upload(st.session_state.uploaded_file, st.session_state.deep_scan)
                if parsed:
                    st.session_state.source_text = parsed
                    chars = len(parsed); lines = parsed.count("\\n") + 1
                    st.success(f"✅ Upload processed. Extracted ~{lines} lines / {chars} characters.")
                else:
                    st.warning("No readable text found in that file.")
        except Exception as e:
            st.error(f"Could not process file: {e}")


# --------------------------- main text input ---------------------------

st.write("**Topic / Outcome (optional)**")
st.session_state.source_text = st.text_area(
    "Module description, knowledge & skills outcomes",
    value=st.session_state.source_text,
    height=120,
    label_visibility="collapsed",
)

st.session_state.deep_scan = st.toggle("Deep scan source (slower, better coverage)",
                                       value=st.session_state.get("deep_scan", False))

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)


# --------------------------- Bloom verbs ---------------------------

LOW_VERBS  = ["define","identify","list","recall","describe","label"]
MED_VERBS  = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","critique","create"]

def verb_row(verbs: list[str], band_key: str):
    cols = st.columns(len(verbs))
    for i, v in enumerate(verbs):
        with cols[i]:
            checked = v in st.session_state.bloom_picks
            new_val = st.checkbox(v, value=checked, key=f"verb-{v}")
            if new_val: st.session_state.bloom_picks.add(v)
            else: st.session_state.bloom_picks.discard(v)

def bloom_block(title: str, subtitle: str, verbs: list[str], css_class: str, focus_band: str, band_name: str):
    picks = st.session_state.bloom_picks
    active = any(v in picks for v in verbs)
    classes = ["bloom-group", css_class]
    if band_name == focus_band: classes.append("bloom-focus")
    if active: classes.append("bloom-active")
    st.markdown(f'<div class="{" ".join(classes)}">', unsafe_allow_html=True)
    st.markdown(f"**{title}**  <span class='bloom-caption'>{subtitle}</span>", unsafe_allow_html=True)
    verb_row(verbs, band_name)
    st.markdown("</div>", unsafe_allow_html=True)

focus = week_focus(int(st.session_state.week))
st.markdown(f"<div style='text-align:right'><span class='bloom-pill'>Week {int(st.session_state.week)}: {focus}</span></div>",
            unsafe_allow_html=True)

bloom_block("Low (Weeks 1–4)",  "Remember / Understand", LOW_VERBS,  "bloom-low",  focus, "Low")
bloom_block("Medium (Weeks 5–9)","Apply / Analyse",       MED_VERBS,  "bloom-med",  focus, "Medium")
bloom_block("High (Weeks 10–14)","Evaluate / Create",     HIGH_VERBS, "bloom-high", focus, "High")

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)


# --------------------------- Builders ---------------------------

def _clean_shuffle(options):
    banned = {"all of the above","none of the above","true","false"}
    clean = [o for o in options if o.strip().lower() not in banned]
    random.shuffle(clean)
    return clean

def build_mcqs(topic: str, verbs: list[str], n: int):
    out = []
    for i in range(n):
        v = random.choice(verbs) if verbs else "identify"
        stem = f"{v.title()} — {topic or 'Topic'} — Q{i+1}"
        opts = _clean_shuffle(["Option A","Option B","Option C","Correct answer","Option D"])
        out.append({"stem": stem, "options": opts, "answer": "Correct answer"})
    return out

def build_activities(topic: str, n: int, minutes: int, verbs: list[str]):
    verbs = verbs or ["apply","demonstrate","solve"]
    acts = []
    for i in range(1, n+1):
        acts.append(f"Activity {i} ({minutes} min): {verbs[i % len(verbs)]} on {topic or 'today’s concept'} via example / mini-lab.")
        # rotate verbs safely even if fewer than n
    return acts

def build_revision(topic: str, verbs: list[str], qty: int = 5):
    verbs = verbs or ["recall","classify","compare","justify","design"]
    rev = []
    for i in range(1, qty+1):
        v = verbs[i % len(verbs)]
        rev.append(f"Rev {i}: {v.title()} — connect this week to prior learning for {topic or 'the module'} (3–4 sentences).")
    return rev


# --------------------------- Section Cards (no tabs) ---------------------------

picked = sorted(list(st.session_state.bloom_picks))
topic_text = st.session_state.source_text.strip()

c_left, c_right = st.columns([1,1])

# LEFT: Activities
with c_left:
    st.markdown('<div class="card card-gold">', unsafe_allow_html=True)
    st.markdown("### Activities  <small>skills practice</small>", unsafe_allow_html=True)

    st.session_state.activities_count = st.selectbox("Number of activities", [1,2,3,4], index=1, key="acts_count")
    st.session_state.activity_minutes = st.number_input(
        "Minutes per activity", min_value=5, max_value=60, step=5, value=st.session_state.get("activity_minutes",20), key="acts_minutes"
    )
    st.caption("Pick Bloom verbs above; tasks align wording automatically.")

    if st.button("Generate Activities", type="primary", key="gen-acts"):
        try:
            acts = build_activities(topic_text, st.session_state.activities_count,
                                    st.session_state.activity_minutes, picked)
            st.session_state.last_generated["activities"] = acts
            st.success(f"Generated {len(acts)} activities.")
        except Exception as e:
            st.error(f"Could not generate activities: {e}")

    acts = st.session_state.last_generated.get("activities") or build_activities(topic_text, 2, 15, picked)
    for a in acts: st.write("• " + a)

    adb = docx_download("ADI_Activities.docx", [f"{i+1}. {a}" for i,a in enumerate(acts)])
    st.download_button("Download Activities (DOCX)", data=adb,
                       file_name="ADI_Activities.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       key=f"dlact-box")
    st.markdown('</div>', unsafe_allow_html=True)

# RIGHT TOP: MCQs
with c_right:
    st.markdown('<div class="card card-green">', unsafe_allow_html=True)
    st.markdown("### Knowledge MCQs  <small>ADI policy</small>", unsafe_allow_html=True)

    cA, cB, _ = st.columns([1,1,6])
    with cA:
        st.session_state.mcq_count = st.selectbox("How many MCQs?", [5,10,15,20,25,30], index=1, key="mcq_count")
    with cB:
        st.session_state.include_answer_key = st.checkbox(
            "Include answer key in export", value=st.session_state.get("include_answer_key", True), key="mcq_ans"
        )

    if st.button("Generate MCQs", type="primary", key="gen-mcqs"):
        try:
            mcqs = build_mcqs(topic_text, picked, st.session_state.mcq_count)
            st.session_state.last_generated["mcqs"] = mcqs
            st.success(f"Generated {len(mcqs)} MCQs.")
        except Exception as e:
            st.error(f"Could not generate MCQs: {e}")

    mcqs = st.session_state.last_generated.get("mcqs") or build_mcqs(topic_text, picked, 5)

    for i, q in enumerate(mcqs, 1):
        st.markdown(f"**Q{i}. {q['stem']}**")
        for opt in q["options"]: st.write(f"- {opt}")
        if st.session_state.include_answer_key: st.caption(f"Answer: {q['answer']}")
        st.divider()

    lines = []
    for i, q in enumerate(mcqs, 1):
        lines.append(f"Q{i}. {q['stem']}")
        lines.extend([f"- {o}" for o in q["options"]])
        if st.session_state.include_answer_key: lines.append(f"Answer: {q['answer']}")
        lines.append("")
    doc = docx_download("ADI_MCQs.docx", lines)
    st.download_button("Download MCQs (DOCX)", data=doc,
                       file_name="ADI_MCQs.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       key=f"dlmcq-box")
    st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT BOTTOM: Revision
    st.markdown('<div class="card card-blue">', unsafe_allow_html=True)
    st.markdown("### Revision  <small>link to prior learning</small>", unsafe_allow_html=True)

    rev_qty = st.selectbox("How many revision prompts?", list(range(3,13)), index=2, key="rev_qty")
    if st.button("Generate Revision", type="primary", key="gen-rev"):
        try:
            rev = build_revision(topic_text, picked, rev_qty)
            st.session_state.last_generated["revision"] = rev
            st.success(f"Generated {len(rev)} revision prompts.")
        except Exception as e:
            st.error(f"Could not generate revision: {e}")

    rev = st.session_state.last_generated.get("revision") or build_revision(topic_text, picked, 5)
    for r in rev: st.write("• " + r)

    rdb = docx_download("ADI_Revision.docx", [f"{i+1}. {r}" for i,r in enumerate(rev)])
    st.download_button("Download Revision (DOCX)", data=rdb,
                       file_name="ADI_Revision.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       key=f"dlrev-box")
    st.markdown('</div>', unsafe_allow_html=True)


# --------------------------- Print Summary ---------------------------

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### Print Summary")
g = st.session_state.last_generated
topic_text = st.session_state.source_text.strip()
st.write(
    f"**Course**: {st.session_state.course}  \\n"
    f"**Cohort**: {st.session_state.cohort}  \\n"
    f"**Instructor**: {st.session_state.instructor}  \\n"
    f"**Week**: {st.session_state.week}  \\n"
    f"**Lesson**: {st.session_state.lesson}  \\n"
    f"**Date**: {st.session_state.date_str}"
)
if topic_text:
    st.subheader("Module notes / outcomes")
    st.write(topic_text)
if g.get("mcqs"):
    st.subheader("Latest MCQs")
    for i, q in enumerate(g["mcqs"][:5], 1):
        st.write(f"{i}. {q['stem']}")
if g.get("activities"):
    st.subheader("Latest Activities")
    for a in g["activities"]:
        st.write("• " + a)
if g.get("revision"):
    st.subheader("Latest Revision")
    for r in g["revision"]:
        st.write("• " + r)
st.markdown('</div>', unsafe_allow_html=True)
