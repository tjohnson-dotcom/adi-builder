
import streamlit as st
import io, os, json, random, hashlib
from datetime import date
from pathlib import Path

# ---------- Optional PDF support ----------
try:
    import fitz  # PyMuPDF
    PDF_ENABLED = True
except Exception:
    fitz = None
    PDF_ENABLED = False

# ---------- Theme ----------
ADI_GREEN = "#245a34"; ADI_GOLD = "#C8A85A"
LOW_BG,  LOW_BORDER,  LOW_TEXT  = "#cfe8d9", "#245a34", "#153a27"
MED_BG,  MED_BORDER,  MED_TEXT  = "#f8e6c9", "#C8A85A", "#3f2c13"
HIGH_BG, HIGH_BORDER, HIGH_TEXT = "#dfe6ff", "#4F46E5", "#1E1B4B"
BAND_LOW, BAND_MED, BAND_HIGH = "#eaf3ed", "#fcf8ef", "#eef2ff"

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="🗂️", layout="wide")

st.markdown(f"""
<style>
:root{{
  --adi-green:{ADI_GREEN}; --adi-gold:{ADI_GOLD};
  --band-low:{BAND_LOW}; --band-med:{BAND_MED}; --band-high:{BAND_HIGH};
  --low-bg:{LOW_BG}; --low-border:{LOW_BORDER}; --low-text:{LOW_TEXT};
  --med-bg:{MED_BG}; --med-border:{MED_BORDER}; --med-text:{MED_TEXT};
  --high-bg:{HIGH_BG}; --high-border:{HIGH_BORDER}; --high-text:{HIGH_TEXT};
}}
section[data-testid="stSidebar"]{{background:#fff;border-right:1px solid #e5e7eb;}}
.adi-banner{{background:var(--adi-green);color:#fff;padding:14px 18px;border-radius:12px;font-weight:600;margin-bottom:14px;}}
.adi-subtle{{color:#e7f2ea;font-weight:400;font-size:.9rem;}}
/* Band tints */
div.low-band>div>div{{background:var(--band-low)!important;}}
div.med-band>div>div{{background:var(--band-med)!important;}}
div.high-band>div>div{{background:var(--band-high)!important;}}

/* Strong chip overrides */
#low-wrap  div[data-testid="stMultiSelect"] [data-baseweb="tag"],
#low-wrap  [data-baseweb="tag"],
#low-wrap  span[data-baseweb="tag"] {{
  background:var(--low-bg)!important; border:1px solid var(--low-border)!important; color:var(--low-text)!important; font-weight:600;
}}
#med-wrap  div[data-testid="stMultiSelect"] [data-baseweb="tag"],
#med-wrap  [data-baseweb="tag"],
#med-wrap  span[data-baseweb="tag"] {{
  background:var(--med-bg)!important; border:1px solid var(--med-border)!important; color:var(--med-text)!important; font-weight:600;
}}
#high-wrap div[data-testid="stMultiSelect"] [data-baseweb="tag"],
#high-wrap [data-baseweb="tag"],
#high-wrap span[data-baseweb="tag"] {{
  background:var(--high-bg)!important; border:1px solid var(--high-border)!important; color:var(--high-text)!important; font-weight:600;
}}

/* Click cues */
div[data-baseweb="tab"] button{{border-radius:999px!important;cursor:pointer;}}
button[kind="primary"]{{border-radius:12px!important;cursor:pointer;}}
div[data-baseweb="select"] *{{cursor:pointer!important;}}

/* Uploader dashed */
div[data-testid="stFileUploaderDropzone"], section[data-testid="stFileUploaderDropzone"],
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]{{
  border:2px dashed var(--adi-green)!important; background:#fff!important; border-radius:12px!important;
}}
.download-panel{{border:2px dashed var(--adi-green);background:#fff;border-radius:14px;padding:14px;margin-top:12px;max-width:900px;}}
</style>
""", unsafe_allow_html=True)

# ---------- Persistence ----------
DATA_DIR = Path(os.getenv("DATA_DIR", ".")); DATA_DIR.mkdir(parents=True, exist_ok=True)
CFG_FILE = DATA_DIR / "adi_modules.json"
SEED_CFG = {"courses":["GE4-IPM — Integrated Project & Materials Mgmt","Defense Technologies 101"],
            "cohorts":["D1-M01","D1-C01"], "instructors":["Daniel","Staff Instructor"]}

def load_cfg():
    try: cfg = json.loads(CFG_FILE.read_text(encoding="utf-8")) if CFG_FILE.exists() else {}
    except Exception: cfg = {}
    for k,v in SEED_CFG.items():
        if k not in cfg or not isinstance(cfg[k], list) or not cfg[k]: cfg[k]=v[:]
    return cfg
