
import streamlit as st
import io, os, json, random, textwrap
from datetime import date
from pathlib import Path

# ---------- Optional PDF support ----------
try:
    import fitz  # PyMuPDF
    PDF_ENABLED = True
except Exception:
    fitz = None
    PDF_ENABLED = False

# ---------- Page + Styles ----------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#f7f8f7"
BAND_LOW  = "#eaf3ed"
BAND_MED  = "#fcf8ef"
BAND_HIGH = "#eef2ff"

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="🗂️", layout="wide")

st.markdown(f"""
<style>
:root {{
  --adi-green:{ADI_GREEN}; --adi-gold:{ADI_GOLD}; --adi-stone:{ADI_STONE};
  --band-low:{BAND_LOW}; --band-med:{BAND_MED}; --band-high:{BAND_HIGH};
}}
/* Sidebar look */
section[data-testid="stSidebar"]{{background:#fff;border-right:1px solid #e5e7eb;}}
/* Banner */
.adi-banner{{background:var(--adi-green);color:#fff;padding:14px 18px;border-radius:12px;
  font-weight:600;margin-bottom:14px;box-shadow:0 1px 0 rgba(0,0,0,.03),0 6px 18px rgba(0,0,0,.06) inset;}}
.adi-subtle{{color:#e7f2ea;font-weight:400;font-size:.9rem;}}
/* Bloom tints */
div.low-band>div>div{{background:var(--band-low)!important;}}
div.med-band>div>div{{background:var(--band-med)!important;}}
div.high-band>div>div{{background:var(--band-high)!important;}}
/* Clickable feel */
div[data-baseweb="tab"] button{{border-radius:999px!important;cursor:pointer;}}
button[kind="primary"]{{border-radius:12px!important;cursor:pointer;}}
div[data-baseweb="select"] *{{cursor:pointer!important;}}
/* Uploader: green dashed */
div[data-testid="stFileUploaderDropzone"]{{
  border:2px dashed var(--adi-green)!important;
  background:#fff;border-radius:12px;
}}
/* Download panel: green dashed */
.download-panel{{border:2px dashed var(--adi-green);background:#fff;border-radius:14px;padding:14px;margin-top:8px;}}
</style>
""", unsafe_allow_html=True)

# ---------- Persistence (courses/cohorts/instructors) ----------
DATA_DIR = Path(os.getenv("DATA_DIR", "."))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CFG_FILE = DATA_DIR / "adi_modules.json"
SEED_CFG = {
    "courses": ["Defense Technologies 101", "Integrated Project & Systems"],
    "cohorts": ["D1-C01"],
    "instructors": ["Staff Instructor"]
}

def load_cfg():
    try:
        cfg = json.loads(CFG_FILE.read_text(encoding="utf-8")) if CFG_FILE.exists() else {}
    except Exception:
        cfg = {}
    for k in ("courses","cohorts","instructors"):
        if k not in cfg or not isinstance(cfg[k], list) or len(cfg[k])==0:
            cfg[k] = SEED_CFG[k].copy()
    return cfg

def save_cfg(cfg):
    try:
        CFG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        st.warning(f"Could not save settings: {e}")

if "cfg" not in st.session_state:
    st.session_state.cfg = load_cfg()

def ensure_state():
    defaults = {
        "gen_mcqs": [], "gen_acts": [], "gen_rev": [],
        "answer_key": [], "export_ready": False, "upload_meta": None
    }
    for k,v in defaults.items():
        st.session_state.setdefault(k,v)

