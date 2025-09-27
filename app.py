
# app.py — ADI Learning Tracker (v3.1, patched)
# English-only • PDF/PPTX/DOCX input • MCQs & Activities • Print-friendly DOCX
# Exports: CSV / GIFT / Word / Combined Word

import io, os, re, base64, random, unicodedata
from io import BytesIO
from typing import List, Set
from difflib import SequenceMatcher

import pandas as pd
import streamlit as st
import hashlib
def _seed_salt() -> int:
    """Hash the teacher/class seed to a small integer offset."""
    try:
        seed_txt = (st.session_state.get("teacher_seed") or st.session_state.get("teacher_id") or "").strip()
    except Exception:
        seed_txt = ""
    if not seed_txt:
        return 0
    h = hashlib.md5(seed_txt.encode("utf-8")).hexdigest()[:8]
    return int(h, 16)


# ---------- Streamlit base ----------
st.set_page_config(page_title="ADI Learning Tracker", page_icon="🧭", layout="centered")



def _read_pptx(file_bytes: bytes) -> str:
    """Robust PPTX text extractor that ignores unsupported shapes and never touches relationship rIds."""
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except Exception:
        return ""
    def push_text(s: str, bucket: list):
        s = (s or "").strip()
        if s:
            bucket.append(" ".join(s.split()))
    def walk_shape(shape, bucket: list):
        try:
            if getattr(shape, "has_text_frame", False):
                tf = shape.text_frame
                # paragraphs → runs
                if getattr(tf, "paragraphs", None):
                    for p in tf.paragraphs:
                        txt = "".join(getattr(r, "text", "") for r in getattr(p, "runs", []))
                        push_text(txt, bucket)
                else:
                    push_text(getattr(tf, "text", ""), bucket)
            if hasattr(shape, "table"):
                try:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            push_text(getattr(cell, "text", ""), bucket)
                except Exception:
                    pass
            if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP and hasattr(shape, "shapes"):
                for s in shape.shapes:
                    walk_shape(s, bucket)
        except Exception:
            pass

    try:
        prs = Presentation(BytesIO(file_bytes))
    except Exception:
        return ""

    lines = []
    for slide in prs.slides:
        try:
            title_txt = ""
            if getattr(slide, "shapes", None):
                # Try slide title placeholder
                for sh in slide.shapes:
                    if getattr(sh, "has_text_frame", False) and getattr(sh.text_frame, "text", "").strip():
                        title_txt = sh.text_frame.text.strip()
                        break
            if title_txt:
                lines.append(f"# {title_txt}")
            for sh in slide.shapes:
                walk_shape(sh, lines)
            if getattr(slide, "has_notes_slide", False) and slide.notes_slide and slide.notes_slide.notes_text_frame:
                push_text(slide.notes_slide.notes_text_frame.text, lines)
            lines.append("")
        except Exception:
            continue

    return "\n".join(lines).strip()

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

/* Buttons */
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

# ---------- PATCHED: richer sentence harvesting ----------
def _sentences(text: str) -> List[str]:
    # split on punctuation/bullets
    chunks = re.split(r"(?<=[.!?])\s+|[•\u2022\u2023\u25CF]|(?:\n\s*-\s*)|(?:\n\s*\*\s*)", text or "")
    rough = [re.sub(r"\s+", " ", c).strip() for c in chunks if c and c.strip()]
    # split very long sentences into sub-clauses
    split_more = []
    for s in rough:
        if len(s) > 240:
            parts = re.split(r"\s*;\s*|\s*—\s*|\s*–\s*|\s*:\s*", s)
            split_more.extend([p.strip() for p in parts if p and len(p.split()) >= 6])
        else:
            split_more.append(s)
    def good(s: str) -> bool:
        if not (28 <= len(s) <= 240): return False
        if len(s.split()) < 6: return False
        if sum(ch.isdigit() for ch in s) >= max(6, int(0.25*len(s))): return False
        return True
    sents = [s for s in split_more if good(s)]
    return sents[:260]

def _is_sentence_like(s: str) -> bool:
    if len(s.split()) < 6: return False
    if sum(c.isdigit() for c in s) >= 6: return False
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
    return "||".join(sorted(_norm_q(o) for o in options))

# ---------- PATCHED: more permissive option gate ----------
def _quality_gate(options: List[str], ensure_first: bool = True,
                  min_len: int = 30, max_len: int = 230,
                  min_words: int = 5, require_verb: bool = False) -> List[str]:
    ops = [re.sub(r"\s+"," ", o.strip()) for o in options if o and o.strip()]
    out: List[str] = []
    for j, o in enumerate(ops):
        low = o.lower()
        if any(p in low for p in BLOCK_LINE_PHRASES): continue
        if _has_emoji(o): continue
        if re.search(r"\bps\d+\b", low): continue

        ok = True
        if not (min_len <= len(o) <= max_len): ok = False
        if len(o.split()) < min_words: ok = False
        if require_verb and not re.search(VERB_RE, o, re.I): ok = False
        if j == 0 and ensure_first: ok = True

        if ok and not any(_near(o, p, 0.96) for p in out):
            out.append(o)
        if len(out) == 4: break

    k = 0
    while len(out) < 4 and k < len(ops):
        if ops[k] not in out and not _has_emoji(ops[k]) and not any(p in ops[k].lower() for p in BLOCK_LINE_PHRASES):
            out.append(ops[k])
        k += 1
    return out[:4]

