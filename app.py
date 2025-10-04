# app.py — ADI Builder (Streamlit)
# Stable UI + outputs: MCQs (validated & mixed), Skills Activities, Revision
# DOCX + ADI-branded PPTX, deep-scan uploads, directories with +/−
# Now with richer Bloom band styling & pill highlights

from __future__ import annotations
import io, re, random, uuid
from datetime import date
from dataclasses import dataclass
from typing import List
from pathlib import Path

import streamlit as st

# ---------- Optional deps (graceful fallback if missing) ----------
try:
    from docx import Document as Docx
    from docx.shared import Pt
except Exception:
    Docx = None

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt as PptPt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
except Exception:
    Presentation = None

try:
    import fitz  # PyMuPDF for PDF parsing
except Exception:
    fitz = None

# ---------- ADI Theme ----------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#f5f5f3"
TEXT_MUTED = "#6b7280"
TEXT_SLATE = "#1f2937"

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ---------- Catalog defaults (from your screenshots) ----------
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
      /* Overall page rhythm & spacing */
      .block-container {{
        max-width: 1200px;
        padding-top: 1.4rem;  /* extra top space so header never feels cramped */
      }}

      /* Buttons */
      .stButton > button {{
          background:{ADI_GREEN}; color:#fff; border-radius:12px; border:0; padding:0.55rem 0.95rem;
          box-shadow: 0 1px 0 rgba(0,0,0,.05);
      }}
      .stButton > button:hover {{ background:{ADI_GOLD}; }}

      /* Inputs */
      .stTextInput>div>div>input,
      .stTextArea textarea,
      .stSelectbox > div > div {{
        border-radius:10px !important; border-color:#cbd5e1 !important;
      }}
      .stTextArea textarea {{ min-height: 120px; }}

      /* Tabs */
      div[data-baseweb="tab"] button[aria-selected="true"] {{
        border-bottom: 3px solid {ADI_GREEN} !important;
      }}

      /* Header card */
      div[style*="ADI Builder — Lesson Activities"] {{
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border-radius: 18px !important;
      }}

      /* Micro separator */
      .adi-title {{ height:8px; border-radius:999px; background:#eaeaea; margin:6px 0 16px 0; }}

      /* Band container (Low/Medium/High) */
      .adi-band {{
        border-radius:18px; padding:14px 16px; margin:12px 0 10px 0;
        border:1px solid #e6e6e6;
      }}
      .adi-low  {{ background:linear-gradient(180deg, #f2f9f2 0%, #ffffff 80%); }}
      .adi-med  {{ background:linear-gradient(180deg, #fff6e8 0%, #ffffff 80%); }}
      .adi-high {{ background:linear-gradient(180deg, #eef3ff 0%, #ffffff 80%); }}
      .adi-band-cap {{ float:right; color:#6b7280; font-size:13px; }}
      .adi-band.adi-active {{
        border-color:#245a34;
        box-shadow:0 0 0 2px rgba(36,90,52,.14) inset;
      }}

      /* Verb pills (stronger outline + ADI fill when selected) */
      .adi-pills {{ margin: 8px 0 2px 0; }}
      .adi-pills .stCheckbox {{
        display:inline-block; margin:4px 6px 8px 0;
      }}
      .adi-pills .stCheckbox label {{
        border:1px solid #d1d5db; border-radius:9999px;
        padding:6px 14px; display:inline-flex; align-items:center; gap:8px;
        background:#fafafa; color:#374151; transition: all .15s ease-in-out;
        box-shadow: 0 1px 0 rgba(0,0,0,.03);
      }}
      .adi-pills .stCheckbox label:hover {{
        border-color:#9ca3af; background:#f3f4f6;
      }}
      .adi-pills .stCheckbox div[role="checkbox"] {{ transform: scale(0.9); }}

      /* Band-tinted default */
      .adi-low  .stCheckbox label {{ background:#edf7ef; }}
      .adi-med  .stCheckbox label {{ background:#fff2e0; }}
      .adi-high .stCheckbox label {{ background:#e9f0ff; }}

      /* Selected state: strong ADI green pill */
      .adi-pills .stCheckbox label:has(div[role="checkbox"][aria-checked="true"]) {{
        color:#fff; background:{ADI_GREEN}; border-color:{ADI_GREEN};
        box-shadow: 0 0 0 2px rgba(36,90,52,.18) inset;
        font-weight:600;
      }}
    </style>
    """, unsafe_allow_html=True)

def header():
    logo_html = ""
    logo_path = Path("adi_logo.png")
    if logo_path.exists():
        logo_html = '<img src="adi_logo.png" style="height:34px; float:right; margin-top:-6px;" />'
    st.markdown(
        f"""
        <div style="background:{ADI_STONE};border-radius:14px;padding:14px 18px;margin:8px 0 16px 0;border:1px solid #e5e7eb">
          {logo_html}
          <div style="font-weight:800;color:{ADI_GREEN};letter-spacing:.2px;">ADI Builder — Lesson Activities & Questions</div>
          <div style="color:{TEXT_MUTED};font-size:14px">Sleek, professional and engaging. Print-ready handouts for instructors.</div>
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
            d = Docx(io.BytesIO(raw)); return "\n".join(p.text for p in d.paragraphs)
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(io.BytesIO(raw)); out=[]
            for sld in prs.slides:
                for shp in sld.shapes:
                    if hasattr(shp, "text"): out.append(shp.text)
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
        key=f"dl_{scope}_{uuid.uuid4().hex[:8]}"  # unique keys => no duplicate element id
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
def _similar_len(options:list[str], tolerance:0.55.__class__=0.55) -> bool:
    lens = [max(1, len(o)) for o in options]; return (min(lens)/max(lens)) >= tolerance
def validate_mcq_item(stem:str, options:list[str], answer_idx:int) -> tuple[bool,str]:
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
    # Fallback if validation repeatedly fails
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

# ---------- PPTX (ADI-branded Smart-TV decks) ----------
def _rgb(hex_color: str) -> RGBColor:
    hex_color = hex_color.lstrip("#")
    return RGBColor(int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16))

def _add_brand_header(slide, title_text: str, subtitle_text: str | None = None):
    left, top, width, height = Inches(0), Inches(0), Inches(13.33), Inches(1.0)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    bar.fill.solid(); bar.fill.fore_color.rgb = _rgb(ADI_GREEN); bar.line.fill.background()
    title = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(12.5), Inches(0.7)).text_frame
    title.clear(); p = title.paragraphs[0]
    p.text = title_text; p.font.size = PptPt(28); p.font.bold = True; p.font.color.rgb = RGBColor(255,255,255)
    if subtitle_text:
        sub = slide.shapes.add_textbox(Inches(0.4), Inches(1.15), Inches(12.5), Inches(0.45)).text_frame
        sub.clear(); ps = sub.paragraphs[0]
        ps.text = subtitle_text; ps.font.size = PptPt(14); ps.font.color.rgb = _rgb(TEXT_SLATE)

def _body_frame(slide):
    return slide.shapes.add_textbox(Inches(0.6), Inches(1.8), Inches(12.1), Inches(5.0)).text_frame

def mcqs_to_pptx(mcqs: List[MCQ], title: str, show_key: bool) -> bytes:
    if Presentation is None:
        st.warning("PPTX export requires python-pptx in requirements.txt"); return b""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6]); _add_brand_header(slide, title, "MCQ deck for classroom display")
    for i, q in enumerate(mcqs, 1):
        slide = prs.slides.add_slide(prs.slide_layouts[6]); _add_brand_header(slide, f"[{q.bloom}] Question {i}")
        body = _body_frame(slide); body.clear()
        p = body.paragraphs[0]; p.text = q.stem; p.font.size = PptPt(20)
        for j, c in enumerate(q.choices):
            par = body.add_paragraph(); par.text = f"{'ABCD'[j]}. {c}"; par.level = 1; par.font.size = PptPt(20)
    if show_key:
        slide = prs.slides.add_slide(prs.slide_layouts[6]); _add_brand_header(slide, "Answer Key")
        body = _body_frame(slide); body.clear()
        for i, q in enumerate(mcqs, 1):
            p = body.add_paragraph(); p.text = f"{i}. {'ABCD'[q.answer_idx]}"; p.font.size = PptPt(22)
    out = io.BytesIO(); prs.save(out); return out.getvalue()

def activities_to_pptx(cards: List[dict], title: str) -> bytes:
    if Presentation is None:
        st.warning("PPTX export requires python-pptx in requirements.txt"); return b""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6]); _add_brand_header(slide, title, "Lesson activities")
    for c in cards:
        slide = prs.slides.add_slide(prs.slide_layouts[6]); _add_brand_header(slide, f"{c['title']}  ({c['time']} min)")
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
    slide = prs.slides.add_slide(prs.slide_layouts[6]); _add_brand_header(slide, title, "Revision prompts")
    for it in items:
        slide = prs.slides.add_slide(prs.slide_layouts[6]); _add_brand_header(slide, "Revision")
        body = _body_frame(slide); body.clear()
        p = body.paragraphs[0]; p.text = it; p.font.size = PptPt(22)
    out = io.BytesIO(); prs.save(out); return out.getvalue()

# ---------- MAIN ----------
def main():
    inject_css()
    header()

    # Sidebar
    with st.sidebar:
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
    st.markdown('<div class="adi-title"></div>', unsafe_allow_html=True)
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

    # Upload deep scan
    uploaded_text = read_text_from_upload(up)
    with st.expander("Source (from upload) — optional", expanded=False):
        if up:
            with st.status("Processing upload…", expanded=True) as status:
                st.write(f"**File:** {up.name}  •  **Size:** {up.size/1024:.1f} KB")
                if uploaded_text:
                    stats = quick_stats(uploaded_text)
                    st.write(f"- Extracted **{stats['chars']:,}** chars, **{stats['words']:,}** words, **{stats['sentences']:,}** sentences")
                    if stats["top_terms"]:
                        terms = ", ".join([f"{k} ({v})" for k,v in stats["top_terms"]])
                        st.write(f"- Top terms: {terms}")
                    status.update(label="Upload parsed", state="complete")
                else:
                    status.update(label="Could not parse file (try txt/docx/pptx/pdf).", state="error")
        src = st.text_area("", value=uploaded_text or "", height=140,
                           placeholder="Any key notes extracted from your upload will appear here…")
    if up and up.name.lower().endswith(".pdf") and fitz is None:
        st.warning("PDF uploaded, but PDF parsing is not enabled on this build. Add `pymupdf==1.24.9` to requirements.txt.")

    # Bloom bands + pills (now wrapped in poppy band boxes)
    # LOW
    st.markdown(
        f'<div class="adi-band adi-low {"adi-active" if band=="LOW" else ""}">'
        f'<span class="adi-band-cap">Remember / Understand</span><b>Low (Weeks 1–4)</b>'
        f'</div>', unsafe_allow_html=True
    )
    st.markdown('<div class="adi-pills adi-low">', unsafe_allow_html=True)
    low_cols = st.columns(len(LOW_VERBS)); low_sel=[]
    for c, v in zip(low_cols, LOW_VERBS):
        with c:
            if st.checkbox(v, key=f"low_{v}", value=(band=="LOW")): low_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    # MEDIUM
    st.markdown(
        f'<div class="adi-band adi-med {"adi-active" if band=="MEDIUM" else ""}">'
        f'<span class="adi-band-cap">Apply / Analyse</span><b>Medium (Weeks 5–9)</b>'
        f'</div>', unsafe_allow_html=True
    )
    st.markdown('<div class="adi-pills adi-med">', unsafe_allow_html=True)
    med_cols = st.columns(len(MED_VERBS)); med_sel=[]
    for c, v in zip(med_cols, MED_VERBS):
        with c:
            if st.checkbox(v, key=f"med_{v}", value=(band=="MEDIUM")): med_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    # HIGH
    st.markdown(
        f'<div class="adi-band adi-high {"adi-active" if band=="HIGH" else ""}">'
        f'<span class="adi-band-cap">Evaluate / Create</span><b>High (Weeks 10–14)</b>'
        f'</div>', unsafe_allow_html=True
    )
    st.markdown('<div class="adi-pills adi-high">', unsafe_allow_html=True)
    high_cols = st.columns(len(HIGH_VERBS)); high_sel=[]
    for c, v in zip(high_cols, HIGH_VERBS):
        with c:
            if st.checkbox(v, key=f"high_{v}", value=(band=="HIGH")): high_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    picks = list(dict.fromkeys(low_sel + med_sel + high_sel))
    if not picks:
