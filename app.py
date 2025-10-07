
import streamlit as st
import io, random, textwrap, json, os
from datetime import date
from pathlib import Path

# ------------------------
# Optional PDF support
# ------------------------
try:
    import fitz  # PyMuPDF
    PDF_ENABLED = True
except Exception:
    fitz = None
    PDF_ENABLED = False

# ------------------------
# ADI brand + page config
# ------------------------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#f7f8f7"
BAND_LOW  = "#eaf3ed"
BAND_MED  = "#fcf8ef"
BAND_HIGH = "#eef2ff"

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="🗂️", layout="wide")

# global styles (visual only)
st.markdown(f"""
<style>
:root {{
  --adi-green: {ADI_GREEN};
  --adi-gold: {ADI_GOLD};
  --adi-stone: {ADI_STONE};
  --band-low: {BAND_LOW};
  --band-med: {BAND_MED};
  --band-high:{BAND_HIGH};
}}
/* sidebar */
section[data-testid="stSidebar"] {{
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
}}
/* header banner */
.adi-banner {{
  background: var(--adi-green);
  color: #fff;
  padding: 14px 18px;
  border-radius: 12px;
  font-weight: 600;
  margin-bottom: 14px;
  box-shadow: 0 1px 0 rgba(0,0,0,.03), 0 6px 18px rgba(0,0,0,.06) inset;
}}
.adi-subtle {{
  color: #e7f2ea;
  font-weight: 400;
  font-size: .9rem;
}}
/* band tints */
div.low-band > div > div {{ background: var(--band-low) !important; }}
div.med-band > div > div {{ background: var(--band-med) !important; }}
div.high-band > div > div {{ background: var(--band-high) !important; }}
/* pill-like tabs */
div[data-baseweb="tab"] button {{ border-radius: 999px !important; cursor: pointer; }}
/* primary buttons */
button[kind="primary"] {{ border-radius: 12px !important; cursor: pointer; }}
/* selects feel clickable */
div[data-baseweb="select"] * {{ cursor: pointer !important; }}
/* download panel */
.download-panel {{
  border: 2px dashed var(--adi-green);
  background: #ffffff;
  border-radius: 14px;
  padding: 14px;
  margin-top: 8px;
}}
</style>
""", unsafe_allow_html=True)

# ------------------------
# Persistence for lists
# ------------------------
DATA_DIR = Path(os.getenv("DATA_DIR", "."))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CFG_FILE = DATA_DIR / "adi_modules.json"
SEED_CFG = {
    "courses": ["Defense Technologies 101", "Integrated Project & Systems"],
    "instructors": ["Staff Instructor", "Course Lead"]
}

def load_cfg():
    try:
        if CFG_FILE.exists():
            cfg = json.loads(CFG_FILE.read_text(encoding="utf-8")) or {}
        else:
            cfg = {}
    except Exception:
        cfg = {}
    for k in ("courses", "instructors"):
        if k not in cfg or not isinstance(cfg[k], list) or len(cfg[k]) == 0:
            cfg[k] = SEED_CFG[k].copy()
    return cfg

def save_cfg(cfg):
    try:
        CFG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        st.warning(f"Could not save config: {e}")

if "cfg" not in st.session_state:
    st.session_state.cfg = load_cfg()