def save_cfg(cfg): CFG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
if "cfg" not in st.session_state: st.session_state.cfg = load_cfg()

def ensure_state():
    for k,v in {"gen_mcqs":[], "gen_acts":[], "gen_rev":[], "answer_key":[], "upload_meta":None, "last_sig":None}.items():
        st.session_state.setdefault(k,v)

def edit_list(label, key, placeholder):
    items = st.session_state.cfg.get(key, [])
    opts=[f"— {placeholder} —"]+items
    c1,c2,c3=st.columns([5,1,1])
    choice=c1.selectbox(label, opts, index=0, key=f"sel_{key}")
    add=c2.button("＋", key=f"add_{key}"); rm=c3.button("−", key=f"rm_{key}")
    selected=None if choice==opts[0] else choice
    if add: st.session_state[f"adding_{key}"]=True
    if rm and selected:
        try: items.remove(selected); save_cfg(st.session_state.cfg)
        except ValueError: pass
    if st.session_state.get(f"adding_{key}"):
        new_val=st.text_input(f"Add new {label.lower()}", key=f"new_{key}")
        colA,colB=st.columns([1,1])
        if colA.button("Save", key=f"save_{key}"):
            if new_val and new_val not in items: items.append(new_val); save_cfg(st.session_state.cfg)
            st.session_state[f"adding_{key}"]=False
        if colB.button("Cancel", key=f"cancel_{key}"): st.session_state[f"adding_{key}"]=False
    return selected

# ---------- Upload parsing ----------
def detect_filetype(f)->str:
    n=(f.name or "").lower(); m=(f.type or "").lower()
    if n.endswith(".pdf") or "pdf" in m: return "pdf"
    if n.endswith(".pptx") or "ppt" in m: return "pptx"
    if n.endswith(".docx") or "word" in m: return "docx"
    return "txt"

@st.cache_data(show_spinner=False)
def parse_upload_cached(b:bytes, t:str, deep:bool):
    try:
        if t=="pdf":
            if not PDF_ENABLED: return "", "PDF parsing disabled"
            import fitz
            doc=fitz.open(stream=b, filetype="pdf")
            total=len(doc); limit = total if deep else min(10,total)
            text="\n".join(doc[p].get_text("text") for p in range(limit))
            return text, f"Parsed {limit}/{total} pages ({'deep' if deep else 'quick'})"
        if t=="pptx":
            from pptx import Presentation
            prs=Presentation(io.BytesIO(b))
            texts=[getattr(s,'text','') for slide in prs.slides for s in slide.shapes if hasattr(s,'text')]
            return "\n".join(texts), f"Parsed {len(prs.slides)} slides"
        if t=="docx":
            from docx import Document
            doc=Document(io.BytesIO(b))
            return "\n".join(p.text for p in doc.paragraphs), f"Parsed {len(doc.paragraphs)} paragraphs"
        return b.decode("utf-8",errors="ignore"), "Parsed text file"
    except Exception as e:
        return "", f"Error: {e}"

def file_signature(uploaded, deep)->str:
    try:
        b = uploaded.getvalue(); h = hashlib.sha1(b).hexdigest()[:12]
        return f"{uploaded.name}|{len(b)}|{deep}|{h}"
    except Exception:
        return f"{uploaded.name}|{deep}|unknown"

# ---------- Generators ----------
LOW  = ["define","identify","list","recall","describe","label"]
MED  = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH = ["evaluate","synthesize","design","justify","critique","create"]

def pick_terms(text,k=20):
    if not text:
        corpus=["safety","procedure","system","component","principle","policy","mission","calibration","diagnostics","maintenance"]
    else:
        toks=[w.strip(".,:;()[]{}!?\"'").lower() for w in text.split()]
        toks=[w for w in toks if w.isalpha() and 3<=len(w)<=14]
        stops=set("the of and to in for is are be a an on from with that this these those which using as by or it at we you they can may into over under".split())
        corpus=[w for w in toks if w not in stops] or ["concept","process","system","protocol","hazard","control"]
    random.shuffle(corpus); return corpus[:k]

def gen_mcqs(n, verbs, txt, include=True):
    terms=pick_terms(txt, max(20,n*5)); out=[]; key=[]
    for i in range(n):
        term=random.choice(terms); v=random.choice(verbs or LOW)
        q=f"{i+1}. {v.capitalize()} the following term as it relates to the lesson: **{term}**."
        right=f"Accurate statement about {term}."
        opts=[f"Unrelated detail about {random.choice(terms)}.", f"Common misconception about {term}.", f"Vague statement with {random.choice(terms)}.", right]
        random.shuffle(opts); out.append((q,opts)); 
        if include: key.append(opts.index(right)+1)
    return out, key