def edit_list(label, key, placeholder):
    """Selectbox with ＋ / − controls; persists to cfg."""
    items = st.session_state.cfg.get(key, [])
    opts  = [f"— {placeholder} —"] + items
    c1,c2,c3 = st.columns([5,1,1])
    choice = c1.selectbox(label, opts, index=0, key=f"sel_{key}")
    add = c2.button("＋", key=f"add_{key}")
    rm  = c3.button("−", key=f"rm_{key}")
    selected = None if choice == opts[0] else choice

    if add:
        st.session_state[f"adding_{key}"] = True
    if rm and selected:
        try:
            items.remove(selected); save_cfg(st.session_state.cfg); st.rerun()
        except ValueError:
            pass

    if st.session_state.get(f"adding_{key}"):
        new_val = st.text_input(f"Add new {label.lower()}", key=f"new_{key}")
        csa, csb = st.columns([1,1])
        if csa.button("Save", key=f"save_{key}"):
            if new_val and new_val not in items:
                items.append(new_val); save_cfg(st.session_state.cfg)
            st.session_state[f"adding_{key}"] = False; st.rerun()
        if csb.button("Cancel", key=f"cancel_{key}"):
            st.session_state[f"adding_{key}"] = False
    return selected

# ---------- Upload parsing (cached + gentle messaging) ----------
def detect_filetype(uploaded_file)->str:
    name=(uploaded_file.name or "").lower(); mime=(uploaded_file.type or "").lower()
    for ext,ft in ((".pdf","pdf"),(".pptx","pptx"),(".docx","docx"),(".txt","txt")):
        if name.endswith(ext): return ft
    if "pdf" in mime: return "pdf"
    if "ppt" in mime: return "pptx"
    if "word" in mime: return "docx"
    if "text" in mime: return "txt"
    return "txt"

@st.cache_data(show_spinner=False)
def parse_upload_cached(file_bytes:bytes, filetype:str, deep:bool):
    try:
        if filetype=="pdf":
            if not PDF_ENABLED: return "", "PDF parsing disabled"
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page_total = len(doc)
            max_pages  = page_total if deep else min(10, page_total)
            text = "\n".join(doc[p].get_text("text") for p in range(max_pages))
            return text, f"Parsed {max_pages}/{page_total} pages ({'deep' if deep else 'quick'})"
        if filetype=="pptx":
            from pptx import Presentation
            prs = Presentation(io.BytesIO(file_bytes))
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        texts.append(shape.text)
            return "\n".join(texts), f"Parsed {len(prs.slides)} slides"
        if filetype=="docx":
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs), f"Parsed {len(doc.paragraphs)} paragraphs"
        return file_bytes.decode("utf-8", errors="ignore"), "Parsed text file"
    except Exception as e:
        return "", f"Error: {e}"

# ---------- Generators (placeholder logic) ----------
BLOOM_VERBS_LOW  = ["define","identify","list","recall","describe","label"]
BLOOM_VERBS_MED  = ["apply","demonstrate","solve","illustrate","classify","compare"]
BLOOM_VERBS_HIGH = ["evaluate","synthesize","design","justify","critique","create"]

def pick_terms(text,k=20):
    if not text:
        corpus=["safety","procedure","system","component","principle","policy","mission","calibration","diagnostics","maintenance"]
    else:
        tokens=[t.strip(".,:;()[]{}!?\"'").lower() for t in text.split()]
        tokens=[t for t in tokens if t.isalpha() and 3<=len(t)<=14]
        stops=set("the of and to in for is are be a an on from with that this these those which using as by or it at we you they can may into over under".split())
        corpus=[t for t in tokens if t not in stops] or ["concept","process","system","protocol","hazard","control"]
    random.shuffle(corpus); return corpus[:k]

def generate_mcqs(n, verbs, source_text, include_answers=True):
    terms=pick_terms(source_text, k=max(20,n*5)); mcqs=[]; key=[]
    for i in range(n):
        term=random.choice(terms); verb=random.choice(verbs or BLOOM_VERBS_LOW)
        q=f"{i+1}. {verb.capitalize()} the following term as it relates to the lesson: **{term}**."
        correct=f"Accurate statement about {term}."
        distract=[f"Unrelated detail about {random.choice(terms)}.",
                  f"Common misconception about {term}.",
                  f"Vague statement with {random.choice(terms)}."]
        opts=distract+[correct]; random.shuffle(opts); mcqs.append((q,opts))
        if include_answers: key.append(opts.index(correct)+1)
    return mcqs, key

