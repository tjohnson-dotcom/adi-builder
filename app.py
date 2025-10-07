# app.py — ADI Builder (native-Streamlit UI, stable)
import io, base64, random
from datetime import date
from uuid import uuid4
import streamlit as st

# put near the top of app.py
try:
    import fitz  # PyMuPDF
    PDF_ENABLED = True
except Exception:
    fitz = None
    PDF_ENABLED = False


# Optional libs (still runs if not installed)
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

def _b64(p):
    try:
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")
    except Exception: return ""

def week_focus(w:int)->str:
    return "Low" if 1<=w<=4 else ("Medium" if 5<=w<=9 else "High")

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")
LOGO64 = _b64("adi_logo.png")

# ---------- CSS (native controls only) ----------
st.markdown("""
<style>
.block-container{padding-top:.8rem;}
.adi-hero{background:#245a34;color:#fff;border-radius:14px;padding:14px 18px;
  box-shadow:0 6px 18px rgba(0,0,0,.06);margin:6px 0 10px 0;}
.adi-hero *{color:#fff !important;}
.adi-hero h1{font-size:1.06rem;margin:0 0 3px 0;font-weight:700;}
.adi-hero p{font-size:.86rem;margin:0;opacity:.96;}
.adi-logo{height:70px;width:auto;display:block;margin:2px 0 8px 0;}
.hr-soft{height:1px;border:0;background:#e5e7eb;margin:.4rem 0 1rem 0;}

.bloom-wrap{border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;margin:10px 0;}
.low{background:linear-gradient(180deg,#f1f8f1,#ffffff);}
.med{background:linear-gradient(180deg,#fff7e8,#ffffff);}
.high{background:linear-gradient(180deg,#eef2ff,#ffffff);}
.focus{box-shadow:0 0 0 2px rgba(36,90,52,.12) inset;border-color:#245a34;}
.active{box-shadow:0 0 0 2px rgba(36,90,52,.18) inset;border-color:#245a34;}

.bloom-caption{font-size:.80rem;color:#6b7280;margin-left:6px;}
.bloom-pill{display:inline-block;background:#edf2ee;color:#245a34;
  border-radius:999px;padding:4px 10px;font-weight:600;font-size:.75rem;}
/* Make Streamlit checkboxes look like chips */
.stCheckbox > label{border:1px solid #d1d5db;border-radius:999px;padding:6px 12px !important;
  background:#fff;display:inline-flex;align-items:center;gap:8px;}
.stCheckbox:hover > label{box-shadow:0 2px 10px rgba(0,0,0,.06);}
.stCheckbox input{margin:0;}
/* Checked state */
.stCheckbox:has(input:checked) > label{
  background:#def7e3;border-color:#245a34;box-shadow:0 0 0 2px rgba(36,90,52,.15);
}
</style>
""", unsafe_allow_html=True)

