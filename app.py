# app.py — ADI Builder (Streamlit)
# MCQs (validated & mixed), Skills Activities, Revision, Print Summary
# DOCX + ADI-branded PPTX exports, stable styling, deep-scan uploads, directory manager with +/−

from __future__ import annotations
import io, re, random, uuid, base64
from datetime import date
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from pathlib import Path

import streamlit as st

# ---------- Optional deps (graceful fallback if missing) ----------
try:
    from docx import Document as Docx
    from docx.shared import Pt
except Exception:
    Docx = None  # fall back to plain text exports

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt as PptPt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
except Exception:
    Presentation = None

# PDF support (enable via requirements.txt: pymupdf==1.24.9)
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# ---------- ADI Theme ----------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#f5f5f3"
TEXT_MUTED = "#6b7280"
TEXT_SLATE = "#1f2937"

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ---------- Catalog defaults ----------
DEFAULT_COURSES = [
    "Defense Technology Practices: Experimentation, Quality Management and Inspection (GE4-EPM)",
    "Integrated Project and Materials Management in Defense Technology (GE4-IPM)",
    "Military Vehicle and Aircraft MRO: Principles & Applications (GE4-MRO)",
    "Computation for Chemical Technologists (CT4-COM)",
    "Explosives Manufacturing (CT4-EMG)",
    "Thermofluids (CT4-TFL)",
    "Composite Manufacturing (MT4-CMG)",
    "Computer Aided Design (MT4-CAD)",
    "Machine Elements (MT4-MAE)",
    "Electrical Materials (EE4-MFC)",
    "PCB Manufacturing (EE4-PMG)",
    "Power Circuits & Transmission (EE4-PCT)",
    "Mechanical Product Dissection (MT5-MPD)",
    "Assembly Technology (MT5-AST)",
    "Aviation Maintenance (MT5-AVM)",
    "Hydraulics and Pneumatics (MT5-HYP)",
    "Computer Aided Design and Additive Manufacturing (MT5-CAD)",
    "Industrial Machining (MT5-CNC)",
    "Thermochemistry of Explosives (CT5-TCE)",
    "Separation Technologies 1 (CT5-SET)",
    "Explosives Plant Operations and Troubleshooting (CT5-POT)",
    "Coating Technologies (CT5-COT)",
    "Chemical Technology Laboratory Techniques (CT5-LAB)",
    "Chemical Process Technology (CT5-CPT)",
]
DEFAULT_COHORTS = [
    "D1-C01", "D1-E01", "D1-E02",
    "D1-M01", "D1-M02", "D1-M03", "D1-M04", "D1-M05",
    "D2-C01",
    "D2-M01", "D2-M02", "D2-M03", "D2-M04", "D2-M05", "D2-M06",
]
DEFAULT_INSTRUCTORS = [
    "GHAMZA LABEEB KHADER","DANIEL JOSEPH LAMB","NARDEEN TARIQ","FAIZ LAZAM ALSHAMMARI",
    "DR. MASHAEL ALSHAMMARI","AHMED ALBADER","Noura Aldossari","Ahmed Gasem Alharbi",
    "Mohammed Saeed Alfarhan","Abdulmalik Halawani","Dari AlMutairi","Meshari AlMutrafi",
    "Myra Crawford","Meshal Alghurabi","Ibrahim Alrawili","Michail Mavroftas",
    "Gerhard Van der Poel","Khalil Razak","Mohammed Alwuthylah","Rana Ramadan",
    "Salem Saleh Subaih","Barend Daniel Esterhuizen",
]
if "COURSES" not in st.session_state: st.session_state.COURSES = list(DEFAULT_COURSES)
if "COHORTS" not in st.session_state: st.session_state.COHORTS = list(DEFAULT_COHORTS)
if "INSTRS"  not in st.session_state: st.session_state.INSTRS  = list(DEFAULT_INSTRUCTORS)