def generate_activities(n, verbs, source_text):
    terms=pick_terms(source_text,k=max(10,n*2)); acts=[]
    for i in range(n):
        verb=random.choice(verbs or BLOOM_VERBS_MED); focus=random.choice(terms)
        acts.append(f"{i+1}. {verb.capitalize()} a short activity where learners work in pairs to address **{focus}** and present findings in 3 minutes.")
    return acts

def generate_revision(n, verbs, source_text):
    terms=pick_terms(source_text,k=max(10,n*2)); revs=[]
    for i in range(n):
        verb=random.choice(verbs or BLOOM_VERBS_LOW); focus=random.choice(terms)
        revs.append(f"{i+1}. {verb.capitalize()} key points on **{focus}** in a 5-bullet summary.")
    return revs

# ---------- Export ----------
def export_docx(title, mcqs=None, acts=None, rev=None, include_answers=False, answer_key=None)->bytes:
    from docx import Document
    doc=Document(); doc.add_heading(title,level=1)
    if mcqs:
        doc.add_heading("Knowledge MCQs",level=2)
        for q,opts in mcqs:
            r=doc.add_paragraph().add_run(q); r.bold=True
            for j,opt in enumerate(opts, start=1): doc.add_paragraph(f"{chr(64+j)}. {opt}")
    if acts:
        doc.add_heading("Skills Activities",level=2); [doc.add_paragraph(a) for a in acts]
    if rev:
        doc.add_heading("Revision",level=2); [doc.add_paragraph(r) for r in rev]
    if include_answers and answer_key:
        doc.add_heading("Answer Key",level=2)
        for i,ans in enumerate(answer_key, start=1): doc.add_paragraph(f"Q{i}: {['A','B','C','D'][ans-1]}")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_txt_mcqs(mcqs, answer_key=None, include_answers=False)->bytes:
    lines=[]; 
    for q,opts in mcqs:
        lines.append(q); [lines.append(f"{chr(64+j)}. {opt}") for j,opt in enumerate(opts, start=1)]; lines.append("")
    if include_answers and answer_key:
        lines.append("Answer Key"); [lines.append(f"Q{i}: {['A','B','C','D'][ans-1]}") for i,ans in enumerate(answer_key, start=1)]
    return ("\n".join(lines)).encode("utf-8")