def _quality_gate_loose(options: List[str], ensure_first: bool = True) -> List[str]:
    return _quality_gate(options, ensure_first=ensure_first, min_len=25, min_words=5, require_verb=False)

def _window(sentences: List[str], idx: int, w: int = 2) -> List[str]:
    L=max(0, idx-w); R=min(len(sentences), idx+w+1)
    return sentences[L:R]

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
        if name.endswith(".pptx"):
            buf = file.read() if hasattr(file,"read") else file.getvalue()
            try:
                text = _read_pptx(buf)
                if not text.strip():
                    return "[Parsed 0 text — PPTX contained no readable text. Try exporting to PDF and upload.]"
                return _clean_lines(text)
            except Exception as ee:
                return f"[Could not parse file: {ee}]"
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

def _strip_noise(s: str) -> str:
    if not s: return s
    s = re.sub(r"\s*\((?:PS|LO|CO)\d+(?:,\s*(?:PS|LO|CO)\d+)*\)\s*", " ", s)
    s = re.sub(r"\s*\([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*,\s*\d{4}\)\s*", " ", s)
    s = re.sub(r"\s+[o•\-]\s+", " ", s)
    s = re.sub(r"defence\s*systems", "defence systems", s, flags=re.I)
    s = re.sub(r"defence\s*personnel", "defence personnel", s, flags=re.I)
    return re.sub(r"\s{2,}", " ", s).strip()

# ---------- MCQ stem templates (diversified) ----------
STEMS = {
    "Low": [
        "Identify the correct feature of {kw}.",
        "Select the term that best matches {kw}.",
        "Which definition fits {kw}?",
        "What is the primary purpose of {kw}?",
        "Choose the statement that accurately describes {kw}.",
        "Name the property that characterizes {kw}.",
        "Complete the statement about {kw}."
    ],
    "Medium": [
        "How does {kw} improve the outcome in this context?",
        "Why is {kw} important for the scenario described?",
        "Which factor best influences {kw}?",
        "Compare {kw1} and {kw2} in terms of {kw3}.",
        "Select the option that correctly applies {kw}.",
        "According to the text, what should be done regarding {kw}?",
        "Which step is most appropriate when addressing {kw}?"
    ],
    "High": [
        "Evaluate the best justification for using {kw} here.",
        "Which conclusion is best supported about {kw}?",
        "What is the strongest rationale concerning {kw}?",
        "Predict the outcome if {kw} is changed.",
        "Design the most defensible approach using {kw}.",
        "Identify the most defensible explanation for {kw}.",
        "Which option provides the strongest evidence about {kw}?"
    ],
}
def _stem_for_tier(tier: str, idx: int) -> str:
    """Choose a stem with diversity across week/lesson/source and throttle 'Which/What'."""
    try:
        src = st.session_state.get("src_edit") or st.session_state.get("src_text") or ""
    except Exception:
        src = ""
    week = int(st.session_state.get("week", 1) or 1)
    lesson = int(st.session_state.get("lesson", 1) or 1)
    source_type = (st.session_state.get("source_type") or "PPT")

    kws = _keywords(src, top_n=36) if src else []
    if not kws:
        kws = ["the topic", "the concept", "the process", "the system", "the standard"]
    base_idx = idx + week*3 + lesson*7 + (_seed_salt() % 31)
    kw  = kws[ base_idx % len(kws) ]
    kw1 = kws[(base_idx + 5) % len(kws)]
    kw2 = kws[(base_idx + 11) % len(kws)]
    kw3 = kws[(base_idx + 17) % len(kws)]

    bank = STEMS.get(tier, STEMS["Medium"])[:]
    bias = {
        "PPT": ["Compare {kw1} and {kw2} in terms of {kw3}.", "Select the option that correctly applies {kw}."],
        "E-book": ["Why is {kw} important for the scenario described?", "How does {kw} improve the outcome in this context?"],
        "Lesson plan": ["Which step is most appropriate when addressing {kw}?", "Design the most defensible approach using {kw}."],
    }.get(source_type, [])
    bank = (bias + bank) if bias else bank

    rnd = random.Random(1000 + base_idx)
    rnd.shuffle(bank)

    def ok(s: str, i: int) -> bool:
        h = s.split(" ", 1)[0].lower()
        if h in {"which", "what"} and (i % 3) != 0:
            return False
        return True
    chosen = next((s for s in bank if ok(s, base_idx)), bank[0])
    return chosen.format(kw=kw, kw1=kw1, kw2=kw2, kw3=kw3)