# ---------- CSS / Branding ----------
def inject_css():
    st.markdown(f"""
    <style>
      /* App canvas */
      body {{ background:#f6f8fb; }}
      .block-container {{
        max-width: 1200px;
        padding-top: 1.0rem;
        background:#ffffff;
        border:1px solid #eef2f7;
        border-radius: 20px;
        box-shadow: 0 6px 24px rgba(0,0,0,.06);
      }}

      /* Streamlit header spacing */
      header, .css-18ni7ap {{ margin-top: 10px !important; }}

      /* Buttons */
      .stButton > button {{
          background:{ADI_GREEN}; color:#fff; border-radius:12px; border:0; padding:0.55rem 0.95rem;
          box-shadow: 0 1px 0 rgba(0,0,0,.05);
      }}
      .stButton > button:hover {{ background:{ADI_GOLD}; }}

      /* Inputs */
      .stTextInput>div>div>input, .stTextArea textarea, .stSelectbox > div > div {{
        border-radius:10px !important; border-color:#cbd5e1 !important;
      }}
      .stTextArea textarea {{ min-height: 120px; }}

      /* Tabs */
      div[data-baseweb="tab"] button[aria-selected="true"] {{
        border-bottom: 3px solid {ADI_GREEN} !important;
      }}

      /* ADI hero banner */
      .adi-hero {{
        background:{ADI_GREEN};
        color:#fff;
        border-radius:16px;
        padding:18px 20px 16px 20px;
        position:relative;
        margin: 4px 0 14px 0;
        box-shadow:0 6px 22px rgba(0,0,0,.12);
      }}
      .adi-hero__title {{ font-weight:800; font-size:20px; letter-spacing:.2px }}
      .adi-hero__sub   {{ opacity:.92; font-size:13px; margin-top:4px }}

      /* hero as a left-logo row */
      .adi-hero--row {{ display:flex; align-items:center; gap:14px; }}
      .adi-hero__logo img {{
        height:42px; width:auto; display:block; filter:brightness(0) invert(1);
      }}
      .adi-hero__text {{ display:flex; flex-direction:column; }}

      .adi-chip {{
        border:1px solid #d1d5db; border-radius:10px; padding:6px 10px; font-size:13px; color:#374151;
        background:#f9fafb; display:inline-block;
      }}

      /* Bloom bands */
      .adi-band {{ border-radius:18px; padding:14px 16px; margin:12px 0 8px 0; border:1px solid #ececec;
                  box-shadow:0 2px 10px rgba(0,0,0,.04); }}
      .adi-low  {{ background:linear-gradient(180deg, #f2f9f2 0%, #ffffff 80%); }}
      .adi-med  {{ background:linear-gradient(180deg, #fff8ec 0%, #ffffff 80%); }}
      .adi-high {{ background:linear-gradient(180deg, #f4f6ff 0%, #ffffff 80%); }}
      .adi-band-cap {{ float:right; color:#6b7280; font-size:13px; }}
      .adi-band.adi-active {{
        border-color:#245a34;
        box-shadow:0 0 0 3px rgba(36,90,52,.18) inset, 0 8px 20px rgba(36,90,52,.06);
      }}

      /* Verb pills */
      .adi-pills {{ margin-bottom: .35rem; }}
      .adi-pills .stCheckbox {{ display:inline-block; margin-right:.35rem; margin-bottom:.35rem; }}
      .adi-pills .stCheckbox label {{
        border:1px solid #d1d5db; border-radius:9999px; padding:6px 12px;
        display:inline-flex; align-items:center; gap:8px; background:#f9fafb; transition:all .2s;
        box-shadow: 0 1px 0 rgba(0,0,0,.03);
      }}
      .adi-pills .stCheckbox label:hover {{ border-color:#245a34; background:#e9f3ec; }}
      .adi-pills .stCheckbox [data-testid="stCheckbox"] input:checked + div + label {{
        color:#fff !important; background:#245a34 !important; border-color:#245a34 !important; font-weight:600;
        box-shadow:0 4px 14px rgba(36,90,52,.22);
      }}

      .stExpander > details {{ border-radius:12px; border:1px solid #ececec; background:#fafafa; }}
      .stExpander > details[open] {{ background:#fff; }}
    </style>
    """, unsafe_allow_html=True)

# Base64 logo helper
def _logo_base64() -> str | None:
    # Try path next to this file
    logo_path = Path(__file__).with_name("adi_logo.png")
    if not logo_path.exists():
        logo_path = Path("adi_logo.png")
    if logo_path.exists():
        try:
            return base64.b64encode(logo_path.read_bytes()).decode("ascii")
        except Exception:
            return None
    return None

