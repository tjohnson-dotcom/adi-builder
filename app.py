# app.py — ADI Learning Tracker (full rebuild, ADI-styled, anchored generation)

import io, os, re, base64, random
from io import BytesIO
from typing import List
import pandas as pd
import streamlit as st

# ---------- Page config ----------
st.set_page_config(page_title="ADI Learning Tracker", page_icon="🧭", layout="centered")

# ---------- ADI Theme / CSS ----------
CSS = r'''
<style>
:root{
  --adi:#245a34;  /* ADI green */
  --gold:#C8A85A; /* ADI gold  */
  --stone:#f6f8f7;
  --ink:#0f172a;
  --muted:#667085;
  --border:#e7ecea;
  --shadow:0 10px 30px rgba(36,90,52,0.10);
}
*{font-family: ui-sans-serif, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif;}
html, body { background:var(--stone); }
main .block-container { padding-top:.75rem; max-width: 980px; }

/* Header */
.h1{ font-size:30px; font-weight:900; color:var(--ink); margin:0 0 2px 0; letter-spacing:.2px; }
.small{ color:var(--muted); font-size:14px; }
hr{ border:none; height:1px; background:linear-gradient(90deg, rgba(36,90,52,0.25), rgba(36,90,52,0.06)); margin:.8rem 0 1rem; }

/* Cards + Headings */
.card{ background:#fff; border:1px solid var(--border); border-radius:18px; padding:18px; box-shadow:var(--shadow); margin-bottom:1rem; }
.h2{ font-size:19px; font-weight:800; color:var(--ink); margin:0 0 10px 0; }

/* Tabs */
.stTabs [role="tablist"] { gap:.5rem; }
.stTabs [role="tab"] { font-weight:800; padding:.6rem .9rem; border-radius:12px 12px 0 0; }
.stTabs [data-baseweb="tab-highlight"]{ height:3px; background:linear-gradient(90deg,var(--adi),var(--gold)) !important; }
.stTabs [aria-selected="true"] { color: var(--adi) !important; }

/* Primary buttons */
.stButton>button{
  background: linear-gradient(180deg, #2b6c40, var(--adi));
  color:#fff; border:1px solid #1f4e31; font-weight:800; border-radius:12px;
  padding:.62rem 1rem; box-shadow:0 8px 20px rgba(36,90,52,0.25);
}
.stButton>button:hover{ filter:brightness(1.06); }
.stButton>button:focus{ outline:3px solid rgba(36,90,52,0.28); }

/* Inputs */
.stNumberInput > div > div, .stTextInput > div > div, .stTextArea > div > div{
  border-radius:12px !important; border-color:#e4e9e6 !important;
}
.stTextArea textarea::placeholder{ color:#9aa6a0; }

/* ① Upload – POP drag/drop */
[data-testid="stFileUploaderDropzone"]{
  border:2.5px dashed #b9cfc4 !important;
  border-radius:18px !important;
  background: radial-gradient(1200px 300px at 20% -20%, rgba(36,90,52,0.08), transparent 60%), #ffffff !important;
  box-shadow:0 10px 26px rgba(36,90,52,0.08);
}
[data-testid="stFileUploaderDropzone"]:hover{
  border-color:#8fb8a3 !important;
  background: radial-gradient(1200px 300px at 20% -20%, rgba(36,90,52,0.12), transparent 60%), #fcfefd !important;
  outline:3px solid rgba(36,90,52,0.25);
}

/* ② Setup – accent panels */
.panel{
  border:2px solid var(--border); border-radius:16px; padding:14px; margin:.6rem 0 1rem;
  background:#fff; box-shadow:0 8px 22px rgba(36,90,52,0.06);
}
.accent-mcq{   border-color:#dfe7e3; box-shadow:0 10px 24px rgba(36,90,52,0.08), inset 0 0 0 2px rgba(36,90,52,0.10); }
.accent-act{   border-color:#eadebd; box-shadow:0 10px 24px rgba(200,168,90,0.18), inset 0 0 0 2px rgba(200,168,90,0.18); }
.accent-bloom{ border-color:#cfd6d4; box-shadow:0 10px 24px rgba(0,0,0,0.06), inset 0 0 0 2px rgba(36,90,52,0.10); }

/* Bloom chips (pop + highlight by week) */
.bloom-row{ display:flex; flex-wrap:wrap; gap:.5rem .6rem; margin:.35rem 0 1rem; }
.chip{
  display:inline-flex; align-items:center; justify-content:center; padding:6px 14px;
  border-radius:999px; font-size:13px; font-weight:800; letter-spacing:.2px;
  box-shadow: 0 6px 16px rgba(0,0,0,0.10), inset 0 -2px 0 rgba(255,255,255,0.25);
  border:1px solid rgba(0,0,0,0.10);
}
.chip.low   { background:#245a34; color:#fff; border-color:#1a4628; }
.chip.med   { background:#C8A85A; color:#111; border-color:#9c874b; }
.chip.high  { background:#333;    color:#fff; border-color:#222; }
.chip.hl { outline:3px solid rgba(36,90,52,0.40); box-shadow:0 12px 32px rgba(36,90,52,0.20); }

/* MCQ preview */
.badge{ display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; border-radius:999px; color:#fff; font-weight:800; font-size:12px; margin-right:10px; }
.badge.g{ background:#245a34; } .badge.a{ background:#C8A85A; color:#111; } .badge.r{ background:#333; color:#fff; }
.qcard{ border:1px solid var(--border); border-radius:14px; padding:10px 12px; background:#fff; }
.qitem{ display:flex; gap:10px; align-items:flex-start; padding:6px 0; }

/* Notes (replace blue info) */
.note{ padding:12px 14px; border-radius:12px; border:1px solid #eadebd; background:linear-gradient(180deg,#fffdf5,#fffaf0); color:#3b351c; }

/* ④ Export – grid + green buttons */
.export-grid{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:1rem; }
@media (max-width: 760px){ .export-grid{ grid-template-columns: 1fr; } }
.export-card{ background:#fff; border:1px solid var(--border); border-radius:16px; padding:14px; box-shadow:var(--shadow); }
.export-title{ font-weight:900; color:var(--ink); margin-bottom:.3rem; }
.export-note{ color:var(--muted); font-size:13px; margin-bottom:.6rem; }

.stDownloadButton>button{
  background: linear-gradient(180deg, #2b6c40, var(--adi)) !important;
  color:#fff !important; border:1px solid #1f4e31 !important; font-weight:800 !important;
  border-radius:12px !important; padding:.55rem .9rem !important; box-shadow:0 8px 20px rgba(36,90,52,0.25) !important;
}
.stDownloadButton>button:hover{ filter:brightness(1.06); }
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)

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
try:
    from docx import Document
    from docx.shared import Pt, Inches
except Exception:
    Document = None
    Pt = Inches = None

# ---------- Logo helper ----------
_FALLBACK_LOGO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABABAAAAACqG3XIAAACMElEQVR4nM2WsW7TQBiFf6a0H5yq"
    "zF0y2y5hG0c6zF4k1u5u9m3JHqz4dM7M9kP3C0k1bC0bC2A1vM9Y7mY0JgVv8uJbVYy0C4d6i3gC"
    "9b4n2QxgE7iTnk9z9k9w4rH4g6YyKc3H5rW3q2m8Qw3wUuJKGkqQ8jJr1h3v9J0o9l6zQn9qV2mN"
    "2l8c1mXi5Srgm2cG3wYQz7a1nS0CkqgkQz0o4Kx5l9yJc8KEMt8h2tqfWm0y8x2T8Jw0+o8S8b8"
    "Jw3emcQ0n9Oq7dZrXw9kqgk5yA9iO1l0wB7mQxI3o3eV+o3oM2v8YUpbG6c6WcY8B6bZ9FfQLQ+"
    "s5n8n4Zb3T3w9y7K0gN4d8c4sR4mxD9j8c+J6o9+3yCw1o0b7YpAAAAAElFTkSuQmCC"
)
def _load_logo_bytes() -> bytes:
    try:
        if os.path.exists("Logo.png"):
            with open("Logo.png", "rb") as f:
                return f.read()
    except Exception:
        pass
    return base64.b64decode(_FALLBACK_LOGO_B64)

# ---------- Bloom policy ----------
LOW_VERBS  = ["define","identify","list","describe","recall","label"]
MED_VERBS  = ["apply","demonstrate","solve","illustrate","analyze","interpret","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","formulate","critique"]
def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# ---------- Text helpers ----------
from difflib import SequenceMatcher
_STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","as","is","are","be","was","were","this","that","these","those",
    "it","its","at","from","into","over","under","about","between","within","use","used","using","also","than","which","such","may",
    "can","could","should","would","will","not","if","when","while","after","before","each","per","via","more","most","less","least",
    "other","another","see","example","examples","appendix","figure","table","chapter","section","page","pages","ref","ibid",
    "module","lesson","week","activity","activities","objective","objectives","outcome","outcomes","question","questions","topic","topics",
    "student","students","teacher","instructor","course","unit","learning","overview","summary","introduction","conclusion","content","contents"
}
def _clean_lines(text: str) -> str:
    lines = [ln.strip() for ln in (text or "").replace("\r","\n").split("\n") if ln.strip()]
    lines = [ln for ln in lines if not re.fullmatch(r"(page\s*\d+|\d+)", ln, flags=re.I)]
    out, seen = [], set()
    for ln in lines:
        k = ln[:96].lower()
        if k in seen: continue
        seen.add(k); out.append(ln)
    return "\n".join(out)[:8000]
def _sentences(text: str) -> List[str]:
    chunks = re.split(r"[.\u2022\u2023\u25CF•]|(?:\n\s*\-\s*)|(?:\n\s*\*\s*)", text or "")
    rough = [re.sub(r"\s+", " ", c).strip() for c in chunks if c and c.strip()]
    return [s for s in rough if 30 <= len(s) <= 180][:400]
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
def _near(a:str,b:str,th:float=0.90)->bool:
    return SequenceMatcher(a=a.lower(), b=b.lower()).ratio() >= th
def _uniq_keep(seq: List[str], key=lambda s: s.lower()):
    seen=set(); out=[]
    for s in seq:
        k=key(s)
        if k and k not in seen:
            seen.add(k); out.append(s)
    return out
def _quality_gate(options: List[str]) -> List[str]:
    ops=[re.sub(r"\s+"," ",o.strip()) for o in options if o and o.strip()]
    out=[]
    for o in ops:
        if len(o)<25 or len(o)>180: continue
        if not any(_near(o,p,0.96) for p in out): out.append(o)
        if len(out)==4: break
    return out[:4]
def _window(sentences: List[str], idx: int, w: int = 2) -> List[str]:
    L=max(0, idx-w); R=min(len(sentences), idx+w+1)
    return sentences[L:R]

# ---------- Upload parsing ----------
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
            return _clean_lines("\n".join((p.text or "") for p in doc.paragraphs[:300]))
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(file)
            parts=[]
            for s in prs.slides[:50]:
                for shp in s.shapes:
                    if hasattr(shp,"text") and shp.text:
                        parts.append(shp.text)
                if getattr(s,"has_notes_slide",False) and getattr(s.notes_slide,"notes_text_frame",None):
                    parts.append(s.notes_slide.notes_text_frame.text or "")
            return _clean_lines("\n".join(parts))
        return "[Unsupported file type or missing parser]"
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ---------- Anchored MCQs ----------
def generate_mcqs_exact(topic: str, source: str, total_q: int, week: int, lesson: int = 1) -> pd.DataFrame:
    if total_q < 1: raise ValueError("Total questions must be ≥ 1.")
    ctx = (topic or "").strip() or f"Lesson {lesson} • Week {week}"
    sents = _sentences(source or "")
    if len(sents) < 12:
        raise ValueError("Not enough source text (need ~12+ good sentences).")
    keys = _keywords(source or topic or "", top_n=max(24, total_q*4))
    if not keys: raise ValueError("Couldn’t mine keywords; upload a richer section.")
    rows=[]; rnd=random.Random(2025); made=0; tiers=["Low","Medium","High"]
    for k in keys:
        try:
            idx = next(i for i,s in enumerate(sents) if k.lower() in s.lower())
        except StopIteration:
            continue
        correct = sents[idx].strip()
        neigh = _window(sents, idx, 3)
        cand = [s for s in neigh if s != correct]
        if len(cand) < 6:
            extra = [s for s in sents if re.search(r"\b(avoid|verify|select|compare|justify|ensure|limit|risk|threshold|condition)\b", s, re.I)]
            rnd.shuffle(extra); cand += extra[:8]
        options = _quality_gate([correct] + cand)
        if len(options) < 4: continue
        tier = tiers[made % 3]
        if tier == "Low":
            q = f"Which statement about **{k}** best fits *{ctx}*?"
        elif tier == "Medium":
            q = f"When applying **{k}** in *{ctx}*, which statement is most appropriate?"
        else:
            q = f"Which option provides the strongest justification related to **{k}** in *{ctx}*?"
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(correct)]
        rows.append({
            "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": q,
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans, "Explanation": f"Answer sentence contains '{k}'.",
            "Order": {"Low":1,"Medium":2,"High":3}[tier],
        })
        made += 1
        if made == total_q: break
    if made == 0:
        raise ValueError("Could not extract enough anchored items — try a different section.")
    return pd.DataFrame(rows).reset_index(drop=True)

# ---------- Anchored Activities ----------
def generate_activities(count: int, duration: int, tier: str, topic: str, lesson: int, week: int, source: str = "") -> pd.DataFrame:
    topic = (topic or "").strip()
    ctx = f"Lesson {lesson} • Week {week}" + (f" — {topic}" if topic else "")
    verbs = {"Low":LOW_VERBS,"Medium":MED_VERBS,"High":HIGH_VERBS}.get(tier, MED_VERBS)[:6]
    sents = _sentences(source or "")
    if len(sents) < 12:
        raise ValueError("Not enough source text to build activities (need ~12+ sentences).")
    hints = [s for s in sents if re.search(
        r"\b(first|then|next|measure|calculate|record|verify|inspect|threshold|risk|control|select|compare|interpret|justify|design)\b",
        s, re.I)]
    hints = _uniq_keep(hints)[:60]
    if not hints:
        raise ValueError("Couldn’t find steps/constraints in the source to anchor activities.")
    rnd = random.Random(99)
    rows=[]
    for i in range(1, count + 1):
        v = verbs[(i - 1) % len(verbs)]
        t1=max(5,int(duration*0.2)); t2=max(10,int(duration*0.55)); t3=max(5,duration-(t1+t2))
        core = rnd.choice(hints)
        core_idx = sents.index(core) if core in sents else 0
        nearby = [h for h in _window(sents, core_idx, 2) if h != core]
        step_line = "; ".join(_uniq_keep([core] + nearby))[:360]
        rows.append({
            "Lesson": lesson, "Week": week, "Policy focus": tier,
            "Title": f"{ctx} — {tier} Activity {i}", "Tier": tier,
            "Objective": f"Students will {v} key ideas anchored to today’s source.",
            "Steps": f"Starter ({t1}m): {v.capitalize()} prior knowledge. "
                     f"Main ({t2}m): Follow these anchored steps — {step_line}. "
                     f"Plenary ({t3}m): Compare outputs to the source; justify choices against constraints.",
            "Materials": "Lesson PDF/PPT, mini-whiteboards, markers; timer",
            "Assessment": "Performance check aligned to the anchored steps; short justification.",
            "Duration (mins)": duration,
        })
    return pd.DataFrame(rows)

# ---------- DOCX helpers ----------
def _docx_heading(doc, text, level=0):
    p=doc.add_paragraph(); r=p.add_run(text)
    if level==0: r.bold=True; r.font.size=Pt(16)
    elif level==1: r.bold=True; r.font.size=Pt(13)
    else: r.font.size=Pt(11)
def export_mcqs_docx(df: pd.DataFrame, lesson:int, week:int, topic:str="")->bytes:
    if Document is None: return b""
    doc=Document(); sec=doc.sections[0]
    if Inches: sec.left_margin=Inches(0.8); sec.right_margin=Inches(0.8)
    _docx_heading(doc, f"Knowledge MCQs — Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else ""), 0)
    doc.add_paragraph()
    for i, r in df.reset_index(drop=True).iterrows():
        doc.add_paragraph(f"{i+1}. ({r['Tier']}) {r['Question']}")
        doc.add_paragraph(f"A. {r['Option A']}"); doc.add_paragraph(f"B. {r['Option B']}")
        doc.add_paragraph(f"C. {r['Option C']}"); doc.add_paragraph(f"D. {r['Option D']}")
        doc.add_paragraph()
    _docx_heading(doc, "Answer Key", 1)
    for i, r in df.reset_index(drop=True).iterrows():
        doc.add_paragraph(f"Q{i+1}: {r['Answer']}")
    bio=BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()
def export_acts_docx(df: pd.DataFrame, lesson:int, week:int, topic:str="")->bytes:
    if Document is None: return b""
    doc=Document(); sec=doc.sections[0]
    if Inches: sec.left_margin=Inches(0.8); sec.right_margin=Inches(0.8)
    _docx_heading(doc, f"Skills Activities — Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else ""), 0)
    doc.add_paragraph()
    for i,r in df.iterrows():
        _docx_heading(doc, r.get("Title", f"Activity {i+1}"), 1)
        doc.add_paragraph(f"Policy focus: {r['Policy focus']}")
        doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph(f"Steps: {r['Steps']}")
        doc.add_paragraph(f"Materials: {r['Materials']}")
        doc.add_paragraph(f"Assessment: {r['Assessment']}")
        doc.add_paragraph(f"Duration: {r['Duration (mins)']} mins")
        doc.add_paragraph()
    bio=BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

# ---------- GIFT export ----------
_GIFT_ESCAPE = str.maketrans({"~": r"\~","=": r"\=","#": r"\#","{": r"\{","}": r"\}",":": r"\:","\n": r"\n"})
def _gift_escape(s:str)->str: return (s or "").translate(_GIFT_ESCAPE)
def export_mcqs_gift(df:pd.DataFrame, lesson:int, week:int, topic:str="")->str:
    lines=[]; title_prefix=f"Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else "")
    for i,r in df.reset_index(drop=True).iterrows():
        qname=f"{title_prefix} — Q{i+1} ({r.get('Tier','')})"
        stem=_gift_escape(str(r.get("Question","")).strip())
        opts=[str(r.get("Option A","")).strip(),str(r.get("Option B","")).strip(),
              str(r.get("Option C","")).strip(),str(r.get("Option D","")).strip()]
        idx={"A":0,"B":1,"C":2,"D":3}.get(str(r.get("Answer","A")).strip().upper(),0)
        parts=[("="+_gift_escape(o)) if j==idx else ("~"+_gift_escape(o)) for j,o in enumerate(opts)]
        exp=str(r.get("Explanation","")).strip()
        comment=f"#### {_gift_escape(exp)}" if exp else ""
        lines.append(f"::{_gift_escape(qname)}:: {stem} {{\n" + "\n".join(parts) + f"\n}} {comment}\n")
    return "\n".join(lines).strip()+"\n"

# ---------- App state ----------
st.session_state.setdefault("lesson", 1)
st.session_state.setdefault("week", 1)
st.session_state.setdefault("mcq_total", 10)
st.session_state.setdefault("act_n", 1)
st.session_state.setdefault("act_dur", 30)
st.session_state.setdefault("topic", "")
st.session_state.setdefault("logo_bytes", _load_logo_bytes())
st.session_state.setdefault("src_text", "")
st.session_state.setdefault("src_edit", "")

# ---------- Header ----------
col_logo, col_title = st.columns([1,4])
with col_logo:
    if st.session_state.logo_bytes:
        b64 = base64.b64encode(st.session_state.logo_bytes).decode()
        st.image(f"data:image/png;base64,{b64}", use_container_width=True)
with col_title:
    st.markdown("<div class='h1'>ADI Learning Tracker</div>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Transform lessons into measurable learning</div>", unsafe_allow_html=True)
st.divider()

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["① Upload", "② Setup", "③ Generate", "④ Export"])

# ===== ① Upload =====
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Upload Lesson File</div>", unsafe_allow_html=True)
    up = st.file_uploader("Upload .pptx / .pdf / .docx", type=["pptx","pdf","docx"])
    if up:
        st.session_state.src_text = extract_text_from_upload(up)
        st.session_state.src_edit = st.session_state.src_text
        if st.session_state.src_text.startswith("[Could not parse"):
            st.error(st.session_state.src_text)
        else:
            st.success("File uploaded and parsed.")
    st.markdown("</div>", unsafe_allow_html=True)

# ===== ② Setup =====
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Setup</div>", unsafe_allow_html=True)

    # Lesson & Week
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.session_state.lesson = st.selectbox("Lesson", [1,2,3,4], index=st.session_state.lesson-1)
    with c2:
        st.session_state.week   = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1)
    with c3:
        st.text_input("Bloom focus (auto)",
                      value=f"Week {st.session_state.week}: {bloom_focus_for_week(st.session_state.week)}",
                      disabled=True)

    st.session_state.topic = st.text_input("Learning Objective / Topic (optional)", value=st.session_state.topic)
    st.session_state.src_edit = st.text_area("Source (editable)", value=st.session_state.src_edit,
                                             height=160, placeholder="Paste or edit full sentences here…")

    # --- MCQ setup panel
    st.markdown("<div class='panel accent-mcq'>", unsafe_allow_html=True)
    st.write("### MCQ Setup")
    choices = [5,10,20,30]
    default_idx = choices.index(st.session_state.mcq_total) if st.session_state.mcq_total in choices else 1
    st.session_state.mcq_total = st.radio("Number of MCQs", choices, index=default_idx, horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Activity setup panel
    st.markdown("<div class='panel accent-act'>", unsafe_allow_html=True)
    st.write("### Activity Setup")
    colA, colB = st.columns([1,2])
    with colA:
        st.session_state.act_n = st.radio("Activities", [1,2,3], index=st.session_state.act_n-1, horizontal=True)
    with colB:
        st.session_state.act_dur = st.slider("Duration per Activity (mins)", 10, 60, st.session_state.act_dur, 5)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Bloom panel
    st.markdown("<div class='panel accent-bloom'>", unsafe_allow_html=True)
    st.write("### Bloom’s Verbs (ADI Policy)")
    focus = bloom_focus_for_week(st.session_state.week)
    def bloom_row(label, verbs):
        cls  = "low" if label=="Low" else "med" if label=="Medium" else "high"
        hl   = " hl" if label==focus else ""
        weeks = "1–4" if label=="Low" else "5–9" if label=="Medium" else "10–14"
        chips = " ".join([f"<span class='chip {cls}{hl}'>{v}</span>" for v in verbs])
        st.markdown(f"**{label} (Weeks {weeks})**", unsafe_allow_html=True)
        st.markdown(f"<div class='bloom-row'>{chips}</div>", unsafe_allow_html=True)
    bloom_row("Low", LOW_VERBS); bloom_row("Medium", MED_VERBS); bloom_row("High", HIGH_VERBS)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # end card

# ===== ③ Generate =====
with tab3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Generate Questions & Activities</div>", unsafe_allow_html=True)

    tip_needed = (not st.session_state.src_edit) or len(_sentences(st.session_state.src_edit)) < 12
    if tip_needed:
        st.markdown("<div class='note'>Tip: use a section with ~12+ full sentences. Bullets should be expanded into sentences.</div>", unsafe_allow_html=True)

    colQ, colA = st.columns([1,1])
    with colQ:
        if st.button("📝 Generate MCQs", use_container_width=True):
            try:
                st.session_state.mcq_df = generate_mcqs_exact(
                    st.session_state.topic, st.session_state.src_edit, int(st.session_state.mcq_total),
                    st.session_state.week, st.session_state.lesson
                )
                st.success("MCQs generated.")
            except Exception as e:
                st.error(f"Couldn’t generate MCQs: {e}")
    with colA:
        if st.button("🧩 Generate Activities", use_container_width=True):
            try:
                focus = bloom_focus_for_week(st.session_state.week)
                st.session_state.act_df = generate_activities(
                    int(st.session_state.act_n), int(st.session_state.act_dur), focus,
                    st.session_state.topic, st.session_state.lesson, st.session_state.week, st.session_state.src_edit
                )
                st.success("Activities generated.")
            except Exception as e:
                st.error(f"Couldn’t generate activities: {e}")

    # Previews
    if "mcq_df" in st.session_state:
        st.write("**MCQs (preview)**")
        st.markdown("<div class='qcard'>", unsafe_allow_html=True)
        for i,row in st.session_state.mcq_df.reset_index(drop=True).iterrows():
            c = "g" if row["Tier"]=="Low" else "a" if row["Tier"]=="Medium" else "r"
            st.markdown(f"<div class='qitem'><span class='badge {c}'>{i+1}</span><div><b>{row['Question']}</b></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if "act_df" in st.session_state:
        st.write("**Activities (preview)**")
        for i,r in st.session_state.act_df.reset_index(drop=True).iterrows():
            with st.expander(f"{i+1}. {r.get('Title','Activity')}"):
                st.write(f"**Policy focus:** {r['Policy focus']}")
                st.write(f"**Objective:** {r['Objective']}")
                st.write(f"**Steps:** {r['Steps']}")
                st.write(f"**Duration:** {r['Duration (mins)']} mins")
    st.markdown("</div>", unsafe_allow_html=True)

# ===== ④ Export =====
with tab4:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Export</div>", unsafe_allow_html=True)

    st.markdown("<div class='export-grid'>", unsafe_allow_html=True)

    # MCQ card
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>MCQs</div>", unsafe_allow_html=True)
    st.markdown("<div class='export-note'>Download your question set in multiple formats.</div>", unsafe_allow_html=True)
    if "mcq_df" in st.session_state:
        st.download_button("Download MCQs (CSV)",
                           st.session_state.mcq_df.to_csv(index=False).encode("utf-8"),
                           f"mcqs_l{st.session_state.lesson}_w{st.session_state.week}.csv",
                           "text/csv")
        gift_txt = export_mcqs_gift(st.session_state.mcq_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
        st.download_button("Download MCQs (Moodle GIFT)",
                           gift_txt.encode("utf-8"),
                           f"mcqs_l{st.session_state.lesson}_w{st.session_state.week}.gift",
                           "text/plain")
        if Document:
            mcq_docx = export_mcqs_docx(st.session_state.mcq_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
            st.download_button("Download MCQs (Word)",
                               mcq_docx,
                               f"mcqs_l{st.session_state.lesson}_w{st.session_state.week}.docx",
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.caption("Install python-docx for Word export.")
    else:
        st.markdown("<div class='note'>Generate MCQs in <b>③ Generate</b> to enable downloads.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Activities card
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>Activities</div>", unsafe_allow_html=True)
    st.markdown("<div class='export-note'>Export practical activities aligned to Bloom’s focus.</div>", unsafe_allow_html=True)
    if "act_df" in st.session_state:
        st.download_button("Download Activities (CSV)",
                           st.session_state.act_df.to_csv(index=False).encode("utf-8"),
                           f"activities_l{st.session_state.lesson}_w{st.session_state.week}.csv",
                           "text/csv")
        if Document:
            act_docx = export_acts_docx(st.session_state.act_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
            st.download_button("Download Activities (Word)",
                               act_docx,
                               f"activities_l{st.session_state.lesson}_w{st.session_state.week}.docx",
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.caption("Install python-docx for Word export.")
    else:
        st.markdown("<div class='note'>Generate Activities in <b>③ Generate</b> to enable downloads.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # grid
    st.markdown("</div>", unsafe_allow_html=True)  # card
