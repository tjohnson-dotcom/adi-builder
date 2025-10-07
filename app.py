

import streamlit as st
import io, os, json, random
from datetime import date
from pathlib import Path

# ---------- Optional PDF support ----------
try:
    import fitz  # PyMuPDF
    PDF_ENABLED = True
except Exception:
    fitz = None
    PDF_ENABLED = False

ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
BAND_LOW  = "#eaf3ed"
BAND_MED  = "#fcf8ef"
BAND_HIGH = "#eef2ff"

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🗂️", layout="wide")

st.markdown(f"""
<style>
:root {{
  --adi-green:{ADI_GREEN}; --adi-gold:{ADI_GOLD};
  --band-low:{BAND_LOW}; --band-med:{BAND_MED}; --band-high:{BAND_HIGH};
}}
section[data-testid="stSidebar"]{{background:#fff;border-right:1px solid #e5e7eb;}}
.adi-banner{{background:var(--adi-green);color:#fff;padding:14px 18px;border-radius:12px;font-weight:600;margin-bottom:14px;}}
.adi-subtle{{color:#e7f2ea;font-weight:400;font-size:.9rem;}}
/* Band tints */
div.low-band>div>div{{background:var(--band-low)!important;}}
div.med-band>div>div{{background:var(--band-med)!important;}}
div.high-band>div>div{{background:var(--band-high)!important;}}
/* Colored chips inside our wrappers */
.chips-low   [data-baseweb="tag"]{{background: #dff1e4 !important; border:1px solid var(--adi-green); color:#153a27; font-weight:600;}}
.chips-med   [data-baseweb="tag"]{{background: #fff2dc !important; border:1px solid #c9a65d; color:#3f2c13; font-weight:600;}}
.chips-high  [data-baseweb="tag"]{{background: #e7ecff !important; border:1px solid #6b79ff; color:#1a2260; font-weight:600;}}
/* Uploader dashed */
div[data-testid="stFileUploaderDropzone"], section[data-testid="stFileUploaderDropzone"], 
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]{{
  border:2px dashed var(--adi-green)!important; background:#fff!important; border-radius:12px!important;
}}
.download-panel{{border:2px dashed var(--adi-green); background:#fff; border-radius:14px; padding:14px; margin-top:8px;}}
</style>
""", unsafe_allow_html=True)

# simple persistence file
DATA_DIR = Path(os.getenv("DATA_DIR", ".")); DATA_DIR.mkdir(parents=True, exist_ok=True)
CFG_FILE = DATA_DIR / "adi_modules.json"
SEED_CFG = {"courses":["Defense Technologies 101"], "cohorts":["D1-C01"], "instructors":["Staff Instructor"]}

def load_cfg():
    try:
        cfg = json.loads(CFG_FILE.read_text(encoding="utf-8")) if CFG_FILE.exists() else {}
    except Exception:
        cfg = {}
    for k,v in SEED_CFG.items():
        if k not in cfg or not isinstance(cfg[k], list) or len(cfg[k])==0: cfg[k]=v[:]
    return cfg
def save_cfg(cfg): CFG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

if "cfg" not in st.session_state: st.session_state.cfg = load_cfg()

def edit_list(label, key, placeholder):
    items = st.session_state.cfg.get(key, [])
    opts=[f"— {placeholder} —"]+items
    c1,c2,c3=st.columns([5,1,1])
    choice=c1.selectbox(label, opts, index=0, key=f"sel_{key}")
    add=c2.button("＋", key=f"add_{key}"); rm=c3.button("−", key=f"rm_{key}")
    selected=None if choice==opts[0] else choice
    if add: st.session_state[f"adding_{key}"]=True
    if rm and selected:
        try: items.remove(selected); save_cfg(st.session_state.cfg); st.rerun()
        except ValueError: pass
    if st.session_state.get(f"adding_{key}"):
        new_val=st.text_input(f"Add new {label.lower()}", key=f"new_{key}")
        colA,colB=st.columns([1,1])
        if colA.button("Save", key=f"save_{key}"):
            if new_val and new_val not in items: items.append(new_val); save_cfg(st.session_state.cfg)
            st.session_state[f"adding_{key}"]=False; st.rerun()
        if colB.button("Cancel", key=f"cancel_{key}"): st.session_state[f"adding_{key}"]=False
    return selected

# parsing (cached) — shortened for demo
@st.cache_data(show_spinner=False)
def parse_upload(file_bytes:bytes,filetype:str,deep:bool):
    try:
        if filetype=="pdf" and PDF_ENABLED:
            import fitz
            doc=fitz.open(stream=file_bytes, filetype="pdf")
            pages=range(len(doc)) if deep else range(min(10,len(doc)))
            return "\n".join(doc[p].get_text("text") for p in pages), f"Parsed {len(list(pages))}/{len(doc)} pages ({'deep' if deep else 'quick'})"
        if filetype=="pptx":
            from pptx import Presentation
            prs=Presentation(io.BytesIO(file_bytes))
            texts=[getattr(s,'text','') for slide in prs.slides for s in slide.shapes if hasattr(s,'text')]
            return "\n".join(texts), f"Parsed {len(prs.slides)} slides"
        if filetype=="docx":
            from docx import Document
            doc=Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs), f"Parsed {len(doc.paragraphs)} paragraphs"
        return file_bytes.decode("utf-8", errors="ignore"), "Parsed text file"
    except Exception as e:
        return "", f"Error: {e}"

