
import streamlit as st
import io, os, json, random, hashlib
from datetime import date
from pathlib import Path

# ---------- Page config & build tag
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🗂️", layout="wide")
st.caption("Build tag: 2025-10-07T23:32 full-safe-ADI-polished")

# ---------- Styles (ALL CSS inside this block)
st.markdown('''
<style>
/* ===== ADI palette (darker) ===== */
:root{
  --adi-green:#1e4d2b;     /* darker primary */
  --adi-green-2:#153a27;   /* deeper for text/accents */

  --low:#cfe8d9;  --low-b:#1e4d2b;  --low-t:#123222;
  --med:#f3dfba;  --med-b:#a97d2b;  --med-t:#3a2a11;
  --high:#d7e0ff; --high-b:#3f3ac7; --high-t:#17155a;
}

/* Page body tweaks */
section[data-testid="stSidebar"]{ background:#fff; border-right:1px solid #e5e7eb; }
.block-container{ padding-top: 0.8rem !important; }

/* Top banner */
.adi-banner{
  background: linear-gradient(90deg, var(--adi-green) 0%, var(--adi-green-2) 100%);
  color:#fff; font-weight:700; letter-spacing:.3px;
  padding:14px 18px; border-radius:8px; margin:8px 0 18px 0;
  box-shadow:0 2px 4px rgba(0,0,0,.06);
}

/* Uploader */
div[data-testid="stFileUploaderDropzone"]{
  border:3px dotted var(--adi-green) !important;
  border-radius:12px !important;
  background:#ffffff !important;
}

/* Chip colors — label first, then order fallback */
div[aria-label="Low verbs"]    [data-baseweb="tag"]{  background:var(--low)!important;  border:1px solid var(--low-b)!important;  color:var(--low-t)!important; }
div[aria-label="Medium verbs"] [data-baseweb="tag"]{  background:var(--med)!important;  border:1px solid var(--med-b)!important;  color:var(--med-t)!important; }
div[aria-label="High verbs"]   [data-baseweb="tag"]{  background:var(--high)!important; border:1px solid var(--high-b)!important; color:var(--high-t)!important; }

div[data-testid="stMultiSelect"]:nth-of-type(1) [data-baseweb="tag"]{ background:var(--low)!important;  border:1px solid var(--low-b)!important;  color:var(--low-t)!important; }
div[data-testid="stMultiSelect"]:nth-of-type(2) [data-baseweb="tag"]{ background:var(--med)!important;  border:1px solid var(--med-b)!important;  color:var(--med-t)!important; }
div[data-testid="stMultiSelect"]:nth-of-type(3) [data-baseweb="tag"]{ background:var(--high)!important; border:1px solid var(--high-b)!important; color:var(--high-t)!important; }

/* Chip sizing */
[data-baseweb="tag"]{
  border-radius: 9999px !important;
  padding: 6px 10px !important;
  font-weight: 700 !important;
  letter-spacing:.1px;
}
[data-baseweb="tag"]:hover{ filter:brightness(.98)!important; }

/* Download panel */
.download-panel{ border:2px dashed var(--adi-green); border-radius:14px; padding:14px; margin-top:12px; background:#fff; }

/* Buttons & primary accents */
button[kind], button {
  background: var(--adi-green) !important;
  border-color: var(--adi-green) !important;
  color:#fff !important;
  padding: 10px 14px !important;
  font-weight: 700 !important;
  border-radius: 10px !important;
}
button:hover{ filter:brightness(0.95)!important; }

/* Softer expander look */
div[data-testid="stExpander"] {
  border: 1px solid rgba(30,77,43,.25) !important;
  border-radius: 10px !important;
}
div[data-testid="stExpander"] > details[open] > summary {
  box-shadow: 0 0 0 2px rgba(30,77,43,.25) inset !important;
}

/* Tabs: flatter with active underline */
div[role="tablist"] button[role="tab"]{
  background: transparent !important;
  border: none !important;
  color: #374151 !important;
  padding: 8px 12px !important;
}
div[role="tablist"] button[aria-selected="true"]{
  color: var(--adi-green) !important;
  box-shadow: inset 0 -3px 0 0 var(--adi-green) !important;
  font-weight: 700 !important;
}

/* ===== Pointer + hover fix (uploader, selects, multiselects, buttons) ===== */
/* Make interactive bits feel clickable */
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
button[kind],
button {
  cursor: pointer !important;
}

/* Hover feedback */
/* Uploader hover transition */
div[data-testid="stFileUploaderDropzone"]{ transition: box-shadow .12s ease-in-out, border-color .12s ease-in-out; }
div[data-testid="stFileUploaderDropzone"]:hover {
  box-shadow: 0 0 0 3px var(--adi-green) inset !important;
}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover {
  box-shadow: 0 0 0 2px var(--adi-green) inset !important;
}

/* Keyboard focus ring for accessibility */
:focus-visible {
  outline: 2px solid var(--adi-green) !important;
  outline-offset: 2px;
}

/* Sidebar selects specific pointer/hover */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button,
section[data-testid="stSidebar"] [data-baseweb="select"] div[role="button"],
section[data-testid="stSidebar"] div[role="combobox"],
section[data-testid="stSidebar"] [aria-haspopup="listbox"] {
  cursor: pointer !important;
}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button:hover,
section[data-testid="stSidebar"] [data-baseweb="select"] div[role="button"]:hover,
section[data-testid="stSidebar"] div[role="combobox"]:hover,
section[data-testid="stSidebar"] [aria-haspopup="listbox"]:hover {
  box-shadow: 0 0 0 2px var(--adi-green) inset !important;
}

/* === Global picker hover & pointer (MAIN content) === */
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button,
[data-baseweb="select"] div[role="button"]{
  cursor: pointer !important;
  transition: box-shadow .12s ease-in-out;
}
div[data-testid="stSelectbox"] button:hover,
div[data-testid="stMultiSelect"] button:hover,
[data-baseweb="select"] div[role="button"]:hover{
  box-shadow: 0 0 0 2px var(--adi-green) inset !important;
}

/* Number inputs (Lesson, Week) – ring on hover */
[data-baseweb="input"] { transition: box-shadow .12s ease-in-out; }
[data-baseweb="input"]:hover { box-shadow: 0 0 0 2px var(--adi-green) inset !important; }

/* Dropdown menu styling + hover */
[data-baseweb="menu"]{
  border: 1px solid rgba(30,77,43,.25) !important;
  box-shadow: 0 6px 18px rgba(0,0,0,.08) !important;
}
[data-baseweb="menu"] li{ cursor: pointer !important; }
[data-baseweb="menu"] li:hover{ background: rgba(30,77,43,.08) !important; }

/* Compact select appearance to reduce 'double box' look */
div[data-testid="stSelectbox"] button,
div[data-testid="stMultiSelect"] button{
  background: #f7f7f7 !important;
  border: 1px solid rgba(30,77,43,.18) !important;
  border-radius: 10px !important;
}

</style>
''', unsafe_allow_html=True)