def header():
    b64 = _logo_base64()
    logo_html = f'<img src="data:image/png;base64,{b64}" alt="ADI" />' if b64 else ""
    st.markdown(
        f"""
        <div class="adi-hero adi-hero--row">
          <div class="adi-hero__logo">{logo_html}</div>
          <div class="adi-hero__text">
            <div class="adi-hero__title">ADI Builder — Lesson Activities & Questions</div>
            <div class="adi-hero__sub">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Utilities ----------
def policy_band(week:int)->str:
    if 1 <= week <= 4: return "LOW"
    if 5 <= week <= 9: return "MEDIUM"
    return "HIGH"

LOW_VERBS = ["define","identify","list","recall","describe","label"]
MED_VERBS = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","critique","create"]
BAND_TO_VERBS = {"LOW": LOW_VERBS,"MEDIUM": MED_VERBS,"HIGH": HIGH_VERBS}

def chunk_text(s:str)->List[str]:
    if not s: return []
    parts = re.split(r"(?<=[.!?])\s+", s.strip())
    return [p.strip() for p in parts if len(p.strip())>=25][:60]

@st.cache_data(show_spinner=False)
def _read_upload_cached(name: str, raw: bytes) -> str:
    try:
        if name.endswith(".txt"):
            return raw.decode("utf-8", errors="ignore")
        if name.endswith(".docx") and Docx:
            d = Docx(io.BytesIO(raw))
            return "\n".join(p.text for p in d.paragraphs)
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(io.BytesIO(raw))
            out = []
            for sld in prs.slides:
                for shp in sld.shapes:
                    if hasattr(shp, "text"):
                        out.append(shp.text)
            return "\n".join(out)
        if name.endswith(".pdf") and fitz:
            doc = fitz.open(stream=raw, filetype="pdf")
            return "\n".join(page.get_text("text") for page in doc)
    except Exception:
        pass
    return ""

def read_text_from_upload(upload)->str:
    if upload is None: return ""
    return _read_upload_cached(upload.name.lower(), upload.read())

def safe_download(label:str,data:bytes,filename:str,mime:str,scope:str):
    st.download_button(
        label,
        data=data,
        file_name=filename,
        mime=mime,
        key=f"dl_{scope}_{uuid.uuid4().hex[:8]}"
    )

def build_title(prefix,course,lesson,week,topic,instr,cohort,lesson_date):
    return " — ".join([s for s in [
        prefix, course or None, f"Lesson {lesson} Week {week}",
        topic or None, instr or None, cohort or None,
        lesson_date.strftime("%Y-%m-%d") if lesson_date else None] if s])

def sanitize_filename(val: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", val.strip()) if val else ""

# ---------- Directory UI: selector with ➕ / − ----------
def select_with_add_delete(label: str, list_key: str, placeholder: str = "") -> str:
    options = st.session_state[list_key]
    col_sel, col_add, col_del = st.columns([0.72, 0.14, 0.14])
    with col_sel:
        choice = st.selectbox(label, options + ["➕ Add new…"], key=f"{list_key}_sel")
    with col_add:
        add_click = st.button("➕", key=f"{list_key}_add_btn", help=f"Add a new {label.lower()}")
    adding = (choice == "➕ Add new…") or add_click
    new_val = ""
    if adding:
        new_val = st.text_input(f"Add {label}", key=f"{list_key}_new",
                                placeholder=placeholder or f"Type a new {label.lower()}…")
        if st.button(f"Add {label}", key=f"{list_key}_add_confirm") and new_val.strip():
            new_val = new_val.strip()
            if new_val not in options:
                options.append(new_val); st.success(f"Added {new_val}"); st.rerun()
            else:
                st.info(f"“{new_val}” already exists.")
    with col_del:
        can_delete = choice not in ("", "➕ Add new…")
        del_click = st.button("−", key=f"{list_key}_del_btn", disabled=not can_delete,
                              help=f"Delete selected {label.lower()}")
    if can_delete and del_click:
        try:
            options.remove(choice); st.warning(f"Deleted {choice}"); st.rerun()
        except ValueError:
            pass
    return new_val if choice == "➕ Add new…" else choice

# ---------- Deep-scan helpers ----------
def quick_stats(txt: str) -> dict:
    words = re.findall(r"[A-Za-z']+", txt)
    sents = re.split(r"(?<=[.!?])\s+", txt.strip()) if txt else []
    freq = {}
    for w in words:
        w2 = w.lower()
        if len(w2) <= 3:
            continue
        freq[w2] = freq.get(w2, 0) + 1
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    return {"chars": len(txt), "words": len(words), "sentences": len([s for s in sents if s]), "top_terms": top}

# ---------- MCQs ----------
@dataclass
class MCQ:
    stem:str; choices:List[str]; answer_idx:int; bloom:str

def make_mcq(seed_text:str,verb:str,i:int)->MCQ:
    base=re.sub(r"\s+"," ",seed_text.strip())
    stem=f"{i+1}. {verb.capitalize()} the best answer based on the notes: {base[:160]}…"
    correct=f"{verb.capitalize()} the main concept accurately."
    distractors=[
        f"{verb.capitalize()} a partially correct idea.",
        f"{verb.capitalize()} an unrelated detail.",
        f"{verb.capitalize()} the concept but misapply it."
    ]
    choices=[correct]+distractors
    random.shuffle(choices)
    answer_idx=choices.index(correct)
    return MCQ(stem,choices,answer_idx,"LOW")  # bloom updated later

def allocate_mcq_mix(n:int, bloom_focus:str, selected_verbs:list[str]) -> list[dict]:
    focus = (bloom_focus or "LOW").upper()
    if focus == "LOW":
        mix = {"LOW": 0.80, "MEDIUM": 0.20, "HIGH": 0.00}
    elif focus == "MEDIUM":
        mix = {"LOW": 0.20, "MEDIUM": 0.60, "HIGH": 0.20}
    else:
        mix = {"LOW": 0.00, "MEDIUM": 0.40, "HIGH": 0.60}
    counts = {b: int(round(n * p)) for b, p in mix.items()}
    delta = n - sum(counts.values())
    if delta:
        largest = max(counts, key=lambda k: counts[k]); counts[largest] += delta
    verbs = selected_verbs or BAND_TO_VERBS[focus]
    slots = []
    for bloom in ["LOW","MEDIUM","HIGH"]:
        for i in range(counts[bloom]):
            slots.append({"verb": verbs[i % len(verbs)], "bloom": bloom})
    if n >= 5 and len({s["bloom"] for s in slots}) == 1:
        slots[-1]["bloom"] = "MEDIUM" if slots[-1]["bloom"] == "LOW" else "LOW"
    random.shuffle(slots)
    return slots

BANNED_PATTERN = re.compile(
    r"\b(all\s*of\s*the\s*above|none\s*of\s*the\s*above|all\s*of\s*these|none\s*of\s*these|"
    r"both\s*a\s*and\s*b|true|false|true\/false|t\/f)\b",
    flags=re.IGNORECASE
)
def _looks_true_false(options:list[str]) -> bool:
    normalized = [o.strip().lower() for o in options]
    return set(normalized) in ({"true","false"}, {"false","true"})
def _similar_len(options:list[str], tolerance:float=0.55) -> bool:
    lens = [max(1, len(o)) for o in options]; return (min(lens)/max(lens)) >= tolerance
def validate_mcq_item(stem:str, options:list[str], answer_idx:int) -> Tuple[bool,str]:
    if len(options) != 4: return False, "Need exactly 4 options."
    if not (0 <= answer_idx < 4): return False, "Answer index out of range."
    if BANNED_PATTERN.search(stem or ""): return False, "Banned phrase in stem."
    for o in options:
        if not o or BANNED_PATTERN.search(o): return False, "Banned phrase in options."
    if _looks_true_false(options): return False, "True/False pattern not allowed."
    if len(set(o.strip().lower() for o in options)) < 4: return False, "Duplicate options detected."
    if not _similar_len(options): return False, "Options vary too much in length."
    return True, ""

def make_validated_mcq(seed_text:str, verb:str, bloom:str, i:int, attempts:int=4) -> MCQ:
    for _ in range(attempts):
        q = make_mcq(seed_text, verb, i); q.bloom = bloom
        ok, _ = validate_mcq_item(q.stem, q.choices, q.answer_idx)
        if ok: return q
    stem = f"{i+1}. {verb.capitalize()} the best answer based on the notes."
    correct = f"{verb.capitalize()} the main concept accurately."
    alt = [f"{verb.capitalize()} a partially correct idea from the notes.",
           f"{verb.capitalize()} a plausible but incorrect detail.",
           f"{verb.capitalize()} the concept, but misapply it."]
    options = [correct] + random.sample(alt, 3); random.shuffle(options)
    answer_idx = options.index(correct)
    return MCQ(stem, options, answer_idx, bloom)

def build_mcqs(source:str, count:int, verbs:list[str], bloom_focus:str) -> List[MCQ]:
    sents = chunk_text(source) or [source or "Instructor-provided notes."]
    plan = allocate_mcq_mix(count, bloom_focus, verbs)
    items, seen_stems = [], set()
    for i, slot in enumerate(plan):
        v, b = slot["verb"], slot["bloom"]
        q = make_validated_mcq(sents[i % len(sents)], v, b, i)
        if q.stem in seen_stems:
            q = make_validated_mcq(sents[(i+1) % len(sents)], v, b, i)
        seen_stems.add(q.stem); items.append(q)
    random.shuffle(items); return items

def mcqs_to_docx(mcqs:List[MCQ],title:str,show_key:bool)->bytes:
    if not Docx:
        buf=io.StringIO(); buf.write(title+"\n\n")
        for q in mcqs:
            buf.write(f"[{q.bloom}] {q.stem}\n")
            for j,c in enumerate(q.choices): buf.write(f"  {'ABCD'[j]}. {c}\n")
            buf.write("\n")
        if show_key:
            buf.write("Answer Key:\n")
            for i,q in enumerate(mcqs,1): buf.write(f"{i}. {'ABCD'[q.answer_idx]}\n")
        return buf.getvalue().encode("utf-8")
    doc=Docx(); style=doc.styles["Normal"]; style.font.name="Calibri"; style.font.size=Pt(11)
    doc.add_heading(title,level=1)
    for q in mcqs:
        doc.add_paragraph(f"[{q.bloom}] {q.stem}")
        for j,c in enumerate(q.choices): doc.add_paragraph(f"{'ABCD'[j]}. {c}")
        doc.add_paragraph("")
    if show_key:
        doc.add_heading("Answer Key",level=2)
        for i,q in enumerate(mcqs,1): doc.add_paragraph(f"{i}. {'ABCD'[q.answer_idx]}")
    b=io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- Activities ----------
def build_activity_cards(src:str, verbs:List[str], count:int, minutes_each:int)->List[dict]:
    base=chunk_text(src) or [src or "Topic notes"]
    out=[]
    for i in range(count):
        v = verbs[i % len(verbs or ['apply'])]
        snippet=re.sub(r"\s+"," ",base[i%len(base)])[:120]
        out.append({
            "title": f"{v.capitalize()} task #{i+1}",
            "objective": f"Students will {v} core ideas using the provided notes/context.",
            "time": minutes_each,
            "materials": ["Notes/handout", "Worksheet", "Pen/highlighter"],
            "steps": [
                f"Review the excerpt: “{snippet}…”",
                f"Work in pairs to {v} the concept on a simple example.",
                "Record your reasoning and result in the worksheet.",
                "Share one insight with the class."
            ],
            "evidence": "Completed worksheet (photo or upload).",
            "assessment": ["Meets objective", "Clear reasoning", "Accurate outcome"]
        })
    return out

def activities_to_docx(cards:List[dict],title:str)->bytes:
    if not Docx:
        lines=[title,""]
        for c in cards:
            lines += [
                f"{c['title']}  ({c['time']} min)",
                f"Objective: {c['objective']}",
                f"Materials: {', '.join(c['materials'])}",
                "Steps:"
            ]
            lines += [f"  - {s}" for s in c["steps"]]
            lines += [f"Evidence: {c['evidence']}", f"Assessment: {', '.join(c['assessment'])}", ""]
        return ("\n".join(lines)).encode("utf-8")
    doc=Docx(); s=doc.styles["Normal"]; s.font.name="Calibri"; s.font.size=Pt(11)
    doc.add_heading(title,level=1)
    for c in cards:
        doc.add_heading(f"{c['title']}  ({c['time']} min)", level=2)
        doc.add_paragraph(f"Objective: {c['objective']}")
        doc.add_paragraph(f"Materials: {', '.join(c['materials'])}")
        doc.add_paragraph("Steps:")
        for step in c["steps"]: doc.add_paragraph(step, style=None)
        doc.add_paragraph(f"Evidence: {c['evidence']}")
        doc.add_paragraph(f"Assessment: {', '.join(c['assessment'])}")
        doc.add_paragraph("")
    b=io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- Revision ----------
def build_revision(src:str,count:int=8)->List[str]:
    bits=chunk_text(src) or [src or "Topic notes"]; out=[]
    for i in range(count):
        sn=re.sub(r"\s+"," ",bits[i%len(bits)])[:110]
        out.append(f"{i+1}. Recall: Summarize the key point from — “{sn}…”")
    return out

def revision_to_docx(items:List[str],title:str)->bytes:
    if not Docx: return ("\n".join([title,""]+items)).encode("utf-8")
    doc=Docx(); s=doc.styles["Normal"]; s.font.name="Calibri"; s.font.size=Pt(11)
    doc.add_heading(title,level=1)
    doc.add_heading("Key Facts & Prompts", level=2)
    for it in items: doc.add_paragraph(it)
    b=io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- PPTX EXPORTERS (ADI-branded Smart-TV decks) ----------
def _rgb(hex_color: str) -> RGBColor:
    hex_color = hex_color.lstrip("#")
    return RGBColor(int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16))

def _add_brand_header(slide, title_text: str, subtitle_text: str | None = None):
    left, top, width, height = Inches(0), Inches(0), Inches(13.33), Inches(1.0)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    bar.fill.solid(); bar.fill.fore_color.rgb = _rgb(ADI_GREEN)
    bar.line.fill.background()
    title = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(12.5), Inches(0.7)).text_frame
    title.clear()
    p = title.paragraphs[0]; p.text = title_text; p.font.size = PptPt(28); p.font.bold = True
    p.font.color.rgb = RGBColor(255,255,255)
    if subtitle_text:
        sub = slide.shapes.add_textbox(Inches(0.4), Inches(1.15), Inches(12.5), Inches(0.45)).text_frame
        sub.clear()
        ps = sub.paragraphs[0]; ps.text = subtitle_text; ps.font.size = PptPt(14)
        ps.font.color.rgb = _rgb(TEXT_SLATE)

def _body_frame(slide):
    return slide.shapes.add_textbox(Inches(0.6), Inches(1.8), Inches(12.1), Inches(5.0)).text_frame

def mcqs_to_pptx(mcqs: List[MCQ], title: str, show_key: bool) -> bytes:
    if Presentation is None:
        st.warning("PPTX export requires python-pptx in requirements.txt"); return b""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_brand_header(slide, title, "MCQ deck for classroom display")
    for i, q in enumerate(mcqs, 1):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _add_brand_header(slide, f"[{q.bloom}] Question {i}")
        body = _body_frame(slide); body.clear()
        p = body.paragraphs[0]; p.text = q.stem; p.font.size = PptPt(20)
        for j, c in enumerate(q.choices):
            par = body.add_paragraph(); par.text = f"{'ABCD'[j]}. {c}"; par.level = 1; par.font.size = PptPt(20)
    if show_key:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _add_brand_header(slide, "Answer Key")
        body = _body_frame(slide); body.clear()
        for i, q in enumerate(mcqs, 1):
            p = body.add_paragraph(); p.text = f"{i}. {'ABCD'[q.answer_idx]}"; p.font.size = PptPt(22)
    out = io.BytesIO(); prs.save(out); return out.getvalue()

def activities_to_pptx(cards: List[dict], title: str) -> bytes:
    if Presentation is None:
        st.warning("PPTX export requires python-pptx in requirements.txt"); return b""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_brand_header(slide, title, "Lesson activities")
    for c in cards:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _add_brand_header(slide, f"{c['title']}  ({c['time']} min)")
        body = _body_frame(slide); body.clear()
        p = body.paragraphs[0]; p.text = f"Objective: {c['objective']}"; p.font.size = PptPt(20)
        p = body.add_paragraph(); p.text = f"Materials: {', '.join(c['materials'])}"; p.level = 1; p.font.size = PptPt(18)
        p = body.add_paragraph(); p.text = "Steps:"; p.font.size = PptPt(20)
        for idx, step in enumerate(c["steps"], 1):
            s = body.add_paragraph(); s.text = f"{idx}. {step}"; s.level = 1; s.font.size = PptPt(18)
        p = body.add_paragraph(); p.text = f"Evidence: {c['evidence']}"; p.font.size = PptPt(18)
        p = body.add_paragraph(); p.text = f"Assessment: {', '.join(c['assessment'])}"; p.font.size = PptPt(18)
    out = io.BytesIO(); prs.save(out); return out.getvalue()

def revision_to_pptx(items: List[str], title: str) -> bytes:
    if Presentation is None:
        st.warning("PPTX export requires python-pptx in requirements.txt"); return b""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_brand_header(slide, title, "Revision prompts")
    for it in items:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _add_brand_header(slide, "Revision")
        body = _body_frame(slide); body.clear()
        p = body.paragraphs[0]; p.text = it; p.font.size = PptPt(22)
    out = io.BytesIO(); prs.save(out); return out.getvalue()

# ---------- SUMMARY (print-friendly) ----------
def _context_snapshot(course, cohort, instr, lesson_date, lesson, week, topic, band, picks):
    return {
        "Course": course or "—",
        "Cohort": cohort or "—",
        "Instructor": instr or "—",
        "Date": lesson_date.strftime("%Y-%m-%d") if lesson_date else "—",
        "Lesson": f"{lesson}",
        "Week": f"{week} ({band.title()})",
        "Topic / Outcome": topic or "—",
        "Selected verbs": ", ".join(picks) if picks else "—",
    }

def summary_to_docx(ctx: dict, mcqs: list | None, acts: list | None, revs: list | None, title: str) -> bytes:
    if Docx is None:
        out = io.StringIO()
        out.write(title + "\n\n")
        out.write("Context\n-------\n")
        for k,v in ctx.items(): out.write(f"{k}: {v}\n")
        out.write("\n")
        if mcqs:
            out.write("MCQs (stems only)\n-----------------\n")
            for q in mcqs: out.write(f"- [{q.bloom}] {q.stem}\n")
            out.write("\n")
        if acts:
            out.write("Activities\n----------\n")
            for a in acts: out.write(f"- {a['title']} ({a['time']} min) — {a['objective']}\n")
            out.write("\n")
        if revs:
            out.write("Revision\n--------\n")
            for r in revs: out.write(f"- {r}\n")
        return out.getvalue().encode("utf-8")

    doc = Docx()
    style = doc.styles["Normal"]; style.font.name = "Calibri"; style.font.size = Pt(11)
    doc.add_heading(title, level=1)

    doc.add_heading("Context", level=2)
    for k,v in ctx.items(): doc.add_paragraph(f"{k}: {v}")

    if mcqs:
        doc.add_heading("MCQs (stems only)", level=2)
        for q in mcqs:
            doc.add_paragraph(f"[{q.bloom}] {q.stem}")

    if acts:
        doc.add_heading("Activities", level=2)
        for a in acts:
            doc.add_paragraph(f"{a['title']} ({a['time']} min) — {a['objective']}")

    if revs:
        doc.add_heading("Revision", level=2)
        for r in revs:
            doc.add_paragraph(r)

    buf = io.BytesIO(); doc.save(buf); return buf.getvalue()

# ---------- MAIN ----------
def main():
    inject_css()
    header()

    # Sidebar
    with st.sidebar:
        # optional tiny logo for constant branding
        b64 = _logo_base64()
        if b64:
            st.image(f"data:image/png;base64,{b64}", caption="ADI", use_column_width=False)

        st.caption("Upload (optional)")
        up = st.file_uploader("Drag & drop file", type=["txt","docx","pptx","pdf"],
                              help="We parse .txt, .docx, .pptx, and .pdf", label_visibility="collapsed")

        st.caption("Course details")
        course = select_with_add_delete("Course name","COURSES","e.g., Electrical Materials (EE4-MFC)")
        cohort = select_with_add_delete("Class / Cohort","COHORTS","e.g., Cohort 2: T3-24-25 (D1)")
        instr  = select_with_add_delete("Instructor name","INSTRS","Type instructor’s full name…")
        lesson_date = st.date_input("Date", value=date.today())

        st.caption("Context")
        c1,c2 = st.columns(2)
        with c1: lesson = st.selectbox("Lesson",[1,2,3,4,5],0)
        with c2: week   = st.selectbox("Week", list(range(1,15)), 0)

        st.markdown(f"<div style='font-size:12px;color:{TEXT_MUTED};margin-top:2px'>"
                    f"ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.</div>", unsafe_allow_html=True)

        with st.expander("Manage directory (optional)"):
            st.subheader("Courses — bulk import")
            bulk = st.text_area("Paste course names (one per line)", height=120, key="bulk_courses")
            if st.button("Import courses", key="btn_import_courses"):
                new_items = [x.strip() for x in bulk.splitlines() if x.strip()]
                st.session_state.COURSES.extend([c for c in new_items if c not in st.session_state.COURSES])
                st.success(f"Imported {len(new_items)} courses.")

    # Right pane
    band = policy_band(int(week))
    focus_color = {"LOW":"#dff7e8","MEDIUM":"#ffe7cc","HIGH":"#dfe8ff"}[band]

    gc1, gc2 = st.columns([1,1])
    with gc1:
        st.caption("Topic / Outcome (optional)")
        topic = st.text_input("", value="", placeholder="Module description, knowledge & skills outcomes")
    with gc2:
        st.caption("Bloom focus (auto)")
        st.markdown(f'<span class="adi-chip" style="background:{focus_color}">Week {week}: '
                    f'{"Low" if band=="LOW" else "Medium" if band=="MEDIUM" else "High"}</span>',
                    unsafe_allow_html=True)

    # Upload deep scan (no nested status)
    uploaded_text = read_text_from_upload(up)
    with st.expander("Source (from upload) — optional", expanded=False):
        if up:
            st.write(f"**File:** {up.name}  •  **Size:** {up.size/1024:.1f} KB")
            if uploaded_text:
                stats = quick_stats(uploaded_text)
                st.success("Upload parsed successfully.")
                st.write(
                    f"- Extracted **{stats['chars']:,}** chars, **{stats['words']:,}** words, "
                    f"**{stats['sentences']:,}** sentences"
                )
                if stats["top_terms"]:
                    terms = ", ".join([f"{k} ({v})" for k,v in stats["top_terms"]])
                    st.write(f"- Top terms: {terms}")
            else:
                st.error("Could not parse file (try TXT/DOCX/PPTX/PDF).")

        src = st.text_area(
            "",
            value=uploaded_text or "",
            height=140,
            placeholder="Any key notes extracted from your upload will appear here…",
        )
    if up and up.name.lower().endswith(".pdf") and fitz is None:
        st.warning("PDF uploaded, but PDF parsing is not enabled on this build. Add `pymupdf==1.24.9` to requirements.txt.")

    # Bloom bands + pills
    low_active  = "adi-active" if band == "LOW" else ""
    med_active  = "adi-active" if band == "MEDIUM" else ""
    high_active = "adi-active" if band == "HIGH" else ""

    st.markdown(f'<div class="adi-band adi-low {low_active}">'
                f'<span class="adi-band-cap">Remember / Understand</span><b>Low (Weeks 1–4)</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="adi-pills">', unsafe_allow_html=True)
    low_cols = st.columns(len(LOW_VERBS)); low_sel=[]
    for c, v in zip(low_cols, LOW_VERBS):
        with c:
            if st.checkbox(v, key=f"low_{v}", value=(band=="LOW")): low_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="adi-band adi-med {med_active}">'
                f'<span class="adi-band-cap">Apply / Analyse</span><b>Medium (Weeks 5–9)</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="adi-pills">', unsafe_allow_html=True)
    med_cols = st.columns(len(MED_VERBS)); med_sel=[]
    for c, v in zip(med_cols, MED_VERBS):
        with c:
            if st.checkbox(v, key=f"med_{v}", value=(band=="MEDIUM")): med_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="adi-band adi-high {high_active}">'
                f'<span class="adi-band-cap">Evaluate / Create</span><b>High (Weeks 10–14)</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="adi-pills">', unsafe_allow_html=True)
    high_cols = st.columns(len(HIGH_VERBS)); high_sel=[]
    for c, v in zip(high_cols, HIGH_VERBS):
        with c:
            if st.checkbox(v, key=f"high_{v}", value=(band=="HIGH")): high_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    picks = list(dict.fromkeys(low_sel + med_sel + high_sel))
    if not picks:
        st.info("Pick at least one Bloom verb block above (you can select multiple). Using the auto-selected week focus for now.")
        picks = BAND_TO_VERBS[band]

    # ------------------ TABS ------------------
    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision", "Print Summary"])

    # === MCQs ===
    with tabs[0]:
        colL, colR = st.columns([1,1])
        with colL: mcq_n = st.selectbox("How many MCQs?", [5,10,15,20,30], index=1)
        with colR: show_key = st.checkbox("Include answer key in export", True)
        if st.button("Generate MCQs", type="primary", key="btn_mcq"):
            source_text = src or "Instructor-provided notes about this week’s topic."
            qs = build_mcqs(source_text, mcq_n, picks, bloom_focus=band)
            st.session_state["last_mcqs"] = qs
            st.success(f"Generated {len(qs)} MCQs (mixed Bloom; no All/None/True/False).")
            for q in qs:
                st.markdown(f"**[{q.bloom}] {q.stem}**")
                for j, copt in enumerate(q.choices):
                    st.markdown(f"- {'ABCD'[j]}. {copt}")
                st.markdown("<hr/>", unsafe_allow_html=True)
            title = build_title("ADI MCQs", course, lesson, week, topic, instr, cohort, lesson_date)
            doc = mcqs_to_docx(qs, title, show_key)
            fname = f"adi_mcqs{'_' + sanitize_filename(course) if course else ''}.docx"
            safe_download("⬇️ Download MCQs (.docx)", doc, fname,
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "mcqs_docx")
            ppt = mcqs_to_pptx(qs, title, show_key)
            if ppt:
                fname_ppt = f"adi_mcqs{'_' + sanitize_filename(course) if course else ''}.pptx"
                safe_download("📽️ Download MCQs (.pptx)", ppt, fname_ppt,
                              "application/vnd.openxmlformats-officedocument.presentationml.presentation", "mcqs_pptx")

    # === Activities ===
    with tabs[1]:
        c1, c2 = st.columns([1,1])
        with c1: act_lessons = st.selectbox("Activities per lesson", [1,2,3,4], index=1)
        with c2: act_time = st.slider("Minutes per activity", 5, 60, step=5, value=15)
        act_count = act_lessons
        if st.button("Generate Activities", key="btn_act"):
            source_text = src or "Topic notes"
            cards = build_activity_cards(source_text, picks, act_count, act_time)
            st.session_state["last_activities"] = cards
            st.success(f"Generated {len(cards)} activity card(s) — {act_time} min each.")
            for c in cards:
                st.markdown(f"### {c['title']}  ({c['time']} min)")
                st.markdown(f"**Objective:** {c['objective']}")
                st.markdown(f"**Materials:** {', '.join(c['materials'])}")
                st.markdown("**Steps:**")
                for sstep in c["steps"]:
                    st.markdown(f"- {sstep}")
                st.markdown(f"**Evidence:** {c['evidence']}")
                st.markdown(f"**Assessment:** {', '.join(c['assessment'])}")
                st.markdown("---")
            title = build_title(f"ADI Activities ({act_lessons} × {act_time} min)",
                                course, lesson, week, topic, instr, cohort, lesson_date)
            doc = activities_to_docx(cards, title)
            fname = f"adi_activities{'_' + sanitize_filename(course) if course else ''}.docx"
            safe_download("⬇️ Download Activities (.docx)", doc, fname,
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "activities_docx")
            ppt = activities_to_pptx(cards, title)
            if ppt:
                fname_ppt = f"adi_activities{'_' + sanitize_filename(course) if course else ''}.pptx"
                safe_download("📽️ Download Activities (.pptx)", ppt, fname_ppt,
                              "application/vnd.openxmlformats-officedocument.presentationml.presentation", "activities_pptx")

    # === Revision ===
    with tabs[2]:
        rev_n = st.selectbox("How many revision items?", [6,8,10,12], index=1)
        if st.button("Generate Revision Items", key="btn_rev"):
            source_text = src or "Topic notes"
            rev = build_revision(source_text, rev_n)
            st.session_state["last_revision"] = rev
            st.success(f"Generated {len(rev)} revision prompts.")
            for r in rev: st.markdown(r)
            title = build_title("ADI Revision", course, lesson, week, topic, instr, cohort, lesson_date)
            doc = revision_to_docx(rev, title)
            fname = f"adi_revision{'_' + sanitize_filename(course) if course else ''}.docx"
            safe_download("⬇️ Download Revision (.docx)", doc, fname,
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "revision_docx")
            ppt = revision_to_pptx(rev, title)
            if ppt:
                fname_ppt = f"adi_revision{'_' + sanitize_filename(course) if course else ''}.pptx"
                safe_download("📽️ Download Revision (.pptx)", ppt, fname_ppt,
                              "application/vnd.openxmlformats-officedocument.presentationml.presentation", "revision_pptx")

    # === Print Summary ===
    with tabs[3]:
        st.caption("A single, printable overview of your session context and the latest generated content.")
        ctx = _context_snapshot(course, cohort, instr, lesson_date, lesson, week, topic, band, picks)

        st.subheader("Context")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Course:** {ctx['Course']}")
            st.write(f"**Cohort:** {ctx['Cohort']}")
            st.write(f"**Instructor:** {ctx['Instructor']}")
            st.write(f"**Date:** {ctx['Date']}")
        with c2:
            st.write(f"**Lesson:** {ctx['Lesson']}")
            st.write(f"**Week:** {ctx['Week']}")
            st.write(f"**Topic / Outcome:** {ctx['Topic / Outcome']}")
            st.write(f"**Selected verbs:** {ctx['Selected verbs']}")

        st.markdown("---")
        mcqs = st.session_state.get("last_mcqs")
        acts = st.session_state.get("last_activities")
        revs = st.session_state.get("last_revision")

        has_any = False
        if mcqs:
            has_any = True
            st.subheader(f"MCQs (latest set: {len(mcqs)})")
            for i, q in enumerate(mcqs, 1):
                st.markdown(f"- **Q{i} [{q.bloom}]** {q.stem}")

        if acts:
            has_any = True
            st.subheader(f"Activities (latest set: {len(acts)})")
            for a in acts:
                st.markdown(f"- **{a['title']}** ({a['time']} min) — {a['objective']}")

        if revs:
            has_any = True
            st.subheader(f"Revision (latest set: {len(revs)})")
            for r in revs:
                st.markdown(f"- {r}")

        if not has_any:
            st.info("No generated content found yet. Create MCQs/Activities/Revision in their tabs and come back here.")

        st.markdown("---")
        title = build_title("ADI Print Summary", course, lesson, week, topic, instr, cohort, lesson_date)
        doc = summary_to_docx(ctx, mcqs, acts, revs, title)
        fname = f"adi_summary{'_' + sanitize_filename(course) if course else ''}.docx"
        safe_download("🖨️ Download Summary (.docx)", doc, fname,
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "summary_docx")

        st.caption("Tip: you can also print this page directly from your browser (Ctrl/Cmd + P).")

    st.markdown(f"<div style='color:{TEXT_MUTED};font-size:12px;margin-top:18px'>"
                f"Styling is locked via .streamlit/config.toml and inject_css(). Keys for downloads are unique to avoid duplicate-element errors."
                f"</div>", unsafe_allow_html=True)

if __name__=="__main__":
    main()