# ---------- MCQs (Exact mode) ----------
def generate_mcqs_exact(topic: str, src_text: str, total: int, week: int, lesson: int, mode: str) -> pd.DataFrame:
    """Exact mode with week/lesson-based variety."""
    text = _strip_noise(src_text or "")
    if not text:
        return pd.DataFrame(columns=MCQ_COLS)
    sents = [s for s in re.split(r'(?<=[.!?])\s+', text) if len(s.split()) >= 4]
    rnd = random.Random(int(week) * 100 + int(lesson) + (_seed_salt() % 100000))
    rnd.shuffle(sents)

    rows = []
    local_sigs = set()
    tiers = ["Low","Medium","High"]
    for sent in sents:
        if len(rows) >= int(total): break
        distractors, correct = _distractors_for_sentence(sent, mode or "exact")
        if not correct: continue
        options = _quality_gate_loose([correct] + distractors, ensure_first=True)
        if len(options) < 4: continue
        sig = _q_signature(options)
        if sig in local_sigs: continue

        tier = tiers[len(rows) % len(tiers)]
        stem = _stem_for_tier(tier, len(rows))
        options = [_strip_noise(o) for o in options]
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(_strip_noise(correct))]

        rows.append({
            "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": stem,
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans,
            "Explanation": _explain_choice(correct, options, topic)
        })
        local_sigs.add(sig)
    return pd.DataFrame(rows, columns=MCQ_COLS)

# ---------- Safe helpers ----------
def _pick_distractors(pool: List[str], correct: str, want: int = 3) -> List[str]:
    out = []
    for cand in pool:
        if cand == correct: continue
        if abs(len(cand) - len(correct)) > 140: continue
        sim = SequenceMatcher(a=correct.lower(), b=cand.lower()).ratio()
        if 0.40 <= sim <= 0.88:
            out.append(cand)
        if len(out) == want: break
    i = 0
    while len(out) < want and i < len(pool):
        c = pool[i]; i += 1
        if c != correct and c not in out:
            out.append(c)
    return out[:want]

# ---------- MCQs (Safe mode) with Pass C fill ----------
def generate_mcqs_safe(topic: str, src_text: str, total: int, week: int, lesson: int, mode: str) -> pd.DataFrame:
    """Safe generator with week/lesson-based variety and global anchor de-dup."""
    text = _strip_noise(src_text or "")
    if not text:
        return pd.DataFrame(columns=MCQ_COLS)
    sents = [s for s in re.split(r'(?<=[.!?])\s+', text) if len(s.split()) >= 4]
    if len(sents) < 6:
        return pd.DataFrame(columns=MCQ_COLS)

    used_pool = _seen_pool(text)
    rows = []
    local_sigs = set()
    tiers = ["Low","Medium","High"]
    rnd = random.Random(int(week) * 100 + int(lesson) + (_seed_salt() % 100000))
    rnd.shuffle(sents)

    kws_global = _keywords(text, top_n=36)

    for sent in sents:
        if len(rows) >= int(total): break
        distractors, correct = _distractors_for_sentence(sent, mode or "safe")
        if not correct: continue
        options = _quality_gate_loose([correct] + distractors, ensure_first=True)
        if correct not in options: options = ([correct] + options)[:4]
        if len(options) < 4: continue
        if any(o in used_pool for o in options): continue

        sig = _q_signature(options)
        if sig in local_sigs or sig in st.session_state.get("seen_q_sigs", set()): 
            continue

        tier = tiers[len(rows) % len(tiers)]
        anchor = (kws_global[(len(rows) + (_seed_salt() % max(1, len(kws_global)))) % len(kws_global)] if kws_global else correct.split()[0].lower())
        if anchor in st.session_state.get("seen_q_sigs_global", set()):
            continue

        stem = _stem_for_tier(tier, len(rows))
        stem = _strip_noise(stem)
        options = [_strip_noise(o) for o in options]
        rnd.shuffle(options)
        ans = ["A","B","C","D"][options.index(_strip_noise(correct))]
        st.session_state.seen_q_sigs_global.add(anchor)

        rows.append({
            "Tier": tier, "Q#": {"Low":1,"Medium":2,"High":3}[tier],
            "Question": stem,
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ans,
            "Explanation": _explain_choice(correct, options, topic)
        })
        local_sigs.add(sig)

    df = pd.DataFrame(rows, columns=MCQ_COLS)
    return df

# ---------- Activities ----------
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

def _seen_pool(text: str) -> set:
    """Return a set of banned/seen option strings to avoid low‑value choices.
    Minimal fallback implementation: empty set. Extend later if needed.
    """
    return set()


