# app.py — ADI Learning Tracker (stable, all fixes incl. MCQ de-dup across session)
# English-only • PDF/PPTX/DOCX input • MCQs & Activities • Print-friendly DOCX
# Exports: CSV / GIFT / Word / Combined Word

import io, os, re, base64, random, unicodedata
from io import BytesIO
from typing import List, Set
from difflib import SequenceMatcher

import pandas as pd
import streamlit as st

# ---------- Streamlit base ----------
st.set_page_config(page_title="ADI Learning Tracker", page_icon="🧭", layout="centered")

# ---------- Parsers ----------
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

# DOCX reader (separate from python-docx writer)
try:
    import docx  # reader
    DocxReader = docx.Document
except Exception:
    DocxReader = None

# PPTX
try:
    from pptx import Presentation
except Exception:
    Presentation = None

# Word export (writer)
try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
except Exception:
    Document = None
    Pt = Inches = RGBColor = None

# ---------- CSS ----------
CSS = r'''
<style>
:root{ --adi:#245a34; --gold:#C8A85A; --stone:#f6f8f7; --ink:#0f172a; --border:#e7ecea; --shadow:0 10px 30px rgba(36,90,52,0.10); }
*{font-family: ui-sans-serif,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif;}
main .block-container { padding-top:.75rem; max-width:980px; }
.header-wrap{display:flex; align-items:center; gap:16px; margin-bottom:6px;}
.logo-wrap{width:240px;}
.h1{ font-size:30px; font-weight:900; color:var(--ink); margin:0 0 2px 0; letter-spacing:.2px; }
.small{ color:#667085; font-size:14px; }
.stTabs [role="tablist"]{ gap:.5rem; padding:0 .25rem .35rem .25rem; border-bottom:0; }
.stTabs [role="tab"]{ position:relative; padding:.65rem 1.2rem; border-radius:14px 14px 0 0; font-weight:800; font-size:1.05rem; background:#fff;
  border:1px solid #e7ecea; border-bottom:none; box-shadow:0 6px 14px rgba(36,90,52,0.06); }
.stTabs [role="tab"] p{ margin:0; color:#223047; font-weight:800; display:flex; gap:.45rem; }
.stTabs [role="tab"][aria-selected="true"] p{ color:#245a34 !important; }
.stTabs [role="tab"][aria-selected="true"]{ border-color:#dfe7e3; box-shadow:0 12px 26px rgba(36,90,52,0.16); transform: translateY(-1px); }
.stTabs [role="tab"][aria-selected="true"]::after{ content:""; position:absolute; left:10px; right:10px; bottom:-3px; height:4px; border-radius:999px;
  background:linear-gradient(90deg,#245a34,#C8A85A); }
.card{ background:#fff; border:1px solid var(--border); border-radius:18px; padding:18px; box-shadow:var(--shadow); margin-bottom:1rem; }
.h2{ font size:19px; font-weight:800; color:var(--ink); margin:0 0 10px 0; }
.bloom-row{ display:flex; flex-wrap:wrap; gap:.5rem .6rem; margin:.35rem 0 .5rem; }
.chip{ padding:6px 14px; border-radius:999px; font-size:13px; font-weight:800; border:1px solid rgba(0,0,0,.08); box-shadow:0 6px 16px rgba(0,0,0,.06); }
.chip.low{background:#245a34;color:#fff;} .chip.med{background:#C8A85A;color:#111;} .chip.high{background:#333;color:#fff;}
.chip.dimmed{opacity:.55;} .chip.hl{ outline:3px solid rgba(36,90,52,0.35); }
.preview-card{ border:1px solid var(--border); border-radius:14px; padding:10px 12px; background:#fff; }
.mcq-item{ border-left:6px solid #e5e7eb; padding-left:10px; margin:10px 0; }
.mcq-low{border-left-color:#245a34;} .mcq-med{border-left-color:#C8A85A;} .mcq-high{border-left-color:#333;}
.act-card{ border-left:6px solid #e7e7e7; border-radius:12px; padding:10px 12px; margin:10px 0; background:#fff; box-shadow:0 6px 16px rgba(36,90,52,0.06); }
.act-low{border-left-color:#245a34;} .act-med{border-left-color:#C8A85A;} .act-high{border-left-color:#333;}
.export-grid{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:1rem; }
@media (max-width:760px){ .export-grid{ grid-template-columns:1fr; } }

/* Buttons: Generate + Download (ADI green) */
.stButton > button,
.stDownloadButton > button {
  background: linear-gradient(90deg, #245a34, #387a4b);
  color: #fff;
  border: 1px solid #1f4d2c;
  border-radius: 12px;
  font-weight: 800;
  box-shadow: 0 6px 16px rgba(36,90,52,.18);
}
.stButton > button:hover,
.stDownloadButton > button:hover { filter: brightness(1.05); transform: translateY(-1px); }
.stButton > button:active,
.stDownloadButton > button:active { filter: brightness(.95); transform: translateY(0); }
.stButton > button:disabled,
.stDownloadButton > button:disabled {
  background: #e6eae8 !important; color: #6b7280 !important; border-color: #d8e0dc !important; box-shadow: none !important;
}

/* Preview highlighting */
.mcq-stem { display:inline-block; background:#f1f6f3; padding:6px 8px; border-radius:10px; font-weight:800; margin-bottom:6px; }
.act-title { display:inline-block; background:#f1f6f3; padding:6px 8px; border-radius:10px; font-weight:800; }
.mcq-meta { font-size:.9rem; color:#475569; margin-top:2px; }
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Logo ----------
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

# ---------- Bloom ----------
LOW_VERBS  = ["define","identify","list","describe","recall","label"]
MED_VERBS  = ["apply","demonstrate","solve","illustrate","analyze","interpret","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","formulate","critique"]
def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# ---------- Helpers & filters ----------
VERB_RE = r"\b(is|are|was|were|be|being|been|has|have|can|should|may|include|includes|use|uses|measure|calculate|design|evaluate|apply|compare|justify|explain|describe|identify)\b"
BAD_ANCHORS = {"rationale","engineering","data","sheet","concepts","theories","case","studies","real","world","overview","introduction","chapter","module","lesson","appendix","journal","glossary","summary"}
STOP = set("a an the and or of for to in on with by from as at into over under than then is are was were be been being this that these those it its they them he she we you your our their not no".split())
STOP_EXTRA = {"will","ensuring","ensure","various","several","overall","general","saudi","arabia","vision","project’s","project-based","activity","exercise","diagram","figure"}
BLOCK_LINE_PHRASES = ["exercise","diagram","figure","glossary","learning outcomes","error! bookmark not defined","lesson","week"]

def _has_emoji(s: str) -> bool:
    return any(0x1F300 <= ord(ch) <= 0x1FAFF or 0x2600 <= ord(ch) <= 0x27BF for ch in s or "")

def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r'(\w)-\s+(\w)', r'\1\2', s)
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
    return "\n".join(out)[:16000]

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
    sents = [s for s in rough if good(s)]
    return sents[:180]

def _is_sentence_like(s: str) -> bool:
    if len(s.split()) < 8: return False
    if sum(c.isdigit() for c in s) >= 6: return False
    if not re.search(VERB_RE, s, re.I): return False
    letters = [c for c in s if c.isalpha()]
    if letters and sum(c.isupper() for c in letters)/len(letters) > 0.55: return False
    return True

def _is_clean_sentence(s: str) -> bool:
    if not _is_sentence_like(s): return False
    low = s.lower()
    if any(p in low for p in BLOCK_LINE_PHRASES): return False
    if _has_emoji(s): return False
    return True

def _near(a:str,b:str,th:float=0.90)->bool:
    return SequenceMatcher(a=a.lower(), b=b.lower()).ratio() >= th

# --- MCQ de-dup helpers (content-level) ---
def _norm_q(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()

def _q_signature(options: List[str]) -> str:
    # Order-independent signature of the option set
    return "||".join(sorted(_norm_q(o) for o in options))

# ---------- Option filter (fixed) ----------
def _quality_gate(options: List[str], ensure_first: bool = True) -> List[str]:
    ops = [re.sub(r"\s+"," ", o.strip()) for o in options if o and o.strip()]
    out: List[str] = []
    for j, o in enumerate(ops):
        low = o.lower()
        if any(p in low for p in BLOCK_LINE_PHRASES):
            continue
        if _has_emoji(o):
            continue
        if re.search(r"\bps\d+\b", low):
            continue

        ok = True
        if len(o) < 40 or len(o) > 220:
            ok = False
        letters = [c for c in o if c.isalpha()]
        if letters and (sum(1 for c in letters if c.isupper()) / len(letters)) > 0.55:
            ok = False
        if len(o.split()) < 6:
            ok = False
        if not re.search(VERB_RE, o, re.I):
            ok = False

        if j == 0 and ensure_first:
            ok = True

        if ok and not any(_near(o, p, 0.96) for p in out):
            out.append(o)
        if len(out) == 4:
            break

    k = 0
    while len(out) < 4 and k < len(ops):
        if ops[k] not in out and not _has_emoji(ops[k]) and not any(p in ops[k].lower() for p in BLOCK_LINE_PHRASES):
            out.append(ops[k])
        k += 1
    return out[:4]

# Ultra-compatible fallback
def _quality_gate_loose(options: List[str], ensure_first: bool = True) -> List[str]:
    ops = [re.sub(r"\s+"," ", o.strip()) for o in options if o and o.strip()]
    out: List[str] = []
    for j, o in enumerate(ops):
        if j == 0 and ensure_first:
            out.append(o); continue
        if _has_emoji(o): continue
        if len(o) < 25: continue
        if any(SequenceMatcher(a=o.lower(), b=p.lower()).ratio() >= 0.98 for p in out): continue
        out.append(o)
        if len(out) == 4: break
    k = 0
    while len(out) < 4 and k < len(ops):
        if ops[k] not in out: out.append(ops[k])
        k += 1
    return out[:4]

def _window(sentences: List[str], idx: int, w: int = 2) -> List[str]:
    L=max(0, idx-w); R=min(len(sentences), idx+w+1)
    return sentences[L:R]

# NEW: near-duplicate filter for MCQs (correct sentence variety)
def _too_similar(a: str, b: str, thr: float = 0.88) -> bool:
    return SequenceMatcher(a=(a or "").lower(), b=(b or "").lower()).ratio() >= thr

# ---------- Upload parsing ----------
def extract_text_from_upload(file)->str:
    if file is None: return ""
    name = (getattr(file, "name", "") or "").lower()
    try:
        if name.endswith(".pdf"):
            buf = file.read() if hasattr(file,"read") else file.getvalue()
            if fitz:
                doc = fitz.open(stream=buf, filetype="pdf")
                text = "\n".join((page.get_text("text") or "") for page in doc[:40])
                if len(text.strip()) < 200:
                    return "[Parsed 0 text — likely a scanned PDF. Export as a text PDF or paste a section into Step 4.]"
                return _clean_lines(text)
            if pdfplumber:
                pages=[]
                with pdfplumber.open(io.BytesIO(buf)) as pdf:
                    for p in pdf.pages[:40]:
                        pages.append(p.extract_text() or "")
                text = "\n".join(pages)
                if len(text.strip()) < 200:
                    return "[Parsed 0 text — likely a scanned PDF. Export as a text PDF or paste a section into Step 4.]"
                return _clean_lines(text)
            if PdfReader:
                reader = PdfReader(io.BytesIO(buf))
                text=""
                for pg in reader.pages[:40]:
                    text += (pg.extract_text() or "") + "\n"
                if len(text.strip()) < 200:
                    return "[Parsed 0 text — likely a scanned PDF. Export as a text PDF or paste a section into Step 4.]"
                return _clean_lines(text)
            return "[Could not parse PDF: install pymupdf or pdfplumber or PyPDF2]"
        if name.endswith(".docx") and DocxReader:
            doc = DocxReader(file)
            return _clean_lines("\n".join((p.text or "") for p in doc.paragraphs[:500]))
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(file)
            parts=[]
            for s in prs.slides[:100]:
                for shp in s.shapes:
                    if hasattr(shp,"text") and shp.text:
                        parts.append(shp.text)
                if getattr(s,"has_notes_slide",False) and getattr(s.notes_slide,"notes_text_frame",None):
                    parts.append(s.notes_slide.notes_text_frame.text or "")
            return _clean_lines("\n".join(parts))
        return "[Unsupported file type or missing parser]"
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ---------- Keyword miner ----------
def _keywords(text: str, top_n:int=24) -> List[str]:
    t = re.sub(r"[^A-Za-z0-9\s-]", " ", (text or "").lower())
    words = [w for w in t.split()
             if len(w) >= 4 and w not in STOP and w not in BAD_ANCHORS and w not in STOP_EXTRA and not w.isdigit()]
    from collections import Counter
    bigrams = [f"{a} {b}" for a,b in zip(words, words[1:]) if a not in STOP and b not in STOP]
    out = [w for w,_ in Counter(bigrams).most_common(top_n*2) if len(w.replace(" ","")) >= 8][:top_n]
    if len(out) < top_n:
        for w,_ in Counter(words).most_common(top_n*4):
            if len(w) >= 5 and w not in STOP_EXTRA and w not in out:
                out.append(w)
            if len(out) >= top_n: break
    return out

def _has_context_neighbors(sents: List[str], idx: int) -> bool:
    neighbors = _window(sents, idx, 3)
    return sum(1 for x in neighbors if x and x != sents[idx] and _is_sentence_like(x)) >= 2

# ---------- Noise cleaner ----------
def _strip_noise(s: str) -> str:
    if not s: return s
    s = re.sub(r"\s*\((?:PS|LO|CO)\d+(?:,\s*(?:PS|LO|CO)\d+)*\)\s*", " ", s)
    s = re.sub(r"\s*\([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*,\s*\d{4}\)\s*", " ", s)
    s = re.sub(r"\s+[o•\-]\s+", " ", s)
    s = re.sub(r"defence\s*systems", "defence systems", s, flags=re.I)
    s = re.sub(r"defence\s*personnel", "defence personnel", s, flags=re.I)
    return re.sub(r"\s{2,}", " ", s).strip()

# ---------- MCQ stem templates ----------
STEMS = {
    "Low":    ["Which statement is most accurate?",
               "Which sentence best reflects the idea?"],
    "Medium": ["Which statement is most appropriate?",
               "Which claim best applies?"],
    "High":   ["Which option provides the strongest justification?",
               "Which choice offers the best rationale?"],
}

# ---------- MCQs (Exact mode) ----------
def generate_mcqs_exact(topic: str, source: str, total_q: int, week: int, lesson: int = 1, mode: str = "Mixed") -> pd.DataFrame:
    if total_q < 1: raise ValueError("Total questions must be ≥ 1.")
    sents = [s for s in _sentences(_clean_lines(source or "")) if _is_sentence_like(s)]
    sents = [s for s in sents if not any(p in s.lower() for p in BLOCK_LINE_PHRASES)]
    if len(sents) < 12:
        raise ValueError("Not enough usable sentences after trimming headings/TOC (need ~12+).")
    keys = [k for k in _keywords(" ".join(sents), top_n=max(24, total_q*4)) if k not in BAD_ANCHORS]

    rows = []; rnd = random.Random(2025); made = 0; tiers = ["Low","Medium","High"]
    used_corrects: List[str] = []
    used_pool: Set[str] = set()   # prevent option reuse within set
    local_sigs: Set[str] = set()  # prevent repeated question content in this run

    def tier_for_q(i):
        if mode == "All Low": return "Low"
        if mode == "All Medium": return "Medium"
        if mode == "All High": return "High"
        return tiers[i % 3]

    for k in keys:
        try:
            idx = next(i for i, s in enumerate(sents) if k in s.lower())
        except StopIteration:
            continue
        if not _has_context_neighbors(sents, idx): continue
        correct = sents[idx].strip()

        if any(_too_similar(correct, u) for u in used_corrects):
            continue

        neigh = [x for x in _window(sents, idx, 3) if x != correct and _is_sentence_like(x)]
        extra = [x for x in sents if x not in neigh and _is_sentence_like(x)]
        rnd.shuffle(extra)
        cand = neigh + extra[:8]

        options = _quality_gate([correct] + cand, ensure_first=True)
        if len(options) < 4:
            options = _quality_gate_loose([correct] + cand, ensure_first=True)
        if correct not in options: options = ([correct] + options)[:4]
        if len(options) < 4: continue

        # De-dup at question-level (options as a set) and no option reuse
        if any(o in used_pool for o in options):
            continue
        sig = _q_signature(options)
        if sig in local_sigs or sig in st.session_state.get("seen_q_sigs", set()):
            continue

        tier = tier_for_q(made)
        stem = STEMS[tier][made % len(STEMS[tier])]
        stem = _strip_noise(stem)
        options = [_strip_noise(o) for o in options]
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(_strip_noise(correct))]

        rows.append({
            "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": stem,
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans, "Explanation": _strip_noise(f"Anchored on a sentence mentioning '{k}'."),
            "Order": {"Low":1,"Medium":2,"High":3}[tier],
        })
        used_corrects.append(correct)
        used_pool.update(options)
        local_sigs.add(sig)
        st.session_state.seen_q_sigs.add(sig)
        made += 1
        if made == total_q: break

    if made < total_q:
        pool = [s for s in sents if 50 <= len(s) <= 200]
        pool = [s for s in pool if ("," in s or ";" in s)] + [s for s in pool if ("," not in s and ";" not in s)]
        used=set(); i=0
        while made < total_q and i < len(pool):
            correct = pool[i]; i += 1
            if correct in used: continue
            if any(_too_similar(correct, u) for u in used_corrects): continue
            dist=[]
            for cand in pool:
                if cand == correct: continue
                if SequenceMatcher(a=correct.lower(), b=cand.lower()).ratio() > 0.80: continue
                if abs(len(cand) - len(correct)) > 120: continue
                dist.append(cand)
                if len(dist) == 6: break
            options = _quality_gate([correct] + dist, ensure_first=True)
            if len(options) < 4:
                options = _quality_gate_loose([correct] + dist, ensure_first=True)
            if correct not in options: options = ([correct] + options)[:4]
            if len(options) < 4: continue

            if any(o in used_pool for o in options):
                continue
            sig = _q_signature(options)
            if sig in local_sigs or sig in st.session_state.get("seen_q_sigs", set()):
                continue

            tier = tier_for_q(made)
            stem = STEMS[tier][made % len(STEMS[tier])]
            stem = _strip_noise(stem)
            options = [_strip_noise(o) for o in options]
            rnd.shuffle(options)
            ans = ["A","B","C","D"][options.index(_strip_noise(correct))]
            rows.append({
                "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
                "Question": stem,
                "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
                "Answer": ans, "Explanation": "Fallback mode: contrasts between plausible sentences.",
                "Order": {"Low":1,"Medium":2,"High":3}[tier],
            })
            used_corrects.append(correct)
            used_pool.update(options)
            local_sigs.add(sig)
            st.session_state.seen_q_sigs.add(sig)
            used.add(correct); made += 1

    if made == 0:
        raise ValueError("Still couldn’t form MCQs from this section. Paste a narrative paragraph (not bullets).")
    return pd.DataFrame(rows).reset_index(drop=True)

# ---------- MCQs (Safe mode) ----------
def _pick_distractors(pool: List[str], correct: str, want: int = 3) -> List[str]:
    out = []
    for cand in pool:
        if cand == correct: continue
        if abs(len(cand) - len(correct)) > 120: continue
        sim = SequenceMatcher(a=correct.lower(), b=cand.lower()).ratio()
        if 0.40 <= sim <= 0.85:
            out.append(cand)
        if len(out) == want: break
    i = 0
    while len(out) < want and i < len(pool):
        c = pool[i]; i += 1
        if c != correct and c not in out:
            out.append(c)
    return out[:want]

def generate_mcqs_safe(topic: str, source: str, total_q: int, week: int, lesson: int = 1, mode: str = "Mixed") -> pd.DataFrame:
    if total_q < 1: raise ValueError("Total questions must be ≥ 1.")
    raw_sents = _sentences(_clean_lines(source or ""))
    sents = [s for s in raw_sents if _is_clean_sentence(s)]
    if len(sents) < 6:
        extra=[]
        for s in raw_sents:
            extra.extend([p.strip() for p in s.split(";") if len(p.strip().split()) >= 6])
        sents = [s for s in (sents + extra) if _is_clean_sentence(s)]
    if len(sents) < 4:
        raise ValueError("Need at least 4 clean sentences. Paste a short narrative paragraph (no bullets).")

    rich = [s for s in sents if ("," in s or ";" in s)]
    plain = [s for s in sents if s not in rich]
    pool = rich + plain
    if len(pool) > 200:
        random.Random(2025).shuffle(pool)
        pool = pool[:200]

    tiers = ["Low","Medium","High"]
    def tier_for_q(i):
        if mode == "All Low": return "Low"
        if mode == "All Medium": return "Medium"
        if mode == "All High": return "High"
        return tiers[i % 3]

    rnd = random.Random(2025)
    rows = []; i = 0
    used_corrects: List[str] = []
    used_pool: Set[str] = set()
    local_sigs: Set[str] = set()
    stride = max(1, len(pool) // max(4, total_q))
    while len(rows) < total_q and i < len(pool):
        correct = pool[i]
        if any(_too_similar(correct, u) for u in used_corrects):
            i += stride; continue
        distractors = _pick_distractors(pool, correct, 3)
        options = _quality_gate([correct] + distractors, ensure_first=True)
        if len(options) < 4:
            options = _quality_gate_loose([correct] + distractors, ensure_first=True)
        if correct not in options: options = ([correct] + options)[:4]
        if len(options) < 4:
            i += stride; continue

        # De-dup checks BEFORE shuffle/answer calc
        if any(o in used_pool for o in options):
            i += stride; continue
        sig = _q_signature(options)
        if sig in local_sigs or sig in st.session_state.get("seen_q_sigs", set()):
            i += stride; continue

        tier = tier_for_q(len(rows))
        stem = STEMS[tier][len(rows) % len(STEMS[tier])]
        stem = _strip_noise(stem)
        options = [_strip_noise(o) for o in options]
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(_strip_noise(correct))]
        rows.append({
            "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": stem,
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans, "Explanation": "Safe Mode: contrasts between plausible sentences.",
            "Order": {"Low":1,"Medium":2,"High":3}[tier],
        })
        used_corrects.append(correct)
        used_pool.update(options)
        local_sigs.add(sig)
        st.session_state.seen_q_sigs.add(sig)
        i += stride

    j = 0
    while len(rows) < total_q and j < len(pool):
        correct = pool[j]; j += 1
        if any(_too_similar(correct, u) for u in used_corrects):
            continue
        distractors = _pick_distractors(pool, correct, 3)
        options = _quality_gate([correct] + distractors, ensure_first=True)
        if len(options) < 4:
            options = _quality_gate_loose([correct] + distractors, ensure_first=True)
        if correct not in options: options = ([correct] + options)[:4]
        if len(options) < 4: continue

        if any(o in used_pool for o in options):
            continue
        sig = _q_signature(options)
        if sig in local_sigs or sig in st.session_state.get("seen_q_sigs", set()):
            continue

        tier = tier_for_q(len(rows))
        stem = STEMS[tier][len(rows) % len(STEMS[tier])]
        stem = _strip_noise(stem)
        options = [_strip_noise(o) for o in options]
        random.shuffle(options)
        ans = ["A","B","C","D"][options.index(_strip_noise(correct))]
        rows.append({
            "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": stem,
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans, "Explanation": "Safe Mode (backfill).",
            "Order": {"Low":1,"Medium":2,"High":3}[tier],
        })
        used_corrects.append(correct)
        used_pool.update(options)
        local_sigs.add(sig)
        st.session_state.seen_q_sigs.add(sig)

    return pd.DataFrame(rows).reset_index(drop=True)

# ---------- Activities (sentence style; student-handout wording optional) ----------
def generate_activities(count: int, duration: int, tier: str, topic: str,
                        lesson: int, week: int, source: str = "", style: str = "Standard",
                        student: bool = False) -> pd.DataFrame:
    topic = (topic or "Project scope, WBS, risk register, stakeholders").strip()
    verbs = {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}.get(tier, MED_VERBS)
    _ = _strip_noise(_clean_lines(source or ""))

    t1 = max(5, int(duration*0.17)); t3 = max(8, int(duration*0.17)); t2 = max(10, duration - (t1+t3))
    subj = "You" if student else "Students"

    rows = []
    for i in range(1, count+1):
        v = verbs[(i-1) % len(verbs)]
        steps = [
            f"Starter ({t1}m). {subj} {v} prior knowledge using a short checklist for time, cost, quality, and security.",
            (
                f"Main ({t2}m). {subj} write a clear scope (what is in / out), sketch a level-2 WBS, "
                f"list risks with an owner and a response, and map stakeholders with a simple RACI."
            ),
            f"Plenary ({t3}m). Teams swap work, share one strength and one question, then justify one change."
        ]
        if style == "Lab": steps[1] += " Follow lab safety rules and verify each step."
        elif style == "Group Task": steps[1] += " Teams assign roles: Lead, Scribe, Risk Owner, Reviewer."
        elif style == "Reflection": steps[2] += " Each student writes a two-minute reflection."

        rows.append({
            "Lesson": lesson, "Week": week, "Policy focus": tier,
            "Title": f"{tier} Activity {i}",
            "Tier": tier,
            "Objective": f"{subj} will {v} key ideas anchored to {topic}.",
            "Steps": " ".join(steps),
            "Materials": "Brief handout, A3 paper, markers; timer.",
            "Assessment": "Rubric: scope clarity, WBS level-2, risks with owner/response, and RACI (each /3 → /12).",
            "Duration (mins)": duration
        })
    return pd.DataFrame(rows)

def generate_activities_safe(*args, **kwargs) -> pd.DataFrame:
    return generate_activities(*args, **kwargs)

# ---------- Export helpers ----------
def _docx_heading(doc, text, level=0):
    p=doc.add_paragraph(); r=p.add_run(text)
    if level==0: r.bold=True; r.font.size=Pt(20)
    elif level==1: r.bold=True; r.font.size=Pt(16)
    else: r.font.size=Pt(13)

def _set_doc_defaults(doc):
    try:
        doc.styles["Normal"].font.size = Pt(13)
        doc.styles["Normal"].paragraph_format.line_spacing = 1.25
    except Exception:
        pass

def _add_mcq_stem(doc, qnum: int, text: str, highlight: bool = True):
    p = doc.add_paragraph()
    r = p.add_run(f"Q{qnum}. {text}")
    r.bold = True
    r.font.size = Pt(14)
    if highlight and RGBColor is not None:
        try:
            r.font.color.rgb = RGBColor(0x24, 0x5A, 0x34)
        except Exception:
            pass
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)

def _add_mcq_option(doc, label: str, text: str):
    p = doc.add_paragraph()
    if Inches is not None:
        p.paragraph_format.left_indent = Inches(0.30)
        p.paragraph_format.first_line_indent = Inches(0)
    p.paragraph_format.space_after = Pt(1)
    p.add_run(f"{label}. ").bold = True
    p.add_run(text)

def export_mcqs_docx(df: pd.DataFrame, lesson:int, week:int, topic:str="", highlight_stems: bool = True)->bytes:
    if Document is None: return b""
    doc=Document(); _set_doc_defaults(doc)
    if Inches:
        sec=doc.sections[0]; sec.left_margin=Inches(0.8); sec.right_margin=Inches(0.8)
    _docx_heading(doc, "Knowledge MCQs" + (f" • {topic}" if topic else ""), 0)
    doc.add_paragraph()
    for i, r in df.reset_index(drop=True).iterrows():
        _add_mcq_stem(doc, i+1, r['Question'], highlight=highlight_stems)
        _add_mcq_option(doc, "A", r['Option A'])
        _add_mcq_option(doc, "B", r['Option B'])
        _add_mcq_option(doc, "C", r['Option C'])
        _add_mcq_option(doc, "D", r['Option D'])
        doc.add_paragraph()
    _docx_heading(doc, "Answer Key", 1)
    for i, r in df.reset_index(drop=True).iterrows():
        doc.add_paragraph(f"Q{i+1}: {r['Answer']}")
    bio=BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

def export_acts_docx(df: pd.DataFrame, lesson:int, week:int, topic:str="")->bytes:
    if Document is None: return b""
    doc=Document(); _set_doc_defaults(doc)
    if Inches:
        sec=doc.sections[0]; sec.left_margin=Inches(0.8); sec.right_margin=Inches(0.8)
    _docx_heading(doc, "Skills Activities" + (f" • {topic}" if topic else ""), 0)
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

def export_combined_docx(mcq_df: pd.DataFrame | None, act_df: pd.DataFrame | None,
                         lesson:int, week:int, topic:str="", highlight_stems: bool = True)->bytes:
    if Document is None: return b""
    doc=Document(); _set_doc_defaults(doc)
    if Inches:
        sec=doc.sections[0]; sec.left_margin=Inches(0.8); sec.right_margin=Inches(0.8)
    title = "Combined — MCQs & Activities" + (f" • {topic}" if topic else "")
    _docx_heading(doc, title, 0)
    doc.add_paragraph()
    if mcq_df is not None and len(mcq_df)>0:
        _docx_heading(doc, "Part A — Knowledge MCQs", 1)
        for i, r in mcq_df.reset_index(drop=True).iterrows():
            _add_mcq_stem(doc, i+1, r['Question'], highlight=highlight_stems)
            _add_mcq_option(doc, "A", r['Option A'])
            _add_mcq_option(doc, "B", r['Option B'])
            _add_mcq_option(doc, "C", r['Option C'])
            _add_mcq_option(doc, "D", r['Option D'])
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
    lines=[]
    for i,r in df.reset_index(drop=True).iterrows():
        qname=f"Q{i+1} ({r.get('Tier','')})"
        stem=_gift_escape(str(r.get("Question",""))).strip()
        opts=[str(r.get("Option A","")),str(r.get("Option B","")),str(r.get("Option C","")),str(r.get("Option D",""))]
        idx={"A":0,"B":1,"C":2,"D":3}.get(str(r.get("Answer","A")).strip().upper(),0)
        parts=[("="+_gift_escape(o)) if j==idx else ("~"+_gift_escape(o)) for j,o in enumerate(opts)]
        exp=str(r.get("Explanation",""))
        comment=f"#### {_gift_escape(exp)}" if exp else ""
        lines.append(f"::{_gift_escape(qname)}:: {stem} {{\n" + "\n".join(parts) + f"\n}} {comment}\n")
    return "\n".join(lines).strip()+"\n"

# ---------- Sample text ----------
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

# ---------- State defaults ----------
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
st.session_state.setdefault("safe_mode", True)
st.session_state.setdefault("hl_stems_docx", True)
st.session_state.setdefault("hl_stems_preview", True)
st.session_state.setdefault("hl_act_titles_preview", True)
st.session_state.setdefault("student_handout", False)
st.session_state.setdefault("seen_q_sigs", set())  # remembers MCQs this session

# ---------- Header ----------
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

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["① 📂 Upload", "② ⚙️ Setup", "③ ✨ Generate", "④ 📤 Export"])

def progress_fraction()->float:
    steps = 0; total = 4
    if (st.session_state.get("src_edit") or "").strip(): steps += 1
    if len(_sentences(st.session_state.get("src_edit",""))) >= 6: steps += 1
    if ("mcq_df" in st.session_state) or ("act_df" in st.session_state): steps += 1
    if ("mcq_df" in st.session_state) or ("act_df" in st.session_state): steps += 1
    return steps/total

# ===== ① Upload =====
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Upload Lesson File</div>", unsafe_allow_html=True)
    st.caption("Upload .pptx / .pdf / .docx. We’ll extract text (avoid scanned PDFs).")
    up = st.file_uploader("Upload .pptx / .pdf / .docx", type=["pptx","pdf","docx"])
    if up:
        st.session_state.src_text = extract_text_from_upload(up)
        st.session_state.src_edit = st.session_state.src_text
        if st.session_state.src_text.startswith("[Could not parse") or st.session_state.src_text.startswith("[Parsed 0 text"):
            st.error(st.session_state.src_text)
            st.info("Tip: If a PPTX fails, export it as PDF and upload the PDF.")
        else:
            st.success(f"File parsed: **{up.name}**")
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

    # Step 1
    st.markdown("<b>Step 1 — Choose Lesson & Week</b>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,2])
    with c1: st.session_state.lesson = st.selectbox("Lesson", [1,2,3,4], index=st.session_state.lesson-1)
    with c2: st.session_state.week   = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1)
    with c3:
        focus = bloom_focus_for_week(st.session_state.week)
        st.markdown(f"**Bloom focus (auto): Week {st.session_state.week}: {focus}**")
    _focus = focus
    _cls = "low" if _focus=="Low" else ("med" if _focus=="Medium" else "high")
    st.markdown(f"<div class='bloom-row'><span class='chip {_cls} hl'>🎯 Focus {_focus}</span></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # Step 2
    st.markdown("<b>Step 2 — Review Bloom’s Focus</b>", unsafe_allow_html=True)
    def bloom_row(label, verbs):
        cls  = "low" if label=="Low" else "med" if label=="Medium" else "high"
        hl   = " hl" if label==_focus else ""
        weeks = "1–4" if label=="Low" else "5–9" if label=="Medium" else "10–14"
        chips = " ".join([f"<span class='chip {cls}{hl}'>{v}</span>" if label==_focus else f"<span class='chip {cls} dimmed'>{v}</span>" for v in verbs])
        st.markdown(f"**{label} (Weeks {weeks})**", unsafe_allow_html=True)
        st.markdown(f"<div class='bloom-row'>{chips}</div>", unsafe_allow_html=True)
    bloom_row("Low", LOW_VERBS); bloom_row("Medium", MED_VERBS); bloom_row("High", HIGH_VERBS)
    st.markdown("<hr>", unsafe_allow_html=True)

    # Step 3
    st.markdown("<b>Step 3 — Learning Objective / Topic (optional)</b>", unsafe_allow_html=True)
    st.session_state.topic = st.text_input("Learning Objective / Topic", value=st.session_state.topic, placeholder="e.g., Understand Ohm’s Law and apply it to simple circuits")
    st.markdown("<hr>", unsafe_allow_html=True)

    # Step 4
    st.markdown("<b>Step 4 — Paste/Edit Source Text</b>", unsafe_allow_html=True)
    csa, csb = st.columns([4,1])
    with csa:
        st.session_state.src_edit = st.text_area("Source (editable)", value=st.session_state.src_edit, height=180, placeholder="Add 12–25 full sentences (avoid bullets).")
        txt = st.session_state.src_edit or ""
        sc = len(_sentences(txt)); ready = sc >= 6 if st.session_state.get("safe_mode", True) else sc >= 12
        bullet_hit = ("•" in txt) or re.search(r"^\s*[-*]\s+", txt, re.M)
        target = 6 if st.session_state.get("safe_mode", True) else 12
        st.caption(f"Detected **{sc}** sentence(s). Need **{target}+**.")
        if bullet_hit:
            st.info("Bullets detected. Convert to full sentences for best results (Safe Mode helps too).")
    with csb:
        if st.button("Paste sample text"): st.session_state.src_edit = SAMPLE_TEXT; st.rerun()
        if st.button("Reset all"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
        st.caption("Quick actions")

    # Step 5 — MCQs
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<b>Step 5 — MCQ Setup</b>", unsafe_allow_html=True)
    choices = [5,10,20,30]
    default_idx = choices.index(st.session_state.mcq_total) if st.session_state.mcq_total in choices else 1
    st.session_state.mcq_total = st.radio("Number of MCQs", choices, index=default_idx, horizontal=True)
    st.session_state.mcq_mode = st.selectbox("MCQ distribution", ["Mixed","All Low","All Medium","All High"], index=["Mixed","All Low","All Medium","All High"].index(st.session_state.mcq_mode))
    st.session_state.safe_mode = st.checkbox("Safe Mode (always works) — ignore anchors; use only clean sentences", value=st.session_state.safe_mode)

    # Optional: clear duplicate memory
    if st.button("Reset MCQ duplicate memory"):
        st.session_state.seen_q_sigs = set()
        st.toast("🧽 Cleared MCQ duplicate memory")

    # Step 6 — Activities
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<b>Step 6 — Activity Setup</b>", unsafe_allow_html=True)
    colA, colB = st.columns([1,2])
    with colA:
        st.session_state.act_n = st.radio("Activities", [1,2,3], index=st.session_state.act_n-1, horizontal=True)
        st.session_state.act_style = st.selectbox("Activity style", ["Standard","Lab","Group Task","Reflection"], index=["Standard","Lab","Group Task","Reflection"].index(st.session_state.act_style))
    with colB:
        st.session_state.act_dur = st.slider("Duration per Activity (mins)", 10, 60, st.session_state.act_dur, 5)
    st.session_state.student_handout = st.checkbox("Student handout wording (use 'You/We' in activities)", value=st.session_state.student_handout)

    st.progress(progress_fraction())
    st.markdown("</div>", unsafe_allow_html=True)

# ===== ③ Generate =====
with tab3:
    sc = len(_sentences(st.session_state.get("src_edit","")))
    min_req = 6 if st.session_state.get("safe_mode", True) else 12
    if sc < min_req:
        st.info(f"Add at least {min_req} full sentences in **② Setup** to enable Generate.")
        st.progress(progress_fraction()); st.stop()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Generate Questions & Activities</div>", unsafe_allow_html=True)

    colQ, colA = st.columns([1,1])
    with colQ:
        if st.button("📝 Generate MCQs", use_container_width=True):
            with st.spinner("Generating MCQs…"):
                try:
                    if st.session_state.safe_mode:
                        st.session_state.mcq_df = generate_mcqs_safe(
                            st.session_state.topic, st.session_state.src_edit, int(st.session_state.mcq_total),
                            st.session_state.week, st.session_state.lesson, st.session_state.mcq_mode
                        )
                    else:
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
                    st.session_state.act_df = generate_activities_safe(
                        int(st.session_state.act_n), int(st.session_state.act_dur), focus,
                        st.session_state.topic, st.session_state.lesson, st.session_state.week,
                        st.session_state.src_edit, st.session_state.act_style,
                        student=st.session_state.student_handout
                    )
                    st.success("Activities generated.")
                except Exception as e:
                    st.error(f"Couldn’t generate activities: {e}")

    show_answers = st.checkbox("Show answer key in preview", value=False)
    st.session_state.hl_stems_preview = st.checkbox(
        "🔆 Highlight MCQ question stems (preview)", value=st.session_state.get("hl_stems_preview", True)
    )
    st.session_state.hl_act_titles_preview = st.checkbox(
        "🔆 Highlight activity titles (preview)", value=st.session_state.get("hl_act_titles_preview", True)
    )

    if "mcq_df" in st.session_state:
        st.write("**MCQs (preview)**")
        st.markdown("<div class='preview-card'>", unsafe_allow_html=True)
        for i,row in st.session_state.mcq_df.reset_index(drop=True).iterrows():
            cls = "mcq-low" if row["Tier"]=="Low" else ("mcq-med" if row["Tier"]=="Medium" else "mcq-high")
            ans = f" <i>(Answer: {row['Answer']})</i>" if show_answers else ""
            if st.session_state.get("hl_stems_preview", True):
                stem_html = f"<div class='mcq-stem'>Q{i+1}. {row['Question']}</div>"
            else:
                stem_html = f"<b>Q{i+1}. {row['Question']}</b>"
            meta_html = f"<div class='mcq-meta'><b>{row['Tier']}</b>{ans}</div>"
            st.markdown(f"<div class='mcq-item {cls}'>{stem_html}{meta_html}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if "act_df" in st.session_state:
        st.write("**Activities (preview)**")
        for i,r in st.session_state.act_df.reset_index(drop=True).iterrows():
            tier = r.get("Policy focus","Medium")
            cls = "act-low" if tier=="Low" else ("act-med" if tier=="Medium" else "act-high")
            title = r.get('Title','Activity')
            title_html = f"<span class='act-title'>{i+1}. {title}</span>" if st.session_state.get("hl_act_titles_preview", True) else f"<b>{i+1}. {title}</b>"
            st.markdown(
                f"<div class='act-card {cls}'>{title_html}<br>"
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

    st.session_state.hl_stems_docx = st.checkbox(
        "🔆 Highlight question stems in DOCX",
        value=st.session_state.get("hl_stems_docx", True)
    )

    st.markdown("<div class='export-grid'>", unsafe_allow_html=True)

    # MCQs
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>MCQs</div>", unsafe_allow_html=True)
    if "mcq_df" in st.session_state:
        if st.download_button("Download MCQs (CSV)", st.session_state.mcq_df.to_csv(index=False).encode("utf-8"),
                              f"mcqs_w{st.session_state.week:02d}.csv", "text/csv"):
            st.toast("✅ MCQs CSV download started")
        gift_txt = export_mcqs_gift(st.session_state.mcq_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
        if st.download_button("Download MCQs (Moodle GIFT)", gift_txt.encode("utf-8"),
                              f"mcqs_w{st.session_state.week:02d}.gift", "text/plain"):
            st.toast("✅ MCQs GIFT download started")
        if Document:
            mcq_docx = export_mcqs_docx(
                st.session_state.mcq_df, st.session_state.lesson, st.session_state.week,
                st.session_state.topic, highlight_stems=st.session_state.hl_stems_docx
            )
            if st.download_button("Download MCQs (Word)", mcq_docx,
                                  f"mcqs_w{st.session_state.week:02d}.docx",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
                st.toast("✅ MCQs Word download started")
        else:
            st.caption("Install python-docx for Word export.")
    else:
        st.caption("Generate MCQs in ③ Generate to enable downloads.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Activities
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>Activities</div>", unsafe_allow_html=True)
    if "act_df" in st.session_state:
        if st.download_button("Download Activities (CSV)", st.session_state.act_df.to_csv(index=False).encode("utf-8"),
                              f"activities_w{st.session_state.week:02d}.csv", "text/csv"):
            st.toast("✅ Activities CSV download started")
        if Document:
            act_docx = export_acts_docx(st.session_state.act_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
            if st.download_button("Download Activities (Word)", act_docx,
                                  f"activities_w{st.session_state.week:02d}.docx",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
                st.toast("✅ Activities Word download started")
        else:
            st.caption("Install python-docx for Word export.")
    else:
        st.caption("Generate Activities in ③ Generate to enable downloads.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Combined
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>Combined Lesson (Word)</div>", unsafe_allow_html=True)
    if Document:
        mcq_df = st.session_state.get('mcq_df') if 'mcq_df' in st.session_state else None
        act_df = st.session_state.get('act_df') if 'act_df' in st.session_state else None
        if (mcq_df is not None and len(mcq_df)>0) or (act_df is not None and len(act_df)>0):
            combined_docx = export_combined_docx(
                mcq_df, act_df, st.session_state.lesson, st.session_state.week, st.session_state.topic,
                highlight_stems=st.session_state.hl_stems_docx
            )
            if st.download_button("Download Combined Lesson (Word)", combined_docx,
                                  f"combined_w{st.session_state.week:02d}.docx",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
                st.toast("✅ Combined Lesson Word download started")
        else:
            st.caption("Generate MCQs and/or Activities in ③ Generate to enable this.")
    else:
        st.caption("Install python-docx for Combined Word export.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.progress(progress_fraction())
    st.markdown("</div>", unsafe_allow_html=True)
