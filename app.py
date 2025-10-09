

import streamlit as st
import io, os, json, random, hashlib
from datetime import date
from pathlib import Path

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🗂️", layout="wide")
st.caption("Build tag: 2025-10-08T00:08 classic-v3-ADI + editable-MCQs")

st.markdown('''
<style>
:root{
  --adi-green:#245a34;
  --low:#cfe8d9;  --low-b:#1e4d2b;  --low-t:#123222;
  --med:#f8e6c9;  --med-b:#a97d2b;  --med-t:#3a2a11;
  --high:#dfe6ff; --high-b:#3f3ac7; --high-t:#17155a;
}
.block-container{padding-top:0.6rem !important}
.adi-banner{ background:var(--adi-green); color:#fff; font-weight:700; padding:12px 16px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.06); margin:8px 0 12px 0; }
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"],
section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"],
div[data-testid="stFileUploaderDropzone"]{ border:4px dashed var(--adi-green) !important; border-radius:12px !important; background:rgba(36,90,52,.05) !important; padding:14px !important; min-height:84px !important; transition:box-shadow .12s, background-color .12s, border-color .12s; }
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"]:hover,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"]:hover,
div[data-testid="stFileUploaderDropzone"]:hover{ box-shadow:0 0 0 4px var(--adi-green) inset !important; background:rgba(36,90,52,.10) !important; }
div[aria-label="Low verbs"]    [data-baseweb="tag"]{background:var(--low)!important;border:1px solid var(--low-b)!important;color:var(--low-t)!important;border-radius:9999px!important;font-weight:700!important}
div[aria-label="Medium verbs"] [data-baseweb="tag"]{background:var(--med)!important;border:1px solid var(--med-b)!important;color:var(--med-t)!important;border-radius:9999px!important;font-weight:700!important}
div[aria-label="High verbs"]   [data-baseweb="tag"]{background:var(--high)!important;border:1px solid var(--high-b)!important;color:var(--high-t)!important;border-radius:9999px!important;font-weight:700!important}
div[aria-label="Low verbs"], div[aria-label="Medium verbs"], div[aria-label="High verbs"]{ background:#f7f7f7 !important; border:1px solid rgba(36,90,52,.18)!important; border-radius:10px!important; padding:6px!important; }
div[aria-label="Low verbs"]:hover, div[aria-label="Low verbs"]:focus-within{box-shadow:0 0 0 2px var(--low-b) inset!important}
div[aria-label="Medium verbs"]:hover, div[aria-label="Medium verbs"]:focus-within{box-shadow:0 0 0 2px var(--med-b) inset!important}
div[aria-label="High verbs"]:hover, div[aria-label="High verbs"]:focus-within{box-shadow:0 0 0 2px var(--high-b) inset!important}
div[role="tablist"] button[role="tab"]{ background:transparent!important;border:none!important;color:#374151!important;padding:8px 12px!important }
div[role="tablist"] button[aria-selected="true"]{ color:var(--adi-green)!important; box-shadow:inset 0 -3px 0 0 var(--adi-green)!important; font-weight:700!important }
button[kind], button{background:var(--adi-green)!important;border-color:var(--adi-green)!important;color:#fff!important;border-radius:10px!important;font-weight:700!important}
button:hover{filter:brightness(.96)!important}
div[data-testid="stSelectbox"] button, div[data-testid="stMultiSelect"] button, [data-baseweb="select"] div[role="button"], section[data-testid="stSidebar"] div[data-testid="stSelectbox"] button{ cursor:pointer!important; background:#f7f7f7!important; border:1px solid rgba(36,90,52,.18)!important; border-radius:10px!important; transition:box-shadow .12s }
div[data-testid="stSelectbox"] button:hover, div[data-testid="stMultiSelect"] button:hover, [data-baseweb="select"] div[role="button"]:hover{ box-shadow:0 0 0 2px var(--adi-green) inset!important }
[data-baseweb="input"]:hover{ box-shadow:0 0 0 2px var(--adi-green) inset!important } :focus-visible{ outline:2px solid var(--adi-green)!important; outline-offset:2px }
.mcq-card{ border:1px solid rgba(36,90,52,.18); border-radius:12px; padding:12px; background:#fff; margin:10px 0; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
</style>
''', unsafe_allow_html=True)