# ---------- Config persistence
DATA_DIR = Path(os.getenv("DATA_DIR",".")); DATA_DIR.mkdir(parents=True, exist_ok=True)
CFG_FILE = DATA_DIR / "adi_modules.json"
SEED_CFG = {"courses":["GE4-IPM — Integrated Project & Materials Mgmt","Defense Technologies 101"],
            "cohorts":["D1-M01","D1-C01","D1-C02","D2-M01"],
            "instructors":["Daniel","Ghamza Labeeb","Nerdeen Tariq","Abdulmalik"]}
def load_cfg():
    try: return json.loads(CFG_FILE.read_text(encoding="utf-8")) if CFG_FILE.exists() else SEED_CFG.copy()
    except Exception: return SEED_CFG.copy()
def save_cfg(cfg): CFG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
if "cfg" not in st.session_state: st.session_state.cfg = load_cfg()

def edit_list(label, key, placeholder):
    items = st.session_state.cfg.get(key, [])
    opts=[placeholder]+items
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
            if new_val and new_val not in items:
                items.append(new_val); st.session_state.cfg[key]=items; save_cfg(st.session_state.cfg)
            st.session_state[f"adding_{key}"]=False
        if colB.button("Cancel", key=f"cancel_{key}"): st.session_state[f"adding_{key}"]=False
    return selected

# ---------- Upload parsing
try:
    import fitz
    PDF_ENABLED=True
except Exception:
    fitz=None; PDF_ENABLED=False

def detect_filetype(uploaded)->str:
    n=(uploaded.name or "").lower(); m=(uploaded.type or "").lower()
    if n.endswith(".pdf") or "pdf" in m: return "pdf"
    if n.endswith(".pptx") or "ppt" in m: return "pptx"
    if n.endswith(".docx") or "word" in m: return "docx"
    return "txt"

