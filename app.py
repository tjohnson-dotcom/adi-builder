# app.py — ADI Builder (stable: no flicker, clean pages, full lists, real MCQs)

import io, base64, random, re
from collections import Counter
from datetime import date
import streamlit as st

# -------------------- optional libs (soft imports) --------------------
try:
    from docx import Document
except Exception:
    Document = None
try:
    from pptx import Presentation
except Exception:
    Presentation = None
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# -------------------- setup --------------------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# Strong, readable UI + focus highlight for current week band
st.markdown("""
<style>
.block-container { padding-top: 1rem; }
.adi-hero {background: linear-gradient(180deg,#245a34 0%, #214d2f 100%);
  color:#fff;border-radius:14px;padding:14px 16px;box-shadow:0 6px 18px rgba(0,0,0,.06);margin-bottom:10px;}
.adi-hero * {color:#fff !important;}
.adi-hero h1 {font-size:1.0rem;margin:0 0 4px 0;font-weight:700;}
.adi-hero p  {font-size:.85rem;margin:0;opacity:.96;}
.adi-logo { width: 180px; max-width: 100%; height:auto; display:block; }
.hr-soft { height:1px; border:0; background:#e5e7eb; margin:.4rem 0 1rem 0; }
.bloom-group {border:1px solid #e5e7eb;border-radius:12px;padding:12px 12px 8px 12px;margin:10px 0;background:#fff;}
.bloom-low  { background: linear-gradient(180deg,#f1f8f1, #ffffff); }
.bloom-med  { background: linear-gradient(180deg,#fff7e8, #ffffff); }
.bloom-high { background: linear-gradient(180deg,#eef2ff, #ffffff); }
.bloom-focus {
  border: 2px solid #245a34 !important;
  box-shadow: 0 0 0 3px rgba(36,90,52,.12) inset !important;
  background: linear-gradient(180deg, #eaf4ec, #ffffff) !important;
}
.bloom-caption {font-size:.80rem;color:#6b7280;margin-left:6px;}
.bloom-pill {display:inline-block;background:#edf2ee;color:#245a34;border-radius:999px;padding:4px 10px;font-weight:600;font-size:.75rem;}
.card {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#fff;}
</style>
""", unsafe_allow_html=True)

# -------------------- small helpers --------------------
def _b64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""

def week_focus_band(w: int) -> str:
    try: w = int(w)
    except: w = 1
    if 1 <= w <= 4: return "Low"
    if 5 <= w <= 9: return "Medium"
    return "High"

@st.cache_data(show_spinner=False)
def parse_upload_bytes(name: str, data: bytes, deep=False) -> str:
    """Parse upload from raw bytes; cached to prevent flicker & rework."""
    name = (name or "").lower()
    try:
        if name.endswith(".txt"):
            return data.decode("utf-8", errors="ignore")

        if name.endswith(".docx") and Document:
            bio = io.BytesIO(data)
            d = Document(bio)
            return "\n".join(p.text for p in d.paragraphs)

        if name.endswith(".pptx") and Presentation:
            prs = Presentation(io.BytesIO(data))
            lines = []
            for slide in prs.slides:
                for sh in slide.shapes:
                    if hasattr(sh, "text") and sh.text:
                        lines.append(sh.text)
            return "\n".join(lines)

        if name.endswith(".pdf") and fitz:
            doc = fitz.open(stream=data, filetype="pdf")
            texts = []
            for pg in doc:
                try:
                    t = pg.get_text("blocks" if deep else "text") or ""
                except Exception:
                    t = ""
                texts.append(t)
            return "\n".join(texts)
    except Exception as e:
        return f"[Parse error] {e}"
    return ""

def docx_download(lines):
    # DOCX if python-docx available; else TXT
    if not Document:
        buf = io.BytesIO()
        buf.write("\n".join(lines).encode("utf-8"))
        buf.seek(0); return buf
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    buf = io.BytesIO(); doc.save(buf); buf.seek(0); return buf

def _keywords(text: str, k: int = 6):
    words = re.findall(r"[A-Za-zأ-ي]+", (text or ""))
    stop = set("""a an the and or of for with to in on at by from this that these those is are was were be been being
                  into about as it its they them then than can could should would may might will shall
                  اذا هذا هذه تلك الذي التي الذين اللواتي وال او ثم لما لأن إن كان كانت يكون""".split())
    toks = [w.lower() for w in words if len(w) > 2 and w.lower() not in stop]
    common = [w for w,_ in Counter(toks).most_common(k)]
    return common or ["system","process","quality","inspection","materials","safety"]