def ensure_state():
    defaults = {
        "gen_mcqs": [],
        "gen_acts": [],
        "gen_rev": [],
        "answer_key": [],
        "export_ready": False,
        "adding_courses": False,
        "adding_instructors": False,
        "upload_meta": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

def edit_list(label: str, items_key: str, placeholder: str):
    items = st.session_state.cfg.get(items_key, [])
    options = [f"— {placeholder} —"] + items
    c1, c2, c3 = st.columns([5,1,1])
    choice = c1.selectbox(label, options, index=0, key=f"sel_{items_key}")
    add = c2.button("＋", key=f"add_{items_key}")
    rm  = c3.button("−", key=f"rm_{items_key}")
    selected = None if choice == options[0] else choice

    if add:
        st.session_state[f"adding_{items_key}"] = True
    if rm and selected:
        try:
            items.remove(selected)
            save_cfg(st.session_state.cfg)
            st.rerun()
        except ValueError:
            pass

    if st.session_state.get(f"adding_{items_key}"):
        new_val = st.text_input(f"Add new {label.lower()}", key=f"new_{items_key}")
        csa, csb = st.columns([1,1])
        if csa.button("Save", key=f"save_{items_key}"):
            if new_val and new_val not in items:
                items.append(new_val)
                save_cfg(st.session_state.cfg)
            st.session_state[f"adding_{items_key}"] = False
            st.rerun()
        if csb.button("Cancel", key=f"cancel_{items_key}"):
            st.session_state[f"adding_{items_key}"] = False

    return selected

# ------------------------
# File parsing (cached + robust)
# ------------------------
def detect_filetype(uploaded_file) -> str:
    name = (uploaded_file.name or "").lower()
    if name.endswith(".pdf"):   return "pdf"
    if name.endswith(".pptx"):  return "pptx"
    if name.endswith(".docx"):  return "docx"
    if name.endswith(".txt"):   return "txt"
    mime = (uploaded_file.type or "").lower()
    if "pdf" in mime:    return "pdf"
    if "ppt" in mime:    return "pptx"
    if "word" in mime:   return "docx"
    if "text" in mime:   return "txt"
    return "txt"

@st.cache_data(show_spinner=False)
def parse_upload_cached(file_bytes: bytes, filetype: str, deep: bool):
    try:
        if filetype == "pdf":
            if not PDF_ENABLED:
                return "", "PDF parsing disabled"
            text = []
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page_total = len(doc)
            max_pages = page_total if deep else min(10, page_total)  # quick scan reads first 10
            for p in range(max_pages):
                text.append(doc[p].get_text("text"))
            note = f"Parsed {max_pages}/{page_total} pages ({'deep' if deep else 'quick'})"
            return "\n".join(text), note

        if filetype == "pptx":
            from pptx import Presentation
            prs = Presentation(io.BytesIO(file_bytes))
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        texts.append(shape.text)
            return "\n".join(texts), f"Parsed {len(prs.slides)} slides"

        if filetype == "docx":
            from docx import Document
            bio = io.BytesIO(file_bytes)
            doc = Document(bio)
            return "\n".join([p.text for p in doc.paragraphs]), f"Parsed {len(doc.paragraphs)} paragraphs"

        # txt default
        return file_bytes.decode("utf-8", errors="ignore"), "Parsed text file"
    except Exception as e:
        return "", f"Error: {e}"

# ------------------------
# Generators (rule-based placeholders)
# ------------------------
BLOOM_VERBS_LOW = ["define", "identify", "list", "recall", "describe", "label"]
BLOOM_VERBS_MED = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
BLOOM_VERBS_HIGH = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

def pick_terms(text, k=20):
    if not text:
        corpus = ["safety", "procedure", "system", "component", "principle", "policy", "mission", "calibration", "diagnostics", "maintenance"]
    else:
        tokens = [t.strip(".,:;()[]{}!?\"'").lower() for t in text.split()]
        tokens = [t for t in tokens if t.isalpha() and 3 <= len(t) <= 14]
        common_stops = set("the of and to in for is are be a an on from with that this these those which using as by or it at we you they can may into over under".split())
        corpus = [t for t in tokens if t not in common_stops]
        if not corpus:
            corpus = ["concept", "process", "system", "protocol", "hazard", "control"]
    random.shuffle(corpus)
    return corpus[:k]

def generate_mcqs(n, verbs, source_text, include_answers=True):
    terms = pick_terms(source_text, k=max(20, n*5))
    mcqs, key = [], []
    for i in range(n):
        term = random.choice(terms)
        verb = random.choice(verbs or BLOOM_VERBS_LOW)
        question = f"{i+1}. {verb.capitalize()} the following term as it relates to the lesson: **{term}**."
        correct = f"Accurate statement about {term}."
        distractors = [
            f"Unrelated detail about {random.choice(terms)}.",
            f"Common misconception about {term}.",
            f"Vague statement with {random.choice(terms)}."
        ]
        options = distractors + [correct]
        random.shuffle(options)
        mcqs.append((question, options))
        if include_answers:
            key.append(options.index(correct) + 1)
    return mcqs, key

def generate_activities(n, verbs, source_text):
    terms = pick_terms(source_text, k=max(10, n*2))
    acts = []
    for i in range(n):
        verb = random.choice(verbs or BLOOM_VERBS_MED)
        focus = random.choice(terms)
        acts.append(f"{i+1}. {verb.capitalize()} a short activity where learners work in pairs to address **{focus}** and present findings in 3 minutes.")
    return acts

def generate_revision(n, verbs, source_text):
    terms = pick_terms(source_text, k=max(10, n*2))
    revs = []
    for i in range(n):
        verb = random.choice(verbs or BLOOM_VERBS_LOW)
        focus = random.choice(terms)
        revs.append(f"{i+1}. {verb.capitalize()} key points on **{focus}** in a 5-bullet summary.")
    return revs

# ------------------------
# Exporters
# ------------------------
def export_docx(title, mcqs=None, acts=None, rev=None, include_answers=False, answer_key=None) -> bytes:
    from docx import Document
    doc = Document()
    doc.add_heading(title, level=1)

    if mcqs:
        doc.add_heading("Knowledge MCQs", level=2)
        for idx, (q, options) in enumerate(mcqs, start=1):
            p = doc.add_paragraph()
            run = p.add_run(q)
            run.bold = True
            for j, opt in enumerate(options, start=1):
                doc.add_paragraph(f"{chr(64+j)}. {opt}", style=None)

    if acts:
        doc.add_heading("Skills Activities", level=2)
        for i, a in enumerate(acts, start=1):
            doc.add_paragraph(a)

    if rev:
        doc.add_heading("Revision", level=2)
        for i, r in enumerate(rev, start=1):
            doc.add_paragraph(r)

    if include_answers and answer_key:
        doc.add_heading("Answer Key", level=2)
        for i, ans in enumerate(answer_key, start=1):
            doc.add_paragraph(f"Q{i}: {['A','B','C','D'][ans-1]}")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def export_txt_mcqs(mcqs, answer_key=None, include_answers=False) -> bytes:
    lines = []
    for idx, (q, options) in enumerate(mcqs, start=1):
        lines.append(q)
        for j, opt in enumerate(options, start=1):
            lines.append(f"{chr(64+j)}. {opt}")
        lines.append("")
    if include_answers and answer_key:
        lines.append("Answer Key")
        for i, ans in enumerate(answer_key, start=1):
            lines.append(f"Q{i}: {['A','B','C','D'][ans-1]}")
    return ("\n".join(lines)).encode("utf-8")

# ------------------------
# UI
# ------------------------
def main():
    ensure_state()

    with st.sidebar:
        # Local logo with graceful fallback
        logo_path = Path("adi_logo.png")
        if logo_path.exists():
            st.image(str(logo_path), use_column_width=True)
        else:
            st.markdown("<small style='color:#6b7280'>Logo not found (adi_logo.png). Add it to the repo root.</small>", unsafe_allow_html=True)

        st.subheader("Upload (optional)")
        uploaded_file = st.file_uploader("Drag and drop file here", type=["txt", "docx", "pptx", "pdf"])
        deep_scan = st.toggle("Deep scan source (slower, better coverage)", value=False)
        st.caption("Quick scan reads the first 10 PDF pages. Turn on deep scan for full documents.")
        st.divider()

        st.subheader("Course details")
        course = edit_list("Course name", "courses", "Choose a course")
        cohort = st.text_input("Class / Cohort", value="D1-C01")
        instructor = edit_list("Instructor name", "instructors", "Choose an instructor")
        the_date = st.date_input("Date", value=date.today())

        st.subheader("Context")
        colA, colB = st.columns(2)
        lesson = colA.number_input("Lesson", 1, 5, 1, step=1)
        week = colB.number_input("Week", 1, 14, 1, step=1)
        st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

    # Banner
    st.markdown(
        '<div class="adi-banner">ADI Builder — Lesson Activities & Questions'
        '<div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    topic = st.text_area("Topic / Outcome (optional)", height=80, placeholder="e.g., Integrated Project and ...")

    # Bloom bands
    low_expander = st.expander("**Low (Weeks 1–4)** — Remember / Understand", expanded=True)
    med_expander = st.expander("**Medium (Weeks 5–9)** — Apply / Analyse", expanded=False)
    high_expander = st.expander("**High (Weeks 10–14)** — Evaluate / Create", expanded=False)

    with st.container():
        with low_expander:
            st.markdown('<div class="low-band">', unsafe_allow_html=True)
            low = st.multiselect("Low verbs", BLOOM_VERBS_LOW, default=BLOOM_VERBS_LOW[:3], key="lowverbs")
            st.markdown('</div>', unsafe_allow_html=True)
        with med_expander:
            st.markdown('<div class="med-band">', unsafe_allow_html=True)
            med = st.multiselect("Medium verbs", BLOOM_VERBS_MED, default=BLOOM_VERBS_MED[:3], key="medverbs")
            st.markdown('</div>', unsafe_allow_html=True)
        with high_expander:
            st.markdown('<div class="high-band">', unsafe_allow_html=True)
            high = st.multiselect("High verbs", BLOOM_VERBS_HIGH, default=BLOOM_VERBS_HIGH[:3], key="highverbs")
            st.markdown('</div>', unsafe_allow_html=True)

    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision", "Print Summary"])

    # Source text + status
    source_text = ""
    if 'upload_meta' not in st.session_state:
        st.session_state.upload_meta = None

    if uploaded_file is not None:
        with st.status("Processing upload…", expanded=False) as s:
            ftype = detect_filetype(uploaded_file)
            data = uploaded_file.read()
            text, note = parse_upload_cached(data, ftype, deep_scan)
            source_text = text
            st.session_state.upload_meta = {"name": uploaded_file.name, "type": ftype, "note": note}
            if text:
                s.update(label=f"Upload processed: {uploaded_file.name} — {note}", state="complete")
                st.toast(f"Loaded {uploaded_file.name} ({ftype}). {note}")
            else:
                s.update(label=f"Upload failed: {note}", state="error")
                st.error(note)

    if st.session_state.upload_meta:
        meta = st.session_state.upload_meta
        st.write(f"**Source loaded:** {meta['name']}  \n_Type:_ {meta['type']} — {meta['note']}")

    # Tab 1 — MCQs
    with tabs[0]:
        cols = st.columns([2,1,1])
        with cols[0]:
            n_mcq = st.selectbox("How many MCQs?", [5,10,15,20], index=1)
        with cols[1]:
            include_key = st.checkbox("Include answer key in export", value=True)
        if st.button("Generate MCQs", type="primary"):
            mcqs, key = generate_mcqs(n_mcq, (low or BLOOM_VERBS_LOW), source_text, include_answers=include_key)
            st.session_state.gen_mcqs = mcqs
            st.session_state.answer_key = key if include_key else []
            st.session_state.export_ready = True
            st.success("MCQs ready. See download panel below.")

        if st.session_state.get("gen_mcqs"):
            for i, (q, options) in enumerate(st.session_state.gen_mcqs, start=1):
                st.markdown(f"**{q}**")
                for j, opt in enumerate(options, start=1):
                    st.markdown(f"{chr(64+j)}. {opt}")
                st.write("")

            # Download panel
            st.markdown('<div class="download-panel">', unsafe_allow_html=True)
            colDL = st.columns(2)
            with colDL[0]:
                docx_bytes = export_docx(
                    title=f"{(course or 'Course')} — Lesson {lesson} (Week {week})",
                    mcqs=st.session_state.gen_mcqs,
                    acts=None,
                    rev=None,
                    include_answers=include_key,
                    answer_key=st.session_state.answer_key,
                )
                st.download_button("⬇️ Download DOCX", data=docx_bytes, file_name="ADI_Knowledge_MCQs.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with colDL[1]:
                txt_bytes = export_txt_mcqs(st.session_state.gen_mcqs, st.session_state.answer_key, include_answers=include_key)
                st.download_button("⬇️ Download TXT", data=txt_bytes, file_name="ADI_Knowledge_MCQs.txt", mime="text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    # Tab 2 — Activities
    with tabs[1]:
        n_act = st.selectbox("How many activities?", [3,5,8,10], index=1, key="n_act")
        if st.button("Generate Activities"):
            acts = generate_activities(n_act, (med or BLOOM_VERBS_MED), source_text)
            st.session_state.gen_acts = acts
            st.session_state.export_ready = True
            st.success("Activities ready.")

        if st.session_state.get("gen_acts"):
            for a in st.session_state.gen_acts:
                st.markdown(f"- {a}")

    # Tab 3 — Revision
    with tabs[2]:
        n_rev = st.selectbox("How many revision prompts?", [3,5,8,10], index=1, key="n_rev")
        if st.button("Generate Revision"):
            revs = generate_revision(n_rev, (low or BLOOM_VERBS_LOW), source_text)
            st.session_state.gen_rev = revs
            st.session_state.export_ready = True
            st.success("Revision prompts ready.")

        if st.session_state.get("gen_rev"):
            for r in st.session_state.gen_rev:
                st.markdown(f"- {r}")

    # Tab 4 — Print Summary
    with tabs[3]:
        st.subheader("Print Summary")
        st.markdown(f"**Course:** {course or '—'}  \n**Cohort:** {cohort}  \n**Instructor:** {instructor or '—'}  \n**Date:** {the_date}  \n**Lesson:** {lesson}  \n**Week:** {week}")
        st.divider()
        if st.session_state.get("gen_mcqs"):
            st.markdown("### Knowledge MCQs")
            for i, (q, options) in enumerate(st.session_state.gen_mcqs, start=1):
                st.markdown(f"**{q}**")
                for j, opt in enumerate(options, start=1):
                    st.markdown(f"{chr(64+j)}. {opt}")
                st.write("")

        if st.session_state.get("gen_acts"):
            st.markdown("### Skills Activities")
            for a in st.session_state.gen_acts:
                st.markdown(f"- {a}")

        if st.session_state.get("gen_rev"):
            st.markdown("### Revision")
            for r in st.session_state.gen_rev:
                st.markdown(f"- {r}")

    st.caption("ADI Builder — sleek, professional and engaging. Print-ready handouts for your instructors.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        # prevent Streamlit from crashing server-side
        st.stop()
