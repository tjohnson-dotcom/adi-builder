# Learning Tracker Question Generator — ADI
# Streamlit app that matches the “modal card” style you like.
# Tabs: Upload • Setup • Generate • Edit • Export
# Features: Upload PDF/DOCX/PPTX → Bloom-aware MCQs & Activities → Edit → Export (Word/CSV)

import io, re, random, base64
from typing import Any, List, Tuple

import pandas as pd
import streamlit as st

# ---------- Optional parsers ----------
try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None
try:
    from pptx import Presentation
except Exception:
    Presentation = None

# ---------- Word export ----------
from io import BytesIO
try:
    from docx import Document
    from docx.shared import Pt, Inches
except Exception:
    Document = None
    Pt = None
    Inches = None

# ---------- Page & CSS (replicates the modal look) ----------
st.set_page_config(page_title="Learning Tracker Question Generator — ADI", page_icon="🧭", layout="centered")

CSS = """
<style>
:root{
  --card:#ffffff; --ink:#141414; --muted:#6b7280; --border:#e7e7ea; --bg:#f6f7fb;
  --accent:#3865ff; --accent-600:#2a4ed6; --chip:#eef2ff; --adi:#245a34;
}
html, body { background: var(--bg); }
main .block-container { padding-top: 1.2rem; max-width: 860px; }
.modal {
  background: var(--card); border-radius: 22px; border: 1px solid var(--border);
  box-shadow: 0 24px 60px rgba(0,0,0,.1); padding: 24px 26px; position: relative;
}
.logo-row { display:flex; align-items:center; gap:16px; justify-content:center; margin-bottom:10px; }
.logo-img { height:64px; width:auto; border-radius:10px; }
.brand-title { text-align:center; font-size:28px; font-weight:800; letter-spacing:.0em; margin:2px 0 0 0;}
.brand-sub { text-align:center; color:var(--muted); margin-top:2px; }
.big-cta { display:block; width:100%; background:var(--accent); color:#fff; border:none; padding:14px 16px;
  border-radius:12px; font-weight:700; font-size:16px; box-shadow:0 8px 20px rgba(56,101,255,.25); }
.big-cta:hover { background: var(--accent-600); }
.tabs-row { display:flex; gap:26px; margin:18px 0 8px 0; padding-bottom:8px; border-bottom:1px solid var(--border); }
.tab { font-weight:700; color:var(--muted); }
.help-box { border:1px dashed var(--border); background:#fafbff; padding:16px; border-radius:16px; }
.pill { display:inline-flex; align-items:center; gap:8px; border-radius:12px; padding:8px 12px; border:1px solid var(--border); background:#fff; }
.small { font-size:12px; color:var(--muted); }
.row { display:flex; gap:12px; }
.col { flex:1; }
.chips { display:flex; gap:8px; flex-wrap:wrap; margin-top:6px; }
.chip { border:1px solid var(--border); padding:4px 10px; border-radius:999px; font-size:12px; background:#fff; }
.chip.low { background:#eaf5ec; }
.chip.med { background:#fbf6ec; }
.chip.high{ background:#f3f1ee; }
.row-head { display:flex; justify-content:space-between; align-items:center; margin-top:12px; }
.row-cap { font-size:11px; color:var(--muted); }
.row.active .chip { border-color: var(--adi); box-shadow:0 4px 10px rgba(36,90,52,.12); }
.section-title { font-weight:800; font-size:16px; margin-top:16px; }
.download-row { display:flex; gap:10px; flex-wrap:wrap; }
hr.soft { height:1px; background:var(--border); border:0; margin:18px 0; }
.badge { background:#eef1f7; color:#475569; border:1px solid var(--border); font-size:12px; border-radius:999px; padding:2px 8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Bloom policy ----------
LOW_VERBS  = ["define","identify","list","describe","recall","label"]
MED_VERBS  = ["apply","demonstrate","solve","illustrate","analyze","interpret","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","formulate","critique"]
ADI_VERBS  = {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}

def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# ---------- Upload parsing ----------
def _clean_lines(text: str) -> str:
    lines = [ln.strip() for ln in (text or "").replace("\r","\n").split("\n") if ln.strip()]
    lines = [ln for ln in lines if not re.fullmatch(r"(page\s*\d+|\d+)", ln, flags=re.I)]
    seen, out = set(), []
    for ln in lines:
        k = ln[:80].lower()
        if k in seen: continue
        seen.add(k); out.append(ln)
    return "\n".join(out)[:6000]

def extract_text_from_upload(file)->str:
    if file is None: return ""
    name = (getattr(file, "name", "") or "").lower()
    try:
        if name.endswith(".pdf"):
            buf = file.read() if hasattr(file,"read") else file.getvalue()
            if pdfplumber:
                pages=[]
                with pdfplumber.open(io.BytesIO(buf)) as pdf:
                    for p in pdf.pages[:30]:
                        pages.append(p.extract_text() or "")
                return _clean_lines("\n".join(pages))
            elif PdfReader:
                reader = PdfReader(io.BytesIO(buf))
                text=""
                for pg in reader.pages[:30]:
                    text += (pg.extract_text() or "") + "\n"
                return _clean_lines(text)
            else:
                return "[Could not parse PDF: add pdfplumber or PyPDF2]"
        if name.endswith(".docx") and DocxDocument:
            doc = DocxDocument(file)
            return _clean_lines("\n".join((p.text or "") for p in doc.paragraphs[:250]))
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(file)
            parts=[]
            for s in prs.slides[:40]:
                for shp in s.shapes:
                    if hasattr(shp,"text") and shp.text:
                        parts.append(shp.text)
                if getattr(s,"has_notes_slide",False) and getattr(s.notes_slide,"notes_text_frame",None):
                    parts.append(s.notes_slide.notes_text_frame.text or "")
            return _clean_lines("\n".join(parts))
        return "[Unsupported file type or missing parser]"
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ---------- Tiny NLP helpers ----------
_STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","as","is","are","be","was","were","this","that","these","those",
    "it","its","at","from","into","over","under","about","between","within","use","used","using","also","than","which","such","may",
    "can","could","should","would","will","not","if","when","while","after","before","each","per","via","more","most","less","least",
    "other","another","see","example","examples","appendix","figure","table","chapter","section","page","pages","ref","ibid",
    "module","lesson","week","activity","activities","objective","objectives","outcome","outcomes","question","questions","topic","topics",
    "student","students","teacher","instructor","course","unit","learning","overview","summary","introduction","conclusion","content","contents"
}

def _sentences(text: str) -> List[str]:
    chunks = re.split(r"[.\u2022\u2023\u25CF•]|(?:\n\s*\-\s*)|(?:\n\s*\*\s*)", text or "")
    rough = [re.sub(r"\s+", " ", c).strip() for c in chunks if c and c.strip()]
    out, seen = [], set()
    for s in rough:
        if 30 <= len(s) <= 180:
            k = s.lower()
            if k not in seen:
                out.append(s); seen.add(k)
    return out[:200]

def _keywords(text: str, top_n:int=24) -> List[str]:
    from collections import Counter
    toks=[]
    for w in re.split(r"[^A-Za-z0-9]+", text or ""):
        w=w.lower()
        if len(w)>=4 and w not in _STOP: toks.append(w)
    common = Counter(toks).most_common(top_n*2)
    roots=[]
    for w,_ in common:
        if all(not w.startswith(r[:5]) and not r.startswith(w[:5]) for r in roots):
            roots.append(w)
        if len(roots)>=top_n: break
    return roots

def _find_sentence_with(term: str, sentences: List[str]) -> str | None:
    t=term.lower()
    for s in sentences:
        if t in s.lower(): return s
    return None

# ---------- MCQs ----------
def _distractors(correct:str, pool:List[str], n:int)->List[str]:
    rand = random.Random(42)
    base = (correct or "").strip()
    outs=[]
    def tweak(s:str)->str:
        s2 = re.sub(r"\b(increase[s]?|higher|more)\b","decrease",s,flags=re.I)
        s2 = re.sub(r"\b(decrease[s]?|lower|less)\b","increase",s2,flags=re.I)
        s2 = re.sub(r"(\d{1,3})(\s?(?:km/h|mph|%|units?))",lambda m:str(max(1,int(m.group(1))+10))+(m.group(2) or ""), s2)
        s2 = re.sub(r"\balways\b","sometimes",s2,flags=re.I)
        s2 = re.sub(r"\bmust\b","may",s2,flags=re.I)
        return s2 if s2.lower()!=s.lower() else s + " (in the wrong context)"
    if base:
        outs.append(tweak(base))
        outs.append(tweak(base[::-1])[::-1])
    ckey = base.lower()[:60]
    cands=[p for p in pool if p and 20<=len(p)<=160 and p.lower()[:60]!=ckey]
    rand.shuffle(cands)
    for s in cands:
        if len(outs)==n: break
        if s not in outs: outs.append(s)
    while len(outs)<n: outs.append("This statement misinterprets a key constraint.")
    return outs[:n]

def generate_mcq_blocks(topic:str, source:str, num_blocks:int, week:int, lesson:int=1)->pd.DataFrame:
    ctx = topic.strip() or f"Lesson {lesson} • Week {week}"
    sents=_sentences(source or "")
    keys=_keywords(source or topic or "", top_n=max(24,num_blocks*6))
    if not sents:
        sents=[f"{ctx}: core concepts, steps, constraints, and safety considerations."]
        for k in keys[:5]: sents.append(f"{k.capitalize()} relates to practical application and pitfalls.")
    low_templates=[
        lambda t,c: f"Which statement correctly defines **{t}** in *{c}*?",
        lambda t,c: f"Identify the accurate description of **{t}** for *{c}*.",
        lambda t,c: f"Recall: what does **{t}** mean in *{c}*?",
    ]
    med_templates=[
        lambda t,c: f"When applying **{t}** in *{c}*, which action is most appropriate?",
        lambda t,c: f"Which option best interprets how to use **{t}** in *{c}*?",
        lambda t,c: f"Compare the options — which best operationalises **{t}** for *{c}*?",
    ]
    high_templates=[
        lambda t,c: f"Which option provides the strongest justification involving **{t}** for *{c}*?",
        lambda t,c: f"Analyze: which reasoning about **{t}** is most valid in *{c}*?",
        lambda t,c: f"Which design choice best satisfies constraints related to **{t}** within *{c}*?",
    ]
    rows=[]; rnd=random.Random(2025)
    def add_row(b:int, tier:str, stem:str, correct:str, wrongs:List[str]):
        opts=[correct]+wrongs[:3]; rnd.shuffle(opts)
        ans=["A","B","C","D"][opts.index(correct)]
        rows.append({
            "Block":b,"Tier":tier,"Q#":{"Low":1,"Medium":2,"High":3}[tier],
            "Question":stem.strip(),
            "Option A":opts[0],"Option B":opts[1],"Option C":opts[2],"Option D":opts[3],
            "Answer":ans,"Explanation":"Chosen option aligns with the source context.",
            "Order":{"Low":1,"Medium":2,"High":3}[tier],
        })
    for b in range(1,num_blocks+1):
        tL=keys[(b*3-3)%len(keys)] if keys else "principles"
        tM=keys[(b*3-2)%len(keys)] if keys else "process"
        tH=keys[(b*3-1)%len(keys)] if keys else "criteria"
        c1=_find_sentence_with(tL,sents) or f"{tL.capitalize()} is a foundational element in this context."
        c2=_find_sentence_with(tM,sents) or f"When applying {tM}, follow steps that respect constraints and safety."
        c3=_find_sentence_with(tH,sents) or f"An effective approach to {tH} prioritizes evidence and feasibility."
        add_row(b,"Low",   low_templates[(b-1)%len(low_templates)](tL,ctx), c1, _distractors(c1,sents,3))
        add_row(b,"Medium",med_templates[(b-1)%len(med_templates)](tM,ctx), c2, _distractors(c2,sents,3))
        add_row(b,"High",  high_templates[(b-1)%len(high_templates)](tH,ctx), c3, _distractors(c3,sents,3))
    return pd.DataFrame(rows).sort_values(["Block","Order"], kind="stable").reset_index(drop=True)

# ---------- Activities ----------
def generate_activities(count:int, duration:int, tier:str, topic:str, lesson:int, week:int, source:str="")->pd.DataFrame:
    topic=(topic or "").strip()
    ctx=f"Lesson {lesson} • Week {week}" + (f" — {topic}" if topic else "")
    verbs=ADI_VERBS.get(tier, MED_VERBS)[:6]
    steps_hints=[]
    if source:
        sents=_sentences(source)
        for s in sents:
            if re.search(r"\b(first|then|next|after|before|ensure|use|apply|select|measure|calculate|record|verify|inspect|document|compare|interpret|justify|design)\b", s, re.I):
                steps_hints.append(s.strip())
        steps_hints=steps_hints[:24]
    rows=[]
    for i in range(1,count+1):
        v=verbs[(i-1)%len(verbs)]
        t1=max(5,int(duration*0.2)); t2=max(10,int(duration*0.5)); t3=max(5,duration-(t1+t2))
        main=(steps_hints[(i-1)%len(steps_hints)] if steps_hints else
              f"In small groups, {v} a case/task related to the content; capture outcomes on a mini-whiteboard.")
        assess={"Low":"5-item exit ticket (recall/identify).",
                "Medium":"Performance check using worked-example rubric.",
                "High":"Criteria-based critique/design justification; short reflection."}[tier]
        rows.append({
            "Lesson":lesson,"Week":week,"Policy focus":tier,
            "Title":f"{ctx} — {tier} Activity {i}","Tier":tier,
            "Objective":f"Students will {v} key ideas from the uploaded content{(' on ' + topic) if topic else ''}.",
            "Steps":" ".join([
                f"Starter ({t1}m): {v.capitalize()} prior knowledge via think–pair–share.",
                f"Main ({t2}m): {main}",
                f"Plenary ({t3}m): Share, compare and refine answers; agree success criteria."
            ]),
            "Materials":"Slides/board, markers, timer; optional handout",
            "Assessment":assess + " Collect: Team submits artefact photo + 3-sentence rationale.",
            "Duration (mins)":duration,
        })
    return pd.DataFrame(rows)

# ---------- Word exports ----------
def _docx_heading(doc, text, level=0):
    p=doc.add_paragraph(); r=p.add_run(text)
    if level==0: r.bold=True; r.font.size=Pt(16)
    elif level==1: r.bold=True; r.font.size=Pt(13)
    else: r.font.size=Pt(11)

def export_mcqs_docx(df, lesson:int, week:int, topic:str="")->bytes:
    if Document is None: return b""
    doc=Document(); sec=doc.sections[0]
    if Inches: sec.left_margin=Inches(0.8); sec.right_margin=Inches(0.8)
    _docx_heading(doc, f"Knowledge MCQs — Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else ""), 0)
    doc.add_paragraph()
    for b in sorted(df["Block"].unique()):
        _docx_heading(doc, f"Block {b}", 1)
        sub=df[df["Block"]==b].sort_values("Q#")
        for _,r in sub.iterrows():
            doc.add_paragraph(f"{r['Q#']}. ({r['Tier']}) {r['Question']}")
            doc.add_paragraph(f"A. {r['Option A']}"); doc.add_paragraph(f"B. {r['Option B']}")
            doc.add_paragraph(f"C. {r['Option C']}"); doc.add_paragraph(f"D. {r['Option D']}")
            doc.add_paragraph()
        doc.add_paragraph()
    _docx_heading(doc, "Answer Key", 1)
    for b in sorted(df["Block"].unique()):
        sub=df[df["Block"]==b].sort_values("Q#")
        for _,r in sub.iterrows():
            doc.add_paragraph(f"Block {int(b)} Q{int(r['Q#'])}: {r['Answer']}")
    bio=BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

def export_acts_docx(df, lesson:int, week:int, topic:str="")->bytes:
    if Document is None: return b""
    doc=Document(); sec=doc.sections[0]
    if Inches: sec.left_margin=Inches(0.8); sec.right_margin=Inches(0.8)
    _docx_heading(doc, f"Skills Activities — Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else ""), 0)
    doc.add_paragraph()
    for i,r in df.iterrows():
        _docx_heading(doc, r.get("Title", f"Activity {i+1}"), 1)
        doc.add_paragraph(f"Policy focus: {r['Policy focus']}"); doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph(f"Steps: {r['Steps']}"); doc.add_paragraph(f"Materials: {r['Materials']}")
        doc.add_paragraph(f"Assessment: {r['Assessment']}"); doc.add_paragraph(f"Duration: {r['Duration (mins)']} mins")
        doc.add_paragraph()
    bio=BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

# ---------- State defaults ----------
st.session_state.setdefault("lesson", 1)
st.session_state.setdefault("week", 1)
st.session_state.setdefault("topic", "")
st.session_state.setdefault("mcq_blocks", 5)
st.session_state.setdefault("act_n", 3)
st.session_state.setdefault("act_dur", 45)
st.session_state.setdefault("logo_bytes", b"")
st.session_state.setdefault("src_text", "")

# ---------- Modal card ----------
with st.container():
    st.markdown("<div class='modal'>", unsafe_allow_html=True)

    # Header row (logo + title)
    col_logo, = st.columns(1)
    with col_logo:
        st.markdown("<div class='logo-row'>", unsafe_allow_html=True)
        if st.session_state.logo_bytes:
            b64 = base64.b64encode(st.session_state.logo_bytes).decode()
            st.markdown(f"<img class='logo-img' src='data:image/png;base64,{b64}' />", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='brand-title'>Learning Tracker Question Generator</div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-sub'>Transforming Lessons into Measurable Learning</div>", unsafe_allow_html=True)
        st.write("")

    st.markdown("<button class='big-cta'>Begin Tracking Learning</button>", unsafe_allow_html=True)
    st.write("")

    # Tabs (Streamlit)
    t1, t2, t3, t4, t5 = st.tabs(["Upload", "Setup", "Generate", "Edit", "Export"])

    # --- Upload tab ---
    with t1:
        st.write("#### Drag and drop a **PowerPoint** or **e-book** file here, or click to browse")
        logo = st.file_uploader("Optional: upload ADI/School logo (PNG/JPG)", type=["png","jpg","jpeg"], accept_multiple_files=False, key="logo_up")
        if logo is not None:
            st.session_state.logo_bytes = logo.read()
            st.success("Logo added.")
        up = st.file_uploader("Upload PPTX/PDF/DOCX", type=["pptx","pdf","docx"], accept_multiple_files=False, key="source_up")
        if up:
            st.session_state.src_text = extract_text_from_upload(up)
            st.info("Source parsed. Switch to **Setup** or **Generate** when ready.")
        st.markdown("<div class='help-box small'>Supported: <b>pptx, pdf, docx</b>. If a PDF fails to parse, add <code>pdfplumber</code> in requirements.</div>", unsafe_allow_html=True)

    # --- Setup tab ---
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.lesson = st.selectbox("Lesson", [f"Lesson {i}" for i in range(1,21)], index=st.session_state.lesson-1)
            st.session_state.lesson = int(st.session_state.lesson.split()[-1])
        with c2:
            st.session_state.week = st.selectbox("Week", [f"Week {i}" for i in range(1,15)], index=st.session_state.week-1)
            st.session_state.week = int(st.session_state.week.split()[-1])

        bloom = bloom_focus_for_week(st.session_state.week)
        c3, c4 = st.columns([3,1])
        st.session_state.topic = c3.text_input("Learning Objective / Topic", st.session_state.topic, placeholder="Identify key-themes and arguments in the text")
        c4.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom}", disabled=True)

        # Source preview/edit
        st.text_area("Source (editable)", value=st.session_state.src_text, height=160, key="src_edit")

        # Bloom verbs (highlight active tier)
        st.write("#### Bloom’s verbs (ADI Policy)")
        st.caption("Grouped by policy tiers and week ranges")

        def _row(title:str, verbs:List[str], right:str, active:bool=False):
            row_cls = "row active" if active else "row"
            st.markdown(f"<div class='{row_cls}'>", unsafe_allow_html=True)
            st.markdown(f"<div class='row-head'><div><strong>{title}</strong></div><div class='row-cap'>{right}</div></div>", unsafe_allow_html=True)
            cls = 'low' if title.startswith('Low') else 'med' if title.startswith('Medium') else 'high'
            chips = " ".join([f\"<span class='chip {cls}'>{v}</span>\" for v in verbs])
            st.markdown(f\"<div class='chips'>{chips}</div>\", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        _row("Low (Weeks 1–4)", LOW_VERBS, "Remember / Understand", active=(bloom=="Low"))
        _row("Medium (Weeks 5–9)", MED_VERBS, "Apply / Analyze", active=(bloom=="Medium"))
        _row("High (Weeks 10–14)", HIGH_VERBS, "Evaluate / Create", active=(bloom=="High"))

    # --- Generate tab ---
    with t3:
        st.write("#### Create Questions & Activities")
        g1, g2, g3 = st.columns([1,1,2])
        with g1:
            blocks = st.number_input("MCQ Blocks (3 Qs per block)", min_value=1, value=5, step=1)
        with g2:
            act_n = st.number_input("Activities (count)", min_value=1, value=st.session_state.act_n, step=1)
        with g3:
            act_d = st.number_input("Activity duration (mins)", min_value=5, value=st.session_state.act_dur, step=5)

        bloom = bloom_focus_for_week(st.session_state.week)
        if st.button("Create Questions", type="primary"):
            st.session_state.mcq_df = generate_mcq_blocks(
                st.session_state.topic, st.session_state.src_edit, blocks, st.session_state.week, st.session_state.lesson
            )
            st.success("MCQs generated.")

        if st.button("Create Activities"):
            st.session_state.act_df = generate_activities(
                act_n, act_d, bloom, st.session_state.topic, st.session_state.lesson, st.session_state.week, st.session_state.src_edit
            )
            st.success("Activities generated.")

        st.write("")
        if "mcq_df" in st.session_state:
            st.markdown("**Preview — MCQs**")
            st.dataframe(st.session_state.mcq_df, use_container_width=True, height=260)
        if "act_df" in st.session_state:
            st.markdown("**Preview — Activities**")
            st.dataframe(st.session_state.act_df, use_container_width=True, height=220)

    # --- Edit tab ---
    with t4:
        st.write("#### Edit MCQs / Activities (inline)")
        if "mcq_df" in st.session_state:
            st.session_state.mcq_df = st.data_editor(st.session_state.mcq_df, use_container_width=True, key="edit_mcq")
        else:
            st.info("No MCQs yet — generate them in the **Generate** tab.")
        st.write("")
        if "act_df" in st.session_state:
            st.session_state.act_df = st.data_editor(st.session_state.act_df, use_container_width=True, key="edit_act")
        else:
            st.info("No Activities yet — generate them in the **Generate** tab.")

    # --- Export tab ---
    with t5:
        st.write("#### Export")
        dl = []
        if "mcq_df" in st.session_state:
            mcq_csv = st.session_state.mcq_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download MCQs (CSV)", mcq_csv, "mcqs.csv", "text/csv")
            if Document is not None:
                mcq_docx = export_mcqs_docx(st.session_state.mcq_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
                st.download_button("Download MCQs (Word)", mcq_docx, "mcqs.docx",
                                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.info("Generate MCQs to enable downloads.")

        st.write("")
        if "act_df" in st.session_state:
            act_csv = st.session_state.act_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Activities (CSV)", act_csv, "activities.csv", "text/csv")
            if Document is not None:
                act_docx = export_acts_docx(st.session_state.act_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
                st.download_button("Download Activities (Word)", act_docx, "activities.docx",
                                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.info("Generate Activities to enable downloads.")

    st.markdown("</div>", unsafe_allow_html=True)