DATA_DIR = Path(os.getenv("DATA_DIR",".")); DATA_DIR.mkdir(parents=True, exist_ok=True)
CFG_FILE = DATA_DIR / "adi_modules.json"
SEED_CFG = {"courses":["GE4-IPM — Integrated Project & Materials Mgmt","Defense Technologies 101"],
            "cohorts":["D1-M01","D1-C01","D1-C02","D2-M01"],
            "instructors":["Daniel","Ghamza Labeeb","Nerdeen Tariq","Abdulmalik","Ben","Gerhard","Chetan","Yasser"]}
def load_cfg():
    try: return json.loads(CFG_FILE.read_text(encoding="utf-8")) if CFG_FILE.exists() else SEED_CFG.copy()
    except Exception: return SEED_CFG.copy()
def save_cfg(cfg): CFG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
if "cfg" not in st.session_state: st.session_state.cfg = load_cfg()

def edit_list(label, key, placeholder):
    items = st.session_state.cfg.get(key, [])
    opts=[f"Select {placeholder}"]+items
    c1,c2,c3=st.columns([5,1,1])
    choice=c1.selectbox(label, opts, index=0, key=f"sel_{key}")
    add=c2.button("＋", key=f"add_{key}"); rm=c3.button("−", key=f"rm_{key}")
    selected=None if choice==opts[0] else choice
    if add: st.session_state[f"adding_{key}"]=True
    if rm and selected:
        try: items.remove(selected); st.session_state.cfg[key]=items; save_cfg(st.session_state.cfg)
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

def gen_mcqs_struct(n, verbs, txt):
    terms=pick_terms(txt, max(20,n*5)); out=[]
    for i in range(n):
        term=random.choice(terms); v=random.choice((verbs or LOW))
        q=f"{i+1}. {v.capitalize()} the following term as it relates to the lesson: {term}."
        right=f"Accurate statement about {term}."
        opts=[f"Unrelated detail about {random.choice(terms)}.",
              f"Common misconception about {term}.",
              f"Vague statement with {random.choice(terms)}.",
              right]
        random.shuffle(opts)
        correct = opts.index(right)  # 0-3
        out.append({"stem": q, "options": opts, "correct": correct})
    return out

def export_docx_from_state(mcqs, include_key=True, title="Knowledge MCQs"):
    from docx import Document
    doc=Document(); doc.add_heading(title, level=1)
    for i,item in enumerate(mcqs, start=1):
        r=doc.add_paragraph().add_run(item["stem"]); r.bold=True
        for j,opt in enumerate(item["options"], start=1): doc.add_paragraph(f"{chr(64+j)}. {opt}")
    if include_key:
        doc.add_heading("Answer Key", level=2)
        for i,item in enumerate(mcqs, start=1): doc.add_paragraph(f"Q{i}: {['A','B','C','D'][item['correct']]}")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_txt_from_state(mcqs, include_key=True):
    lines=[]
    for item in mcqs:
        lines.append(item["stem"])
        for j,opt in enumerate(item["options"], start=1): lines.append(f"{chr(64+j)}. {opt}")
        lines.append("")
    if include_key:
        lines.append("Answer Key")
        for i,item in enumerate(mcqs, start=1): lines.append(f"Q{i}: {['A','B','C','D'][item['correct']]}")
    return ("\n".join(lines)).encode("utf-8")

