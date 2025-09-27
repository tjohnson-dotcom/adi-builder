# ADI — Learning Tracker Question Generator
# Streamlit app: Upload (PDF/PPTX/DOCX) → Source-anchored MCQs & Activities → Edit → Export (CSV/Word)

import io, os, re, base64, random
from io import BytesIO
from typing import List
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
try:
    from docx import Document
    from docx.shared import Pt, Inches
except Exception:
    Document = None
    Pt = None
    Inches = None

# ---------- Page & theme ----------
st.set_page_config(
    page_title="ADI — Learning Tracker Question Generator",
    page_icon="🧭",
    layout="centered"
)

CSS = """
<style>
:root{
  --adi:#1f5a35;       /* ADI deep green */
  --adi-600:#194a2c;
  --ink:#0f172a;
  --muted:#6b7280;
  --bg:#f7faf8;
  --card:#ffffff;
  --border:#e6e9ec;
  --accent:#3865ff;
}
html, body { background: var(--bg); }
main .block-container { padding-top: 1.0rem; max-width: 920px; }

.header-card{
  background:var(--card); border:1px solid var(--border); border-radius:16px; padding:14px 16px;
  box-shadow:0 6px 18px rgba(31,90,53,.06); margin-bottom:10px;
}
.titlebox .brand { font-size: 26px; font-weight: 800; color: var(--ink); line-height:1.08; }
.titlebox .brand-sub { color: var(--muted); margin-top:2px; }
.hero-btn {
  display:block; width:100%; background: linear-gradient(180deg, #3B69FF, #2A4ED6);
  color:#fff; border:none; padding:12px 16px; border-radius:12px; font-weight:800; font-size:16px;
  box-shadow:0 10px 28px rgba(56,101,255,.25); margin: 10px 0 2px 0;
}

.card {
  background:var(--card); border:1px solid var(--border); border-radius:16px; padding:16px 16px;
  box-shadow:0 6px 18px rgba(31,90,53,.06);
}
.section-title { font-weight:800; color:var(--ink); margin-bottom:6px; font-size:18px; }
.tip { font-size:12px; color:var(--muted); }
.dashed { border:2px dashed #e3e6ef; padding:16px; border-radius:14px; background:#fff; }

/* Top Icon Nav */
.navbar { display:flex; gap:10px; align-items:center; padding:8px 12px;
  background:#fff; border:1px solid var(--border); border-radius:12px; 
  box-shadow:0 6px 18px rgba(31,90,53,.06); margin: 8px 0 18px 0; overflow:auto; }
.navbtn { display:flex; align-items:center; gap:8px; padding:8px 12px; border-radius:10px;
  border:1px solid #edf0f4; background:#f8fafc; color:#0f172a; font-weight:700; font-size:13px;
  white-space:nowrap; cursor:pointer; user-select:none; }
.navbtn:hover { background:#f1f5f9; }
.navbtn.active { background:#eaf5ec; border-color:#d4e8da; outline:2px solid #cfe5d8; }
.navicon { width:18px; height:18px; display:inline-flex; align-items:center; justify-content:center; }

/* Upload panel */
.upload-panel { border:2px dashed #e5e7eb; background:#fff; border-radius:14px; padding:18px; }
.file-icons { display:flex; gap:14px; align-items:center; margin:4px 0 10px 0; }
.file-icon { width:42px; height:42px; display:inline-block; }
.file-chip {
  display:flex; align-items:center; gap:10px; padding:10px 12px; border:1px solid var(--border);
  border-radius:12px; background:#fff; box-shadow:0 2px 8px rgba(16,24,40,.06);
}
.file-chip .dotdot { margin-left:auto; color:#9aa1ad; font-weight:900; }
.upload-hint { color:#374151; font-size:16px; line-height:1.5; margin-top:6px; }
.ext-pill {
  display:inline-flex; align-items:center; justify-content:center; min-width:36px; height:22px; padding:0 6px;
  border-radius:8px; font-weight:700; color:#fff; font-size:12px; text-transform:lowercase;
}
.ext-pptx { background:#f59e0b; }
.ext-pdf  { background:#22c55e; }
.ext-epub { background:#facc15; color:#111827; }
.ext-docx { background:#3b82f6; }

/* MCQ list */
.qcard { border:1px solid var(--border); border-radius:12px; background:#fff; padding:10px 12px; }
.qitem { display:flex; gap:8px; align-items:flex-start; padding:8px 0; }
.badge { display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px;
         border-radius:999px; font-weight:800; font-size:12px; color:#fff; margin-right:10px; }
.badge.g { background:#1f5a35; }
.badge.a { background:#f59e0b; }
.badge.r { background:#ef4444; }
.qtext { line-height:1.5; font-size:16px; }

/* Bloom chips */
.chips { display:flex; flex-wrap:wrap; gap:8px; }
.chip { padding:4px 10px; border-radius:999px; border:1px solid var(--border); background:#fff; font-size:12px; }
.chip.low  { background:#eaf5ec; border-color:#cfe5d8; }
.chip.med  { background:#fbf6ec; border-color:#efe6cf; }
.chip.high { background:#f3f1ee; border-color:#e5ded6; }
.row.active .chip { outline: 2px solid var(--adi); box-shadow:0 3px 10px rgba(31,90,53,.15); }

.warn { color:#b91c1c; font-weight:600; }
.success { color:#166534; font-weight:600; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- ADI logo ----------
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
ADI_VERBS  = {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}

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
        seen.add(k)
        out.append(ln)
    return "\n".join(out)[:8000]

def _sentences(text: str) -> List[str]:
    chunks = re.split(r"[.\u2022\u2023\u25CF•]|(?:\n\s*\-\s*)|(?:\n\s*\*\s*)", text or "")
    rough = [re.sub(r"\s+", " ", c).strip() for c in chunks if c and c.strip()]
    out = []
    for s in rough:
        if 30 <= len(s) <= 180:
            out.append(s)
    return out[:400]

def _keywords(text: str, top_n:int=24) -> List[str]:
    from collections import Counter
    toks=[]
    for w in re.split(r"[^A-Za-z0-9]+", text or ""):
        w=w.lower()
        if len(w)>=4 and w not in _STOP:
            toks.append(w)
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
    opts=[re.sub(r"\s+", " ", o.strip()) for o in options if o and o.strip()]
    out=[]
    for o in opts:
        if "core concepts, steps, constraints" in o.lower():  # boilerplate
            continue
        if o[::-1].lower()==o.lower():                        # mirrored
            continue
        if len(o)<25 or len(o)>180:
            continue
        if not any(_near(o,p,0.96) for p in out):
            out.append(o)
        if len(out)==4: break
    return out[:4]

def _window_sentences(sentences: List[str], idx: int, w: int = 2) -> List[str]:
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

# ---------- Strict, source-anchored MCQs ----------
def generate_mcqs_exact(topic: str, source: str, total_q: int, week: int, lesson: int = 1) -> pd.DataFrame:
    if total_q < 1:
        raise ValueError("Total questions must be at least 1.")
    ctx = (topic or "").strip() or f"Lesson {lesson} • Week {week}"
    sents = _sentences(source or "")
    if len(sents) < 12:
        raise ValueError("Not enough source text to generate quality MCQs. Upload/paste a denser section (≈12+ usable sentences).")

    keys = _keywords(source or topic or "", top_n=max(24, total_q * 4))
    if not keys:
        raise ValueError("Couldn’t mine keywords from the source. Paste outcomes or upload a richer chapter/slide set.")

    rows=[]
    rnd=random.Random(2025)
    made=0
    tier_cycle=["Low","Medium","High"]

    for k in keys:
        idx = next((i for i, s in enumerate(sents) if k.lower() in s.lower()), -1)
        if idx == -1:
            continue
        correct = sents[idx].strip()
        neigh = _window_sentences(sents, idx, 3)
        cand = [s for s in neigh if s.strip() and s.strip() != correct]
        if len(cand) < 6:
            extra = [s for s in sents if re.search(r"\b(avoid|verify|select|compare|justify|ensure|limit|risk|threshold|condition)\b", s, re.I)]
            rnd.shuffle(extra); cand += extra[:8]
        options = _quality_gate([correct] + cand)
        if len(options) < 4:
            continue

        tier = tier_cycle[made % 3]
        if tier == "Low":
            q = f"Which statement about **{k}** best fits *{ctx}*?"
        elif tier == "Medium":
            q = f"When applying **{k}** in *{ctx}*, which statement is most appropriate?"
        else:
            q = f"Which option provides the strongest justification related to **{k}** in *{ctx}*?"

        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(correct)]

        rows.append({
            "Tier": tier,
            "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": q,
            "Option A": options[0],
            "Option B": options[1],
            "Option C": options[2],
            "Option D": options[3],
            "Answer": ans,
            "Explanation": f"Source-anchored: answer sentence contains '{k}'.",
            "Order": {"Low":1,"Medium":2,"High":3}[tier],
        })
        made += 1
        if made == total_q:
            break

    if made == 0:
        raise ValueError("Could not find enough high-quality sentences tied to mined terms. Try a different chapter/slide deck section.")
    return pd.DataFrame(rows).reset_index(drop=True)

# ---------- Strict, source-anchored Activities ----------
def generate_activities(count: int, duration: int, tier: str, topic: str,
                        lesson: int, week: int, source: str = "") -> pd.DataFrame:
    topic = (topic or "").strip()
    ctx = f"Lesson {lesson} • Week {week}" + (f" — {topic}" if topic else "")
    verbs = ADI_VERBS.get(tier, MED_VERBS)[:6]
    sents = _sentences(source or "")
    if len(sents) < 12:
        raise ValueError("Not enough source text to build activities. Upload/paste a denser section (≈12+ sentence-quality lines).")

    hints = [s for s in sents if re.search(
        r"\b(first|then|next|measure|calculate|record|verify|inspect|threshold|risk|control|select|compare|interpret|justify|design)\b",
        s, re.I)]
    hints = _uniq_keep(hints)[:60]
    if not hints:
        raise ValueError("Couldn’t find procedural/constraint lines in the source to anchor activities.")

    rnd = random.Random(99)
    rows=[]
    for i in range(1, count + 1):
        v = verbs[(i - 1) % len(verbs)]
        t1=max(5,int(duration*0.2)); t2=max(10,int(duration*0.55)); t3=max(5,duration-(t1+t2))
        core = rnd.choice(hints)
        core_idx = sents.index(core) if core in sents else 0
        nearby = [h for h in _window_sentences(sents, core_idx, 2) if h != core]
        step_line = "; ".join(_uniq_keep([core] + nearby))[:360]

        rows.append({
            "Lesson": lesson,
            "Week": week,
            "Policy focus": tier,
            "Title": f"{ctx} — {tier} Activity {i}",
            "Tier": tier,
            "Objective": f"Students will {v} key ideas directly from today’s source (anchored to text).",
            "Steps": f"Starter ({t1}m): {v.capitalize()} prior knowledge tied to the context. "
                     f"Main ({t2}m): Follow these anchored steps — {step_line}. "
                     f"Plenary ({t3}m): Compare outputs to the source; justify choices against stated constraints.",
            "Materials": "Lesson PDF/PPT, mini-whiteboards, markers; timer",
            "Assessment": "Performance check aligned to the anchored steps; brief justification referencing the source.",
            "Duration (mins)": duration,
        })
    return pd.DataFrame(rows)

# ---------- Word exports ----------
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

# ---------- Pretty list render ----------
def render_mcq_list(df: pd.DataFrame):
    st.markdown("<div class='qcard'>", unsafe_allow_html=True)
    for i, row in df.reset_index(drop=True).iterrows():
        c = "g" if row["Tier"]=="Low" else "a" if row["Tier"]=="Medium" else "r"
        st.markdown(
            f"<div class='qitem'><span class='badge {c}'>{i+1}</span>"
            f"<div class='qtext'><strong>{row['Question']}</strong></div></div>",
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- App state ----------
st.session_state.setdefault("lesson", 1)
st.session_state.setdefault("week", 1)
st.session_state.setdefault("topic", "")
st.session_state.setdefault("q_total", 10)
st.session_state.setdefault("act_n", 3)
st.session_state.setdefault("act_dur", 45)
st.session_state.setdefault("logo_bytes", _load_logo_bytes())
st.session_state.setdefault("src_text", "")
st.session_state.setdefault("src_edit", st.session_state.get("src_text", ""))
st.session_state.setdefault("nav_tab", "Upload")
st.session_state.setdefault("last_uploaded_name", None)

# ---------- Header ----------
with st.container():
    st.markdown("<div class='header-card'>", unsafe_allow_html=True)
    col_logo, col_title = st.columns([1,4])
    with col_logo:
        if st.session_state.logo_bytes:
            b64 = base64.b64encode(st.session_state.logo_bytes).decode()
            st.image(f"data:image/png;base64,{b64}", caption=None, use_container_width=True)
    with col_title:
        st.markdown("<div class='titlebox'>", unsafe_allow_html=True)
        st.markdown("<div class='brand'>Learning Tracker Question Generator</div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-sub'>Transforming Lessons into Measurable Learning</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<button class='hero-btn'>Begin Tracking Learning</button>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Icon Nav ----------
NAV = [("Upload","📤"),("Setup","🛠️"),("Generate","✨"),("Edit","✏️"),("Export","📄")]
def render_nav():
    st.markdown("<div class='navbar'>", unsafe_allow_html=True)
    cols = st.columns(len(NAV))
    for i,(label,icon) in enumerate(NAV):
        with cols[i]:
            active = " active" if st.session_state.nav_tab == label else ""
            st.markdown(f"<div class='navbtn{active}'><span class='navicon'>{icon}</span> {label}</div>", unsafe_allow_html=True)
            if st.button(label, key=f"nav_{label}", help=f"Go to {label}"):
                st.session_state.nav_tab = label
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

render_nav()
tab = st.session_state.nav_tab

# ---------- Upload helpers (icons)
SVG = {
    "pptx": """<svg class="file-icon" viewBox="0 0 24 24" fill="none"><rect x="3" y="2" width="18" height="20" rx="4" fill="#FDE68A"/><path d="M8 8h6a2 2 0 0 1 0 4H8V8z" fill="#F59E0B"/><circle cx="9" cy="15" r="1" fill="#92400E"/><circle cx="13" cy="15" r="1" fill="#92400E"/></svg>""",
    "pdf":  """<svg class="file-icon" viewBox="0 0 24 24" fill="none"><rect x="3" y="2" width="18" height="20" rx="4" fill="#DCFCE7"/><path d="M7 15c3-2 5-4 6-7 2 2 3 4 4 7" stroke="#16A34A" stroke-width="2" fill="none"/></svg>""",
    "epub": """<svg class="file-icon" viewBox="0 0 24 24" fill="none"><rect x="3" y="2" width="18" height="20" rx="4" fill="#FEF3C7"/><path d="M7 9h10M7 13h10M7 17h6" stroke="#F59E0B" stroke-width="2"/></svg>""",
    "docx": """<svg class="file-icon" viewBox="0 0 24 24" fill="none"><rect x="3" y="2" width="18" height="20" rx="4" fill="#DBEAFE"/><path d="M7 8h4l2 8h-4l-2-8z" fill="#2563EB"/></svg>""",
}
def render_upload_panel(uploaded_name: str | None):
    icons = SVG["pptx"] + SVG["pdf"] + SVG["epub"] + SVG["docx"]
    st.markdown(f"<div class='upload-panel'><div class='file-icons'>{icons}</div>", unsafe_allow_html=True)
    if uploaded_name:
        ext = uploaded_name.split(".")[-1].lower()
        pill_cls = {"pptx":"ext-pptx","pdf":"ext-pdf","epub":"ext-epub","docx":"ext-docx"}.get(ext, "ext-docx")
        st.markdown(
            f"<div class='file-chip'>"
            f"<span class='ext-pill {pill_cls}'>{ext}</span>"
            f"<strong>{uploaded_name}</strong>"
            f"<span class='dotdot'>⋯</span>"
            f"</div>", unsafe_allow_html=True
        )
    st.markdown("<div class='upload-hint'>Drag and drop a <strong>PowerPoint</strong> or <strong>e-book</strong> file here, or click to browse</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ====== Upload ======
if tab == "Upload":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Upload</div>", unsafe_allow_html=True)
    render_upload_panel(st.session_state.last_uploaded_name)

    up = st.file_uploader(" ", type=["pptx","pdf","docx"], accept_multiple_files=False, label_visibility="collapsed")
    if up:
        st.session_state.src_text = extract_text_from_upload(up)
        st.session_state.src_edit = st.session_state.src_text
        st.session_state.last_uploaded_name = up.name
        if st.session_state.src_text.startswith("[Could not parse"):
            st.error(st.session_state.src_text)
        else:
            st.success("Source parsed. You can move straight to Generate.")

    st.write("")
    st.caption("Optional: upload ADI/School logo (PNG/JPG)")
    st.markdown("<div class='dashed'>", unsafe_allow_html=True)
    logo = st.file_uploader("Logo", type=["png","jpg","jpeg"], accept_multiple_files=False, key="logo_up")
    if logo is not None:
        st.session_state.logo_bytes = logo.read()
        st.success("Logo updated.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ====== Setup ======
if tab == "Setup":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Setup</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,3])
    with c1:
        st.session_state.lesson = st.number_input("Lesson", min_value=1, max_value=50, value=st.session_state.lesson, step=1)
    with c2:
        st.session_state.week = st.number_input("Week", min_value=1, max_value=14, value=st.session_state.week, step=1)
    with c3:
        bloom_now = bloom_focus_for_week(st.session_state.week)
        st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom_now}", disabled=True)

    st.session_state.topic = st.text_input("Learning Objective / Topic (optional)",
                                           value=st.session_state.topic,
                                           placeholder="Identify key themes and arguments in the text")
    st.session_state.src_edit = st.text_area("Source (editable, from upload)", value=st.session_state.src_edit, height=180)

    st.write("**Bloom’s verbs (ADI Policy)**")
    st.caption("Grouped by policy tiers and week ranges")
    def bloom_row(title, verbs, active=False):
        st.markdown(f"<div class='{'row active' if active else 'row'}'>", unsafe_allow_html=True)
        chips = " ".join([f\"<span class='chip {('low' if title=='Low' else 'med' if title=='Medium' else 'high')}'>{v}</span>\" for v in verbs])
        st.markdown(f"<div class='chips'>{chips}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    bloom_row("Low", LOW_VERBS, active=(bloom_now=="Low"))
    bloom_row("Medium", MED_VERBS, active=(bloom_now=="Medium"))
    bloom_row("High", HIGH_VERBS, active=(bloom_now=="High"))
    st.markdown("</div>", unsafe_allow_html=True)

# ====== Generate ======
if tab == "Generate":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Create Questions & Activities</div>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns([1,1,1])
    with g1:
        st.session_state.q_total = st.number_input("Total questions (exact)", min_value=3, value=st.session_state.q_total, step=1)
    with g2:
        st.session_state.act_n = st.number_input("Activities (count)", min_value=1, value=st.session_state.act_n, step=1)
    with g3:
        st.session_state.act_dur = st.number_input("Activity duration (mins)", min_value=5, value=st.session_state.act_dur, step=5)

    if not st.session_state.src_edit or len(_sentences(st.session_state.src_edit)) < 12:
        st.markdown("<div class='warn'>Upload or paste a denser section (≈12+ good sentences). The generator only uses real sentences from your source.</div>", unsafe_allow_html=True)

    cL, cR = st.columns([1,1])
    with cL:
        if st.button("Create Questions", type="primary"):
            try:
                st.session_state.mcq_df = generate_mcqs_exact(
                    st.session_state.topic, st.session_state.src_edit,
                    int(st.session_state.q_total), st.session_state.week, st.session_state.lesson
                )
                st.success("MCQs generated.")
            except Exception as e:
                st.error(f"Couldn’t generate MCQs: {e}")
    with cR:
        if st.button("Create Activities"):
            try:
                bloom_now = bloom_focus_for_week(st.session_state.week)
                st.session_state.act_df = generate_activities(
                    int(st.session_state.act_n), int(st.session_state.act_dur), bloom_now,
                    st.session_state.topic, st.session_state.lesson, st.session_state.week, st.session_state.src_edit
                )
                st.success("Activities generated.")
            except Exception as e:
                st.error(f"Couldn’t generate activities: {e}")

    if "mcq_df" in st.session_state:
        st.write("**Preview — MCQs**")
        render_mcq_list(st.session_state.mcq_df)

    if "act_df" in st.session_state:
        st.write("**Preview — Activities**")
        for i, r in st.session_state.act_df.reset_index(drop=True).iterrows():
            with st.expander(f"{i+1}. {r.get('Title', 'Activity')}"):
                st.write(f"**Policy focus:** {r['Policy focus']}")
                st.write(f"**Objective:** {r['Objective']}")
                st.write(f"**Steps:** {r['Steps']}")
                st.write(f"**Materials:** {r['Materials']}")
                st.write(f"**Assessment:** {r['Assessment']}")
                st.write(f"**Duration:** {r['Duration (mins)']} mins")
    st.markdown("</div>", unsafe_allow_html=True)

# ====== Edit ======
if tab == "Edit":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Edit</div>", unsafe_allow_html=True)
    if "mcq_df" in st.session_state:
        st.session_state.mcq_df = st.data_editor(st.session_state.mcq_df, key="edit_mcq", use_container_width=True)
    else:
        st.info("No MCQs yet — generate them in the Generate tab.")
    st.write("")
    if "act_df" in st.session_state:
        st.session_state.act_df = st.data_editor(st.session_state.act_df, key="edit_act", use_container_width=True)
    else:
        st.info("No Activities yet — generate them in the Generate tab.")
    st.markdown("</div>", unsafe_allow_html=True)

# ====== Export ======
if tab == "Export":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Export</div>", unsafe_allow_html=True)
    if "mcq_df" in st.session_state:
        mcq_csv = st.session_state.mcq_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download MCQs (CSV)", mcq_csv, "mcqs.csv", "text/csv")
        if Document is not None:
            mcq_docx = export_mcqs_docx(st.session_state.mcq_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
            st.download_button("Download MCQs (Word)", mcq_docx, "mcqs.docx",
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.caption("Install python-docx to enable Word export.")
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
            st.caption("Install python-docx to enable Word export.")
    else:
        st.info("Generate Activities to enable downloads.")
    st.markdown("</div>", unsafe_allow_html=True)
