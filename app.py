# app.py — ADI Builder (all-in-one)

import base64
import io
import random
from uuid import uuid4
from datetime import date

import streamlit as st

# Optional libs for extraction (guarded)
try:
    import docx  # python-docx
    from docx import Document
except Exception:
    Document = None

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
except Exception:
    Presentation = None
    Inches = Pt = None

# PDF parsing (optional)
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# ---------- Helpers: load logo as base64 ----------
def _b64_of(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


_B64_LOGO = _b64_of("adi_logo.png")  # keep file at repo root


# ---------- BRAND CSS ----------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

st.markdown(
    """
<style>
/* Base spacing to avoid toolbar overlap */
.block-container { padding-top: 1.25rem; }

/* ADI banner */
.adi-hero {
  background: linear-gradient(180deg, #245a34 0%, #214d2f 100%);
  color: #fff;
  border-radius: 14px;
  padding: 18px 20px 16px 20px;
  box-shadow: 0 6px 18px rgba(0,0,0,.06);
  margin: 0 0 12px 0;
}
.adi-hero h1 {
  font-size: 1.05rem; margin: 0 0 4px 0; font-weight: 700;
}
.adi-hero p { margin: 0; font-size: .85rem; opacity: .95; }

/* Sidebar logo */
.adi-sidewrap { display:flex; align-items:center; gap:.5rem; }
.adi-logo { width: 180px; max-width: 100%; height:auto; display:block; }
.adi-badge { font-size:.75rem; color:#6b7280; margin-top:.25rem; }

/* Bloom sections */
.bloom-group {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 14px 14px 8px 14px;
  margin: 8px 0 6px 0;
}
.bloom-low    { background: linear-gradient(180deg,#f1f8f1, #ffffff); }
.bloom-med    { background: linear-gradient(180deg,#fff7e8, #ffffff); }
.bloom-high   { background: linear-gradient(180deg,#eef2ff, #ffffff); }

/* Verb chips */
.verb-grid { display:flex; flex-wrap:wrap; gap:14px; }
.verb-chip {
  border-radius: 999px;
  border: 1px solid #d1d5db;
  padding: 8px 14px;
  background:#fff;
  cursor:pointer;
  font-size:.92rem;
  transition: all .15s ease;
  user-select:none;
}
.verb-chip:hover { box-shadow: 0 2px 10px rgba(0,0,0,.06); }
.verb-chip.selected { 
  background:#def7e3; 
  border-color:#245a34; 
  box-shadow: 0 0 0 2px rgba(36,90,52,.15);
}
.bloom-tag {
  display:inline-block; padding:4px 10px; border-radius: 999px;
  font-size:.75rem; background:#edf2ee; color:#245a34; font-weight:600;
}
.hr-soft { height:1px; border:0; background:#e5e7eb; margin: 0.25rem 0 0.75rem 0; }
.small-muted { font-size:.8rem; color:#6b7280; }

/* Top input row alignment */
.top-row { display:grid; grid-template-columns: 1fr 1fr; gap:24px; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Sidebar (logo + directory manager) ----------
with st.sidebar:
    st.markdown(
        f"""
        <div class="adi-sidewrap">
            <img class="adi-logo" src="data:image/png;base64,{_B64_LOGO}" alt="ADI"/>
        </div>
        <div class="adi-badge">ADI</div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Session defaults ----------
def _init_state():
    defaults = dict(
        # directory
        courses=[],
        cohorts=[],
        instructors=[],
        course="",
        cohort="",
        instructor="",
        # context
        today=date.today().isoformat(),
        week=1,
        lesson=1,
        # content
        source_text="",
        uploaded_file=None,
        deep_scan=False,
        # bloom
        bloom_picks=set(),
        # outputs / controls
        include_answer_key=True,
        mcq_count=10,
        activities_count=2,
        activity_minutes=20,
        last_generated=None,
        tab="mcqs",
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Seed with ADI defaults once
    if not st.session_state.courses:
        st.session_state.courses = [
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
    if not st.session_state.cohorts:
        st.session_state.cohorts = [
            "D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
            "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06",
        ]
    if not st.session_state.instructors:
        st.session_state.instructors = [
            "GHAMZA LABEEB KHADER","DANIEL JOSEPH LAMB","NARDEEN TARIQ",
            "FAIZ LAZAM ALSHAMMARI","DR. MASHAEL ALSHAMMARI","AHMED ALBADER",
            "Noura Aldossari","Ahmed Gasem Alharbi","Mohammed Saeed Alfarhan",
            "Abdulmalik Halawani","Dari AlMutairi","Meshari AlMutrafi","Myra Crawford",
            "Meshal Alghurabi","Ibrahim Alrawili","Michail Mavroftas","Gerhard Van der Poel",
            "Khalil Razak","Mohammed Alwuthylah","Rana Ramadan","Salem Saleh Subaih",
            "Barend Daniel Esterhuizen",
        ]

_init_state()


# ---------- Hero ----------
st.markdown(
    """
<div class="adi-hero">
  <h1>ADI Builder — Lesson Activities &amp; Questions</h1>
  <p>Sleek, professional and engaging. Print-ready handouts for your instructors.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Left column controls (sidebar main) ----------
with st.sidebar:
    st.write("### Upload (optional)")
    uploaded = st.file_uploader(
        "Drag and drop file here", type=["txt", "docx", "pptx", "pdf"],
        help="TXT, DOCX, PPTX, PDF (200MB max)"
    )
    st.session_state.uploaded_file = uploaded

    st.write("### Course details")

    # Courses with +/-
    c_col1, c_col2, c_col3 = st.columns([6,1,1])
    with c_col1:
        st.session_state.course = st.selectbox(
            "Course name", options=st.session_state.courses, index=0 if st.session_state.courses else None,
            key="course_select"
        )
    with c_col2:
        if st.button("＋", help="Add Course name"):
            st.session_state.courses.insert(0, "New Course")
            st.session_state.course = st.session_state.courses[0]
    with c_col3:
        if st.button("－", help="Remove selected Course"):
            if st.session_state.course in st.session_state.courses:
                st.session_state.courses.remove(st.session_state.course)
                st.session_state.course = st.session_state.courses[0] if st.session_state.courses else ""

    # Cohorts with +/-
    coh1, coh2, coh3 = st.columns([6,1,1])
    with coh1:
        st.session_state.cohort = st.selectbox("Class / Cohort", st.session_state.cohorts, index=0)
    with coh2:
        if st.button("＋ ", key="add_cohort", help="Add Cohort"):
            st.session_state.cohorts.insert(0, "New Cohort")
            st.session_state.cohort = st.session_state.cohorts[0]
    with coh3:
        if st.button("－ ", key="del_cohort", help="Remove Cohort"):
            if st.session_state.cohort in st.session_state.cohorts:
                st.session_state.cohorts.remove(st.session_state.cohort)
                st.session_state.cohort = st.session_state.cohorts[0] if st.session_state.cohorts else ""

    # Instructors with +/-
    ins1, ins2, ins3 = st.columns([6,1,1])
    with ins1:
        st.session_state.instructor = st.selectbox("Instructor name", st.session_state.instructors, index=0)
    with ins2:
        if st.button("＋  ", key="add_instr", help="Add Instructor"):
            st.session_state.instructors.insert(0, "New Instructor")
            st.session_state.instructor = st.session_state.instructors[0]
    with ins3:
        if st.button("－  ", key="del_instr", help="Remove Instructor"):
            if st.session_state.instructor in st.session_state.instructors:
                st.session_state.instructors.remove(st.session_state.instructor)
                st.session_state.instructor = st.session_state.instructors[0] if st.session_state.instructors else ""

    st.write("### Date")
    st.session_state.today = st.text_input("Date", value=st.session_state.today)

    st.write("### Context")
    l1, l2 = st.columns(2)
    with l1:
        st.session_state.lesson = st.number_input("Lesson", min_value=1, value=int(st.session_state.lesson))
    with l2:
        st.session_state.week = st.number_input("Week", min_value=1, value=int(st.session_state.week))

    st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")


# ---------- Right column main ----------
# Top row: description + Bloom pill
st.markdown('<div class="top-row">', unsafe_allow_html=True)
st.markdown('<div>', unsafe_allow_html=True)

# Topic/Outcome + upload processing
st.write("**Topic / Outcome (optional)**")

st.session_state.source_text = st.text_area(
    "Module description, knowledge & skills outcomes",
    value=st.session_state.source_text, height=120, label_visibility="collapsed"
)

# Deep scan controls
st.session_state.deep_scan = st.toggle(
    "Deep scan source (slower, better coverage)",
    value=st.session_state.deep_scan,
    help="If enabled, we parse slides/tables more aggressively."
)

def extract_text(uploaded_file, deep: bool) -> str:
    if not uploaded_file:
        return ""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".txt"):
            return uploaded_file.getvalue().decode("utf-8", errors="ignore")
        if name.endswith(".docx") and Document:
            d = Document(uploaded_file)
            return "\n".join([p.text for p in d.paragraphs])
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(uploaded_file)
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        texts.append(shape.text)
            return "\n".join(texts)
        if name.endswith(".pdf") and fitz:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            texts = []
            for page in doc:
                texts.append(page.get_text("text" if not deep else "blocks"))
            return "\n".join([t if isinstance(t, str) else str(t) for t in texts])
    except Exception as e:
        st.warning(f"Could not parse {uploaded_file.name}: {e}")
    return ""

if st.session_state.uploaded_file and st.button("Process source"):
    with st.status("Processing upload…", expanded=False) as status:
        text = extract_text(st.session_state.uploaded_file, deep=st.session_state.deep_scan)
        st.session_state.source_text = text or st.session_state.source_text
        status.update(label="Upload processed", state="complete", expanded=False)

st.markdown('</div>', unsafe_allow_html=True)  # close left of top-row

# Bloom focus badge (auto by week)
def bloom_focus_by_week(w: int) -> str:
    if 1 <= w <= 4:
        return "Low"
    if 5 <= w <= 9:
        return "Medium"
    return "High"

focus = bloom_focus_by_week(int(st.session_state.week))
st.markdown(
    f"""
    <div style="display:flex; justify-content:flex-end;">
      <span class="bloom-tag">Week {int(st.session_state.week)}: {focus}</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)  # close top-row

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

# ---------- Bloom chips ----------
def verb_chip(label: str, key: str):
    picked = st.session_state.bloom_picks
    selected = label in picked
    cls = "verb-chip selected" if selected else "verb-chip"
    if st.button(label, key=key, help="Toggle", use_container_width=False):
        if label in picked:
            picked.remove(label)
        else:
            picked.add(label)
    st.markdown(
        f"""<script>
        const btn = window.parent.document.querySelector('button[data-testid="{key}"]');
        if (btn) {{ btn.classList.add('{cls}'); }}
        </script>""",
        unsafe_allow_html=True,
    )

def group(title: str, subtitle: str, verbs: list[str], css_class: str, prefix: str):
    st.markdown(f'<div class="bloom-group {css_class}">', unsafe_allow_html=True)
    st.markdown(f"**{title}**  \n<span class='small-muted'>{subtitle}</span>", unsafe_allow_html=True)
    st.markdown('<div class="verb-grid">', unsafe_allow_html=True)
    for v in verbs:
        verb_chip(v, key=f"{prefix}-{v}")
    st.markdown("</div></div>", unsafe_allow_html=True)

group(
    "Low (Weeks 1–4)",
    "Remember / Understand",
    ["define", "identify", "list", "recall", "describe", "label"],
    "bloom-low",
    "low"
)
group(
    "Medium (Weeks 5–9)",
    "Apply / Analyse",
    ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"],
    "bloom-med",
    "med"
)
group(
    "High (Weeks 10–14)",
    "Evaluate / Create",
    ["evaluate", "synthesize", "design", "justify", "critique", "create"],
    "bloom-high",
    "high"
)

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

# ---------- Content builders & exports ----------
def _shuffle_mcq_options(opts: list[str]) -> list[str]:
    banned = {"all of the above", "none of the above", "true", "false"}
    clean = [o for o in opts if o.strip().lower() not in banned]
    random.shuffle(clean)
    return clean

def build_mcqs(topic: str, verbs: list[str], count: int) -> list[dict]:
    mcqs = []
    for i in range(count):
        v = random.choice(verbs) if verbs else "identify"
        stem = f"{v.title()} — {topic or 'Topic'} — Q{i+1}"
        options = _shuffle_mcq_options(["Option A", "Option B", "Option C", "Option D"])
        if "Correct answer" not in options:
            options = options[:3] + ["Correct answer"]
        options = _shuffle_mcq_options(options)
        mcqs.append({"stem": stem, "options": options, "answer": "Correct answer"})
    return mcqs

def build_activities(topic: str, n: int, minutes: int, verbs: list[str]) -> list[str]:
    verbs = verbs or ["apply", "demonstrate", "solve"]
    out = []
    for i in range(1, n+1):
        out.append(f"Activity {i} ({minutes} min): {verbs[i % len(verbs)]} on {topic or 'today’s concept'} using a worked example / mini-lab.")
    return out

def build_revision(topic: str, verbs: list[str], qty: int = 5) -> list[str]:
    verbs = verbs or ["recall", "classify", "compare", "justify", "design"]
    out = []
    for i in range(1, qty+1):
        v = verbs[i % len(verbs)]
        out.append(f"Rev {i}: {v.title()} — link this week to prior learning for {topic or 'the module'} (3–4 sentences).")
    return out

def docx_download(filename: str, paragraphs: list[str]) -> io.BytesIO:
    if not Document:
        buf = io.BytesIO()
        buf.write("\n".join(paragraphs).encode("utf-8"))
        buf.seek(0)
        return buf
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf); buf.seek(0)
    return buf

def pptx_download(title: str, bullets: list[str]) -> io.BytesIO:
    if not Presentation:
        # Fallback to text buffer if python-pptx missing
        buf = io.BytesIO()
        buf.write((title + "\n" + "\n".join(bullets)).encode("utf-8"))
        buf.seek(0)
        return buf
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # title only
    slide.shapes.title.text = title
    left = Inches(1); top = Inches(1.8); width = Inches(8); height = Inches(4.5)
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame; tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.add_paragraph() if i else tf.paragraphs[0]
        p.text = b; p.level = 0
        if Pt:
            p.font.size = Pt(18)
    buf = io.BytesIO()
    prs.save(buf); buf.seek(0)
    return buf


# ---------- Tabs ----------
tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision", "Print Summary"])
picked_verbs = sorted(list(st.session_state.get("bloom_picks", set())))
topic_text = st.session_state.get("source_text", "").strip()

# MCQs
with tabs[0]:
    cA, cB, _ = st.columns([1,1,4])
    with cA:
        st.session_state.mcq_count = st.selectbox("How many MCQs?", [5,10,15,20,25,30], index=1)
    with cB:
        st.session_state.include_answer_key = st.checkbox("Include answer key in export", value=st.session_state.include_answer_key)

    if st.button("Generate MCQs", type="primary"):
        mcqs = build_mcqs(topic_text, picked_verbs, st.session_state.mcq_count)
        st.session_state.last_generated = st.session_state.get("last_generated") or {}
        st.session_state.last_generated["mcqs"] = mcqs
        st.success(f"Generated {len(mcqs)} MCQs.")

    mcqs = (st.session_state.get("last_generated") or {}).get("mcqs", [])
    if mcqs:
        for i, q in enumerate(mcqs, 1):
            st.markdown(f"**Q{i}. {q['stem']}**")
            for opt in q["options"]:
                st.write(f"- {opt}")
            if st.session_state.include_answer_key:
                st.caption(f"Answer: {q['answer']}")
            st.divider()

        doc_buf = docx_download(
            "ADI_MCQs.docx",
            [
                f"Q{i}. {q['stem']}\n" + "\n".join([f"- {o}" for o in q["options"]]) +
                (f"\nAnswer: {q['answer']}" if st.session_state.include_answer_key else "")
                for i, q in enumerate(mcqs, 1)
            ],
        )
        st.download_button(
            "Download MCQs (DOCX)", data=doc_buf,
            file_name="ADI_MCQs.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dl-mcqs-{uuid4().hex}",
        )

        ppt_buf = pptx_download("MCQs (Preview Deck)", [q["stem"] for q in mcqs[:10]])
        st.download_button(
            "Download MCQs (PPTX)", data=ppt_buf,
            file_name="ADI_MCQs.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key=f"dl-mcqs-ppt-{uuid4().hex}",
        )

# Activities
with tabs[1]:
    a1, a2, a3 = st.columns([1,1,3])
    with a1:
        st.session_state.activities_count = st.selectbox("Number of activities", [1,2,3,4], index=1)
    with a2:
        st.session_state.activity_minutes = st.select_slider("Minutes per activity", options=list(range(5,65,5)), value=20)
    with a3:
        st.markdown("Pick Bloom verbs above; tasks align wording automatically.")

    if st.button("Generate Activities", type="primary", key="btn-acts"):
        acts = build_activities(topic_text, st.session_state.activities_count, st.session_state.activity_minutes, picked_verbs)
        st.session_state.last_generated = st.session_state.get("last_generated") or {}
        st.session_state.last_generated["activities"] = acts
        st.success(f"Generated {len(acts)} activities.")

    acts = (st.session_state.get("last_generated") or {}).get("activities", [])
    if acts:
        for a in acts:
            st.write("• " + a)
        adb = docx_download("ADI_Activities.docx", [f"{i+1}. {a}" for i,a in enumerate(acts)])
        st.download_button(
            "Download Activities (DOCX)", data=adb,
            file_name="ADI_Activities.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dl-acts-{uuid4().hex}",
        )

# Revision
with tabs[2]:
    qty = st.slider("How many revision prompts?", 3, 12, 5, step=1)
    if st.button("Generate Revision", type="primary", key="btn-rev"):
        rev = build_revision(topic_text, picked_verbs, qty)
        st.session_state.last_generated = st.session_state.get("last_generated") or {}
        st.session_state.last_generated["revision"] = rev
        st.success(f"Generated {len(rev)} revision prompts.")

    rev = (st.session_state.get("last_generated") or {}).get("revision", [])
    if rev:
        for r in rev:
            st.write("• " + r)
        rdb = docx_download("ADI_Revision.docx", [f"{i+1}. {r}" for i,r in enumerate(rev)])
        st.download_button(
            "Download Revision (DOCX)", data=rdb,
            file_name="ADI_Revision.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dl-rev-{uuid4().hex}",
        )

# Print Summary
with tabs[3]:
    st.caption("A single, printable overview of your session context and the latest generated content.")
    st.subheader("Context")
    st.write(
        f"**Course**: {st.session_state.get('course', '')}  \n"
        f"**Cohort**: {st.session_state.get('cohort', '')}  \n"
        f"**Instructor**: {st.session_state.get('instructor', '')}  \n"
        f"**Week**: {st.session_state.get('week', 1)}  \n"
        f"**Lesson**: {st.session_state.get('lesson', 1)}"
    )

    if topic_text:
        st.subheader("Module notes / outcomes")
        st.write(topic_text)

    lg = st.session_state.get("last_generated") or {}
    if lg.get("mcqs"):
        st.subheader("Latest MCQs")
        for i, q in enumerate(lg["mcqs"][:5], 1):
            st.write(f"{i}. {q['stem']}")
    if lg.get("activities"):
        st.subheader("Latest Activities")
        for a in lg["activities"]:
            st.write("• " + a)
    if lg.get("revision"):
        st.subheader("Latest Revision")
        for r in lg["revision"]:
            st.write("• " + r)

    lines = []
    lines.append(f"Course: {st.session_state.get('course','')}")
    lines.append(f"Cohort: {st.session_state.get('cohort','')}")
    lines.append(f"Instructor: {st.session_state.get('instructor','')}")
    lines.append(f"Week {st.session_state.get('week',1)}, Lesson {st.session_state.get('lesson',1)}")
    lines.append("")
    if topic_text:
        lines.append("Module notes / outcomes")
        lines.append(topic_text); lines.append("")
    if lg.get("mcqs"):
        lines.append("MCQs (first 5)")
        for i, q in enumerate(lg["mcqs"][:5], 1):
            lines.append(f"{i}. {q['stem']}")
        lines.append("")
    if lg.get("activities"):
        lines.append("Activities")
        for a in lg["activities"]:
            lines.append("• " + a)
        lines.append("")
    if lg.get("revision"):
        lines.append("Revision")
        for r in lg["revision"]:
            lines.append("• " + r)

    psb = docx_download("ADI_Print_Summary.docx", lines)
    st.download_button(
        "Download Print Summary (DOCX)", data=psb,
        file_name="ADI_Print_Summary.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"dl-sum-{uuid4().hex}",
    )