def main():
    if "mcqs" not in st.session_state: st.session_state.mcqs = []
    if "upload_meta" not in st.session_state: st.session_state.upload_meta=None
    if "last_sig" not in st.session_state: st.session_state.last_sig=None

    with st.sidebar:
        logo_path = Path("adi_logo.png")
        if logo_path.exists(): st.image(str(logo_path), use_column_width=True)
        st.subheader("Upload (optional)")
        uploaded = st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"], key="uploader")
        deep = st.toggle("Deep scan source (slower, better coverage)", value=False)
        status = st.empty()
        st.caption("Quick scan reads the first 10 PDF pages. Turn on deep scan for full documents.")
        st.divider()

        st.subheader("Course details")
        course = edit_list("Course name","courses","course")
        cohort = edit_list("Class / Cohort","cohorts","cohort")
        instructor = edit_list("Instructor name","instructors","instructor")
        the_date = st.date_input("Date", value=date.today())

        st.subheader("Context")
        c1,c2 = st.columns(2)
        lesson = c1.number_input("Lesson", 1, 50, 1, step=1)
        week   = c2.number_input("Week", 1, 20, 1, step=1)
        st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

    st.markdown('<div class="adi-banner">ADI Builder — Lesson Activities & Questions</div>', unsafe_allow_html=True)

    topic = st.text_area("Topic / Outcome (optional)", height=80, placeholder="e.g., Integrated Project and ...")

    LOW  = ["define","identify","list","recall","describe","label"]
    MED  = ["apply","demonstrate","solve","illustriate","classify","compare"]
    HIGH = ["evaluate","synthesize","design","justify","critique","create"]

    with st.expander("Low (Weeks 1–4) — Remember / Understand", True):
        low = st.multiselect("Low verbs", LOW, default=LOW[:3], key="lowverbs")
    with st.expander("Medium (Weeks 5–9) — Apply / Analyse", False):
        med = st.multiselect("Medium verbs", MED, default=MED[:3], key="medverbs")
    with st.expander("High (Weeks 10–14) — Evaluate / Create", False):
        high = st.multiselect("High verbs", HIGH, default=HIGH[:3], key="highverbs")

    tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

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
        status.markdown(f"✅ **Uploaded:** {meta['name']}  \n_Type:_ {meta['type']} — {meta['note']}")
    else:
        st.session_state["last_sig"] = None

    with tabs[0]:
        c1,c2,c3 = st.columns([1,1,2])
        with c1:
            n = st.selectbox("How many?", [5,10,15,20], index=1)
        with c2:
            include_key = st.checkbox("Answer key", value=True)
        with c3:
            if st.button("Generate from verbs/topic", type="primary"):
                verbs = (low or []) + (med or []) + (high or [])
                st.session_state.mcqs = gen_mcqs_struct(n, verbs or LOW, text)

        if st.session_state.mcqs:
            for i,item in enumerate(st.session_state.mcqs):
                st.markdown('<div class="mcq-card">', unsafe_allow_html=True)
                st.markdown(f"**Question {i+1}**")
                item["stem"] = st.text_area(f"Stem {i+1}", item["stem"], key=f"stem_{i}")
                colA, colB = st.columns(2)
                with colA:
                    item["options"][0] = st.text_input(f"A", item["options"][0], key=f"optA_{i}")
                    item["options"][1] = st.text_input(f"B", item["options"][1], key=f"optB_{i}")
                with colB:
                    item["options"][2] = st.text_input(f"C", item["options"][2], key=f"optC_{i}")
                    item["options"][3] = st.text_input(f"D", item["options"][3], key=f"optD_{i}")
                item["correct"] = ["A","B","C","D"].index(
                    st.radio("Correct answer", ["A","B","C","D"], index=item["correct"], horizontal=True, key=f"corr_{i}")
                )
                st.markdown('</div>', unsafe_allow_html=True)

            col1,col2,col3 = st.columns(3)
            with col1:
                if st.button("➕ Add blank question"):
                    st.session_state.mcqs.append({"stem":"New question...", "options":["Option A","Option B","Option C","Option D"], "correct":0})
            with col2:
                if st.button("➖ Remove last"):
                    if st.session_state.mcqs: st.session_state.mcqs.pop()
            with col3:
                st.download_button("⬇️ Download DOCX",
                                   data=export_docx_from_state(st.session_state.mcqs, include_key),
                                   file_name="ADI_Knowledge_MCQs.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            st.download_button("⬇️ Download TXT",
                               data=export_txt_from_state(st.session_state.mcqs, include_key),
                               file_name="ADI_Knowledge_MCQs.txt",
                               mime="text/plain")

    with tabs[1]:
        left, right = st.columns([2,2])
        with left:
            act_choices = [("1 per lesson",1),("2 per lesson",2),("3 per lesson",3)]
            act_label = st.selectbox("How many activities?", [l for l,_ in act_choices], index=0, key="n_act")
            n_act = dict(act_choices)[act_label]
        with right:
            minute_values = list(range(5,61,5))
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
            verbs = (med or []) + (low or []) + (high or [])
            if not verbs: verbs = MED
            acts = [f"{i+1}. {random.choice(verbs).capitalize()} a {mins}-minute activity for groups of {group_size} focusing on **{w}**."
                    for i,w in enumerate(terms)]
            st.session_state["gen_acts"] = acts; st.success("Activities generated. See below.")
        if st.session_state.get("gen_acts"):
            for a in st.session_state["gen_acts"]: st.markdown(f"- {a}")
            from docx import Document
            def export_docx_list(lines, title):
                doc=Document(); doc.add_heading(title, level=1)
                for ln in lines: doc.add_paragraph(ln)
                bio=io.BytesIO(); doc.save(bio); return bio.getvalue()
            def export_txt_list(lines): return ("\n".join(lines)).encode("utf-8")
            st.download_button("⬇️ Download DOCX (Activities)",
                               data=export_docx_list(st.session_state["gen_acts"], "Skills Activities"),
                               file_name="ADI_Skills_Activities.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.download_button("⬇️ Download TXT (Activities)",
                               data=export_txt_list(st.session_state["gen_acts"]),
                               file_name="ADI_Skills_Activities.txt",
                               mime="text/plain")

    with tabs[2]:
        n_rev = st.selectbox("How many revision prompts?", [3,5,8,10], index=0, key="n_rev")
        if st.button("Generate Revision"):
            LOW  = ["define","identify","list","recall","describe","label"]
            revs = [f"{i+1}. {random.choice(low or LOW).capitalize()} key points on **{w}** in a 5-bullet summary."
                    for i,w in enumerate(pick_terms(text, max(10,n_rev*2))[:n_rev])]
            st.session_state["gen_rev"] = revs; st.success("Revision prompts generated.")
        if st.session_state.get("gen_rev"):
            for r in st.session_state["gen_rev"]: st.markdown(f"- {r}")
            from docx import Document
            def export_docx_list(lines, title):
                doc=Document(); doc.add_heading(title, level=1)
                for ln in lines: doc.add_paragraph(ln)
                bio=io.BytesIO(); doc.save(bio); return bio.getvalue()
            def export_txt_list(lines): return ("\n".join(lines)).encode("utf-8")
            st.download_button("⬇️ Download DOCX (Revision)",
                               data=export_docx_list(st.session_state["gen_rev"], "Revision Prompts"),
                               file_name="ADI_Revision_Prompts.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.download_button("⬇️ Download TXT (Revision)",
                               data=export_txt_list(st.session_state["gen_rev"]),
                               file_name="ADI_Revision_Prompts.txt",
                               mime="text/plain")

    with tabs[3]:
        st.subheader("Print Summary")
        st.markdown(f"**Course:** {course or '—'}  \n**Cohort:** {cohort or '—'}  \n**Instructor:** {instructor or '—'}  \n**Date:** {the_date}  \n**Lesson:** {lesson}  \n**Week:** {week}")
        st.divider()
        if st.session_state.mcqs:
            st.markdown("### Knowledge MCQs")
            for i,item in enumerate(st.session_state.mcqs, start=1):
                st.markdown(f"**{i}. {item['stem']}**")
                for j,opt in enumerate(item["options"], start=1): st.markdown(f"{chr(64+j)}. {opt}")
                st.write("")
        if st.session_state.get("gen_acts"):
            st.markdown("### Skills Activities"); [st.markdown(f"- {a}") for a in st.session_state["gen_acts"]]
        if st.session_state.get("gen_rev"):
            st.markdown("### Revision"); [st.markdown(f"- {r}") for r in st.session_state["gen_rev"]]

if __name__ == "__main__":
    main()