def build_mcqs(topic: str, verbs: list[str], n: int):
    """Meaningful stems + A/B/C/D options with an answer."""
    verbs = list(verbs) or ["identify","define","list","describe","apply","compare"]
    keys = _keywords(topic or st.session_state.get("source_text",""))
    out = []
    for i in range(n):
        v  = verbs[i % len(verbs)]
        kw = keys[i % len(keys)]
        if v in ("identify","define","list","describe","classify","compare"):
            stem    = f"{v.title()} the best statement about **{kw}**."
            correct = f"{kw.title()}: the most accurate description in the module context."
        elif v in ("apply","demonstrate","solve"):
            stem    = f"{v.title()} how **{kw}** is used in a realistic defense-tech scenario."
            correct = f"Correct application of {kw} aligned to course policy."
        else:
            stem    = f"{v.title()} the implications of **{kw}** in practice."
            correct = f"Reasoned conclusion about {kw} supported by evidence."
        distractors = [
            f"An incomplete or vague statement about {kw}.",
            f"A common misconception regarding {kw}.",
            f"An unrelated detail not tied to {kw}.",
        ]
        options = [correct] + distractors
        random.shuffle(options)
        out.append({"stem": stem, "options": options[:4], "answer": correct})
    return out

def build_activities(topic, n, minutes, verbs):
    verbs = list(verbs) or ["apply","demonstrate","solve"]
    return [f"Activity {i} ({minutes} min): {verbs[(i-1)%len(verbs)]} on {topic or 'today’s concept'} via example / mini-lab."
            for i in range(1, n+1)]

def build_revision(topic, verbs, qty=5):
    verbs = list(verbs) or ["recall","classify","compare","justify","design"]
    return [f"Rev {i}: {verbs[(i-1)%len(verbs)]}. Connect this week to prior learning for {topic or 'the module'} (3–4 sentences)."
            for i in range(1, qty+1)]

# -------------------- defaults (one-time) --------------------
s = st.session_state
if "_ok" not in s:
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
    s.lesson = 1
    s.week = 1
    s.date_str = date.today().isoformat()
    s.source_text = ""
    s.deep_scan = False
    s.bloom_picks = set()
    s.last_generated = {}

# -------------------- hero --------------------
LOGO64 = _b64("adi_logo.png")
st.markdown("""
<div class="adi-hero">
  <h1>ADI Builder — Lesson Activities &amp; Questions</h1>
  <p>Sleek, professional and engaging. Print-ready handouts for your instructors.</p>
</div>
""", unsafe_allow_html=True)

# -------------------- sidebar (stable, no rerun) --------------------
with st.sidebar:
    if LOGO64:
        st.markdown(f'<img class="adi-logo" src="data:image/png;base64,{LOGO64}" alt="ADI logo"/>', unsafe_allow_html=True)
    st.caption("ADI")

    st.write("### Upload (optional)")
    st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"], key="uploader")
    f = s.get("uploader")
    if f is not None:
        size_kb = (getattr(f, "size", 0) or 0) / 1024
        st.success(f"✅ File selected: **{f.name}** ({size_kb:.1f} KB)")
    if st.button("Process source", disabled=(f is None)):
        try:
            with st.spinner("Processing upload…"):
                data = f.getvalue() if hasattr(f, "getvalue") else f.read()
                text = parse_upload_bytes(f.name, data, deep=s.get("deep_scan", False))
                if text.strip() and not text.startswith("[Parse error]"):
                    s["source_text"] = text
                    st.toast("Upload processed.", icon="✅")
                else:
                    st.warning("No readable text found in that file.")
            s["uploader"] = None  # clear to avoid exhausted stream
        except Exception as e:
            st.error(f"Could not process file: {e}")

    st.write("### Course details")
    st.selectbox("Course name", s.courses, index=0, key="course_sel")
    st.selectbox("Class / Cohort", s.cohorts, index=0, key="coh_sel")
    st.selectbox("Instructor name", s.instructors, index=0, key="ins_sel")
    st.text_input("Date", key="date_str")

    st.write("### Context")
    c1, c2 = st.columns(2)
    with c1: st.number_input("Lesson", min_value=1, key="lesson")
    with c2: st.number_input("Week", min_value=1, key="week")
    st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

# -------------------- main inputs --------------------
st.write("**Topic / Outcome (optional)**")
st.text_area("Module description, knowledge & skills outcomes",
             value=s.get("source_text",""), height=110, label_visibility="collapsed", key="source_text")
st.toggle("Deep scan source (slower, better coverage)", value=s.get("deep_scan", False), key="deep_scan")

# -------------------- Bloom blocks with highlight --------------------
LOW = ["define","identify","list","recall","describe","label"]
MED = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH= ["evaluate","synthesize","design","justify","critique","create"]