# ---------- Export helpers ----------
def export_docx(mcqs, include, key, title="Knowledge MCQs"):
    from docx import Document
    doc=Document(); doc.add_heading(title, level=1)
    for q,opts in mcqs:
        r=doc.add_paragraph().add_run(q); r.bold=True
        for j,opt in enumerate(opts, start=1): doc.add_paragraph(f"{chr(64+j)}. {opt}")
    if include and key:
        doc.add_heading("Answer Key", level=2)
        for i,a in enumerate(key, start=1): doc.add_paragraph(f"Q{i}: {['A','B','C','D'][a-1]}")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_txt(mcqs, key, include):
    lines=[]
    for q,opts in mcqs:
        lines.append(q)
        for j,opt in enumerate(opts, start=1): lines.append(f"{chr(64+j)}. {opt}")
        lines.append("")
    if include and key:
        lines.append("Answer Key")
        for i,a in enumerate(key, start=1): lines.append(f"Q{i}: {['A','B','C','D'][a-1]}")
    return ("\n".join(lines)).encode("utf-8")

def export_docx_list(lines, title):
    from docx import Document
    doc=Document(); doc.add_heading(title, level=1)
    for ln in lines: doc.add_paragraph(ln)
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_txt_list(lines):
    return ("\n".join(lines)).encode("utf-8")