def detect(uploaded):
    n=(uploaded.name or "").lower(); m=(uploaded.type or "").lower()
    if n.endswith(".pdf") or "pdf" in m: return "pdf"
    if n.endswith(".pptx") or "ppt" in m: return "pptx"
    if n.endswith(".docx") or "word" in m: return "docx"
    return "txt"

LOW  = ["define","identify","list","recall","describe","label"]
MED  = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH = ["evaluate","synthesize","design","justify","critique","create"]

with st.sidebar:
    logo=Path("adi_logo.png")
    if logo.exists(): st.image(str(logo), use_column_width=True)
    st.subheader("Upload (optional)")
    up = st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"], key="uploader")
    deep = st.toggle("Deep scan source (slower, better coverage)", value=False)
    note_area = st.empty()
    st.divider()
    st.subheader("Course details")
    course = edit_list("Course name","courses","Choose a course")
    cohort = edit_list("Class / Cohort","cohorts","Choose a cohort")
    instructor = edit_list("Instructor name","instructors","Choose an instructor")
    the_date = st.date_input("Date", value=date.today())

st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions'
            '<div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>'
            '</div>', unsafe_allow_html=True)

topic = st.text_area("Topic / Outcome (optional)", height=80, placeholder="e.g., Integrated Project and ...")

# Wrappers that color tags
st.markdown('<div class="chips-low">', unsafe_allow_html=True)
with st.expander("**Low (Weeks 1–4)** — Remember / Understand", True):
    st.markdown('<div class="low-band">', unsafe_allow_html=True)
    low = st.multiselect("Low verbs", LOW, default=LOW[:3], key="lowverbs")
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="chips-med">', unsafe_allow_html=True)
with st.expander("**Medium (Weeks 5–9)** — Apply / Analyse", False):
    st.markdown('<div class="med-band">', unsafe_allow_html=True)
    med = st.multiselect("Medium verbs", MED, default=MED[:3], key="medverbs")
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="chips-high">', unsafe_allow_html=True)
with st.expander("**High (Weeks 10–14)** — Evaluate / Create", False):
    st.markdown('<div class="high-band">', unsafe_allow_html=True)
    high = st.multiselect("High verbs", HIGH, default=HIGH[:3], key="highverbs")
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision", "Print Summary"])

text = ""; 
if up is not None:
    ft = detect(up); data = up.getvalue()
    text, parse_note = parse_upload(data, ft, deep)
    note_area.markdown(f"✅ **Uploaded:** {up.name}  \n_Type:_ {ft} — {parse_note}")

with tabs[0]:
    n = st.selectbox("How many MCQs?", [5,10,15,20], index=1)
    include = st.checkbox("Include answer key in export", value=True)
    def pick_terms(t, k=20):
        if not t: corpus=["safety","procedure","system","component","principle","policy","mission","calibration","diagnostics","maintenance"]
        else:
            toks=[w.strip(".,:;()[]{}!?\"'").lower() for w in t.split()]
            toks=[w for w in toks if w.isalpha() and 3<=len(w)<=14]
            stops=set("the of and to in for is are be a an on from with that this these those which using as by or it at we you they can may into over under".split())
            corpus=[w for w in toks if w not in stops] or ["concept","process","system","protocol","hazard","control"]
        random.shuffle(corpus); return corpus[:k]
    def gen(n, verbs, t, include):
        terms=pick_terms(t, max(20, n*5)); out=[]; key=[]
        for i in range(n):
            term=random.choice(terms); v=random.choice(verbs or LOW)
            q=f"{i+1}. {v.capitalize()} the following term as it relates to the lesson: **{term}**."
            right=f"Accurate statement about {term}."
            opts=[f"Unrelated detail about {random.choice(terms)}.", f"Common misconception about {term}.", f"Vague statement with {random.choice(terms)}.", right]
            random.shuffle(opts); out.append((q,opts)); 
            if include: key.append(opts.index(right)+1)
        return out, key
    if st.button("Generate MCQs", type="primary"):
        mcqs, key = gen(n, (low or LOW), text, include)
        st.session_state["mcqs"]=mcqs; st.session_state["akey"]=key if include else []
        st.success("Download panel is ready below.")
    if st.session_state.get("mcqs"):
        for q,opts in st.session_state["mcqs"]:
            st.markdown(f"**{q}**"); 
            for j,opt in enumerate(opts, start=1): st.markdown(f"{chr(64+j)}. {opt}")
            st.write("")
        st.markdown('<div class="download-panel">', unsafe_allow_html=True)
        from docx import Document
        def export_docx(mcqs, include, key):
            doc=Document(); doc.add_heading("Knowledge MCQs", level=1)
            for q,opts in mcqs:
                r=doc.add_paragraph().add_run(q); r.bold=True
                for j,opt in enumerate(opts, start=1): doc.add_paragraph(f"{chr(64+j)}. {opt}")
            if include and key:
                doc.add_heading("Answer Key", level=2)
                for i,a in enumerate(key, start=1): doc.add_paragraph(f"Q{i}: {['A','B','C','D'][a-1]}")
            import io
            bio=io.BytesIO(); doc.save(bio); return bio.getvalue()
        st.download_button("⬇️ Download DOCX", data=export_docx(st.session_state["mcqs"], include, st.session_state.get("akey")),
                           file_name="ADI_Knowledge_MCQs.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.markdown('</div>', unsafe_allow_html=True)