# ---------- session ----------
def init():
    s=st.session_state
    if s.get("_ok"): return
    s._ok=True
    s.courses=[ "Defense Technology Practices: Experimentation, Quality Management and Inspection (GE4-EPM)",
        "Integrated Project and Materials Management in Defense Technology (GE4-IPM)",
        "Military Vehicle and Aircraft MRO: Principles & Applications (GE4-MRO)",
        "Computation for Chemical Technologists (CT4-COM)","Explosives Manufacturing (CT4-EMG)",
        "Thermofluids (CT4-TFL)","Composite Manufacturing (MT4-CMG)","Computer Aided Design (MT4-CAD)",
        "Machine Elements (MT4-MAE)","Electrical Materials (EE4-MFC)","PCB Manufacturing (EE4-PMG)",
        "Power Circuits & Transmission (EE4-PCT)","Mechanical Product Dissection (MT5-MPD)",
        "Assembly Technology (MT5-AST)","Aviation Maintenance (MT5-AVM)","Hydraulics and Pneumatics (MT5-HYP)",
        "Computer Aided Design and Additive Manufacturing (MT5-CAD)","Industrial Machining (MT5-CNC)",
        "Thermochemistry of Explosives (CT5-TCE)","Separation Technologies 1 (CT5-SET)",
        "Explosives Plant Operations and Troubleshooting (CT5-POT)","Coating Technologies (CT5-COT)",
        "Chemical Technology Laboratory Techniques (CT5-LAB)","Chemical Process Technology (CT5-CPT)" ]
    s.cohorts=["D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
               "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"]
    s.instructors=["GHAMZA LABEEB KHADER","DANIEL JOSEPH LAMB","NARDEEN TARIQ","FAIZ LAZAM ALSHAMMARI",
        "DR. MASHAEL ALSHAMMARI","AHMED ALBADER","Noura Aldossari","Ahmed Gasem Alharbi",
        "Mohammed Saeed Alfarhan","Abdulmalik Halawani","Dari AlMutairi","Meshari AlMutrafi",
        "Myra Crawford","Meshal Alghurabi","Ibrahim Alrawili","Michail Mavroftas",
        "Gerhard Van der Poel","Khalil Razak","Mohammed Alwuthylah","Rana Ramadan",
        "Salem Saleh Subaih","Barend Daniel Esterhuizen"]
    s.course=s.courses[0]; s.cohort=s.cohorts[0]; s.instructor=s.instructors[0]
    s.lesson=1; s.week=1; s.date_str=date.today().isoformat()
    s.upload=None; s.deep=False; s.src=""; s.notes=""
    s.picks=set()
    s.mcq_n=10; s.ans=True; s.act_n=2; s.act_min=20
    s.last={}
init()