def generate_activities_safe(n:int, dur:int, focus:str, topic:str, lesson:int, week:int, src_text:str, style:str, student:bool=False)->pd.DataFrame:
    """
    Safe activity generator with variability by week/lesson and Bloom focus.
    """
    rng_seed = week * 100 + lesson
    random.seed(rng_seed)

    style_pool = ["Standard", "Lab", "Group Task", "Reflection", "Debate", "Simulation", "Case Study", "Gallery Walk"]
    verbs = {
        "Low": ["identify", "list", "describe"],
        "Medium": ["apply", "analyze", "compare"],
        "High": ["evaluate", "design", "create"],
    }
    frames = [("Starter", 5), ("Main", max(10, dur-10)), ("Plenary", 5)]

    # Choose styles
    chosen_styles = []
    for i in range(n):
        if style == "Standard":
            chosen_styles.append(random.choice(style_pool))
        else:
            chosen_styles.append(style)

    rows = []
    base_topic = (topic or "this week’s learning")[:120]
    task_bits = {
        "Lab": ["run a quick experiment", "collect measurements", "plot a simple graph"],
        "Group Task": ["brainstorm alternatives", "split roles", "synthesize on an A3"],
        "Reflection": ["write a minute paper", "pair-share takeaways", "log uncertainties"],
        "Debate": ["form two teams", "list claims & evidence", "rebut with counter-arguments"],
        "Simulation": ["play roles", "simulate a scenario", "debrief decisions"],
        "Case Study": ["skim a short case", "extract key facts", "present recommendations"],
        "Gallery Walk": ["post drafts", "rotate in groups", "leave warm/cool feedback"],
        "Standard": ["work through guided prompts", "check against rubric", "share one improvement"],
    }

    for i in range(n):
        s = chosen_styles[i]
        v = random.choice(verbs.get(focus, verbs["Medium"]))
        bits = list(task_bits.get(s, task_bits["Standard"]))
        random.shuffle(bits)
        starter_mins, main_mins, plenary_mins = frames[0][1], frames[1][1], frames[2][1]
        title = f"{focus} Activity {i+1} — {s}"
        objective = f"You will {v} key ideas related to {base_topic} (Lesson {lesson}, Week {week}, focus: {focus})."
        steps = (
            f"Starter ({starter_mins}m). {v.title()} prior knowledge on {base_topic}.\n"
            f"Starter ({starter_mins}m). {v.title()} prior knowledge on {base_topic}.\n"
            f"Main ({main_mins}m). Teams {bits[0]}, then {bits[1]}; capture outcomes tied to {focus}.\n"
            f"Plenary ({plenary_mins}m). {bits[2].capitalize()}, then share one insight and one question."
            f"Plenary ({plenary_mins}m). {bits[2].capitalize()}, then share one insight and one question."
        )
        materials = "Timer; A3 paper; markers" + ("; student handout" if student else "")
        assessment = f"Rubric aligned to {focus}: clarity, correctness, and application to scenario (each /3 → /9)."
        rows.append({"title": title, "objective": objective, "steps": steps, "materials": materials, "assessment": assessment, "duration": dur})

    return pd.DataFrame(rows, columns=["title","objective","steps","materials","assessment","duration"])


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
    """Export activities to DOCX. Tolerant to varying column names and missing 'Policy focus'."""
    if Document is None: return b""
    doc = Document(); _set_doc_defaults(doc)
    if Inches:
        sec = doc.sections[0]; sec.left_margin = Inches(0.8); sec.right_margin = Inches(0.8)
    _docx_heading(doc, "Skills Activities" + (f" • {topic}" if topic else ""), 0)
    doc.add_paragraph()
    def g(row, *names, default=""):
        for n in names:
            if n in row: return row.get(n, default)
        return default
    try:
        wk_focus = bloom_focus_for_week(int(week))
    except Exception:
        wk_focus = ""
    for i, r in df.reset_index(drop=True).iterrows():
        title = g(r, "Title","title", default=f"Activity {i+1}")
        doc.add_heading(str(title), level=1)
        pf = g(r, "Policy focus","policy_focus", default="").strip() or wk_focus
        if pf: doc.add_paragraph(f"Policy focus: {pf}")
        obj = g(r, "Objective","objective"); 
        if obj: doc.add_paragraph(f"Objective: {obj}")
        steps = g(r, "Steps","steps")
        if steps:
            doc.add_paragraph("Steps:")
            for line in str(steps).splitlines():
                if line.strip(): doc.add_paragraph(line.strip())
        mats = g(r, "Materials","materials")
        if mats: doc.add_paragraph(f"Materials: {mats}")
        assess = g(r, "Assessment","assessment")
        if assess: doc.add_paragraph(f"Assessment: {assess}")
        dur = g(r, "Duration (mins)","duration")
        if dur: doc.add_paragraph(f"Duration: {dur} mins")
        doc.add_paragraph()
    bio = BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()


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
st.session_state.setdefault("seen_q_sigs", set())
st.session_state.setdefault("gen_type", "MCQs")
st.session_state.setdefault("source_type", "PPT")

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

    # Step 4A — What to generate & Source type (new)
    st.markdown("<b>Step 4A — What to generate & Source type</b>", unsafe_allow_html=True)
    sA, sB, sC = st.columns([1.2, 1.2, 2.6])
    with sA:
        st.session_state.gen_type = st.radio(
            "Generate",
            ["MCQs", "Activities"],
            index=["MCQs","Activities"].index(st.session_state.gen_type),
            horizontal=True,
        )
    with sB:
        st.session_state.source_type = st.selectbox(
            "Source",
            ["PPT", "E-book", "Lesson plan"],
            index=["PPT","E-book","Lesson plan"].index(st.session_state.source_type),
        )
    with sC:
        st.caption(
            f"Context → Lesson {st.session_state.lesson} • Week {st.session_state.week} • {st.session_state.source_type}"
        )
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

    st.divider()
    if st.button("Reset MCQ uniqueness memory"):
        st.session_state.seen_q_sigs_global.clear()
        st.toast("Cleared MCQ de-dup memory")