# ---------- UI ----------
def main():
    ensure_state()

    with st.sidebar:
        logo=Path("adi_logo.png")
        if logo.exists(): st.image(str(logo), use_column_width=True)

        st.subheader("Upload (optional)")
        uploaded = st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"], key="uploader")
        deep = st.toggle("Deep scan source (slower, better coverage)", value=False)
        status = st.empty()
        st.caption("Quick scan reads the first 10 PDF pages. Turn on deep scan for full documents.")
        st.divider()

        st.subheader("Course details")
        course = edit_list("Course name","courses","Choose a course")
        cohort = edit_list("Class / Cohort","cohorts","Choose a cohort")
        instructor = edit_list("Instructor name","instructors","Choose an instructor")
        the_date = st.date_input("Date", value=date.today())
        st.subheader("Context")
        c1,c2 = st.columns(2)
        lesson = c1.number_input("Lesson", 1, 50, 1, step=1)
        week   = c2.number_input("Week", 1, 20, 1, step=1)
        st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

    st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions'
                '<div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>'
                '</div>', unsafe_allow_html=True)

    topic = st.text_area("Topic / Outcome (optional)", height=80, placeholder="e.g., Integrated Project and ...")

    # ---- Low
    st.markdown('<div id="low-wrap">', unsafe_allow_html=True)
    with st.expander("**Low (Weeks 1–4)** — Remember / Understand", True):
        st.markdown('<div class="low-band">', unsafe_allow_html=True)
        low = st.multiselect("Low verbs", LOW, default=LOW[:3], key="lowverbs")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Medium
    st.markdown('<div id="med-wrap">', unsafe_allow_html=True)
    with st.expander("**Medium (Weeks 5–9)** — Apply / Analyse", False):
        st.markdown('<div class="med-band">', unsafe_allow_html=True)
        med = st.multiselect("Medium verbs", MED, default=MED[:3], key="medverbs")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- High
    st.markdown('<div id="high-wrap">', unsafe_allow_html=True)
    with st.expander("**High (Weeks 10–14)** — Evaluate / Create", False):
        st.markdown('<div class="high-band">', unsafe_allow_html=True)
        high = st.multiselect("High verbs", HIGH, default=HIGH[:3], key="highverbs")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision", "Print Summary"])

    # Parse once per signature
    text = ""
    if uploaded is not None:
        sig = file_signature(uploaded, deep)
        if st.session_state.get("last_sig") != sig:
            ftype = detect_filetype(uploaded)
            data  = uploaded.getvalue()
            text, note = parse_upload_cached(data, ftype, deep)
            st.session_state.upload_meta = {"name": uploaded.name, "type": ftype, "note": note}
            st.session_state["last_sig"] = sig
        meta = st.session_state.upload_meta
        status.markdown(f"✅ **Uploaded:** {meta['name']}  \n_Type:_ {meta['type']} — {meta['note']}")
    else:
        st.session_state["last_sig"] = None

    # ----- Tab 1: MCQs -----
    with tabs[0]:
        n = st.selectbox("How many MCQs?", [5,10,15,20], index=1)
        include = st.checkbox("Include answer key in export", value=True)
        if st.button("Generate MCQs", type="primary"):
            mcqs, key = gen_mcqs(n, (low or LOW), text, include)
            st.session_state.gen_mcqs = mcqs
            st.session_state.answer_key = key if include else []
            st.success("Download panel is ready below.")

        if st.session_state.get("gen_mcqs"):
            for q,opts in st.session_state.gen_mcqs:
                st.markdown(f"**{q}**")
                for j,opt in enumerate(opts, start=1): st.markdown(f"{chr(64+j)}. {opt}")
                st.write("")
            st.markdown('<div class="download-panel">', unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download DOCX",
                                   data=export_docx(st.session_state.gen_mcqs, include, st.session_state.answer_key),
                                   file_name="ADI_Knowledge_MCQs.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col2:
                st.download_button("⬇️ Download TXT",
                                   data=export_txt(st.session_state.gen_mcqs, st.session_state.answer_key, include),
                                   file_name="ADI_Knowledge_MCQs.txt",
                                   mime="text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    # ----- Tab 2: Activities -----
    with tabs[1]:
        left, right = st.columns([2,2])
        with left:
            n_act = st.selectbox("How many activities?", [3,5,8,10], index=0, key="n_act")
        with right:
            mins = st.selectbox("Minutes per activity", list(range(5,65,5)), index=1, key="act_mins")
        group_size = st.selectbox("Group size", [1,2,3], index=1, key="group_size")

        if st.button("Generate Activities"):
            terms = pick_terms(text, max(10,n_act*2))[:n_act]
            acts = [f"{i+1}. {random.choice(med or MED).capitalize()} a {mins}-minute activity "
                    f"for groups of {group_size} focusing on **{w}**."
                    for i,w in enumerate(terms)]
            st.session_state.gen_acts = acts; st.success("Activities generated.")
        if st.session_state.get("gen_acts"):
            for a in st.session_state.gen_acts: st.markdown(f"- {a}")
            st.markdown('<div class="download-panel">', unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download DOCX (Activities)",
                                   data=export_docx_list(st.session_state.gen_acts, "Skills Activities"),
                                   file_name="ADI_Skills_Activities.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col2:
                st.download_button("⬇️ Download TXT (Activities)",
                                   data=export_txt_list(st.session_state.gen_acts),
                                   file_name="ADI_Skills_Activities.txt",
                                   mime="text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    # ----- Tab 3: Revision -----
    with tabs[2]:
        n_rev = st.selectbox("How many revision prompts?", [3,5,8,10], index=0, key="n_rev")
        if st.button("Generate Revision"):
            revs = [f"{i+1}. {random.choice(low or LOW).capitalize()} key points on **{w}** in a 5-bullet summary."
                    for i,w in enumerate(pick_terms(text, max(10,n_rev*2))[:n_rev])]
            st.session_state.gen_rev = revs; st.success("Revision prompts generated.")
        if st.session_state.get("gen_rev"):
            for r in st.session_state.gen_rev: st.markdown(f"- {r}")
            st.markdown('<div class="download-panel">', unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download DOCX (Revision)",
                                   data=export_docx_list(st.session_state.gen_rev, "Revision Prompts"),
                                   file_name="ADI_Revision_Prompts.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col2:
                st.download_button("⬇️ Download TXT (Revision)",
                                   data=export_txt_list(st.session_state.gen_rev),
                                   file_name="ADI_Revision_Prompts.txt",
                                   mime="text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    # ----- Tab 4: Print Summary -----
    with tabs[3]:
        st.subheader("Print Summary")
        st.markdown(f"**Course:** {course or '—'}  \n**Cohort:** {cohort or '—'}  \n**Instructor:** {instructor or '—'}  \n**Date:** {the_date}  \n**Lesson:** {lesson}  \n**Week:** {week}")
        st.divider()
        if st.session_state.get("gen_mcqs"):
            st.markdown("### Knowledge MCQs")
            for q,opts in st.session_state.gen_mcqs:
                st.markdown(f"**{q}**")
                for j,opt in enumerate(opts, start=1): st.markdown(f"{chr(64+j)}. {opt}")
                st.write("")
        if st.session_state.get("gen_acts"):
            st.markdown("### Skills Activities"); [st.markdown(f"- {a}") for a in st.session_state.gen_acts]
        if st.session_state.get("gen_rev"):
            st.markdown("### Revision"); [st.markdown(f"- {r}") for r in st.session_state.gen_rev]

    st.caption("ADI Builder — sleek, professional and engaging. Print-ready handouts for your instructors.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Unexpected error: {e}"); st.stop()
