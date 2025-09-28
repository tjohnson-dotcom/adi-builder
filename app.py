
# app.py — ADI Builder (single-file Streamlit app) — FIXED
from __future__ import annotations
import io, re, textwrap
from typing import List
import streamlit as st

# ---------- Config ----------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ---------- Styles ----------
CSS = """
:root {
  --adi-green: #245a34;
  --adi-gold: #C8A85A;
  --stone-100: #f5f5f4;
  --stone-200: #e7e5e4;
  --stone-300: #d6d3d1;
  --text-900: #111827;
}
[data-testid="stAppViewContainer"] > .main {
  background: linear-gradient(180deg, var(--stone-100), #fff);
}
.block-container { padding-top: 1.2rem; padding-bottom: 2.2rem; max-width: 1200px; }
.stepbar { display:flex; gap:.5rem; flex-wrap:wrap; padding:.4rem .6rem; border:1px dashed var(--stone-300); border-radius:14px; background:#fff; }
.stepbar .step { display:flex; align-items:center; gap:.5rem; font-weight:700; padding:.45rem .75rem; border-radius:999px; background:var(--stone-200); border:1px solid var(--stone-300); }
.stepbar .step .num { display:inline-flex; width:24px; height:24px; align-items:center; justify-content:center; font-weight:800; border-radius:999px; background:var(--adi-green); color:#fff; }
.pills { display:flex; flex-wrap:wrap; gap:.5rem; }
.pill { background:#fff; border:2px solid rgba(0,0,0,.08); border-radius:999px; padding:.45rem .85rem; font-weight:700; }
.pill.current { border-color: var(--adi-gold); box-shadow: inset 0 0 0 3px var(--adi-gold); }
.pill.match { background:#e8f5ee; border-color:#1f7a4c; }
.pill.mismatch { background:#fff7ed; border-color:#fed7aa; }
.badge-ok, .badge-warn { display:inline-flex; align-items:center; font-weight:700; margin-top:.35rem; border-radius:10px; padding:.35rem .6rem; border:1px solid transparent; }
.badge-ok { background:#e8f5ee; color:#14532d; border-color:#86efac; }
.badge-warn { background:#fff7ed; color:#7c2d12; border-color:#fdba74; }
hr.soft { border:none; border-top:1px solid var(--stone-300); margin: .75rem 0 1rem; }
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ---------- Constants ----------
BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
BLOOM_TIER = {"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}
BLOOM_VERBS = {
    "Remember":["define","list","recall","identify","label","name","state","match","recognize","outline","select","repeat"],
    "Understand":["explain","summarize","classify","describe","discuss","interpret","paraphrase","compare","illustrate","infer"],
    "Apply":["apply","demonstrate","execute","implement","solve","use","calculate","perform","simulate","carry out"],
    "Analyze":["analyze","differentiate","organize","attribute","deconstruct","compare/contrast","examine","test","investigate"],
    "Evaluate":["evaluate","argue","assess","defend","judge","justify","critique","recommend","prioritize","appraise"],
    "Create":["create","design","compose","construct","develop","plan","produce","propose","assemble","formulate"],
}
POLICY_HELP = "ADI policy: Weeks 1–4 = Low, 5–9 = Medium, 10–14 = High"

def policy_tier(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# ---------- Session defaults ----------
defaults = {
    "source_text":"",
    "topics":[],
    "char_count":0,
    "lesson":1,
    "week":1,
    "level":"Remember",
    "verbs": BLOOM_VERBS["Remember"][:5],
    "questions":[],
    "activities":[]
}
for k,v in defaults.items():
    st.session_state.setdefault(k,v)

# ---------- Optional imports (safe) ----------
def _mods():
    m={}
    try:
        import fitz; m["fitz"]=fitz
    except Exception: m["fitz"]=None
    try:
        from pptx import Presentation; m["Presentation"]=Presentation
    except Exception: m["Presentation"]=None
    try:
        import docx; m["docx"]=docx
    except Exception: m["docx"]=None
    return m
MODS=_mods()

# ---------- Parsers ----------
def extract_pdf(file)->str:
    if MODS["fitz"] is None: st.warning("Install PyMuPDF to parse PDFs: pip install pymupdf"); return ""
    try:
        with MODS["fitz"].open(stream=file.read(), filetype="pdf") as doc:
            return "\n".join(p.get_text("text") for p in doc)
    except Exception as e:
        st.error(f"PDF parse error: {e}"); return ""

def extract_pptx(file)->str:
    if MODS["Presentation"] is None: st.warning("Install python-pptx to parse PPTX: pip install python-pptx"); return ""
    try:
        prs = MODS["Presentation"](file)
        out=[]
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape,"text"): out.append(shape.text)
        return "\n".join(out)
    except Exception as e:
        st.error(f"PPTX parse error: {e}"); return ""

def extract_docx(file)->str:
    if MODS["docx"] is None: st.warning("Install python-docx to parse DOCX: pip install python-docx"); return ""
    try:
        doc = MODS["docx"].Document(file)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        st.error(f"DOCX parse error: {e}"); return ""

def simple_topics(txt:str, max_topics:int=25)->List[str]:
    topics=[]; seen=set()
    for raw in txt.splitlines():
        line=raw.strip()
        if not line or len(line)<6 or len(line)>90: continue
        if (line.istitle() or line.isupper() or re.match(r"^\d+[\).\s-]", line)) and not line.endswith(":"):
            key=line.lower()
            if key not in seen:
                topics.append(line); seen.add(key)
        if len(topics)>=max_topics: break
    if not topics and txt:
        import re as _re
        para = _re.split(r"\n\s*\n", txt, maxsplit=1)[0]
        topics = [t.strip() for t in _re.split(r"[.·••]\s+", para) if 6<=len(t.strip())<=80][:8]
    return topics

def make_policy_pills(required:str, selected:str)->str:
    pill={"Low":"pill","Medium":"pill","High":"pill"}
    pill[required]+=" current"
    if selected==required:
        pill[selected]+=" match"
        badge='<div class="badge-ok">✓ ADI policy matched</div>'
    else:
        pill[selected]+=" mismatch"
        badge=f'<div class="badge-warn">Week requires {required}. Selected tier is {selected}.</div>'
    return f"""
    <div class="pills">
      <span class="{pill['Low']}">Low</span>
      <span class="{pill['Medium']}">Medium</span>
      <span class="{pill['High']}">High</span>
    </div>
    {badge}
    """

def build_mcqs(topics:List[str], verbs:List[str], level:str, n:int=5)->List[str]:
    if not verbs: verbs=["identify"]
    if not topics: topics=[f"topic {i+1}" for i in range(n)]
    vcycle=(verbs*((n//max(1,len(verbs)))+1))[:n]
    tcycle=(topics*((n//max(1,len(topics)))+1))[:n]
    qs=[]
    for i in range(n):
        v=vcycle[i].capitalize(); t=tcycle[i]
        stem=f"{v} the MOST appropriate statement about: {t}."
        opts=[
            f"A) A correct point about {t}.",
            f"B) An incorrect detail about {t}.",
            f"C) Another incorrect detail about {t}.",
            f"D) A distractor unrelated to {t}.",
        ]
        qs.append(stem+"\n"+"\n".join(opts)+"\nAnswer: A")
    return qs

def build_activities(topics:List[str], verbs:List[str], level:str, n:int=3)->List[str]:
    if not verbs: verbs=["discuss"]
    if not topics: topics=[f"topic {i+1}" for i in range(n)]
    vcycle=(verbs*((n//max(1,len(verbs)))+1))[:n]
    tcycle=(topics*((n//max(1,len(topics)))+1))[:n]
    acts=[]
    for i in range(n):
        v=vcycle[i].capitalize(); t=tcycle[i]
        if level in ("Evaluate","Create"):
            prompt=f"{v} and present a structured solution/prototype for: {t}."
        elif level in ("Apply","Analyze"):
            prompt=f"{v} and demonstrate/apportion key components of: {t}."
        else:
            prompt=f"{v} and summarize the core idea of: {t}."
        acts.append(f"Activity {i+1}: {prompt}")
    return acts

def as_gift(mcqs:List[str])->str:
    blocks=[]
    for i,q in enumerate(mcqs,1):
        lines=q.splitlines(); stem=lines[0]
        choices=[ln for ln in lines[1:] if re.match(r"^[A-D]\)", ln)]
        gift=f"::Q{i}:: {stem} {{\n"
        for ch in choices:
            letter=ch.split(")")[0]; text=ch.split(") ",1)[1] if ") " in ch else ch
            gift += ("  = "+text+"\n") if letter=="A" else ("  ~ "+text+"\n")
        gift+="}\n"; blocks.append(gift)
    return "\n".join(blocks)

# ---------- Header ----------
col1, col2 = st.columns([1, 5])
with col1:
    # Removed deprecated use_column_width param
    st.image("https://dummyimage.com/80x80/245a34/ffffff.png&text=ADI", caption="ADI")
with col2:
    st.markdown("""
    <div class="stepbar">
      <div class="step"><span class="num">1</span> Upload</div>
      <div class="step"><span class="num">2</span> Setup</div>
      <div class="step"><span class="num">3</span> Generate</div>
      <div class="step"><span class="num">4</span> Export</div>
    </div>
    """, unsafe_allow_html=True)

reset = st.button("↺ Reset app", type="secondary")
if reset:
    for k in list(st.session_state.keys()):
        if k in ("source_text","topics","char_count","lesson","week","level","verbs","questions","activities"):
            st.session_state[k]=defaults[k]
    st.experimental_rerun()

tabs = st.tabs(["① Upload", "② Setup", "③ Generate", "④ Export (Step 4)"])

# ---------- Tab 1: Upload ----------
with tabs[0]:
    st.subheader("Upload source")
    st.caption("Clean, polished ADI look · Strict colors · Logo required")
    file = st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)", type=["pdf","pptx","docx"], accept_multiple_files=False)
    pasted = st.text_area("Or paste source text manually", height=140, placeholder="Paste any relevant lesson/topic text here…", key="pastebox")
    if st.button("Process"):
        text=""
        if pasted and pasted.strip():
            text=pasted.strip()
        elif file is not None:
            suffix=file.name.lower().split(".")[-1]
            if suffix=="pdf": text=extract_pdf(file)
            elif suffix=="pptx": text=extract_pptx(file)
            elif suffix=="docx": text=extract_docx(file)
        if not text:
            st.info("No text extracted. You can still proceed using manual topics.")
        st.session_state.source_text=text
        st.session_state.char_count=len(text)
        st.session_state.topics=simple_topics(text) if text else []
        st.success(f"✓ Processed: {len(text):,} chars")
    if st.session_state.char_count:
        with st.expander("Detected topics"):
            if st.session_state.topics:
                for t in st.session_state.topics: st.write("• "+t)
            else:
                st.caption("No headings found — generation will still work.")
    st.markdown('<hr class="soft" />', unsafe_allow_html=True)
    st.caption("Security: never accept API keys via UI; keep them in env/.streamlit/secrets if added later.")

# ---------- Tab 2: Setup ----------
with tabs[1]:
    st.subheader("Setup")
    lcol, rcol = st.columns([2,3])
    with lcol:
        st.session_state.lesson = st.radio("Lesson", [1,2,3,4,5], index=st.session_state.lesson-1, horizontal=True, key="lesson_radio")
        st.session_state.week = st.radio("Week", list(range(1,15)), index=st.session_state.week-1, horizontal=True, help=POLICY_HELP, key="week_radio")
        st.session_state.level = st.radio("Bloom’s Level", BLOOM_LEVELS, index=BLOOM_LEVELS.index(st.session_state.level), horizontal=True, key="level_radio")
        required = policy_tier(int(st.session_state.week))
        selected_tier = BLOOM_TIER[st.session_state.level]
        st.caption("Policy vs Selected:")
        st.markdown(make_policy_pills(required, selected_tier), unsafe_allow_html=True)
    with rcol:
        verbs_all = BLOOM_VERBS.get(st.session_state.level, [])
        default_take = 5 if len(verbs_all)>=5 else len(verbs_all)
        st.session_state.verbs = st.multiselect("Choose 5–10 verbs", options=verbs_all, default=st.session_state.get("verbs", verbs_all[:default_take]), key="verbs_select")
        if not (5 <= len(st.session_state.verbs) <= 10):
            st.warning(f"Select between 5 and 10 verbs. Currently: {len(st.session_state.verbs)}")
        else:
            st.success("Verb count looks good ✅")

# ---------- Tab 3: Generate ----------
with tabs[2]:
    st.subheader("Generate")
    n_mcq = st.slider("How many MCQs?", 3, 20, 5, 1, key="n_mcq")
    n_act = st.slider("How many activities?", 1, 10, 3, 1, key="n_act")
    if st.button("⚡ Generate"):
        topics = st.session_state.topics or ["Core Concepts","Key Terms","Use Cases","Risks","Summary"]
        try:
            st.session_state.questions = build_mcqs(topics, st.session_state.verbs, st.session_state.level, n_mcq)
            st.session_state.activities = build_activities(topics, st.session_state.verbs, st.session_state.level, n_act)
            st.success("Content generated. Check previews and proceed to Export.")
        except Exception as e:
            st.exception(e)
    if st.session_state.questions:
        st.markdown("#### MCQ Preview")
        for i,q in enumerate(st.session_state.questions,1):
            with st.expander(f"MCQ {i}"):
                st.text(q)
    if st.session_state.activities:
        st.markdown("#### Activities")
        for a in st.session_state.activities: st.write("• "+a)

# ---------- Tab 4: Export ----------
with tabs[3]:
    st.subheader("Export (Step 4)")
    if not st.session_state.questions:
        st.info("Generate content first in Step 3.")
    else:
        txt_payload = "\n\n".join(st.session_state.questions + [""] + st.session_state.activities)
        st.download_button("⬇️ Download .txt", data=txt_payload.encode("utf-8"), file_name="adi_builder_export.txt", mime="text/plain")
        gift_payload = as_gift(st.session_state.questions)
        st.download_button("⬇️ Download Moodle GIFT", data=gift_payload.encode("utf-8"), file_name="adi_mcqs.gift", mime="text/plain")
        # DOCX export (optional install)
        if MODS["docx"] is None:
            st.caption("Install python-docx to enable .docx export: pip install python-docx")
        else:
            import docx, io
            doc = docx.Document()
            doc.add_heading("ADI Builder Export", level=1)
            doc.add_paragraph(POLICY_HELP)
            doc.add_heading("MCQs", level=2)
            for q in st.session_state.questions: doc.add_paragraph(q)
            doc.add_heading("Activities", level=2)
            for a in st.session_state.activities: doc.add_paragraph(a)
            bio = io.BytesIO(); doc.save(bio)
            st.download_button("⬇️ Download .docx", data=bio.getvalue(), file_name="adi_builder_export.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