# ---------- App ----------
def main():
    ensure_state()

    with st.sidebar:
        logo=Path("adi_logo.png")
        if logo.exists(): st.image(str(logo), use_column_width=True)

        st.subheader("Upload (optional)")
        uploaded_file = st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"], key="uploader")
        deep_scan = st.toggle("Deep scan source (slower, better coverage)", value=False)
        st.caption("Quick scan reads the first 10 PDF pages. Turn on deep scan for full documents.")
        st.divider()

        st.subheader("Course details")
        course    = edit_list("Course name",      "courses",   "Choose a course")
        cohort    = edit_list("Class / Cohort",   "cohorts",   "Choose a cohort")
        instructor= edit_list("Instructor name",  "instructors","Choose an instructor")
        the_date  = st.date_input("Date", value=date.today())

        st.subheader("Context")
        c1,c2 = st.columns(2)
        lesson = c1.number_input("Lesson", 1, 5, 1, step=1)
        week   = c2.number_input("Week", 1, 14, 1, step=1)
        st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

    st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions'
                '<div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>'
                '</div>', unsafe_allow_html=True)

    topic = st.text_area("Topic / Outcome (optional)", height=80, placeholder="e.g., Integrated Project and ...")

    low_exp, med_exp, high_exp = st.expander("**Low (Weeks 1–4)** — Remember / Understand", True), \
                                 st.expander("**Medium (Weeks 5–9)** — Apply / Analyse", False), \
                                 st.expander("**High (Weeks 10–14)** — Evaluate / Create", False)

    with low_exp:  st.markdown('<div class="low-band">',  unsafe_allow_html=True);  low  = st.multiselect("Low verbs",  BLOOM_VERBS_LOW,  default=BLOOM_VERBS_LOW[:3], key="lowverbs");  st.markdown('</div>', unsafe_allow_html=True)
    with med_exp:  st.markdown('<div class="med-band">',  unsafe_allow_html=True);  med  = st.multiselect("Medium verbs",BLOOM_VERBS_MED,  default=BLOOM_VERBS_MED[:3], key="medverbs");  st.markdown('</div>', unsafe_allow_html=True)
    with high_exp: st.markdown('<div class="high-band">', unsafe_allow_html=True);  high = st.multiselect("High verbs",  BLOOM_VERBS_HIGH, default=BLOOM_VERBS_HIGH[:3], key="highverbs"); st.markdown('</div>', unsafe_allow_html=True)

    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision", "Print Summary"])

    # Parse upload once (no toast storm)
    source_text = ""
    if uploaded_file is not None:
        ftype = detect_filetype(uploaded_file)
        data  = uploaded_file.getvalue()
        text, note = parse_upload_cached(data, ftype, deep_scan)
        st.session_state.upload_meta = {"name": uploaded_file.name, "type": ftype, "note": note}
        source_text = text

    if st.session_state.upload_meta:
        m = st.session_state.upload_meta
        st.write(f"**Source loaded:** {m['name']}  \n_Type:_ {m['type']} — {m['note']}")

    # ----- Tab 1: MCQs -----
    with tabs[0]:
        cA,cB,_ = st.columns([2,1,1])
        with cA: n_mcq = st.selectbox("How many MCQs?", [5,10,15,20], index=1)
        with cB: include_key = st.checkbox("Include answer key in export", value=True)
        if st.button("Generate MCQs", type="primary"):
            mcqs, key = generate_mcqs(n_mcq, (low or BLOOM_VERBS_LOW), source_text, include_answers=include_key)
            st.session_state.gen_mcqs = mcqs
            st.session_state.answer_key = key if include_key else []
            st.session_state.export_ready = True
            st.success("Download panel is ready below.")

        if st.session_state.get("gen_mcqs"):
            for q, opts in st.session_state.gen_mcqs:
                st.markdown(f"**{q}**")
                for j,opt in enumerate(opts, start=1): st.markdown(f"{chr(64+j)}. {opt}")
                st.write("")

            st.markdown('<div class="download-panel">', unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                docx_bytes = export_docx(
                    title=f"{(course or 'Course')} — Lesson {lesson} (Week {week})",
                    mcqs=st.session_state.gen_mcqs,
                    include_answers=include_key,
                    answer_key=st.session_state.answer_key,
                )
                st.download_button("⬇️ Download DOCX", data=docx_bytes,
                                   file_name="ADI_Knowledge_MCQs.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col2:
                txt_bytes = export_txt_mcqs(st.session_state.gen_mcqs,
                                            st.session_state.answer_key,
                                            include_answers=include_key)
                st.download_button("⬇️ Download TXT", data=txt_bytes,
                                   file_name="ADI_Knowledge_MCQs.txt", mime="text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    # ----- Tab 2: Activities -----
    with tabs[1]:
        n_act = st.selectbox("How many activities?", [3,5,8,10], index=1, key="n_act")
        if st.button("Generate Activities"):
            acts = generate_activities(n_act, (med or BLOOM_VERBS_MED), source_text)
            st.session_state.gen_acts = acts; st.success("Activities generated.")
        if st.session_state.get("gen_acts"):
            for a in st.session_state.gen_acts: st.markdown(f"- {a}")

    # ----- Tab 3: Revision -----
    with tabs[2]:
        n_rev = st.selectbox("How many revision prompts?", [3,5,8,10], index=1, key="n_rev")
        if st.button("Generate Revision"):
            revs = generate_revision(n_rev, (low or BLOOM_VERBS_LOW), source_text)
            st.session_state.gen_rev = revs; st.success("Revision prompts generated.")
        if st.session_state.get("gen_rev"):
            for r in st.session_state.gen_rev: st.markdown(f"- {r}")

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
        # Show a single error, stop cleanly (prevents gray flicker)
        st.error(f"Unexpected error: {e}")
        st.stop()