focus_band = week_focus_band(s.get("week", 1))
st.markdown(f"<div style='text-align:right'><span class='bloom-pill'>Week {int(s.get('week',1))}: {focus_band}</span></div>", unsafe_allow_html=True)

def bloom_group(title, subtitle, verbs, css, band_name):
    picks = s.setdefault("bloom_picks", set())
    classes = f"bloom-group {css}" + (" bloom-focus" if band_name == focus_band else "")
    st.markdown(f'<div class="{classes}">', unsafe_allow_html=True)
    st.markdown(f"**{title}**  <span class='bloom-caption'>{subtitle}</span>", unsafe_allow_html=True)
    cols = st.columns(len(verbs))
    for i, v in enumerate(verbs):
        with cols[i]:
            k = f"verb-{v}"
            val = st.checkbox(v, value=s.get(k, False), key=k)
            if val: picks.add(v)
            else: picks.discard(v)
    st.markdown("</div>", unsafe_allow_html=True)

bloom_group("Low (Weeks 1–4)","Remember / Understand", LOW,"bloom-low","Low")
bloom_group("Medium (Weeks 5–9)","Apply / Analyse", MED,"bloom-med","Medium")
bloom_group("High (Weeks 10–14)","Evaluate / Create", HIGH,"bloom-high","High")

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

# -------------------- Page switcher --------------------
page = st.radio("Mode", ["Activities","MCQs","Revision","Print Summary"], horizontal=True, key="mode_radio")

picked = sorted(list(s.get("bloom_picks", set())))
topic  = s.get("source_text","").strip()

if page == "Activities":
    st.subheader("Activities")
    st.selectbox("Number of activities", [1,2,3,4], index=1, key="acts_count_sel")
    st.number_input("Minutes per activity", min_value=5, max_value=60, step=5, value=20, key="acts_minutes_input")
    if st.button("Generate Activities", type="primary"):
        s.last_generated["activities"] = build_activities(topic, s.get("acts_count_sel",2), s.get("acts_minutes_input",20), picked)
        st.success(f"Generated {len(s.last_generated['activities'])} activities.")
    acts = s.last_generated.get("activities") or build_activities(topic, 2, 15, picked)
    for a in acts: st.write("• " + a)
    st.download_button("Download Activities (DOCX)",
                       data=docx_download([f"{i+1}. {a}" for i,a in enumerate(acts)]),
                       file_name="ADI_Activities.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif page == "MCQs":
    st.subheader("Knowledge MCQs")
    st.selectbox("How many MCQs?", [5,10,15,20,25,30], index=1, key="mcq_count_sel")
    st.checkbox("Include answer key in export", value=True, key="include_answer_chk")
    if st.button("Generate MCQs", type="primary"):
        s.last_generated["mcqs"] = build_mcqs(topic, picked, s.get("mcq_count_sel",10))
        st.success(f"Generated {len(s.last_generated['mcqs'])} MCQs.")
    mcqs = s.last_generated.get("mcqs") or build_mcqs(topic, picked, 5)

    letters = ["A","B","C","D"]
    for i, q in enumerate(mcqs, 1):
        st.markdown(f"**Q{i}. {q['stem']}**")
        for L, opt in zip(letters, q["options"][:4]):
            st.write(f"- **{L}.** {opt}")
        if s.get("include_answer_chk", True):
            st.caption(f"Answer: {q['answer']}")
        st.divider()

    lines = []
    for i, q in enumerate(mcqs, 1):
        lines.append(f"Q{i}. {q['stem']}")
        for L, opt in zip(letters, q["options"][:4]):
            lines.append(f"{L}. {opt}")
        if s.get("include_answer_chk", True):
            lines.append(f"Answer: {q['answer']}")
        lines.append("")
    st.download_button("Download MCQs (DOCX)",
                       data=docx_download(lines),
                       file_name="ADI_MCQs.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif page == "Revision":
    st.subheader("Revision")
    st.selectbox("How many revision prompts?", list(range(3,13)), index=2, key="rev_qty_sel")
    if st.button("Generate Revision", type="primary"):
        s.last_generated["revision"] = build_revision(topic, picked, s.get("rev_qty_sel",5))
        st.success(f"Generated {len(s.last_generated['revision'])} revision prompts.")
    rev = s.last_generated.get("revision") or build_revision(topic, picked, 5)
    for r in rev: st.write("• " + r)
    st.download_button("Download Revision (DOCX)",
                       data=docx_download([f"{i+1}. {r}" for i,r in enumerate(rev)]),
                       file_name="ADI_Revision.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

else:
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