# ===== ③ Generate =====
with tab3:
    sc = len(_sentences(st.session_state.get("src_edit","")))
    min_req = 6 if st.session_state.get("safe_mode", True) else 12
    if sc < min_req:
        st.info(f"Add at least {min_req} full sentences in **② Setup** to enable Generate.")
        st.progress(progress_fraction()); st.stop()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Generate Questions & Activities</div>", unsafe_allow_html=True)

    
    # Context banner
    st.markdown(
        f"<div class='bloom-row'><span class='chip hl'>Lesson {st.session_state.lesson}</span>"
        f"<span class='chip hl'>Week {st.session_state.week}</span>"
        f"<span class='chip hl'>{st.session_state.source_type}</span>"
        f"<span class='chip {'low' if bloom_focus_for_week(st.session_state.week)=='Low' else ('med' if bloom_focus_for_week(st.session_state.week)=='Medium' else 'high')}'>Focus {bloom_focus_for_week(st.session_state.week)}</span></div>",
        unsafe_allow_html=True
    )

    
    # Two explicit generate buttons (MCQs and Activities)
    colQ, colA = st.columns(2)

    with colQ:
        if st.button("📝 Generate MCQs", use_container_width=True):
            with st.spinner("Generating MCQs…"):
                try:
                    if st.session_state.safe_mode:
                        st.session_state.mcq_df = generate_mcqs_safe(
                            st.session_state.topic,
                            st.session_state.src_edit,
                            int(st.session_state.mcq_total),
                            st.session_state.week,
                            st.session_state.lesson,
                            st.session_state.mcq_mode,
                        )
                    else:
                        st.session_state.mcq_df = generate_mcqs_exact(
                            st.session_state.topic,
                            st.session_state.src_edit,
                            int(st.session_state.mcq_total),
                            st.session_state.week,
                            st.session_state.lesson,
                            st.session_state.mcq_mode,
                        )
                    if len(st.session_state.mcq_df) < st.session_state.mcq_total:
                        st.warning(
                            f"Generated {len(st.session_state.mcq_df)} of {st.session_state.mcq_total}. "
                            "Paste a longer narrative to reach the target."
                        )
                    else:
                        st.success(f"MCQs generated for Lesson {st.session_state.lesson}, Week {st.session_state.week} ({st.session_state.source_type}).")
                    # keep a backup for reset
                    if isinstance(st.session_state.mcq_df, pd.DataFrame):
                        st.session_state.mcq_df_backup = st.session_state.mcq_df.copy(deep=True)
                except Exception as e:
                    st.error(f"Couldn’t generate MCQs: {e}")

    with colA:
        if st.button("🧩 Generate Activities", use_container_width=True):
            with st.spinner("Generating Activities…"):
                try:
                    focus = bloom_focus_for_week(st.session_state.week)
                    st.session_state.act_df = generate_activities_safe(
                        int(st.session_state.act_n),
                        int(st.session_state.act_dur),
                        focus,
                        st.session_state.topic,
                        st.session_state.lesson,
                        st.session_state.week,
                        st.session_state.src_edit,
                        st.session_state.act_style,
                        student=st.session_state.student_handout,
                    )
                    st.success(f"Activities generated for Lesson {st.session_state.lesson}, Week {st.session_state.week} ({st.session_state.source_type}).")
                    # keep a backup for reset
                    if isinstance(st.session_state.act_df, pd.DataFrame):
                        st.session_state.act_df_backup = st.session_state.act_df.copy(deep=True)
                except Exception as e:
                    st.error(f"Couldn’t generate Activities: {e}")