@st.cache_data(show_spinner=False)
def parse_upload_cached(b:bytes, t:str, deep:bool):
    try:
        if t=="pdf":
            if not PDF_ENABLED: return "", "PDF parsing disabled"
            doc=fitz.open(stream=b, filetype="pdf")
            total=len(doc); limit = total if deep else min(10,total)
            text="\\n".join(doc[p].get_text("text") for p in range(limit))
            return text, f"Parsed {limit}/{total} pages ({'deep' if deep else 'quick'})"
        if t=="pptx":
            from pptx import Presentation
            prs=Presentation(io.BytesIO(b))
            texts=[getattr(s,'text','') for slide in prs.slides for s in slide.shapes if hasattr(s,'text')]
            return "\\n".join(texts), f"Parsed {len(prs.slides)} slides"
        if t=="docx":
            from docx import Document
            doc=Document(io.BytesIO(b))
            return "\\n".join(p.text for p in doc.paragraphs), f"Parsed {len(doc.paragraphs)} paragraphs"
        return b.decode("utf-8",errors="ignore"), "Parsed text file"
    except Exception as e:
        return "", f"Error: {e}"

def file_signature(uploaded, deep)->str:
    try:
        b = uploaded.getvalue(); h = hashlib.sha1(b).hexdigest()[:12]
        return f"{uploaded.name}|{len(b)}|{deep}|{h}"
    except Exception:
        return f"{uploaded.name}|{deep}|unknown"

# ---------- Verb banks & helpers
LOW  = ["define","identify","list","recall","describe","label"]
MED  = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH = ["evaluate","synthesize","design","justify","critique","create"]

def pick_terms(text,k=20):
    if not text:
        corpus=["safety","procedure","system","component","principle","policy","mission","calibration","diagnostics","maintenance"]
    else:
        toks=[w.strip(".,:;()[]{}!?\\\"'").lower() for w in text.split()]
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
        random.shuffle(opts); out.append((q,opts))
        if include: key.append(opts.index(right)+1)
    return out, key

# ---------- Export helpers
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
    return ("\\n".join(lines)).encode("utf-8")

def export_docx_list(lines, title):
    from docx import Document
    doc=Document(); doc.add_heading(title, level=1)
    for ln in lines: doc.add_paragraph(ln)
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_txt_list(lines):
    return ("\\n".join(lines)).encode("utf-8")