# ---------- hero + sidebar ----------
st.markdown("""
<div class="adi-hero">
  <h1>ADI Builder — Lesson Activities &amp; Questions</h1>
  <p>Sleek, professional and engaging. Print-ready handouts for your instructors.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    if LOGO64:
        st.markdown(f'<img class="adi-logo" src="data:image/png;base64,{LOGO64}" />', unsafe_allow_html=True)
    st.caption("ADI")

    st.write("### Upload (optional)")
    st.session_state.upload = st.file_uploader("Drag and drop file here",
        type=["txt","docx","pptx","pdf"], help="Limit 200MB per file • TXT, DOCX, PPTX, PDF")

    st.write("### Course details")
    c1,c2,c3=st.columns([6,1,1])
    with c1: st.session_state.course = st.selectbox("Course name", st.session_state.courses)
    with c2:
        if st.button("＋", help="Add Course"):
            st.session_state.courses.insert(0,"New Course")
            st.session_state.course=st.session_state.courses[0]
    with c3:
        if st.button("－", help="Remove Course") and len(st.session_state.courses)>1:
            lst=st.session_state.courses; lst.remove(st.session_state.course); st.session_state.course=lst[0]

    d1,d2,d3=st.columns([6,1,1])
    with d1: st.session_state.cohort = st.selectbox("Class / Cohort", st.session_state.cohorts)
    with d2:
        if st.button("＋ ", key="adch"): st.session_state.cohorts.insert(0,"New Cohort")
    with d3:
        if st.button("－ ", key="rmch") and len(st.session_state.cohorts)>1:
            lst=st.session_state.cohorts; lst.remove(st.session_state.cohort); st.session_state.cohort=lst[0]

    i1,i2,i3=st.columns([6,1,1])
    with i1: st.session_state.instructor = st.selectbox("Instructor name", st.session_state.instructors)
    with i2:
        if st.button("＋  ", key="adin"): st.session_state.instructors.insert(0,"New Instructor")
    with i3:
        if st.button("－  ", key="rmin") and len(st.session_state.instructors)>1:
            lst=st.session_state.instructors; lst.remove(st.session_state.instructor); st.session_state.instructor=lst[0]

    st.write("### Date")
    st.session_state.date_str = st.text_input("Date", st.session_state.date_str)

    st.write("### Context")
    a,b=st.columns(2)
    with a: st.session_state.lesson = st.number_input("Lesson",1,100,st.session_state.lesson)
    with b: st.session_state.week   = st.number_input("Week",1,14,st.session_state.week)

    st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

# ---------- parsing ----------
if filetype == "pdf":
    if PDF_ENABLED:
        # existing PDF parsing code...
        pass
    else:
        st.info("PDF parsing temporarily disabled on this build.")
        st.stop()


def parse_upload(file, deep=False)->str:
    if not file: return ""
    nm=file.name.lower()
    try:
        if nm.endswith(".txt"): return file.getvalue().decode("utf-8","ignore")
        if nm.endswith(".docx") and Document:
            d=Document(file); return "\n".join(p.text for p in d.paragraphs)
        if nm.endswith(".pptx") and Presentation:
            prs=Presentation(file); lines=[]
            for sl in prs.slides:
                for sh in sl.shapes:
                    if hasattr(sh,"text"): lines.append(sh.text)
            return "\n".join(lines)
        if nm.endswith(".pdf") and fitz:
            doc=fitz.open(stream=file.read(), filetype="pdf"); txt=[]
            for pg in doc:
                if deep:
                    blocks=pg.get_text("blocks"); txt.append("\n".join(b[4] for b in blocks if isinstance(b,tuple) and len(b)>=5))
                else:
                    txt.append(pg.get_text("text"))
            return "\n".join(txt)
    except Exception as e:
        st.warning(f"Could not parse file: {e}")
    return ""

st.write("**Topic / Outcome (optional)**")
st.session_state.deep = st.toggle("Deep scan source (slower, better coverage)", value=st.session_state.deep)
cU1,cU2=st.columns([1,3])
with cU1:
    if st.session_state.upload and st.button("Process source", type="primary"):
        with st.spinner("Processing upload…"):
            st.session_state.src = parse_upload(st.session_state.upload, st.session_state.deep) or ""
        st.success("Upload processed.")
with cU2:
    st.session_state.notes = st.text_area("Add short notes / outcomes (optional)",
                                          value=st.session_state.notes, height=100, label_visibility="collapsed")
if st.session_state.src:
    pv=st.session_state.src[:1400] + (" …" if len(st.session_state.src)>1400 else "")
    with st.expander("Preview of parsed source", expanded=False): st.write(pv)

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

# ---------- Bloom (all native controls) ----------
LOW  = ["define","identify","list","recall","describe","label"]
MED  = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH = ["evaluate","synthesize","design","justify","critique","create"]

def check_row(verbs:list[str], cols=6):
    cols_list = st.columns(cols)
    for i,v in enumerate(verbs):
        with cols_list[i%cols]:
            val = st.checkbox(v, value=(v in st.session_state.picks), key=f"v-{v}")
            if val: st.session_state.picks.add(v)
            else:   st.session_state.picks.discard(v)

focus = week_focus(int(st.session_state.week))
st.markdown(f"<div style='text-align:right'><span class='bloom-pill'>Week {int(st.session_state.week)}: {focus}</span></div>", unsafe_allow_html=True)

def band(title, subtitle, verbs, cls, focus_name):
    active = any(v in st.session_state.picks for v in verbs)
    classes = ["bloom-wrap", cls]
    if focus==focus_name: classes.append("focus")
    if active: classes.append("active")
    st.markdown(f"<div class='{ ' '.join(classes) }'>**{title}**  <span class='bloom-caption'>{subtitle}</span></div>", unsafe_allow_html=True)
    check_row(verbs)

band("Low (Weeks 1–4)","Remember / Understand", LOW,  "low",  "Low")
band("Medium (Weeks 5–9)","Apply / Analyse",     MED,  "med",  "Medium")
band("High (Weeks 10–14)","Evaluate / Create",   HIGH, "high", "High")

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

# ---------- Generators ----------
def _clean(opts):
    banned={"all of the above","none of the above","true","false"}
    x=[o for o in opts if o.strip().lower() not in banned]; random.shuffle(x); return x

def build_mcqs(topic, verbs, n):
    out=[]; verbs=verbs or ["identify"]
    for i in range(n):
        v=random.choice(verbs); stem=f"{v.title()} — {topic or 'Topic'} — Q{i+1}"
        opts=_clean(["Option A","Option B","Option C","Correct answer","Option D"])
        out.append({"stem":stem,"options":opts,"answer":"Correct answer"})
    return out

def build_activities(topic, n, minutes, verbs):
    verbs=verbs or ["apply","demonstrate","solve"]; a=[]
    for i in range(1,n+1):
        a.append(f"Activity {i} ({minutes} min): {verbs[i%len(verbs)]} on {topic or 'today’s concept'} via example / mini-lab.")
    return a

def build_revision(topic, verbs, qty=5):
    verbs=verbs or ["recall","classify","compare","justify","design"]; r=[]
    for i in range(1,qty+1):
        v=verbs[i%len(verbs)]; r.append(f"Rev {i}: {v.title()} — connect this week to prior learning for {topic or 'the module'} (3–4 sentences).")
    return r

# ---------- Exports ----------
def docx_download(fname, lines):
    if not Document:
        buf=io.BytesIO(); buf.write("\n".join(lines).encode("utf-8")); buf.seek(0); return buf
    d=Document()
    for ln in lines: d.add_paragraph(ln)
    buf=io.BytesIO(); d.save(buf); buf.seek(0); return buf

def pptx_download(title, bullets):
    if not Presentation:
        buf=io.BytesIO(); buf.write((title+"\n"+"\n".join(bullets)).encode("utf-8")); buf.seek(0); return buf
    prs=Presentation(); sl=prs.slides.add_slide(prs.slide_layouts[5]); sl.shapes.title.text=title
    left,top,w,h=Inches(1),Inches(1.8),Inches(8),Inches(4.5)
    tf=sl.shapes.add_textbox(left,top,w,h).text_frame; tf.word_wrap=True
    for i,b in enumerate(bullets):
        p=tf.add_paragraph() if i else tf.paragraphs[0]; p.text=b; p.level=0
        if Pt: p.font.size=Pt(18)
    buf=io.BytesIO(); prs.save(buf); buf.seek(0); return buf

# ---------- Tabs ----------
tabs=st.tabs(["Knowledge MCQs (ADI Policy)","Skills Activities","Revision","Print Summary"])
picked=sorted(list(st.session_state.picks))
topic_text=(st.session_state.notes+"\n\n"+st.session_state.src).strip()

with tabs[0]:
    a,b,_=st.columns([1,1,6])
    with a: st.session_state.mcq_n = st.selectbox("How many MCQs?", [5,10,15,20,25,30], index=1)
    with b: st.session_state.ans   = st.checkbox("Include answer key in export", value=st.session_state.ans)
    if st.button("Generate MCQs", type="primary"):
        st.session_state.last["mcqs"]=build_mcqs(topic_text, picked, st.session_state.mcq_n)
        st.success(f"Generated {len(st.session_state.last['mcqs'])} MCQs.")
    mcqs=st.session_state.last.get("mcqs",[])
    if mcqs:
        for i,q in enumerate(mcqs,1):
            st.markdown(f"**Q{i}. {q['stem']}**")
            for o in q["options"]: st.write(f"- {o}")
            if st.session_state.ans: st.caption(f"Answer: {q['answer']}")
            st.divider()
        lines=[]
        for i,q in enumerate(mcqs,1):
            lines.append(f"Q{i}. {q['stem']}"); lines += [f"- {o}" for o in q["options"]]
            if st.session_state.ans: lines.append(f"Answer: {q['answer']}"); lines.append("")
        st.download_button("Download MCQs (DOCX)",
            data=docx_download("ADI_MCQs.docx",lines),
            file_name="ADI_MCQs.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dlmcq-{uuid4().hex}")
        st.download_button("Download MCQs (PPTX)",
            data=pptx_download("MCQs (Preview Deck)", [q["stem"] for q in mcqs[:10]]),
            file_name="ADI_MCQs.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key=f"dlmcq2-{uuid4().hex}")

with tabs[1]:
    a,b,_=st.columns([1,1,6])
    with a: st.session_state.act_n   = st.selectbox("Number of activities", [1,2,3,4], index=1)
    with b: st.session_state.act_min = st.select_slider("Minutes per activity", options=list(range(5,65,5)), value=20)
    if st.button("Generate Activities", type="primary"):
        st.session_state.last["activities"]=build_activities(topic_text, st.session_state.act_n, st.session_state.act_min, picked)
        st.success(f"Generated {len(st.session_state.last['activities'])} activities.")
    acts=st.session_state.last.get("activities",[])
    if acts:
        for a in acts: st.write("• "+a)
        st.download_button("Download Activities (DOCX)",
            data=docx_download("ADI_Activities.docx",[f"{i+1}. {a}" for i,a in enumerate(acts)]),
            file_name="ADI_Activities.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dlact-{uuid4().hex}")

with tabs[2]:
    qty=st.slider("How many revision prompts?",3,12,5)
    if st.button("Generate Revision", type="primary"):
        st.session_state.last["revision"]=build_revision(topic_text, picked, qty)
        st.success(f"Generated {len(st.session_state.last['revision'])} revision prompts.")
    rev=st.session_state.last.get("revision",[])
    if rev:
        for r in rev: st.write("• "+r)
        st.download_button("Download Revision (DOCX)",
            data=docx_download("ADI_Revision.docx",[f"{i+1}. {r}" for i,r in enumerate(rev)]),
            file_name="ADI_Revision.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dlrev-{uuid4().hex}")

with tabs[3]:
    st.caption("A single, printable overview of your session context and the latest generated content.")
    st.subheader("Context")
    st.write(
        f"**Course**: {st.session_state.course}  \n"
        f"**Cohort**: {st.session_state.cohort}  \n"
        f"**Instructor**: {st.session_state.instructor}  \n"
        f"**Week**: {st.session_state.week}  \n"
        f"**Lesson**: {st.session_state.lesson}  \n"
        f"**Date**: {st.session_state.date_str}"
    )
    if st.session_state.notes:
        st.subheader("Your notes"); st.write(st.session_state.notes)
    if st.session_state.src:
        st.subheader("Source (first 500 chars)")
        st.write(st.session_state.src[:500] + ("…" if len(st.session_state.src)>500 else ""))
for k, v in {"gen": {}, "answers": [], "export_ready": False}.items():
    st.session_state.setdefault(k, v)

    g=st.session_state.last; lines=[
        f"Course: {st.session_state.course}",
        f"Cohort: {st.session_state.cohort}",
        f"Instructor: {st.session_state.instructor}",
        f"Week {st.session_state.week}, Lesson {st.session_state.lesson}",
        f"Date: {st.session_state.date_str}",""
    ]
    if st.session_state.notes: lines += ["Your notes", st.session_state.notes, ""]
    if st.session_state.src:   lines += ["Source (first 500 chars)", st.session_state.src[:500], ""]
    if g.get("mcqs"): lines += ["MCQs (first 5)"] + [f"{i}. {q['stem']}" for i,q in enumerate(g["mcqs"][:5],1)] + [""]
    if g.get("activities"): lines += ["Activities"] + [f"• {a}" for a in g["activities"]] + [""]
    if g.get("revision"):   lines += ["Revision"] + [f"• {r}" for r in g["revision"]]

    st.download_button("Download Print Summary (DOCX)",
        data=docx_download("ADI_Print_Summary.docx", lines),
        file_name="ADI_Print_Summary.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"dlsum-{uuid4().hex}")

