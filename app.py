# app.py — ADI Learning Tracker (full app, English only)
# Features:
# - Upload: PDF / PPTX / DOCX
# - Strong cleaning (removes TOC/headers/page nos; fixes hyphen line breaks)
# - MCQs: sentence-only anchors + banned junk terms + guaranteed fallback
# - FIX: “... is not in list” handled by ensuring the correct option stays in the set
# - Activities: step extractor + safe fallback so it never fails
# - Exports: CSV / GIFT / DOCX (MCQs, Activities, Combined)
# - Polished Streamlit UI

import io, os, re, base64, random, unicodedata
from io import BytesIO
from typing import List
from difflib import SequenceMatcher

import pandas as pd
import streamlit as st

# ---------------- Streamlit setup ----------------
st.set_page_config(page_title="ADI Learning Tracker", page_icon="🧭", layout="centered")

# ---------------- Optional parsers ----------------
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

# Word export (python-docx)
try:
    from docx import Document
    from docx.shared import Pt, Inches
except Exception:
    Document = None
    Pt = Inches = None

# ---------------- CSS ----------------
CSS = r'''
<style>
:root{
  --adi:#245a34; --gold:#C8A85A; --stone:#f6f8f7; --ink:#0f172a; --muted:#667085; --border:#e7ecea; --shadow:0 10px 30px rgba(36,90,52,0.10);
}
*{font-family: ui-sans-serif,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial,"Noto Sans","Liberation Sans",sans-serif;}
html, body { background:var(--stone); }
main .block-container { padding-top:.75rem; max-width: 980px; }

.header-wrap{display:flex; align-items:center; gap:16px; margin-bottom:6px;}
.logo-wrap{display:flex; align-items:center; justify-content:center; width:240px;}
.h1{ font-size:30px; font-weight:900; color:var(--ink); margin:0 0 2px 0; letter-spacing:.2px; }
.small{ color:var(--muted); font-size:14px; }

.stTabs [role="tablist"]{ gap:.5rem; border-bottom:0; padding:0 .25rem .35rem .25rem; }
.stTabs [role="tab"]{
  position:relative; padding:.65rem 1.2rem; border-radius:14px 14px 0 0;
  font-weight:800; font-size:1.05rem; background:#ffffff;
  border:1px solid #e7ecea; border-bottom:none;
  box-shadow:0 6px 14px rgba(36,90,52,0.06);
}
.stTabs [role="tab"]:hover{ transform:translateY(-1px); box-shadow:0 10px 22px rgba(36,90,52,0.12); }
.stTabs [role="tab"] p{ margin:0; font-weight:800; color:#223047; display:flex; align-items:center; gap:.45rem; }
.stTabs [role="tab"][aria-selected="true"] p{ color:#245a34 !important; }
.stTabs [role="tab"][aria-selected="true"]{ border-color:#dfe7e3; box-shadow:0 12px 26px rgba(36,90,52,0.16); transform: translateY(-1px); }
.stTabs [role="tab"][aria-selected="true"]::after{
  content:""; position:absolute; left:10px; right:10px; bottom:-3px; height:4px; border-radius:999px;
  background:linear-gradient(90deg,#245a34,#C8A85A); box-shadow:0 2px 6px rgba(36,90,52,0.18);
}

.card{ background:#fff; border:1px solid var(--border); border-radius:18px; padding:18px; box-shadow:var(--shadow); margin-bottom:1rem; }
.h2{ font-size:19px; font-weight:800; color:var(--ink); margin:0 0 10px 0; }

label, .stMarkdown p + label{ font-weight:700 !important; color:#0f172a !important; margin-bottom:.35rem !important; }
.stTextInput > div > div, .stTextArea  > div > div, .stSelectbox > div > div{
  background:#fff !important; border:1.8px solid #e2e9e5 !important; border-radius:14px !important;
  box-shadow: 0 6px 16px rgba(36,90,52,0.06) !important;
}
.stTextInput > div > div:hover, .stTextArea  > div > div:hover, .stSelectbox > div > div:hover{
  border-color:#cfe1d7 !important; transform: translateY(-1px);
}
.stTextInput > div > div:focus-within, .stTextArea  > div > div:focus-within, .stSelectbox > div > div:focus-within{
  border-color:#245a34 !important; outline:3px solid rgba(36,90,52,0.28);
}

[data-testid="stFileUploaderDropzone"]{
  border:2.5px dashed #b9cfc4 !important; border-radius:18px !important; background:#fff !important;
  box-shadow:0 10px 26px rgba(36,90,52,0.08); transition:all .2s ease;
}
[data-testid="stFileUploaderDropzone"]:hover{
  border-color:#8fb8a3 !important; background:#fcfefd !important; outline:3px solid rgba(36,90,52,0.25);
  box-shadow: 0 14px 32px rgba(36,90,52,0.16);
}

.bloom-row{ display:flex; flex-wrap:wrap; gap:.5rem .6rem; margin:.35rem 0 .5rem; }
.chip{ display:inline-flex; align-items:center; justify-content:center; padding:6px 14px; border-radius:999px; font-size:13px; font-weight:800;
  box-shadow: 0 6px 16px rgba(0,0,0,0.10), inset 0 -2px 0 rgba(255,255,255,0.25); border:1px solid rgba(0,0,0,0.10); }
.chip.low{ background:#245a34; color:#fff; }
.chip.med{ background:#C8A85A; color:#111; }
.chip.high{ background:#333; color:#fff; }
.chip.dimmed{ opacity:0.55; }
.chip.hl{ outline:3px solid rgba(36,90,52,0.40); box-shadow:0 12px 32px rgba(36,90,52,0.20); }

.preview-card{ border:1px solid var(--border); border-radius:14px; padding:10px 12px; background:#fff; }
.mcq-item{ border-left:6px solid #e5e7eb; padding-left:10px; margin:8px 0; }
.mcq-low{   border-left-color:#245a34; }
.mcq-med{   border-left-color:#C8A85A; }
.mcq-high{  border-left-color:#333; }
.act-card{ border-left:6px solid #e5e7eb; border-radius:12px; padding:10px 12px; margin:10px 0; background:#fff; box-shadow:0 6px 16px rgba(36,90,52,0.06); }
.act-low{   border-left-color:#245a34; }
.act-med{   border-left-color:#C8A85A; }
.act-high{  border-left-color:#333; }

.export-grid{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:1rem; }
@media (max-width: 760px){ .export-grid{ grid-template-columns: 1fr; } }
.export-card{ background:#fff; border:1px solid var(--border); border-radius:16px; padding:14px; box-shadow:var(--shadow); }
.export-title{ font-weight:900; margin-bottom:.3rem; }
.export-note{ color:#6b7280; font-size:13px; margin-bottom:.6rem; }

.stButton>button, .stDownloadButton>button{
  background: linear-gradient(180deg, #2b6c40, #245a34) !important; color:#fff !important; border:1px solid #1f4e31 !important;
  font-weight:800 !important; border-radius:12px !important; padding:.55rem .9rem !important; box-shadow:0 8px 20px rgba(36,90,52,0.25) !important;
}
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)

# ---------------- Logo helper ----------------
_FALLBACK_LOGO_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAEAAAABABAAAAACqG3XIAAACMElEQVR4nM2WsW7TQBiFf6a0H5yq"
"zF0y2y5hG0c6zF4k1u5u9m3JHqz4dM7M9kP3C0k1bC0bC2A1vM9Y7mY0JgVv8uJbVYy0C4d6i3gC"
"9b4n2QxgE7iTnk9z9k9w4rH4g6YyKc3H5rW3q2m8Qw3wUuJKGkqQ8jJr1h3v9J0o9l6zQn9qV2mN"
"2l8c1mXi5Srgm2cG3wYQz7a1nS0CkqgkQz0o4Kx5l9yJc8KEMt8h2tqfWm0y8x2T8Jw0+o8S8b8"
"Jw3emcQ0n9Oq7dZrXw9kqgk5yA9iO1l0wB7mQxI3o3eV+o3oM2v8YUpbG6c6WcY8B6bZ9FfQLQ+"
"s5n8n4Zb3T3w9y7K0gN4d8c4sR4mxD9j8c+J6o9+3yCw1o0b7YpAAAAAElFTkSuQmCC")
def _load_logo_bytes() -> bytes:
    try:
        if os.path.exists("Logo.png"):
            with open("Logo.png", "rb") as f: return f.read()
    except Exception:
        pass
    return base64.b64decode(_FALLBACK_LOGO_B64)

# ---------------- Bloom verbs ----------------
LOW_VERBS  = ["define","identify","list","describe","recall","label"]
MED_VERBS  = ["apply","demonstrate","solve","illustrate","analyze","interpret","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","formulate","critique"]

def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# ---------------- Text cleanup helpers ----------------
def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r'(\w)-\s+(\w)', r'\1\2', s)   # fix hyphen line-break joins
    s = s.replace('–','-').replace('—','-')
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _clean_lines(text: str) -> str:
    def looks_like_toc_line(s: str) -> bool:
        if not s: return True
        s = s.strip()
        digits = sum(ch.isdigit() for ch in s)
        if digits >= max(5, int(0.30*len(s))): return True
        if re.search(r"\b(table of contents|chapter|lesson|module|key concepts|case studies|engineering data sheet|learner journal|structure of the e-book)\b", s, re.I):
            return True
        letters = [c for c in s if c.isalpha()]
        if letters and sum(c.isupper() for c in letters)/len(letters) > 0.70: return True
        if re.search(r"\s\d{1,4}(?:\s+\d{1,3})?$", s): return True
        if re.match(r"^\s*\d+(?:\.\d+)*\s+", s): return True
        return False
    lines = [ln.strip() for ln in (text or "").replace("\r","\n").split("\n")]
    lines = [ln for ln in lines if ln and not re.fullmatch(r"(page\s*\d+|\d+)", ln, flags=re.I)]
    out, seen = [], set()
    for ln in lines:
        if looks_like_toc_line(ln): continue
        k = ln[:96].lower()
        if k in seen: continue
        seen.add(k); out.append(ln)
    return "\n".join(out)[:8000]

VERB_RE = r"\b(is|are|was|were|be|being|been|has|have|can|should|may|include|includes|use|uses|measure|calculate|design|evaluate|apply|compare|justify|explain|describe|identify)\b"

def _sentences(text: str) -> List[str]:
    chunks = re.split(r"(?<=[.!?])\s+|[•\u2022\u2023\u25CF]|(?:\n\s*\-\s*)|(?:\n\s*\*\s*)", text or "")
    rough = [re.sub(r"\s+", " ", c).strip() for c in chunks if c and c.strip()]
    def good(s: str) -> bool:
        if not (40 <= len(s) <= 220): return False
        if len(s.split()) < 6: return False
        if sum(ch.isdigit() for ch in s) >= max(6, int(0.25*len(s))): return False
        if not re.search(VERB_RE, s, re.I): return False
        letters = [c for c in s if c.isalpha()]
        if letters and sum(c.isupper() for c in letters)/len(letters) > 0.55: return False
        return True
    return [s for s in rough if good(s)][:400]

def _near(a:str,b:str,th:float=0.90)->bool:
    return SequenceMatcher(a=a.lower(), b=b.lower()).ratio() >= th

def _uniq_keep(seq: List[str], key=lambda s: s.lower()):
    seen=set(); out=[]
    for s in seq:
        k=key(s)
        if k and k not in seen:
            seen.add(k); out.append(s)
    return out

def _quality_gate(options: List[str], ensure_first: bool = True) -> List[str]:
    """Filter to 4 decent sentences; optionally ensure first item survives."""
    ops = [re.sub(r"\s+"," ", o.strip()) for o in options if o and o.strip()]
    out = []
    for j,o in enumerate(ops):
        ok = True
        if len(o) < 40 or len(o) > 220: ok = False
        letters = [c for c in o if c.isalpha()]
        if letters and sum(c.isupper() for c in letters)/len(letters) > 0.55: ok = False
        if len(o.split()) < 6: ok = False
        if not re.search(VERB_RE, o, re.I): ok = False
        if j == 0 and ensure_first:
            ok = True  # force-keep the correct option
        if ok and not any(_near(o,p,0.96) for p in out):
            out.append(o)
        if len(out)==4: break
    # If still <4 and ensure_first, pad from the tail of ops
    k=0
    while len(out)<4 and k < len(ops):
        if ops[k] not in out:
            out.append(ops[k])
        k+=1
    return out[:4]

def _window(sentences: List[str], idx: int, w: int = 2) -> List[str]:
    L=max(0, idx-w); R=min(len(sentences), idx+w+1)
    return sentences[L:R]

# ---------------- Upload parsing ----------------
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
                return "[Could not parse PDF: install pdfplumber or PyPDF2]"
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

# ---------------- MCQ anchor policy ----------------
BAD_ANCHORS = {
    "rationale","engineering","data","sheet","concepts","theories",
    "case","studies","real","world","overview","introduction","chapter",
    "module","lesson","appendix","journal","glossary","summary"
}
STOP = set("a an the and or of for to in on with by from as at into over under than then is are was were be been being this that these those it its they them he she we you your our their not no".split())

def _keywords(text: str, top_n:int=24) -> List[str]:
    toks = []
    for w in re.split(r"[^A-Za-z0-9]+", text or ""):
        w = w.lower()
        if len(w) >= 4 and w not in BAD_ANCHORS and w not in STOP and not w.isdigit():
            toks.append(w)
    from collections import Counter
    common = Counter(toks).most_common(top_n*3)
    roots = []
    for w,_ in common:
        if all(not w.startswith(r[:5]) and not r.startswith(w[:5]) for r in roots):
            roots.append(w)
        if len(roots) >= top_n:
            break
    return roots

def _is_sentence_like(s: str) -> bool:
    if len(s.split()) < 8: return False
    if sum(c.isdigit() for c in s) >= 6: return False
    if not re.search(VERB_RE, s, re.I): return False
    letters = [c for c in s if c.isalpha()]
    if letters and sum(c.isupper() for c in letters)/len(letters) > 0.55: return False
    return True

def _has_context_neighbors(sents: List[str], idx: int) -> bool:
    neighbors = _window(sents, idx, 3)
    return sum(1 for x in neighbors if x and x != sents[idx] and _is_sentence_like(x)) >= 2

# ---------------- Activities: step extraction ----------------
STEP_LINE = re.compile(r"(?:^|\n)\s*(?:step\s*\d+\s*[:\-\.]|[0-9]{1,2}\.\s+|•\s+|\-\s+|—\s+)(.+)", re.I)
def extract_steps(src: str, min_steps=3, max_steps=7):
    rough = _normalize(src.replace("\r",""))
    hits = [m.group(1).strip() for m in STEP_LINE.finditer(rough)]
    if len(hits) < min_steps:
        parts = [p.strip() for p in re.split(r"[;•]", rough) if len(p.strip().split()) > 4]
        hits.extend(parts)
    uniq, seen = [], set()
    for h in hits:
        k = h.lower()
        if k not in seen:
            seen.add(k); uniq.append(h)
    return uniq[:max_steps]

# ---------------- Generators ----------------
def generate_mcqs_exact(topic: str, source: str, total_q: int, week: int, lesson: int = 1, mode: str = "Mixed") -> pd.DataFrame:
    if total_q < 1: raise ValueError("Total questions must be ≥ 1.")
    ctx = (topic or "").strip() or f"Lesson {lesson} • Week {week}"

    # Clean + split; sentence-like only
    sents = [s for s in _sentences(_clean_lines(source or "")) if _is_sentence_like(s)]
    if len(sents) < 12:
        raise ValueError("Not enough usable sentences after trimming headings/TOC (need ~12+).")

    # Keywords only from real sentences; ban bad anchors
    keys = [k for k in _keywords(" ".join(sents), top_n=max(24, total_q*4)) if k not in BAD_ANCHORS]

    rows = []; rnd = random.Random(2025); made = 0; tiers = ["Low","Medium","High"]
    def tier_for_q(i):
        if mode == "All Low": return "Low"
        if mode == "All Medium": return "Medium"
        if mode == "All High": return "High"
        return tiers[i % 3]

    # Anchor-based path
    for k in keys:
        try:
            idx = next(i for i, s in enumerate(sents) if k in s.lower())
        except StopIteration:
            continue
        if not _has_context_neighbors(sents, idx):  # need neighbors for distractors
            continue
        correct = sents[idx].strip()
        neigh = [x for x in _window(sents, idx, 3) if x != correct and _is_sentence_like(x)]
        extra = [x for x in sents if x not in neigh and _is_sentence_like(x)]
        rnd.shuffle(extra)
        cand = neigh + extra[:8]

        options = _quality_gate([correct] + cand, ensure_first=True)
        # Safety: if filter accidentally dropped 'correct', reinsert it and trim
        if correct not in options:
            options = ([correct] + options)[:4]

        if len(options) < 4:
            continue

        tier = tier_for_q(made)
        stem = ("Which statement about **{k}** best fits *{ctx}*?"
                if tier=="Low" else
                "When applying **{k}** in *{ctx}*, which statement is most appropriate?"
                if tier=="Medium" else
                "Which option provides the strongest justification related to **{k}** in *{ctx}*?").format(k=k, ctx=ctx)

        rnd.shuffle(options)
        # Now safe: 'correct' is guaranteed in options
        ans = ["A","B","C","D"][options.index(correct)]
        rows.append({
            "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": stem,
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans, "Explanation": f"Anchored on a sentence mentioning '{k}'.",
            "Order": {"Low":1,"Medium":2,"High":3}[tier],
        })
        made += 1
        if made == total_q: break

    # Fallback path (guaranteed)
    if made < total_q:
        pool = [s for s in sents if 50 <= len(s) <= 200]
        pool = [s for s in pool if re.search(VERB_RE, s, re.I)]
        pool = [s for s in pool if ("," in s or ";" in s)] + [s for s in pool if ("," not in s and ";" not in s)]
        used=set(); i=0
        while made < total_q and i < len(pool):
            correct = pool[i]; i += 1
            if correct in used: continue
            dist=[]
            for cand in pool:
                if cand == correct: continue
                if SequenceMatcher(a=correct.lower(), b=cand.lower()).ratio() > 0.80: continue
                if abs(len(cand) - len(correct)) > 120: continue
                dist.append(cand)
                if len(dist) == 6: break
            options = _quality_gate([correct] + dist, ensure_first=True)
            if correct not in options:
                options = ([correct] + options)[:4]
            if len(options) < 4: continue
            rnd.shuffle(options)
            ans = ["A","B","C","D"][options.index(correct)]
            tier = tier_for_q(made)
            rows.append({
                "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
                "Question": f"Which statement best fits *{ctx}*?",
                "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
                "Answer": ans, "Explanation": "Fallback mode: contrasts between plausible sentences.",
                "Order": {"Low":1,"Medium":2,"High":3}[tier],
            })
            used.add(correct); made += 1

    if made == 0:
        raise ValueError("Still couldn’t form MCQs from this section. Try pasting a narrative paragraph (not bullets).")
    return pd.DataFrame(rows).reset_index(drop=True)

def generate_activities(count: int, duration: int, tier: str, topic: str, lesson: int, week: int, source: str = "", style: str = "Standard") -> pd.DataFrame:
    topic = (topic or "").strip()
    ctx = f"Lesson {lesson} • Week {week}" + (f" — {topic}" if topic else "")
    verbs = {"Low":LOW_VERBS,"Medium":MED_VERBS,"High":HIGH_VERBS}.get(tier, MED_VERBS)[:6]

    sents = [s for s in _sentences(_clean_lines(source or "")) if _is_sentence_like(s)]
    if len(sents) < 12:
        raise ValueError("Not enough source text to build activities (need ~12+ sentences of usable prose).")

    steps = extract_steps(source)
    rnd = random.Random(99)

    rows=[]
    for i in range(1, count + 1):
        v = verbs[(i - 1) % len(verbs)]
        t1=max(5,int(duration*0.2)); t2=max(10,int(duration*0.55)); t3=max(5,duration-(t1+t2))

        if len(steps) < 3:
            pool = [s for s in sents if 50 <= len(s) <= 220]
            rnd.shuffle(pool)
            a = pool[0] if pool else "review key ideas from the text"
            b = pool[1] if len(pool)>1 else "apply the concept to a small case"
            c = pool[2] if len(pool)>2 else "justify your decisions with evidence"
            step_line = f"Starter ({t1}m): {v.capitalize()} prior knowledge. Main ({t2}m): {a}; then {b}. Plenary ({t3}m): {c}."
        else:
            chosen = steps[:5]
            step_line = f"Starter ({t1}m): {v.capitalize()} prior knowledge. Main ({t2}m): " + "; ".join(chosen) + f". Plenary ({t3}m): Compare outputs; justify choices."

        style_note = ""
        if style == "Lab":          style_note = " Emphasize safety checks and hands-on measurement."
        elif style == "Group Task": style_note = " Organize into teams; assign roles for collaboration."
        elif style == "Reflection": style_note = " End with a short written reflection."

        rows.append({
            "Lesson": lesson, "Week": week, "Policy focus": tier,
            "Title": f"{ctx} — {tier} Activity {i}", "Tier": tier,
            "Objective": f"Students will {v} key ideas anchored to today’s source.",
            "Steps": step_line + style_note,
            "Materials": "Lesson PDF/PPT, mini-whiteboards, markers; timer",
            "Assessment": "Performance check aligned to the steps; brief justification.",
            "Duration (mins)": duration,
        })
    return pd.DataFrame(rows)

# ---------------- Exporters ----------------
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

def export_combined_docx(mcq_df: pd.DataFrame | None, act_df: pd.DataFrame | None, lesson:int, week:int, topic:str="")->bytes:
    if Document is None: return b""
    doc=Document(); sec=doc.sections[0]
    if Inches: sec.left_margin=Inches(0.8); sec.right_margin=Inches(0.8)
    title = f"Combined Lesson — Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else "")
    _docx_heading(doc, title, 0)
    doc.add_paragraph()
    if mcq_df is not None and len(mcq_df)>0:
        _docx_heading(doc, "Part A — Knowledge MCQs", 1)
        for i, r in mcq_df.reset_index(drop=True).iterrows():
            doc.add_paragraph(f"{i+1}. ({r['Tier']}) {r['Question']}")
            doc.add_paragraph(f"A. {r['Option A']}"); doc.add_paragraph(f"B. {r['Option B']}")
            doc.add_paragraph(f"C. {r['Option C']}"); doc.add_paragraph(f"D. {r['Option D']}")
            doc.add_paragraph()
        _docx_heading(doc, "Answer Key", 1)
        for i, r in mcq_df.reset_index(drop=True).iterrows():
            doc.add_paragraph(f"Q{i+1}: {r['Answer']}")
        doc.add_paragraph()
    if act_df is not None and len(act_df)>0:
        _docx_heading(doc, "Part B — Skills Activities", 1)
        for i,r in act_df.reset_index(drop=True).iterrows():
            _docx_heading(doc, r.get("Title", f"Activity {i+1}"), 2)
            doc.add_paragraph(f"Policy focus: {r.get('Policy focus','')}")
            doc.add_paragraph(f"Objective: {r.get('Objective','')}")
            doc.add_paragraph(f"Steps: {r.get('Steps','')}")
            doc.add_paragraph(f"Materials: {r.get('Materials','')}")
            doc.add_paragraph(f"Assessment: {r.get('Assessment','')}")
            dur = r.get('Duration (mins)', '')
            if dur != '': doc.add_paragraph(f"Duration: {dur} mins")
            doc.add_paragraph()
    bio=BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

_GIFT_ESCAPE = str.maketrans({"~": r"\~","=": r"\=","#": r"\#","{": r"\{","}": r"\}",":": r"\:","\n": r"\n"})
def _gift_escape(s:str)->str: return (s or "").translate(_GIFT_ESCAPE)

def export_mcqs_gift(df:pd.DataFrame, lesson:int, week:int, topic:str="")->str:
    lines=[]; title_prefix=f"Lesson {lesson} • Week {week}" + (f" • {topic}" if topic else "")
    for i,r in df.reset_index(drop=True).iterrows():
        qname=f"{title_prefix} — Q{i+1} ({r.get('Tier','')})"
        stem=_gift_escape(str(r.get("Question",""))).strip()
        opts=[str(r.get("Option A","")),str(r.get("Option B","")),str(r.get("Option C","")),str(r.get("Option D",""))]
        idx={"A":0,"B":1,"C":2,"D":3}.get(str(r.get("Answer","A")).strip().upper(),0)
        parts=[("="+_gift_escape(o)) if j==idx else ("~"+_gift_escape(o)) for j,o in enumerate(opts)]
        exp=str(r.get("Explanation",""))
        comment=f"#### {_gift_escape(exp)}" if exp else ""
        lines.append(f"::{_gift_escape(qname)}:: {stem} {{\n" + "\n".join(parts) + f"\n}} {comment}\n")
    return "\n".join(lines).strip()+"\n"

# ---------------- Sample text ----------------
SAMPLE_TEXT = (
    "Ohm’s Law states that the current through a conductor between two points is directly proportional "
    "to the voltage across the two points. The constant of proportionality is the resistance. "
    "Thus, if the voltage increases while resistance remains constant, the current increases proportionally. "
    "In practical circuits, components such as resistors limit current to protect devices. "
    "Measuring voltage requires connecting a voltmeter in parallel with the component. "
    "Measuring current requires placing an ammeter in series with the path. "
    "Power dissipated by a resistor equals voltage times current and also equals current squared times resistance. "
    "Designers choose resistor values to meet power and safety constraints. "
    "Tolerances specify the acceptable deviation from the nominal resistance. "
    "When components heat up, resistance may change, affecting current. "
    "Series resistances add, while parallel resistances reduce the total. "
    "A systematic approach records known quantities and applies V=IR to solve unknowns."
)

# ---------------- App state ----------------
st.session_state.setdefault("lesson", 1)
st.session_state.setdefault("week", 1)
st.session_state.setdefault("mcq_total", 10)
st.session_state.setdefault("mcq_mode", "Mixed")
st.session_state.setdefault("act_n", 1)
st.session_state.setdefault("act_dur", 30)
st.session_state.setdefault("act_style", "Standard")
st.session_state.setdefault("topic", "")
st.session_state.setdefault("logo_bytes", _load_logo_bytes())
st.session_state.setdefault("src_text", "")
st.session_state.setdefault("src_edit", "")

# ---------------- Header ----------------
st.markdown("<div class='header-wrap'>", unsafe_allow_html=True)
cols = st.columns([1.2, 4])
with cols[0]:
    if st.session_state.logo_bytes:
        b64 = base64.b64encode(st.session_state.logo_bytes).decode()
        st.markdown("<div class='logo-wrap'>", unsafe_allow_html=True)
        st.image(f"data:image/png;base64,{b64}", width=210)
        st.markdown("</div>", unsafe_allow_html=True)
with cols[1]:
    st.markdown("<div class='h1'>ADI Learning Tracker</div>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Transform lessons into measurable learning</div>", unsafe_allow_html=True)
st.divider()

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4 = st.tabs(["① 📂 Upload", "② ⚙️ Setup", "③ ✨ Generate", "④ 📤 Export"])

def progress_fraction()->float:
    steps = 0; total = 4
    if (st.session_state.get("src_edit") or "").strip(): steps += 1
    if len(_sentences(st.session_state.get("src_edit",""))) >= 12: steps += 1
    if ("mcq_df" in st.session_state) or ("act_df" in st.session_state): steps += 1
    if ("mcq_df" in st.session_state) or ("act_df" in st.session_state): steps += 1
    return steps/total

# ===== ① Upload =====
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Upload Lesson File</div>", unsafe_allow_html=True)
    st.caption("We’ll extract text from your lesson to build MCQs & activities.")
    up = st.file_uploader("Upload .pptx / .pdf / .docx", type=["pptx","pdf","docx"])
    if up:
        st.session_state.src_text = extract_text_from_upload(up)
        st.session_state.src_edit = st.session_state.src_text
        if st.session_state.src_text.startswith("[Could not parse"):
            st.error(st.session_state.src_text)
            st.info("Tip: If a PPTX fails, export it as PDF and upload the PDF.")
        else:
            st.success(f"File parsed: **{up.name}** ({up.type})")
            preview_lines = (st.session_state.src_text or "").split("\n")[:2]
            if any(preview_lines):
                st.caption("Preview:")
                st.code("\n".join(preview_lines), language="markdown")
    st.progress(progress_fraction())
    st.markdown("</div>", unsafe_allow_html=True)

# ===== ② Setup =====
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Setup</div>", unsafe_allow_html=True)

    st.markdown("<div class='step'><b>Step 1 — Choose Lesson & Week</b></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,2])
    with c1: st.session_state.lesson = st.selectbox("Lesson", [1,2,3,4], index=st.session_state.lesson-1)
    with c2: st.session_state.week   = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1)
    with c3: st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom_focus_for_week(st.session_state.week)}", disabled=True)
    _focus = bloom_focus_for_week(st.session_state.week)
    _cls = "low" if _focus=="Low" else ("med" if _focus=="Medium" else "high")
    st.markdown(f"<div class='bloom-row'><span class='chip {_cls} hl'>🎯 Focus {_focus}</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='separator'></div>", unsafe_allow_html=True)

    st.markdown("<div class='step'><b>Step 2 — Review Bloom’s Focus</b></div>", unsafe_allow_html=True)
    def bloom_row(label, verbs):
        cls  = "low" if label=="Low" else "med" if label=="Medium" else "high"
        hl   = " hl" if label==_focus else ""
        weeks = "1–4" if label=="Low" else "5–9" if label=="Medium" else "10–14"
        chips = " ".join([
            f"<span class='chip {cls}{hl}'>{v}</span>" if label==_focus else f"<span class='chip {cls} dimmed'>{v}</span>"
            for v in verbs
        ])
        st.markdown(f"**{label} (Weeks {weeks})**", unsafe_allow_html=True)
        st.markdown(f"<div class='bloom-row'>{chips}</div>", unsafe_allow_html=True)
    bloom_row("Low", LOW_VERBS); bloom_row("Medium", MED_VERBS); bloom_row("High", HIGH_VERBS)
    st.markdown("<div class='separator'></div>", unsafe_allow_html=True)

    st.markdown("<div class='step'><b>Step 3 — Learning Objective / Topic (optional)</b></div>", unsafe_allow_html=True)
    st.session_state.topic = st.text_input("Learning Objective / Topic", value=st.session_state.topic, placeholder="e.g., Understand Ohm’s Law and apply it to simple circuits")
    st.markdown("<div class='separator'></div>", unsafe_allow_html=True)

    st.markdown("<div class='step'><b>Step 4 — Paste/Edit Source Text</b></div>", unsafe_allow_html=True)
    csa, csb = st.columns([4,1])
    with csa:
        st.session_state.src_edit = st.text_area("Source (editable)", value=st.session_state.src_edit, height=180, placeholder="Add 1–2 short paragraphs (≈12+ sentences). Avoid bullet points.")
        txt = st.session_state.src_edit or ""
        sc = len(_sentences(txt)); ready = sc >= 12
        bullet_hit = ("•" in txt) or re.search(r"^\s*[-*]\s+", txt, re.M)
        msg = f"Detected **{sc}** sentence(s). " + ("Ready ✓" if ready else "Need **12+**.")
        st.caption(msg)
        if bullet_hit:
            st.info("Heads up: bullets were detected. Convert bullet points into full sentences for best results.")
    with csb:
        if st.button("Paste sample text"): st.session_state.src_edit = SAMPLE_TEXT; st.rerun()
        if st.button("Reset all"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
        st.caption("Quick actions")

    st.markdown("<div class='separator'></div>", unsafe_allow_html=True)

    st.markdown("<div class='step'><b>Step 5 — MCQ Setup</b></div>", unsafe_allow_html=True)
    choices = [5,10,20,30]
    default_idx = choices.index(st.session_state.mcq_total) if st.session_state.mcq_total in choices else 1
    st.session_state.mcq_total = st.radio("Number of MCQs", choices, index=default_idx, horizontal=True)
    st.session_state.mcq_mode = st.selectbox("MCQ distribution", ["Mixed","All Low","All Medium","All High"], index=["Mixed","All Low","All Medium","All High"].index(st.session_state.mcq_mode))

    st.markdown("<div class='separator'></div>", unsafe_allow_html=True)

    st.markdown("<div class='step'><b>Step 6 — Activity Setup</b></div>", unsafe_allow_html=True)
    colA, colB = st.columns([1,2])
    with colA:
        st.session_state.act_n = st.radio("Activities", [1,2,3], index=st.session_state.act_n-1, horizontal=True)
        st.session_state.act_style = st.selectbox("Activity style", ["Standard","Lab","Group Task","Reflection"], index=["Standard","Lab","Group Task","Reflection"].index(st.session_state.act_style))
    with colB:
        st.session_state.act_dur = st.slider("Duration per Activity (mins)", 10, 60, st.session_state.act_dur, 5)

    st.progress(progress_fraction())
    st.markdown("</div>", unsafe_allow_html=True)

# ===== ③ Generate =====
with tab3:
    sc = len(_sentences(st.session_state.get("src_edit","")))
    if sc < 12:
        st.info("Add at least 12 full sentences in **② Setup** to enable Generate.")
        st.progress(progress_fraction()); st.stop()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Generate Questions & Activities</div>", unsafe_allow_html=True)

    colQ, colA = st.columns([1,1])
    with colQ:
        if st.button("📝 Generate MCQs", use_container_width=True):
            with st.spinner("Generating MCQs…"):
                try:
                    st.session_state.mcq_df = generate_mcqs_exact(
                        st.session_state.topic, st.session_state.src_edit, int(st.session_state.mcq_total),
                        st.session_state.week, st.session_state.lesson, st.session_state.mcq_mode
                    )
                    st.success("MCQs generated.")
                except Exception as e:
                    st.error(f"Couldn’t generate MCQs: {e}")
    with colA:
        if st.button("🧩 Generate Activities", use_container_width=True):
            with st.spinner("Generating Activities…"):
                try:
                    focus = bloom_focus_for_week(st.session_state.week)
                    st.session_state.act_df = generate_activities(
                        int(st.session_state.act_n), int(st.session_state.act_dur), focus,
                        st.session_state.topic, st.session_state.lesson, st.session_state.week,
                        st.session_state.src_edit, st.session_state.act_style
                    )
                    st.success("Activities generated.")
                except Exception as e:
                    st.error(f"Couldn’t generate activities: {e}")

    show_answers = st.checkbox("Show answer key in preview", value=False)

    if "mcq_df" in st.session_state:
        st.write("**MCQs (preview)**")
        st.markdown("<div class='preview-card'>", unsafe_allow_html=True)
        for i,row in st.session_state.mcq_df.reset_index(drop=True).iterrows():
            cls = "mcq-low" if row["Tier"]=="Low" else ("mcq-med" if row["Tier"]=="Medium" else "mcq-high")
            ans = f" <i>(Answer: {row['Answer']})</i>" if show_answers else ""
            st.markdown(f"<div class='mcq-item {cls}'><b>{i+1}. {row['Tier']}</b> {row['Question']}{ans}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if "act_df" in st.session_state:
        st.write("**Activities (preview)**")
        for i,r in st.session_state.act_df.reset_index(drop=True).iterrows():
            tier = r.get("Policy focus","Medium")
            cls = "act-low" if tier=="Low" else ("act-med" if tier=="Medium" else "act-high")
            st.markdown(
                f"<div class='act-card {cls}'><b>{i+1}. {r.get('Title','Activity')}</b><br>"
                f"<span><b>Objective:</b> {r['Objective']}</span><br>"
                f"<span><b>Steps:</b> {r['Steps']}</span><br>"
                f"<span><b>Duration:</b> {r['Duration (mins)']} mins</span></div>",
                unsafe_allow_html=True
            )

    st.progress(progress_fraction())
    st.markdown("</div>", unsafe_allow_html=True)

# ===== ④ Export =====
with tab4:
    if "mcq_df" not in st.session_state and "act_df" not in st.session_state:
        st.info("Generate content in **③ Generate** to enable exports.")
        st.progress(progress_fraction()); st.stop()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Export</div>", unsafe_allow_html=True)
    st.markdown("<div class='export-grid'>", unsafe_allow_html=True)

    # MCQs exports
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>MCQs</div>", unsafe_allow_html=True)
    st.markdown("<div class='export-note'>Download your question set in multiple formats.</div>", unsafe_allow_html=True)
    if "mcq_df" in st.session_state:
        if st.download_button("Download MCQs (CSV)", st.session_state.mcq_df.to_csv(index=False).encode("utf-8"),
                              f"mcqs_l{st.session_state.lesson}_w{st.session_state.week}.csv", "text/csv"):
            st.toast("✅ MCQs CSV download started")
        gift_txt = export_mcqs_gift(st.session_state.mcq_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
        if st.download_button("Download MCQs (Moodle GIFT)", gift_txt.encode("utf-8"),
                              f"mcqs_l{st.session_state.lesson}_w{st.session_state.week}.gift", "text/plain"):
            st.toast("✅ MCQs GIFT download started")
        if Document:
            mcq_docx = export_mcqs_docx(st.session_state.mcq_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
            if st.download_button("Download MCQs (Word)", mcq_docx,
                                  f"mcqs_l{st.session_state.lesson}_w{st.session_state.week}.docx",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
                st.toast("✅ MCQs Word download started")
        else:
            st.caption("Install python-docx for Word export.")
    else:
        st.caption("Generate MCQs in ③ Generate to enable downloads.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Activities exports
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>Activities</div>", unsafe_allow_html=True)
    st.markdown("<div class='export-note'>Export practical activities aligned to Bloom’s focus.</div>", unsafe_allow_html=True)
    if "act_df" in st.session_state:
        if st.download_button("Download Activities (CSV)", st.session_state.act_df.to_csv(index=False).encode("utf-8"),
                              f"activities_l{st.session_state.lesson}_w{st.session_state.week}.csv", "text/csv"):
            st.toast("✅ Activities CSV download started")
        if Document:
            act_docx = export_acts_docx(st.session_state.act_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
            if st.download_button("Download Activities (Word)", act_docx,
                                  f"activities_l{st.session_state.lesson}_w{st.session_state.week}.docx",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
                st.toast("✅ Activities Word download started")
        else:
            st.caption("Install python-docx for Word export.")
    else:
        st.caption("Generate Activities in ③ Generate to enable downloads.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Combined lesson export
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>Combined Lesson (Word)</div>", unsafe_allow_html=True)
    st.markdown("<div class='export-note'>MCQs + Activities in a single Word file (ready to print).</div>", unsafe_allow_html=True)
    if Document:
        mcq_df = st.session_state.get('mcq_df') if 'mcq_df' in st.session_state else None
        act_df = st.session_state.get('act_df') if 'act_df' in st.session_state else None
        if (mcq_df is not None and len(mcq_df)>0) or (act_df is not None and len(act_df)>0):
            combined_docx = export_combined_docx(mcq_df, act_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
            if st.download_button("Download Combined Lesson (Word)", combined_docx,
                                  f"lesson_combined_l{st.session_state.lesson}_w{st.session_state.week}.docx",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
                st.toast("✅ Combined Lesson Word download started")
        else:
            st.caption("Generate MCQs and/or Activities in ③ Generate to enable this.")
    else:
        st.caption("Install python-docx for Combined Word export.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.progress(progress_fraction())
    st.markdown("</div>", unsafe_allow_html=True)