# ---------- UI
def main():
    for k,v in [("gen_mcqs",[]),("answer_key",[]),("gen_acts",[]),("gen_rev",[]),("last_sig",None),("upload_meta",None)]:
        if k not in st.session_state: st.session_state[k]=v

    # Sidebar: logo + controls
    with st.sidebar:
        st.image("adi_logo.png", use_column_width=True)
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

    # Top banner
    st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

    topic = st.text_area("Topic / Outcome (optional)", height=80, placeholder="e.g., Integrated Project and ...")

    with st.expander("Low (Weeks 1–4) — Remember / Understand", True):
        low = st.multiselect("Low verbs", LOW, default=LOW[:3], key="lowverbs")
    with st.expander("Medium (Weeks 5–9) — Apply / Analyse", False):
        med = st.multiselect("Medium verbs", MED, default=MED[:3], key="medverbs")
    with st.expander("High (Weeks 10–14) — Evaluate / Create", False):
        high = st.multiselect("High verbs", HIGH, default=HIGH[:3], key="highverbs")

    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision", "Print Summary"])

    text = ""
    if uploaded is not None:
        sig = file_signature(uploaded, deep)
        if st.session_state["last_sig"] != sig:
            ftype = detect_filetype(uploaded)
            data  = uploaded.getvalue()
            text, note = parse_upload_cached(data, ftype, deep)
            st.session_state["upload_meta"] = {"name": uploaded.name, "type": ftype, "note": note}
            st.session_state["last_sig"] = sig
        meta = st.session_state["upload_meta"]
        status.markdown(f"✅ **Uploaded:** {meta['name']}  \\n_Type:_ {meta['type']} — {meta['note']}")
    else:
        st.session_state["last_sig"] = None

    with tabs[0]:
        n = st.selectbox("How many MCQs?", [5,10,15,20], index=1)
        include = st.checkbox("Include answer key in export", value=True)
        if st.button("Generate MCQs", type="primary"):
            mcqs, key = gen_mcqs(n, (low or LOW), text, include)
            st.session_state["gen_mcqs"] = mcqs
            st.session_state["answer_key"] = key if include else []
            st.success("Download panel is ready below.")
        if st.session_state["gen_mcqs"]:
            for q,opts in st.session_state["gen_mcqs"]:
                st.markdown(f"**{q}**")
                for j,opt in enumerate(opts, start=1): st.markdown(f"{chr(64+j)}. {opt}")
                st.write("")
            st.markdown('<div class="download-panel">', unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download DOCX",
                                   data=export_docx(st.session_state["gen_mcqs"], include, st.session_state["answer_key"]),
                                   file_name="ADI_Knowledge_MCQs.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col2:
                st.download_button("⬇️ Download TXT",
                                   data=export_txt(st.session_state["gen_mcqs"], st.session_state["answer_key"], include),
                                   file_name="ADI_Knowledge_MCQs.txt",
                                   mime="text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        left, right = st.columns([2,2])
        with left:
            act_choices = [("1 per lesson",1),("2 per lesson",2),("3 per lesson",3)]
            act_label = st.selectbox("How many activities?", [l for l,_ in act_choices], index=0, key="n_act")
            n_act = dict(act_choices)[act_label]
        with right:
            minute_values = list(range(5,61,5))  # 5 to 60
            minute_labels = [f"{m} min" for m in minute_values]
            mins = dict(zip(minute_labels, minute_values))[
                st.selectbox("Minutes per activity", minute_labels, index=1, key="act_mins")
            ]
        gs_choices = [("Solo (1)",1),("Pairs (2)",2),("Triads (3)",3),("Quads (4)",4)]
        group_size = dict(gs_choices)[
            st.selectbox("Group size", [l for l,_ in gs_choices], index=1, key="group_size")
        ]
        if st.button("Generate Activities"):
            terms = pick_terms(text, max(10,n_act*2))[:n_act]
            acts = [f"{i+1}. {random.choice(med or MED).capitalize()} a {mins}-minute activity "
                    f"for groups of {group_size} focusing on **{w}**."
                    for i,w in enumerate(terms)]
            st.session_state["gen_acts"] = acts; st.success("Activities generated.")
        if st.session_state["gen_acts"]:
            for a in st.session_state["gen_acts"]: st.markdown(f"- {a}")
            st.markdown('<div class="download-panel">', unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download DOCX (Activities)",
                                   data=export_docx_list(st.session_state["gen_acts"], "Skills Activities"),
                                   file_name="ADI_Skills_Activities.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col2:
                st.download_button("⬇️ Download TXT (Activities)",
                                   data=export_txt_list(st.session_state["gen_acts"]),
                                   file_name="ADI_Skills_Activities.txt",
                                   mime="text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        n_rev = st.selectbox("How many revision prompts?", [3,5,8,10], index=0, key="n_rev")
        if st.button("Generate Revision"):
            revs = [f"{i+1}. {random.choice(low or LOW).capitalize()} key points on **{w}** in a 5-bullet summary."
                    for i,w in enumerate(pick_terms(text, max(10,n_rev*2))[:n_rev])]
            st.session_state["gen_rev"] = revs; st.success("Revision prompts generated.")
        if st.session_state["gen_rev"]:
            for r in st.session_state["gen_rev"]: st.markdown(f"- {r}")
            st.markdown('<div class="download-panel">', unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download DOCX (Revision)",
                                   data=export_docx_list(st.session_state["gen_rev"], "Revision Prompts"),
                                   file_name="ADI_Revision_Prompts.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col2:
                st.download_button("⬇️ Download TXT (Revision)",
                                   data=export_txt_list(st.session_state["gen_rev"]),
                                   file_name="ADI_Revision_Prompts.txt",
                                   mime="text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.subheader("Print Summary")
        st.markdown(f"**Course:** {course or '—'}  \\n**Cohort:** {cohort or '—'}  \\n**Instructor:** {instructor or '—'}  \\n**Date:** {the_date}  \\n**Lesson:** {lesson}  \\n**Week:** {week}")
        st.divider()
        if st.session_state["gen_mcqs"]:
            st.markdown("### Knowledge MCQs")
            for q,opts in st.session_state["gen_mcqs"]:
                st.markdown(f"**{q}**")
                for j,opt in enumerate(opts, start=1): st.markdown(f"{chr(64+j)}. {opt}")
                st.write("")
        if st.session_state["gen_acts"]:
            st.markdown("### Skills Activities"); [st.markdown(f"- {a}") for a in st.session_state["gen_acts"]]
        if st.session_state["gen_rev"]:
            st.markdown("### Revision"); [st.markdown(f"- {r}") for r in st.session_state["gen_rev"]]

if __name__ == "__main__":
    main()