# ---- Live Previews (always visible) ----
    st.markdown("<div class='h3'>MCQs Preview</div>", unsafe_allow_html=True)
    if 'mcq_df' in st.session_state and isinstance(st.session_state.mcq_df, pd.DataFrame) and len(st.session_state.mcq_df) > 0:
        mcq_edited = st.data_editor(
            st.session_state.mcq_df,
            num_rows="dynamic",
            key="mcq_editor",
            use_container_width=True,
            height=560,
            column_config={
                "Question": st.column_config.TextColumn(width="large"),
                "Option A": st.column_config.TextColumn(width="large"),
                "Option B": st.column_config.TextColumn(width="large"),
                "Option C": st.column_config.TextColumn(width="large"),
                "Option D": st.column_config.TextColumn(width="large"),
                "Explanation": st.column_config.TextColumn(width="large"),
            },
            disabled=["Order"] if "Order" in st.session_state.mcq_df.columns else None
        )
        if st.button("💾 Save MCQ edits"):
            st.session_state.mcq_df = mcq_edited
            st.toast("Saved MCQ edits")

        with st.expander("✏️ Full-width editor (one question)"):
            df = st.session_state.mcq_df
            if isinstance(df, pd.DataFrame) and len(df) > 0:
                row = st.number_input("Select question row", 0, len(df)-1, 0)
                c1, c2 = st.columns([2,1])
                with c1:
                    qtxt = st.text_area("Question", value=str(df.loc[row, "Question"]), height=160)
                    expl = st.text_area("Explanation", value=str(df.loc[row, "Explanation"]), height=100)
                with c2:
                    tier = st.selectbox("Tier", ["Low","Medium","High"], index=["Low","Medium","High"].index(str(df.loc[row, "Tier"])) if str(df.loc[row,"Tier"]) in ["Low","Medium","High"] else 0)
                    qnum = st.selectbox("Q#", [1,2,3], index=[1,2,3].index(int(df.loc[row, "Q#"])) if str(df.loc[row, "Q#"]).isdigit() else 0)
                oa = st.text_area("Option A", value=str(df.loc[row, "Option A"]), height=90)
                ob = st.text_area("Option B", value=str(df.loc[row, "Option B"]), height=90)
                oc = st.text_area("Option C", value=str(df.loc[row, "Option C"]), height=90)
                od = st.text_area("Option D", value=str(df.loc[row, "Option D"]), height=90)
                ans = st.selectbox("Answer", ["A","B","C","D"], index=["A","B","C","D"].index(str(df.loc[row, "Answer"])) if str(df.loc[row, "Answer"]) in ["A","B","C","D"] else 0)
                if st.button("💾 Save this question"):
                    df.loc[row, ["Question","Explanation","Tier","Q#","Option A","Option B","Option C","Option D","Answer"]] = [qtxt, expl, tier, qnum, oa, ob, oc, od, ans]
                    st.session_state.mcq_df = df
                    st.toast("Saved single-question edits")
    if st.button("🔄 Reset MCQs"):
        if "mcq_df_backup" in st.session_state:
            st.session_state.mcq_df = st.session_state.mcq_df_backup.copy(deep=True)
            st.toast("Restored last generated MCQs")
        else:
            st.warning("No backup found yet — generate first.")
    else:
        st.info("No MCQs to show yet — choose **MCQs** and click **Generate** above. If you generated but see nothing, add more sentences in Step 4 and try again.")

    st.markdown("<div class='h3' style='margin-top:1rem'>Activities Preview</div>", unsafe_allow_html=True)
    if 'act_df' in st.session_state and isinstance(st.session_state.act_df, pd.DataFrame) and len(st.session_state.act_df) > 0:
        act_edited = st.data_editor(
            st.session_state.act_df,
            num_rows="dynamic",
            key="act_editor",
            use_container_width=True,
            height=560,
            column_config={
                "title": st.column_config.TextColumn(width="large"),
                "objective": st.column_config.TextColumn(width="large"),
                "steps": st.column_config.TextColumn(width="large"),
                "materials": st.column_config.TextColumn(width="medium"),
                "assessment": st.column_config.TextColumn(width="large"),
            },
        )
        if st.button("💾 Save Activity edits"):
            st.session_state.act_df = act_edited
            st.toast("Saved Activity edits")

        with st.expander("✏️ Full-width editor (one activity)"):
            df = st.session_state.act_df
            if isinstance(df, pd.DataFrame) and len(df) > 0:
                row = st.number_input("Select activity row", 0, len(df)-1, 0, key="act_row")
                title = st.text_input("Title", value=str(df.loc[row, "title"]))
                c1, c2 = st.columns([2,1])
                with c1:
                    objective = st.text_area("Objective", value=str(df.loc[row, "objective"]), height=120)
                    steps = st.text_area("Steps", value=str(df.loc[row, "steps"]), height=180)
                with c2:
                    duration = st.number_input("Duration (min)", value=int(df.loc[row, "duration"]) if str(df.loc[row, "duration"]).isdigit() else 15, step=5)
                materials = st.text_area("Materials", value=str(df.loc[row, "materials"]), height=80)
                assessment = st.text_area("Assessment", value=str(df.loc[row, "assessment"]), height=120)
                if st.button("💾 Save this activity"):
                    df.loc[row, ["title","objective","steps","materials","assessment","duration"]] = [title, objective, steps, materials, assessment, duration]
                    st.session_state.act_df = df
                    st.toast("Saved single-activity edits")
    if st.button("🔄 Reset Activities"):
        if "act_df_backup" in st.session_state:
            st.session_state.act_df = st.session_state.act_df_backup.copy(deep=True)
            st.toast("Restored last generated Activities")
        else:
            st.warning("No backup found yet — generate first.")
    else:
        st.info("No Activities to show yet — choose **Activities** and click **Generate** above.")
