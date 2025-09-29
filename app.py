
# app.py — ADI Builder (stable + Simple MCQ editor + UX tweaks)
# Run:
#   pip install streamlit pandas python-docx pdfplumber python-pptx
#   streamlit run app.py
import io, os, re, random, datetime as dt
from typing import List, Optional
import pandas as pd
import streamlit as st

# ----------------
# Page config & CSS
# ----------------
st.set_page_config(page_title="ADI Builder", page_icon="✅", layout="wide")

ADI_GREEN = "#245a34"; ADI_GREEN_DARK = "#1a4426"; ADI_GOLD = "#C8A85A"; ADI_STONE = "#f4f4f2"
CSS = f"""
<style>
:root {{ --adi-green:{ADI_GREEN}; --adi-green-dark:{ADI_GREEN_DARK}; --adi-gold:{ADI_GOLD}; --adi-stone:{ADI_STONE}; }}
html, body {{ background: var(--adi-stone) !important; }}
.block-container {{ max-width: 1200px; }}
.adi-ribbon {{ height:6px; background:linear-gradient(90deg,var(--adi-green),var(--adi-green-dark) 70%, var(--adi-gold)); border-radius:0 0 12px 12px; box-shadow:0 2px 8px rgba(0,0,0,.08); margin-bottom:8px; }}
.adi-title {{ font-size:2.0rem; font-weight:900; color:var(--adi-green); }}
.adi-sub {{ color:#4b5563; font-weight:600; font-size:1.02rem; letter-spacing:.2px; display:block; text-align:left; margin-top:.2rem; }}
.adi-card {{ background:#fff; border:1px solid rgba(0,0,0,.06); border-radius:20px; padding:20px; box-shadow:0 8px 24px rgba(10,24,18,.08); }}
.adi-section {{ border-top:3px solid var(--adi-gold); margin:8px 0 16px; box-shadow:0 -1px 0 rgba(0,0,0,.02) inset; }}

/* Radios as pill look */
.stRadio > div[role="radiogroup"] {{ display:flex; gap:10px; flex-wrap:wrap; }}
.stRadio [role="radiogroup"] > div label {{ border:2px solid var(--adi-green); border-radius:999px; padding:8px 14px; font-weight:800; background:#fff; color:#1f2937; }}
.stRadio [role="radiogroup"] > div[aria-checked="true"] label {{ background:#f7faf8; box-shadow:inset 0 0 0 3px var(--adi-gold); }}

/* Policy pills */
.pills {{ display:flex; gap:.5rem; flex-wrap:wrap; margin:.25rem 0 .5rem; }}
.pill {{ background:#fff;border:2px solid rgba(0,0,0,.08);padding:.35rem .7rem;border-radius:999px;font-weight:800; }}
.pill.current {{ border-color:var(--adi-gold); box-shadow:inset 0 0 0 3px var(--adi-gold); }}
.pill.match {{ background:#e8f5ee; border-color:#1f7a4c; }}
.pill.mismatch {{ background:#fff7ed; border-color:#fed7aa; }}
.badge-ok,.badge-warn{{display:inline-flex;align-items:center;font-weight:800;border-radius:10px;padding:.3rem .55rem;border:1px solid transparent;}}
.badge-ok{{background:#e8f5ee;color:#14532d;border-color:#86efac;}}
.badge-warn{{background:#fff7ed;color:#7c2d12;border-color:#fdba74;}}

/* Buttons */
.stButton > button, .stDownloadButton > button[kind="primary"], .stButton > button[kind="primary"] {{
  background: var(--adi-green) !important; border-color: var(--adi-green) !important; color: #fff !important;
}}
.stButton > button:hover, .stDownloadButton > button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {{
  background: var(--adi-green-dark) !important; border-color: var(--adi-green-dark) !important;
}}
.stButton > button:focus{{ box-shadow:0 0 0 3px rgba(36,90,52,.25) !important; }}

/* Slider thumb & track */
[data-testid="stSlider"] [role="slider"]{{ background: var(--adi-green) !important; border:2px solid var(--adi-green) !important; }}
[data-testid="stSlider"] div[data-baseweb="slider"] > div > div:nth-child(3){{ background: var(--adi-green) !important; }}
[data-testid="stSlider"] div[data-baseweb="slider"] > div > div:nth-child(2){{ background: rgba(36,90,52,.15) !important; }}

/* Verbs chips */
[data-testid="stMultiSelect"] [data-baseweb="tag"]{{ background:#e8f5ee !important; color:#1a3d2f !important; border:2px solid var(--adi-green) !important; border-radius:999px !important; font-weight:700 !important; }}
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg{{ fill: var(--adi-green) !important; color: var(--adi-green) !important; }}

/* Data editor: compact input padding for options */
[data-testid="stDataEditor"] td div[data-baseweb="input"] {{ padding: 4px 8px; }}

/* Sticky headers in editor */
[data-testid="stDataEditor"] thead th {{
  position: sticky; top: 0; background: #ffffff; z-index: 2;
  box-shadow: 0 1px 0 rgba(0,0,0,.06);
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<div class='adi-ribbon'></div>", unsafe_allow_html=True)

# --------------
# Header
# --------------
c1,c2 = st.columns([1,6], vertical_alignment="center")
with c1:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=120)
    else:
        st.markdown("**ADI**")
with c2:
    st.markdown("<div class='adi-title'>ADI Builder</div>", unsafe_allow_html=True)
    st.markdown("<div class='adi-sub'>Clean ADI look · Pill radios · Policy pills · Verb picker</div>", unsafe_allow_html=True)

# --------------
# Constants & helpers
# --------------
BLOOM_LEVELS = ["Remember","Understand","Apply","Analyze","Evaluate","Create"]
BLOOM_TIER = {"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}
BLOOM_VERBS = {
    "Remember": ["define","list","recall","identify","label","name","state","match","recognize","outline","select","repeat"],
    "Understand": ["explain","summarize","classify","describe","discuss","interpret","paraphrase","compare","illustrate","infer"],
    "Apply": ["apply","demonstrate","execute","implement","solve","use","calculate","perform","simulate","carry out"],
    "Analyze": ["analyze","differentiate","organize","attribute","deconstruct","compare/contrast","examine","test","investigate"],
    "Evaluate": ["evaluate","argue","assess","defend","judge","justify","critique","recommend","prioritize","appraise"],
    "Create": ["create","design","compose","construct","develop","plan","produce","propose","assemble","formulate"],
}

def policy_tier(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

def weighted_bloom_sequence(selected:str, n:int, rng:random.Random):
    idx=BLOOM_LEVELS.index(selected); weights=[]
    for i in range(len(BLOOM_LEVELS)):
        dist=abs(i-idx); weights.append({0:5,1:3,2:2,3:1}[min(dist,3)])
    seq=[]
    for _ in range(n):
        x=rng.uniform(0,sum(weights)); acc=0
        for lv,w in zip(BLOOM_LEVELS,weights):
            acc+=w
            if x<=acc: seq.append(lv); break
    return seq

# Optional parsers — degrade gracefully if libs are missing
def extract_pdf(b:bytes)->str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            return "\n".join([(p.extract_text() or "") for p in pdf.pages])
    except Exception:
        return ""

def extract_pptx(b:bytes)->str:
    try:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(b)); out=[]
        for s in prs.slides:
            for sh in s.shapes:
                if hasattr(sh,"text"): out.append(sh.text)
        return "\n".join(out)
    except Exception:
        return ""

def extract_docx(b:bytes)->str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(b))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""

# Generators
def offline_mcqs(src_text:str, blooms:list, verbs:List[str] , n:int):
    base=[s.strip() for s in re.split(r'[.\n]', src_text or "") if s.strip()] or ["This unit covers core concepts and applied practice."]
    if not verbs: verbs=["identify"]
    vcycle=(verbs*((n//max(1,len(verbs)))+1))[:n]
    rows=[]
    for i in range(n):
        b=blooms[i%len(blooms)] if blooms else "Understand"
        tier=BLOOM_TIER[b]
        fact=base[i%len(base)]
        v=vcycle[i].capitalize()
        stem=f"{v} the MOST appropriate statement about: {fact}"
        opts=[f"A) A correct point about {fact}.",
              f"B) An incorrect detail about {fact}.",
              f"C) Another incorrect detail about {fact}.",
              f"D) A distractor unrelated to {fact}."]
        answer="A"
        rows.append({"Bloom":b,"Tier":tier,"Q#":i+1,"Question":stem,"Option A":opts[0],"Option B":opts[1],"Option C":opts[2],"Option D":opts[3],"Answer":answer,"Explanation":f"Verb focus: {v} · Tier: {tier}"})
    return pd.DataFrame(rows, columns=["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"])

def build_activities(src_text:str, blooms:List[str], verbs:List[str], duration:int, diff:str, n:int=3)->List[str]:
    base=[s.strip() for s in re.split(r'[.\n]', src_text or "") if s.strip()] or ["today's topic"]
    vcycle=(verbs*((n//max(1,len(verbs)))+1))[:n] if verbs else ["discuss"]*n
    acts=[]
    for i in range(n):
        lv=blooms[i%len(blooms)] if blooms else "Understand"; vt=vcycle[i].capitalize(); topic=base[i%len(base)]
        if lv in ("Evaluate","Create"):
            prompt=f"{vt} and present a structured solution/prototype for: {topic}."
        elif lv in ("Apply","Analyze"):
            prompt=f"{vt} and demonstrate/apportion key components of: {topic}."
        else:
            prompt=f"{vt} and summarize the core idea of: {topic}."
        acts.append(f"[{duration} min] {prompt} ({diff.lower()})")
    return acts

def to_gift(df:pd.DataFrame)->str:
    out=[]
    for _,r in df.iterrows():
        q=str(r.get("Question","")).replace("\n"," ")
        opts=[r.get("Option A",""),r.get("Option B",""),r.get("Option C",""),r.get("Option D","")]
        ans_letter = str(r.get("Answer","A")).strip().upper()
        if ans_letter not in "ABCD": ans_letter="A"
        ans="ABCD".index(ans_letter)
        parts=[]
        for i,o in enumerate(opts):
            s=str(o).replace("}","\\}")
            parts.append(("=" if i==ans else "~")+s)
        out.append("{"+q+"}{"+" ".join(parts)+"}")
    return "\n\n".join(out)

d
def export_activity_sheet_docx(activities:List[str], lesson:int, week:int, title:str="Activity Sheet")->Optional[bytes]:
    try:
        from docx import Document
        from docx.shared import Cm, Pt
    except Exception:
        return None
    doc = Document()
    # Page setup A4 portrait, margins 2 cm
    for s in doc.sections:
        s.page_height = Cm(29.7)
        s.page_width = Cm(21.0)
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2.0)
    # Styles
    try:
        doc.styles['Normal'].font.name = 'Calibri'
        doc.styles['Normal'].font.size = Pt(12)
    except Exception:
        pass
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"Lesson {lesson} · Week {week}")
    hdr = doc.sections[0].header.paragraphs[0]
    hdr.text = f"{title} — Lesson {lesson} · Week {week}"
    # Student line
    p = doc.add_paragraph()
    p.add_run("Student name: ").bold = True
    p.add_run("_______________________________    ")
    p.add_run("ID: ").bold = True
    p.add_run("______________")
    doc.add_paragraph(" ").add_run()
    if activities:
        doc.add_heading("Activities", level=2)
        for i, a in enumerate(activities, start=1):
            doc.add_paragraph(f"{i}. [  ]  {a}")
    else:
        doc.add_paragraph("No activities available. Generate activities in the Generate tab.")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_mcq_paper_docx(df:pd.DataFrame, lesson:int, week:int, title:str="MCQ Paper")->Optional[bytes]:
    try:
        from docx import Document
        from docx.shared import Cm, Pt
    except Exception:
        return None
    if df is None or df.empty:
        return None
    doc = Document()
    for s in doc.sections:
        s.page_height = Cm(29.7)
        s.page_width = Cm(21.0)
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2.0)
    try:
        doc.styles['Normal'].font.name = 'Calibri'
        doc.styles['Normal'].font.size = Pt(12)
    except Exception:
        pass
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"Lesson {lesson} · Week {week}")
    hdr = doc.sections[0].header.paragraphs[0]
    hdr.text = f"{title} — Lesson {lesson} · Week {week}"
    # Student info
    p = doc.add_paragraph()
    p.add_run("Student name: ").bold = True
    p.add_run("_______________________________    ")
    p.add_run("ID: ").bold = True
    p.add_run("______________")
    doc.add_paragraph(" ").add_run()
    # Render questions cleanly (no Bloom/Tier columns)
    for _, r in df.iterrows():
        qn = int(r.get("Q#", 0)) if pd.notna(r.get("Q#")) else None
        stem = str(r.get("Question","")).strip()
        doc.add_paragraph(f"{qn}. {stem}" if qn else stem)
        def clean(o):
            s = str(o or "")
            return s[3:].strip() if s[:3].upper().startswith(("A) ","B) ","C) ","D) ")) else s
        A = clean(r.get("Option A","")); B = clean(r.get("Option B",""))
        C = clean(r.get("Option C","")); D = clean(r.get("Option D",""))
        doc.add_paragraph(f"   A. {A}")
        doc.add_paragraph(f"   B. {B}")
        doc.add_paragraph(f"   C. {C}")
        doc.add_paragraph(f"   D. {D}")
        doc.add_paragraph(" ")  # spacing
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def export_answer_key_docx(df:pd.DataFrame, lesson:int, week:int, title:str="Answer Key")->Optional[bytes]:
    try:
        from docx import Document
        from docx.shared import Cm, Pt
    except Exception:
        return None
    if df is None or df.empty:
        return None
    doc = Document()
    for s in doc.sections:
        s.page_height = Cm(29.7)
        s.page_width = Cm(21.0)
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2.0)
    try:
        doc.styles['Normal'].font.name = 'Calibri'
        doc.styles['Normal'].font.size = Pt(12)
    except Exception:
        pass
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"Lesson {lesson} · Week {week}")
    tbl = doc.add_table(rows=1, cols=2)
    hdr = tbl.rows[0].cells
    hdr[0].text = "Q#"; hdr[1].text = "Answer"
    for _, r in df.iterrows():
        row = tbl.add_row().cells
        row[0].text = str(r.get("Q#",""))
        row[1].text = str(r.get("Answer",""))
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()
ef export_docx(df:pd.DataFrame, activities:List[str], lesson:int, week:int)->Optional[bytes]:
    try:
        from docx import Document
    except Exception:
        return None
    doc=Document(); doc.add_heading("ADI Builder Export",level=1)
    doc.add_paragraph(f"Lesson {lesson} · Week {week}")
    if df is not None and not df.empty:
        doc.add_heading("MCQs",level=2)
        tbl=doc.add_table(rows=1,cols=9); hdr=tbl.rows[0].cells
        for i,c in enumerate(["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer"]): hdr[i].text=c
        for _,r in df.iterrows():
            row=tbl.add_row().cells
            vals=[r.get("Bloom",""),r.get("Tier",""),str(r.get("Q#","")),r.get("Question",""),
                  r.get("Option A",""),r.get("Option B",""),r.get("Option C",""),r.get("Option D",""),str(r.get("Answer",""))]
            for i,v in enumerate(vals): row[i].text=str(v)
    if activities:
        doc.add_heading("Activities",level=2)
        for i,a in enumerate(activities, start=1): doc.add_paragraph(f"{i}. {a}")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()


# =========================
# Revision helpers (lightweight, offline)
# =========================
STOPWORDS = set("""a an and are as at be by for from has have if in into is it its of on or such
that the their then there these this those to was were will with within without over under about across
""".split())

def _tokenize_words(text:str):
    return re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())

def extract_keywords(text:str, topk:int=15):
    freq = {}
    for w in _tokenize_words(text):
        if w in STOPWORDS or len(w)<3: continue
        freq[w] = freq.get(w,0)+1
    return [w for w,_ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:topk]]

def summarize_sentences(text:str, k:int=8):
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sents: return []
    freq = {}
    for w in _tokenize_words(text):
        if w in STOPWORDS or len(w)<3: continue
        freq[w] = freq.get(w,0)+1
    scores = []
    for s in sents:
        score = sum(freq.get(w,0) for w in _tokenize_words(s))
        scores.append((score, s))
    scores.sort(reverse=True)
    picked = []
    used_idx = set()
    for _, s in scores:
        if len(picked)>=k: break
        picked.append(s)
    return picked

def split_text_by_week_markers(text:str):
    # Detect headings like "Week 1", "Wk 2", "Lesson 3" etc.
    pattern = re.compile(r"(week|wk|lesson)\s*(\d{1,2})", re.I)
    matches = list(pattern.finditer(text))
    if not matches: return {}
    spans = {}
    for i, m in enumerate(matches):
        wk = int(m.group(2))
        start = m.start()
        end = matches[i+1].start() if i+1<len(matches) else len(text)
        spans[wk] = text[start:end]
    return spans

def collect_weeks_text(full_text:str, start:int, end:int):
    if start>end: start,end = end,start
    spans = split_text_by_week_markers(full_text)
    if spans:
        chunks = [spans[w] for w in range(start, end+1) if w in spans]
        return "\n".join(chunks)
    # Fallback: approximate by slicing the text into 14 equal parts
    total_weeks = 14
    n = len(full_text)
    def pos(w): return int((w-1)/total_weeks * n)
    s = pos(start); e = pos(end+1) if end<total_weeks else n
    return full_text[s:e]

def build_revision_pack(full_text:str, weeks_range:tuple, level_hint:str, verbs:list, mcq_count:int=10, duration:int=20, diff:str="Medium"):
    start,end = weeks_range
    rng_text = collect_weeks_text(full_text or "", start, end)
    if not rng_text.strip():
        rng_text = full_text or "No source text available; please upload an e-book or paste text."
    summary = summarize_sentences(rng_text, k=8)
    keywords = extract_keywords(rng_text, topk=15)

    # MCQs: align Bloom weighting with policy implied tier of mid-week in range
    mid = (start+end)//2
    implied_tier = policy_tier(mid)
    # pick a reasonable focal level from tier
    level_from_tier = {"Low":"Understand","Medium":"Apply","High":"Evaluate"}.get(implied_tier, level_hint or "Understand")
    rng = random.Random(mid*37 + mcq_count)
    blooms = weighted_bloom_sequence(level_from_tier, mcq_count, rng)
    df = offline_mcqs(rng_text, blooms, verbs or BLOOM_VERBS.get(level_from_tier, [])[:6], mcq_count)

    practices = build_activities(rng_text, blooms[:3] or [level_from_tier], verbs or BLOOM_VERBS.get(level_from_tier, [])[:6], duration, diff, n=3)
    return {"summary":summary, "keywords":keywords, "mcqs":df, "practices":practices, "tier":implied_tier, "focus":level_from_tier}

def export_revision_docx(title:str, pack:dict):
    try:
        from docx import Document
    except Exception:
        return None
    doc = Document()
    doc.add_heading(title, level=1)
    if pack.get("summary"):
        doc.add_heading("Summary", level=2)
        for s in pack["summary"]:
            doc.add_paragraph("• " + s)
    if pack.get("keywords"):
        doc.add_heading("Key terms", level=2)
        p = doc.add_paragraph()
        p.add_run(", ".join(pack["keywords"]))
    if isinstance(pack.get("mcqs"), pd.DataFrame) and not pack["mcqs"].empty:
        doc.add_heading("Quick MCQs", level=2)
        tbl = doc.add_table(rows=1, cols=7)
        hdr = ["Q#", "Question", "A", "B", "C", "D", "Answer"]
        for i,h in enumerate(hdr): tbl.rows[0].cells[i].text = h
        for _,r in pack["mcqs"].iterrows():
            row = tbl.add_row().cells
            vals = [str(r.get("Q#","")), r.get("Question",""), r.get("Option A",""), r.get("Option B",""), r.get("Option C",""), r.get("Option D",""), str(r.get("Answer",""))]
            for i,v in enumerate(vals): row[i].text = str(v)
    if pack.get("practices"):
        doc.add_heading("Practice prompts", level=2)
        for i,a in enumerate(pack["practices"], start=1):
            doc.add_paragraph(f"{i}. {a}")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()
# ----------------
# Session defaults
# ----------------
if "mcq_df" not in st.session_state: st.session_state.mcq_df=pd.DataFrame(columns=["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"])
if "activities" not in st.session_state: st.session_state.activities=[]
if "src_text" not in st.session_state: st.session_state.src_text=""
if "verbs" not in st.session_state: st.session_state.verbs=[]

# ------
# Tabs
# ------
tabs=st.tabs(["① Upload","② Setup","③ Generate","④ Export","⑤ Revision"])

# ① Upload — material type + uploaded chip
with tabs[0]:
    st.markdown("<div class='adi-card' id='adi-upload'>", unsafe_allow_html=True)
    st.subheader("📤 Upload source"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    st.session_state.material_type = st.radio("Material type", ["Lesson plan","E-book","PowerPoint"],
                                              horizontal=True, index=0, key="material_type_radio")
    up=st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)", type=["pdf","pptx","docx"], key="upload_file")
    pasted=st.text_area("Or paste source text manually", height=180, placeholder="Paste any relevant lesson/topic text here…")

    text=""; uploaded_name=None; uploaded_size=0
    if up is not None:
        data=up.read(); uploaded_name=up.name; uploaded_size=len(data); low=up.name.lower()
        if low.endswith(".pptx"): text=extract_pptx(data)
        elif low.endswith(".docx"): text=extract_docx(data)
        elif low.endswith(".pdf"): text=extract_pdf(data)
        st.caption(f"Selected: {up.name}")
    if not text and pasted.strip(): text=pasted.strip()
    st.session_state.src_text=text
    st.caption(f"Characters loaded: {len(text)}")

    if uploaded_name:
        kbytes = uploaded_size/1024
        st.markdown(
            f"<div style='margin-top:.5rem; display:inline-block; background:#e8f5ee; color:#14532d; "
            f"border:2px solid #1f7a4c; border-radius:999px; padding:.35rem .7rem; font-weight:800;'>"
            f"✓ Uploaded: {uploaded_name} · {kbytes:.0f} KB</div>",
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ② Setup — refined layout
with tabs[1]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("⚙️ Setup"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.8, 1.6])
    with col_left:
        st.markdown("##### Lesson")
        st.session_state.lesson = st.radio("Lesson", [1,2,3,4,5],
                                           index=st.session_state.get("lesson",1)-1, horizontal=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("##### Week  <span style='font-weight:400;opacity:.75'>ADI: 1–4 Low · 5–9 Medium · 10–14 High</span>", unsafe_allow_html=True)
        st.session_state.week = st.radio("Week", list(range(1,15)),
                                         index=st.session_state.get("week",1)-1, horizontal=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("##### Bloom’s Level")
        current_level = st.session_state.get("level","Understand")
        st.session_state.level = st.radio("Choose the focal level", BLOOM_LEVELS,
                                          index=BLOOM_LEVELS.index(current_level), horizontal=True)

    with col_right:
        st.markdown("##### Sequence")
        mode = st.radio("Mode", ["Auto by Focus","Target level(s)"], horizontal=True)
        count = st.slider("How many MCQs?", 4, 30, st.session_state.get("count_auto", 10), 1)

        if mode == "Target level(s)":
            sel = st.multiselect("Target level(s)", BLOOM_LEVELS, default=["Understand","Apply","Analyze"])
            sel = sel or ["Understand"]
        else:
            sel = None

        if sel is None:
            rng = random.Random(int(st.session_state.week)*100 + int(st.session_state.lesson))
            blooms = weighted_bloom_sequence(st.session_state.level, count, rng)
        else:
            blooms = (sel * ((count // len(sel)) + 1))[:count]

        counts = {lv: blooms.count(lv) for lv in BLOOM_LEVELS}
        summary = "  ·  ".join([f"{lv} × {counts[lv]}" for lv in BLOOM_LEVELS if counts[lv]>0])
        st.caption("Sequence preview: " + (summary or "—"))

        required = policy_tier(int(st.session_state.week))
        selected_tier = BLOOM_TIER[st.session_state.level]
        p = {'Low':'pill','Medium':'pill','High':'pill'}
        p[required] += ' current'
        if selected_tier==required:
            p[selected_tier] += ' match'; badge = "<div class='badge-ok'>✓ ADI policy matched</div>"
        else:
            p[selected_tier] += ' mismatch'; badge = f"<div class='badge-warn'>Week requires {required}. Selected is {selected_tier}.</div>"
        st.markdown(f"<div class='pills'><span class='{p['Low']}'>Low</span><span class='{p['Medium']}'>Medium</span><span class='{p['High']}'>High</span></div>{badge}", unsafe_allow_html=True)

        st.session_state.blooms = blooms
        st.session_state.count_auto = count

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown("#### Choose 5–10 verbs")
    verbs_all = BLOOM_VERBS.get(st.session_state.level, [])
    if "verbs" not in st.session_state or not st.session_state.verbs:
        st.session_state.verbs = verbs_all[:5]
    st.session_state.verbs = st.multiselect("Pick verbs that fit your outcomes", options=verbs_all, default=st.session_state.verbs)
    if 5 <= len(st.session_state.verbs) <= 10:
        st.success("Verb count looks good ✅")
    else:
        st.warning(f"Select between 5 and 10 verbs. Currently: {len(st.session_state.verbs)}")
    st.caption("These verbs drive the MCQ stems and activity prompts.")
    st.markdown("</div>", unsafe_allow_html=True)

# ③ Generate — Simple/Advanced MCQ editor
with tabs[2]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("⚡️ Generate"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    src = st.session_state.src_text
    g1,g2,g3,g4 = st.columns([1,1,1,1])
    with g1: act_count=st.slider("Activities (per class)",1,4,2,1)
    with g2: act_diff=st.radio("Difficulty",["Low","Medium","High"], index=1, horizontal=True)
    with g3: duration=st.selectbox("Duration (mins)",[15,20,25,30,35,40,45,50,55,60], index=1)
    with g4:
        st.write(" ")
        # Renamed buttons (behavior unchanged)
        if st.button("⚡ Auto-fill MCQs"):
            st.session_state.mcq_df = offline_mcqs(src,
                st.session_state.get('blooms', ["Understand"]*8),
                st.session_state.verbs,
                len(st.session_state.get('blooms', [])) or 8
            )
        if st.button("🧩 Auto-fill Activities"):
            st.session_state.activities = build_activities(src,
                st.session_state.get('blooms', ["Understand"]*act_count),
                st.session_state.verbs,
                duration,
                act_diff,
                n=act_count
            )

    st.markdown("**MCQs (editable table)**")

    simple_mode = st.toggle("Simple mode", value=True, help="Hide advanced fields for a cleaner view.")
    st.caption("Simple mode — edit just **Question**, **A–D**, and **Correct**. Toggle off to see advanced fields.")

    # Ensure at least one editable row exists
    if st.session_state.mcq_df is None or st.session_state.mcq_df.empty:
        st.session_state.mcq_df = pd.DataFrame([{
            "Bloom":"", "Tier":"", "Q#": 1,
            "Question":"", "Option A":"", "Option B":"", "Option C":"", "Option D":"",
            "Answer":"A", "Explanation":""
        }])

    # Quick add-row button
    cols_add = st.columns([1,5])
    with cols_add[0]:
        if st.button("＋ Add MCQ", help="Insert an empty row at the end"):
            next_q = (int(st.session_state.mcq_df["Q#"].max()) + 1) if "Q#" in st.session_state.mcq_df and st.session_state.mcq_df["Q#"].notna().any() else 1
            new_row = pd.DataFrame([{
                "Bloom":"", "Tier":"", "Q#": next_q,
                "Question":"", "Option A":"", "Option B":"", "Option C":"", "Option D":"",
                "Answer":"A", "Explanation":""
            }])
            st.session_state.mcq_df = pd.concat([st.session_state.mcq_df, new_row], ignore_index=True)

    simple_cols   = ["Question", "Option A", "Option B", "Option C", "Option D", "Answer"]
    advanced_cols = ["Bloom", "Tier", "Q#", "Explanation"]
    column_order = simple_cols + ([] if simple_mode else advanced_cols)
    disabled_cols = ["Bloom", "Tier", "Q#"]  # read-only

    config = {
        "Question":  st.column_config.TextColumn("Question", width="large", help="Write the stem here."),
        "Option A":  st.column_config.TextColumn("A", width=220),
        "Option B":  st.column_config.TextColumn("B", width=220),
        "Option C":  st.column_config.TextColumn("C", width=220),
        "Option D":  st.column_config.TextColumn("D", width=220),
        "Answer":    st.column_config.SelectboxColumn("Correct", options=["A","B","C","D"], default="A", width=110),
        "Explanation": st.column_config.TextColumn("Explanation (optional)", width="large"),
        "Bloom":     st.column_config.TextColumn("Bloom (auto)"),
        "Tier":      st.column_config.TextColumn("Tier (auto)"),
        "Q#":        st.column_config.NumberColumn("Q#", format="%d", step=1),
    }

    st.session_state.mcq_df = st.data_editor(
        st.session_state.mcq_df,
        column_config=config,
        column_order=column_order,
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="mcq_editor_simple"
    )

    # Lightweight validation hint
    missing = []
    for i, r in st.session_state.mcq_df.iterrows():
        if not str(r.get("Question","")).strip():
            missing.append(i+1)
        else:
            for k in ["Option A","Option B","Option C","Option D"]:
                if not str(r.get(k,"")).strip():
                    missing.append(i+1); break

    if missing:
        st.caption(f"⚠️ Incomplete rows: {sorted(set(missing))}. Add a question and all options.")
    else:
        st.caption("✅ Table looks good.")

    st.markdown("**Activities (editable)**")
    acts_text="\n".join(st.session_state.activities)
    acts_text = st.text_area("One per line", value=acts_text, height=140, key="acts_text")
    st.session_state.activities = [a.strip() for a in acts_text.split("\n") if a.strip()]
    st.markdown("</div>", unsafe_allow_html=True)

# ④ Export — Word + GIFT
with tabs[3]:
    st.subheader("📦 Export")
    st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    df = st.session_state.get("mcq_df")
    acts = st.session_state.get("activities", [])
    lesson = st.session_state.get("lesson", 1)
    week = st.session_state.get("week", 1)

    # Check docx availability
    try:
        from docx import Document  # noqa: F401
        docx_available = True
    except Exception:
        docx_available = False

    today = dt.date.today().strftime("%Y-%m-%d")
    base = f"ADI_Lesson{lesson}_Week{week}_{today}"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        act_bytes = export_activity_sheet_docx(acts, lesson, week) if docx_available else None
        st.download_button("⬇️ Activity Sheet (.docx)",
                           data=(act_bytes or b"placeholder"),
                           file_name=base + "_ActivitySheet.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           disabled=not docx_available or not acts,
                           help=("Install python-docx" if not docx_available else ("Ready to print" if acts else "Generate Activities first")))
    with c2:
        mcq_bytes = export_mcq_paper_docx(df, lesson, week) if docx_available else None
        st.download_button("⬇️ MCQ Paper (.docx)",
                           data=(mcq_bytes or b"placeholder"),
                           file_name=base + "_MCQPaper.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           disabled=not docx_available or (df is None or df.empty),
                           help=("Install python-docx" if not docx_available else ("Ready to print" if (df is not None and not df.empty) else "Generate MCQs first")))
    with c3:
        key_bytes = export_answer_key_docx(df, lesson, week) if docx_available else None
        st.download_button("⬇️ Answer Key (.docx)",
                           data=(key_bytes or b"placeholder"),
                           file_name=base + "_AnswerKey.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           disabled=not docx_available or (df is None or df.empty),
                           help=("Install python-docx" if not docx_available else ("Teacher copy" if (df is not None and not df.empty) else "Generate MCQs first")))
    with c4:
        gift_payload = to_gift(df) if (df is not None and not df.empty) else ""
        st.download_button("⬇️ Moodle GIFT (.gift)",
                           data=(gift_payload or "").encode("utf-8"),
                           file_name=base + ".gift", mime="text/plain",
                           disabled=not bool(gift_payload),
                           help="Import to Moodle question bank")

# ⑤ Revision — build revision packs for assessments
with tabs[4]:
    st.subheader("🧠 Revision packs")
    st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    full_text = st.session_state.get("src_text","")
    level_hint = st.session_state.get("level","Understand")
    verbs_pref = st.session_state.get("verbs", [])

    scheme = st.radio("Assessment scheme", ["3 tasks (A: 1–3, B: 4–7, C: 8–14)", "2 tasks (A: 1–7, B: 8–14)", "Custom"], horizontal=False, index=0)
    if scheme.startswith("3 tasks"):
        a_range = st.slider("Task A weeks", 1, 14, (1,3))
        b_range = st.slider("Task B weeks", 1, 14, (4,7))
        c_range = st.slider("Task C weeks", 1, 14, (8,14))
        ranges = [("Task A", a_range), ("Task B", b_range), ("Task C", c_range)]
    elif scheme.startswith("2 tasks"):
        a_range = st.slider("Task A weeks", 1, 14, (1,7))
        b_range = st.slider("Task B weeks", 1, 14, (8,14))
        ranges = [("Task A", a_range), ("Task B", b_range)]
    else:
        a_range = st.slider("Task A weeks", 1, 14, (1,3))
        b_range = st.slider("Task B weeks", 1, 14, (4,7))
        show_c = st.checkbox("Include Task C", value=True)
        if show_c:
            c_range = st.slider("Task C weeks", 1, 14, (8,14))
            ranges = [("Task A", a_range), ("Task B", b_range), ("Task C", c_range)]
        else:
            ranges = [("Task A", a_range), ("Task B", b_range)]

    mcq_count = st.slider("MCQs per pack", 6, 20, 10, 1)
    duration = st.selectbox("Activity duration (mins)", [15,20,25,30,35,40], index=1)
    diff = st.radio("Activity difficulty", ["Low","Medium","High"], index=1, horizontal=True)

    make_btn = st.button("Generate Revision Packs")

    if make_btn:
        packs = []
        for label, rng in ranges:
            pack = build_revision_pack(full_text, rng, level_hint, verbs_pref, mcq_count=mcq_count, duration=duration, diff=diff)
            packs.append((label, rng, pack))

        st.success("Revision packs generated. Scroll to export each pack.")

        # Show and export each pack
        try:
            from docx import Document  # to enable docx export check
            docx_ok = True
        except Exception:
            docx_ok = False

        for label, rng, pack in packs:
            st.markdown(f"### {label} — Weeks {rng[0]}–{rng[1]}  ·  Tier: **{pack['tier']}**  ·  Focus: **{pack['focus']}**")
            with st.expander("Preview summary & key terms", expanded=False):
                if pack['summary']:
                    st.write("**Summary:**")
                    for s in pack['summary']:
                        st.write("- " + s)
                if pack['keywords']:
                    st.write("**Key terms:** " + ", ".join(pack['keywords']))
            st.write("**Quick MCQs (editable):**")
            key = f"rev_mcq_{label}"
            pack['mcqs'] = st.data_editor(pack['mcqs'], hide_index=True, num_rows="dynamic", use_container_width=True, key=key)

            # Export buttons
            docx_bytes = export_revision_docx(f"{label} Revision — Weeks {rng[0]}–{rng[1]}", pack) if docx_ok else None
            today = dt.date.today().strftime("%Y-%m-%d")
            base = f"{label.replace(' ','_')}_Weeks{rng[0]}-{rng[1]}_{today}"
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Download Word pack (.docx)",
                                   data=(docx_bytes or b"placeholder"),
                                   file_name=base + ".docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   disabled=not docx_ok,
                                   help=("Install python-docx" if not docx_ok else "Includes summary, key terms, MCQs & prompts"))
            with c2:
                gift_payload = to_gift(pack['mcqs']) if (isinstance(pack['mcqs'], pd.DataFrame) and not pack['mcqs'].empty) else ""
                st.download_button("⬇️ Download MCQs as GIFT (.gift)",
                                   data=(gift_payload or "").encode("utf-8"),
                                   file_name=base + ".gift",
                                   mime="text/plain",
                                   disabled=not bool(gift_payload),
                                   help="Import to Moodle question bank")