# ===== ④ Export =====
with tab4:
    if "mcq_df" not in st.session_state and "act_df" not in st.session_state:
        st.info("Generate content in **③ Generate** to enable exports.")
        st.progress(progress_fraction()); st.stop()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Export</div>", unsafe_allow_html=True)

    st.session_state.hl_stems_docx = st.checkbox("🔆 Highlight question stems in DOCX", value=st.session_state.get("hl_stems_docx", True))
    st.markdown("<div class='export-grid'>", unsafe_allow_html=True)

    # MCQs
    st.markdown("<div class='export-card'>", unsafe_allow_html=True)
    st.markdown("<div class='export-title'>MCQs</div>", unsafe_allow_html=True)
    if "mcq_df" in st.session_state:
        st.caption(f"Context: Lesson {st.session_state.lesson} • Week {st.session_state.week} • {st.session_state.source_type}")
        if st.download_button("Download MCQs (CSV)", st.session_state.mcq_df.to_csv(index=False).encode("utf-8"),
                              f"mcqs_w{st.session_state.week:02d}_{st.session_state.source_type}.csv", "text/csv"):
            st.toast("✅ MCQs CSV download started")
        gift_txt = export_mcqs_gift(st.session_state.mcq_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
        if st.download_button("Download MCQs (Moodle GIFT)", gift_txt.encode("utf-8"),
                              f"mcqs_w{st.session_state.week:02d}_{st.session_state.source_type}.gift", "text/plain"):
            st.toast("✅ MCQs GIFT download started")
        if Document:
            mcq_docx = export_mcqs_docx(
                st.session_state.mcq_df, st.session_state.lesson, st.session_state.week,
                st.session_state.topic, highlight_stems=st.session_state.hl_stems_docx
            )
            if st.download_button("Download MCQs (Word)", mcq_docx,
                                  f"mcqs_w{st.session_state.week:02d}_{st.session_state.source_type}.docx",
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
        st.caption(f"Context: Lesson {st.session_state.lesson} • Week {st.session_state.week} • {st.session_state.source_type}")
        if st.download_button("Download Activities (CSV)", st.session_state.act_df.to_csv(index=False).encode("utf-8"),
                              f"activities_w{st.session_state.week:02d}_{st.session_state.source_type}.csv", "text/csv"):
            st.toast("✅ Activities CSV download started")
        if Document:
            act_docx = export_acts_docx(st.session_state.act_df, st.session_state.lesson, st.session_state.week, st.session_state.topic)
            if st.download_button("Download Activities (Word)", act_docx,
                                  f"activities_w{st.session_state.week:02d}_{st.session_state.source_type}.docx",
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

# ---------- Sidebar Editor & Validations (non-invasive) ----------
try:
    st.sidebar.header("Edit panel")
    kind = st.sidebar.radio("Edit", ["MCQs","Activities"], horizontal=True)
    def _val_mcqs(df: pd.DataFrame):
        issues = []
        if df is None or df.empty: return ["No MCQs."]
        need = ["Question","Option A","Option B","Option C","Option D","Answer"]
        miss = [c for c in need if c not in df.columns]
        if miss: return [f"Missing columns: {', '.join(miss)}"]
        for i, r in df.iterrows():
            if not str(r.get("Question","")).strip(): issues.append(f"Row {i+1}: empty Question")
            if str(r.get("Answer","")).upper() not in {"A","B","C","D"}: issues.append(f"Row {i+1}: Answer not A-D")
        return issues[:20]
    def _val_acts(df: pd.DataFrame):
        issues = []
        if df is None or df.empty: return ["No Activities."]
        for i, r in df.iterrows():
            if not str(r.get("title", r.get("Title",""))).strip(): issues.append(f"Row {i+1}: empty Title")
            try:
                d = int(r.get("duration", r.get("Duration (mins)", 0)))
                if d <= 0: issues.append(f"Row {i+1}: Duration must be > 0")
            except Exception:
                issues.append(f"Row {i+1}: Duration not a number")
        return issues[:20]
    if kind == "MCQs" and isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df)>0:
        df = st.session_state.mcq_df
        row = st.sidebar.number_input("Row", 0, len(df)-1, 0, step=1)
        qtxt = st.sidebar.text_area("Question", str(df.loc[row,"Question"]), height=150)
        oa = st.sidebar.text_area("Option A", str(df.loc[row,"Option A"]), height=80)
        ob = st.sidebar.text_area("Option B", str(df.loc[row,"Option B"]), height=80)
        oc = st.sidebar.text_area("Option C", str(df.loc[row,"Option C"]), height=80)
        od = st.sidebar.text_area("Option D", str(df.loc[row,"Option D"]), height=80)
        ans = st.sidebar.selectbox("Answer", ["A","B","C","D"], index=["A","B","C","D"].index(str(df.loc[row,"Answer"])) if str(df.loc[row,"Answer"]) in ["A","B","C","D"] else 0)
        expl = st.sidebar.text_area("Explanation", str(df.loc[row,"Explanation"]), height=100)
        if st.sidebar.button("Apply MCQ changes"):
            df.loc[row, ["Question","Option A","Option B","Option C","Option D","Answer","Explanation"]] = [qtxt,oa,ob,oc,od,ans,expl]
            st.session_state.mcq_df = df; st.toast("Applied MCQ changes")
        errs = _val_mcqs(df)
        (st.sidebar.success if not errs else st.sidebar.warning)(f"{'All good' if not errs else f'Checks: {len(errs)} issue(s)'}")

    # Reorder / Duplicate controls
    c_up, c_dn, c_dup = st.sidebar.columns(3)
    if c_up.button("⬆ Move up", key="mcq_up") and row > 0:
        # swap row with row-1
        df.iloc[[row-1, row]] = df.iloc[[row, row-1]].values
        st.session_state.mcq_df = df
        st.toast("Moved up")
    if c_dn.button("⬇ Move down", key="mcq_down") and row < len(df)-1:
        df.iloc[[row, row+1]] = df.iloc[[row+1, row]].values
        st.session_state.mcq_df = df
        st.toast("Moved down")
    if c_dup.button("🧬 Duplicate", key="mcq_dup"):
        top = df.iloc[:row+1]
        mid = df.iloc[row:row+1]
        bot = df.iloc[row+1:]
        st.session_state.mcq_df = pd.concat([top, mid, bot], ignore_index=True)
        st.toast("Duplicated question")
    st.sidebar.divider()
    delc1, delc2 = st.sidebar.columns([2,1])
    if delc1.button("🗑 Delete this question", key="mcq_del_init"):
        st.session_state["pending_mcq_delete"] = int(row)
        st.toast("Click CONFIRM to delete")
    if st.session_state.get("pending_mcq_delete") == int(row):
        c1, c2 = st.sidebar.columns(2)
        with c1:
            if st.button("✅ Confirm delete", key="mcq_del_confirm"):
                df = st.session_state.mcq_df
                _row_backup = df.iloc[int(row)].to_dict()
                st.session_state.undo_mcq.append({"row": int(row), "data": _row_backup})
                df = st.session_state.mcq_df
                st.session_state.mcq_df = df.drop(index=row).reset_index(drop=True)
                st.session_state.pop("pending_mcq_delete", None)
                st.toast("Deleted question")
        with c2:
            if st.button("Cancel", key="mcq_del_cancel"):
                st.session_state.pop("pending_mcq_delete", None)

    elif kind == "Activities" and isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df)>0:
        df = st.session_state.act_df
        row = st.sidebar.number_input("Row", 0, len(df)-1, 0, step=1, key="act_row_sb")
        title = st.sidebar.text_input("Title", str(df.loc[row,"title"] if "title" in df.columns else df.loc[row,"Title"]))
        objective = st.sidebar.text_area("Objective", str(df.loc[row,"objective"] if "objective" in df.columns else df.loc[row,"Objective"]), height=110)
        steps = st.sidebar.text_area("Steps", str(df.loc[row,"steps"] if "steps" in df.columns else df.loc[row,"Steps"]), height=150)
        materials = st.sidebar.text_area("Materials", str(df.loc[row,"materials"] if "materials" in df.columns else df.loc[row,"Materials"]), height=80)
        assessment = st.sidebar.text_area("Assessment", str(df.loc[row,"assessment"] if "assessment" in df.columns else df.loc[row,"Assessment"]), height=100)
        duration_val = df.loc[row,"duration"] if "duration" in df.columns else df.loc[row,"Duration (mins)"]
        try: duration = int(duration_val)
        except Exception: duration = 20
        duration = st.sidebar.number_input("Duration (mins)", duration, step=5)
        if st.sidebar.button("Apply Activity changes"):
            if "title" in df.columns:
                df.loc[row, ["title","objective","steps","materials","assessment","duration"]] = [title,objective,steps,materials,assessment,int(duration)]
            else:
                df.loc[row, ["Title","Objective","Steps","Materials","Assessment","Duration (mins)"]] = [title,objective,steps,materials,assessment,int(duration)]
            st.session_state.act_df = df; st.toast("Applied Activity changes")
        errs = _val_acts(df)
        (st.sidebar.success if not errs else st.sidebar.warning)(f"{'All good' if not errs else f'Checks: {len(errs)} issue(s)'}")

    # Reorder / Duplicate controls (Activities)
    a_up, a_dn, a_dup = st.sidebar.columns(3)
    if a_up.button("⬆ Move up", key="act_up") and row > 0:
        df.iloc[[row-1, row]] = df.iloc[[row, row-1]].values
        st.session_state.act_df = df
        st.toast("Moved up")
    if a_dn.button("⬇ Move down", key="act_down") and row < len(df)-1:
        df.iloc[[row, row+1]] = df.iloc[[row+1, row]].values
        st.session_state.act_df = df
        st.toast("Moved down")
    if a_dup.button("🧬 Duplicate", key="act_dup"):
        top = df.iloc[:row+1]
        mid = df.iloc[row:row+1]
        bot = df.iloc[row+1:]
        st.session_state.act_df = pd.concat([top, mid, bot], ignore_index=True)
        st.toast("Duplicated activity")
    st.sidebar.divider()
    # Undo last MCQ delete
    if st.sidebar.button("↩ Undo last MCQ delete"):
        if st.session_state.undo_mcq:
            last = st.session_state.undo_mcq.pop()
            df = st.session_state.mcq_df
            row = int(last.get("row", len(df)))
            data = last.get("data", {})
            try:
                restored = pd.DataFrame([data])
                st.session_state.mcq_df = pd.concat([df.iloc[:row], restored, df.iloc[row:]], ignore_index=True)
                st.toast("Restored last deleted question")
            except Exception:
                st.warning("Could not undo delete (shape mismatch).")
        else:
            st.info("Nothing to undo.")

    adelc1, adelc2 = st.sidebar.columns([2,1])
    if adelc1.button("🗑 Delete this activity", key="act_del_init"):
        st.session_state["pending_act_delete"] = int(row)
        st.toast("Click CONFIRM to delete")
    if st.session_state.get("pending_act_delete") == int(row):
        c1, c2 = st.sidebar.columns(2)
        with c1:
            if st.button("✅ Confirm delete", key="act_del_confirm"):
                df = st.session_state.act_df
                _row_backup = df.iloc[int(row)].to_dict()
                st.session_state.undo_act.append({"row": int(row), "data": _row_backup})
                df = st.session_state.act_df
                st.session_state.act_df = df.drop(index=row).reset_index(drop=True)
                st.session_state.pop("pending_act_delete", None)
                st.toast("Deleted activity")
        with c2:
            if st.button("Cancel", key="act_del_cancel"):
                st.session_state.pop("pending_act_delete", None)

except Exception as _e:
    pass
