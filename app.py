# app.py
# ADI Builder — Lesson Activities, MCQs, Revision
# API-free generators + Hybrid Course Packs + LMS Importer + Lesson Plan ingestor
# Instructor-aware variation (3-way partition) + Simple Mode (MCQs / Activities / Revision / Bundle)
import streamlit as st
# ...your other imports...

import io, os, re, time, hashlib, random, json, glob, csv, textwrap
from typing import List, Optional, Tuple, Dict
from collections import Counter

import streamlit as st

# Lightweight NLP
import nltk
from nltk.tokenize import sent_tokenize
nltk.download("punkt", quiet=True)

from sklearn.feature_extraction.text import TfidfVectorizer

# Parsers
from docx import Document as DocxDocument
from pptx import Presentation as PptxPresentation
from pypdf import PdfReader
try:
    import fitz   # PyMuPDF (optional)
except Exception:
    fitz = None

import xml.etree.ElementTree as ET

def _rerun():
    """Works on both new and old Streamlit versions."""
    try:
        st.rerun()                     # Streamlit ≥1.27
    except Exception:
        try:
            st.experimental_rerun()    # older Streamlit
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Theming
# ──────────────────────────────────────────────────────────────────────────────

PRIMARY = "#245a34"
ACCENT_BG = "#eef5ef"
PILL_BG = "#f3f4f3"

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

st.markdown(f"""
<style>
.adi-banner {{
  background:{PRIMARY}; color:#fff; border-radius:12px; padding:12px 18px; margin:8px 0 10px 0;
}}
.adi-subtle {{ color:#dfe9e1; font-size:12px; }}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{ border-bottom: 3px solid {PRIMARY}; }}
.bloom-row.low  {{ background:#f7faf7; border-radius:10px; padding:10px; }}
.bloom-row.med  {{ background:#f1f7f1; border-radius:10px; padding:10px; }}
.bloom-row.high {{ background:#ebf4eb; border-radius:10px; padding:10px; }}
.verb-pill {{
  display:inline-block; margin:6px 10px 6px 0; padding:10px 18px; border-radius:999px;
  background:{PILL_BG}; border:1px solid #e6e6e6; color:#222; font-weight:500;
}}
.verb-pill.active {{
  background:{ACCENT_BG}; border-color:{PRIMARY}; box-shadow:0 0 0 1px {PRIMARY} inset; color:#1f3a25;
}}
.badge {{
  display:inline-block; padding:4px 10px; border-radius:999px; background:#f2ecdc; color:#5c4b12; font-weight:600; font-size:12px;
}}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Staff directory (used for per-instructor variation & stamping)
# ──────────────────────────────────────────────────────────────────────────────

STAFF = [
    "GHAMZA LABEEB KHADER",
    "DANIEL JOSEPH LAMB",
    "NARDEEN TARIQ",
    "FAIZ LAZAM ALSHAMMARI",
    "DR. MASHAEL ALSHAMMARI",
    "AHMED ALBADER",
    "Noura Aldossari",
    "Ahmed Gasem Alharbi",
    "Mohammed Saeed Alfarhan",
    "Abdulmalik Halawani",
    "Dari AlMutairi",
    "Meshari AlMutrafi",
    "Myra Crawford",
    "Meshal Alghurabi",
    "Ibrahim Alrawili",
    "Michail Mavroftas",
    "Gerhard Van der Poel",
    "Khalil Razak",
    "Mohammed Alwuthylah",
    "Rana Ramadan",
    "Salem Saleh Subaih",
    "Barend Daniel Esterhuizen",
]

# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────

def sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    sents = [s.strip() for s in sent_tokenize(text)]
    return [s for s in sents if 40 <= len(s) <= 240]

def tfidf_keyterms(text: str, top_k: int = 40) -> List[str]:
    sents = sentences(text)
    if not sents:
        return []
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2), min_df=1, max_df=0.9)
    X = vec.fit_transform(sents)
    scores = X.sum(axis=0).A1
    terms = vec.get_feature_names_out()
    ranked = [t for _, t in sorted(zip(scores, terms), reverse=True)]
    ranked = [r for r in ranked if re.search(r"[A-Za-z]", r)]
    return ranked[:top_k]

def hash_seed(*parts) -> int:
    s = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) % (2**32)

def bloom_from_week(week: int) -> str:
    if week <= 4: return "Low"
    if week <= 9: return "Medium"
    return "High"

def partition_view(items: List[str], instructor_key: str, buckets: int = 3) -> List[str]:
    """
    Deterministically select ~1/buckets of items for a given instructor_key.
    Guarantees minimal overlap across instructors teaching the same slot.
    """
    if not instructor_key or buckets < 2:
        return items
    idx = (hash_seed(instructor_key) % buckets)
    return [s for i, s in enumerate(items) if (i % buckets) == idx]

# ──────────────────────────────────────────────────────────────────────────────
# Built-in Course Packs + Seeding from your course list
# ──────────────────────────────────────────────────────────────────────────────

COURSE_LIST = [
    ("Defense Technology Practices: Experimentation, Quality Management and Inspection", "GE4-EPM"),
    ("Integrated Project and Materials Management in Defense Technology", "GE4-IPM"),
    ("Military Vehicle and Aircraft MRO: Principles & Applications", "GE4-MRO"),
    ("Computation for Chemical Technologists", "CT4-COM"),
    ("Explosives Manufacturing", "CT4-EMG"),
    ("Thermofluids", "CT4-TFL"),
    ("Composite Manufacturing", "MT4-CMG"),
    ("Computer Aided Design", "MT4-CAD"),
    ("Machine Elements", "MT4-MAE"),
    ("Electrical Materials", "EE4-MFC"),
    ("PCB Manufacturing", "EE4-PMG"),
    ("Power Circuits & Transmission", "EE4-PCT"),
    ("Mechanical Product Dissection", "MT5-MPD"),
    ("Assembly Technology", "MT5-AST"),
    ("Aviation Maintenance", "MT5-AVM"),
    ("Hydraulics and Pneumatics", "MT5-HYP"),
    ("Computer Aided Design and Additive Manufacturing", "MT5-CAD"),
    ("Industrial Machining", "MT5-CNC"),
    ("Thermochemistry of Explosives", "CT5-TCE"),
    ("Separation Technologies 1", "CT5-SET"),
    ("Explosives Plant Operations and Troubleshooting", "CT5-POT"),
    ("Coating Technologies", "CT5-COT"),
    ("Chemical Technology Laboratory Techniques", "CT5-LAB"),
    ("Chemical Process Technology", "CT5-CPT")
]

BUILTIN_COURSE_PACKS = {
    "General": {"glossary": [], "activities": {}},

    "CNC Machining": {
        "glossary": [
            "toolpath","G-code","M-code","workpiece","spindle speed","feed rate",
            "coolant","fixture","tolerance","profiling","pocketing","chip load",
            "end mill","lathe","roughing","finishing"
        ],
        "activities": {
            "Medium": [
                ("Program & Simulate", [
                    "Load part drawing; identify features and tolerances.",
                    "Write toolpath (profile + pocket); set feeds/speeds.",
                    "Simulate; fix collisions and gouges."
                ], ["CAM software","example part"], "Runnable program and verified path.")
            ],
            "High": [
                ("Fixture Redesign (Quick)", [
                    "Audit current fixture faults (rigidity, access).",
                    "Sketch a fix that improves clamping and repeatability.",
                    "Pitch changes + risks."
                ], ["A3 paper"], "Design justifications aligned to tolerance stack.")
            ]
        }
    },

    "Explosives Safety": {
        "glossary": [
            "net explosive quantity","blast overpressure","fragmentation","standoff distance",
            "detonation","deflagration","risk zone","donor","acceptor","barrier",
            "PPE","hazard class","magazine","arc flash"
        ],
        "activities": {
            "Medium": [
                ("Distance–Risk Estimator", [
                    "Given NEQ, compute minimum standoff.",
                    "Compare three site layouts; pick the safest."
                ], ["Calculator","Site plans"], "Correct calculations and reasoning.")
            ],
            "High": [
                ("Incident Critique", [
                    "Review incident summary; identify hazard breaks.",
                    "Propose 3 controls ranked by effectiveness."
                ], ["Case sheet"], "Controls map to hierarchy of hazard control.")
            ]
        }
    },

    "Process Simulation (DWSIM)": {
        "glossary": [
            "PID controller","setpoint","controlled variable","manipulated variable",
            "heater duty","cooler duty","disturbance","steady state","NRTL"
        ],
        "activities": {
            "High": [
                ("DWSIM – Heater–Cooler PID Stability (Worksheet)", [
                    "Build flowsheet: Feed → Heater → Cooler → Product (NRTL).",
                    "Define Feed 1000 kg/h, 25 °C, 1 atm; 70% H₂O / 30% EtOH.",
                    "Set duties: Heater 200 kW; Cooler −150 kW.",
                    "Insert PID: CV=Product T; MV=Heater Duty; SP=40 °C.",
                    "Disturbance: raise Feed T to 35 °C; observe response.",
                    "Record Initial / Disturbance / PID-ON results.",
                    "Plot and overlay Product T vs time; save screenshots."
                ], ["DWSIM","PCs"], "Completed table and overlaid plots.")
            ]
        }
    },

    "GE4-IPM (Projects & Ops)": {
        "glossary": [
            "project charter","work breakdown structure","critical path","slack",
            "risk register","mitigation","stakeholder","baseline","variance",
            "ITAR","DFARS","ISO 9001","ISO 27001","MIL-STD","capacity planning"
        ],
        "activities": {
            "Low": [
                ("Term Sprint", [
                    "Define 8 terms (charter, WBS, CPM, slack, baseline, variance, risk, stakeholder).",
                    "Peer-check: merge into a one-page glossary."
                ], ["Cards"], "Clear, concise definitions.")
            ],
            "Medium": [
                ("CPM Tape-Line", [
                    "Arrange task cards; draw dependencies.",
                    "Compute critical path and slack; simulate a 2-day delay."
                ], ["Task cards","Tape"], "Correct path & delay reasoning.")
            ],
            "High": [
                ("Compliance Mapping", [
                    "Map artefacts to ITAR/DFARS/ISO 9001/ISO 27001/MIL-STD.",
                    "Justify choices in 60-sec pitches."
                ], ["Mapping sheet"], "80%+ correct with justification.")
            ]
        }
    }
}

# Seed empty shells for the full list
for name, code in COURSE_LIST:
    label = f"{name} ({code})" if code else name
    if label not in BUILTIN_COURSE_PACKS:
        BUILTIN_COURSE_PACKS[label] = {"glossary": [], "activities": {}}

# Global templates (fallback)
TEMPLATES: Dict[str, List[Tuple[str, List[str], List[str], str]]] = {
    "Low": [
        ("Quick Definitions", [
            "Individually write one-sentence definitions for 6 key terms.",
            "Swap with a peer and refine any unclear wording."
        ], ["Index cards"], "Accurate and concise definitions for all terms."),
    ],
    "Medium": [
        ("Worked Example → Variation", [
            "Solve the worked example collaboratively.",
            "Create and solve one variation that changes a parameter.",
            "Compare answers with another group."
        ], ["Worksheet"], "Correct solution and rationale for both versions."),
    ],
    "High": [
        ("Critique & Redesign", [
            "Review a provided solution; identify 3 weaknesses.",
            "Propose and justify 2 improvements.",
        ], ["A3 paper"], "Clear critiques linked to criteria; viable redesign.")
    ]
}

# ──────────────────────────────────────────────────────────────────────────────
# Hybrid Pack Loader (built-ins + external JSON packs in ./packs)
# ──────────────────────────────────────────────────────────────────────────────

def _validate_pack(obj: dict) -> tuple[bool, str]:
    if not isinstance(obj, dict): return False, "Pack is not a JSON object"
    if "name" not in obj or not obj["name"]: return False, "Missing 'name'"
    if "glossary" in obj and not isinstance(obj["glossary"], list): return False, "'glossary' must be a list"
    if "activities" in obj and not isinstance(obj["activities"], dict): return False, "'activities' must be a dict"
    return True, ""

def load_external_packs(folder: str = "packs") -> dict:
    packs = {}
    for fp in glob.glob(os.path.join(folder, "*.json")):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            ok, why = _validate_pack(data)
            if not ok:
                print(f"[packs] Skip {fp}: {why}")
                continue
            name = data.get("name") or os.path.splitext(os.path.basename(fp))[0]
            packs[name] = {
                "glossary": data.get("glossary", []),
                "activities": data.get("activities", {})
            }
        except Exception as e:
            print(f"[packs] Failed to load {fp}: {e}")
    return packs

def get_course_packs() -> dict:
    merged = {k: v for k, v in BUILTIN_COURSE_PACKS.items()}
    external = load_external_packs()
    for name, pack in external.items():
        merged[name] = pack
    return merged

COURSE_PACKS = get_course_packs()

def apply_glossary_bias(keyterms: List[str], course: str) -> List[str]:
    glossary = COURSE_PACKS.get(course, {}).get("glossary", [])
    seen = set(); out = []
    for g in glossary:
        g2 = g.strip()
        if g2 and g2.lower() not in seen:
            out.append(g2); seen.add(g2.lower())
    for k in keyterms:
        if k.lower() not in seen:
            out.append(k); seen.add(k.lower())
    return out

# ──────────────────────────────────────────────────────────────────────────────
# File parsing
# ──────────────────────────────────────────────────────────────────────────────

def parse_pdf(path: str, deep: bool = False, time_budget: int = 120) -> Tuple[str, str]:
    start = time.time()
    notes = []
    text_chunks = []

    # pypdf
    pages_done = 0
    try:
        reader = PdfReader(path)
        total = len(reader.pages)
        limit = total if deep else min(total, 40)
        for i in range(limit):
            if (time.time() - start) > (time_budget if deep else 25):
                notes.append(f"pypdf timeout • pypdf ({pages_done}/{total} pages)")
                break
            txt = reader.pages[i].extract_text() or ""
            if txt.strip():
                text_chunks.append(txt)
            pages_done += 1
        if pages_done:
            notes.append(f"pypdf ({pages_done}/{total} pages)")
    except Exception as e:
        notes.append(f"pypdf failed: {e}")

    # PyMuPDF (optional)
    if fitz and deep and (time.time() - start) <= time_budget:
        try:
            doc = fitz.open(path)
            mu_done = 0
            for i, page in enumerate(doc):
                if (time.time() - start) > time_budget:
                    notes.append(f"PyMuPDF timeout • PyMuPDF ({mu_done}/{len(doc)} pages)")
                    break
                txt = page.get_text() or ""
                if txt.strip():
                    text_chunks.append(txt)
                mu_done += 1
            if mu_done:
                notes.append(f"PyMuPDF ({mu_done}/{len(doc)} pages)")
        except Exception as e:
            notes.append(f"PyMuPDF failed: {e}")
    elif fitz is None:
        notes.append("PyMuPDF not installed (optional).")

    text = "\n".join(text_chunks)
    if not text.strip():
        notes.append("No extractable text found (likely image-only).")
    else:
        notes.append("Parsed successfully")
    return text, " • ".join(notes)

def parse_docx(path: str) -> Tuple[str, str]:
    try:
        d = DocxDocument(path)
        text = "\n".join([p.text for p in d.paragraphs if p.text.strip()])
        return text, "Parsed successfully (DOCX)"
    except Exception as e:
        return "", f"DOCX parse failed: {e}"

def parse_pptx(path: str) -> Tuple[str, str]:
    try:
        prs = PptxPresentation(path)
        out = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    t = shape.text or ""
                    if t.strip():
                        out.append(t)
        return "\n".join(out), "Parsed successfully (PPTX)"
    except Exception as e:
        return "", f"PPTX parse failed: {e}"

def parse_lesson_plan_docx(path: str) -> Dict[str, any]:
    info = {"topic":"", "los":[], "times":[]}
    try:
        d = DocxDocument(path)
        lines = [p.text.strip() for p in d.paragraphs if p.text.strip()]
        for L in lines[:8]:
            if re.search(r"topic", L, re.I):
                info["topic"] = re.sub(r"(?i).*topic[:\-\s]*", "", L).strip()
                break
        for L in lines:
            if re.match(r"(LO\d+|Learning Objective|\- )", L, re.I) or re.search(r"\bdefine\b|\bdescribe\b|\bexplain\b|\bdistinguish\b", L, re.I):
                info["los"].append(L)
        times = []
        for L in lines:
            m = re.findall(r"(\d+)\s*(?:min|minutes)", L, re.I)
            times += [int(x) for x in m]
        info["times"] = times[:10]
    except Exception:
        pass
    return info

# ──────────────────────────────────────────────────────────────────────────────
# LMS Importers: Moodle XML / GIFT / CSV
# ──────────────────────────────────────────────────────────────────────────────

def parse_moodle_xml_bytes(data: bytes) -> dict:
    out = {"questions": [], "phrases": Counter(), "keywords": Counter()}
    try:
        root = ET.fromstring(data)
    except Exception:
        return out

    def clean(s):
        return re.sub(r"\s+", " ", (s or "").strip())

    for q in root.findall(".//question"):
        qtype = (q.attrib.get("type","") or "").lower()
        if qtype not in ("multichoice","shortanswer","truefalse","matching","cloze"):
            continue
        name = clean(q.findtext("name/text"))
        qtext_node = q.find("questiontext/text")
        text = clean(qtext_node.text if qtext_node is not None else "")
        topic = ""
        cat = q.find("category/text")
        if cat is not None and cat.text:
            topic = clean(cat.text.split("$course$/")[-1])

        answers = []
        for ans in q.findall("answer"):
            frac = ans.attrib.get("fraction", "0")
            a_text = clean((ans.findtext("text") or ""))
            correct = False
            try:
                correct = float(frac) > 0
            except Exception:
                correct = str(frac).strip() not in ("0","0.0","")
            answers.append((a_text, bool(correct)))

        out["questions"].append({"name": name, "text": text, "answers": answers, "topic": topic})

        if text:
            m = re.match(r"(?i)(which|what|when|why|how|identify|select|choose)\b[^\n]{0,80}", text)
            if m: out["phrases"][m.group(0).lower()] += 1
            for tok in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text):
                out["keywords"][tok.lower()] += 1
        for (a_text, _) in answers:
            for tok in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", a_text):
                out["keywords"][tok.lower()] += 1
    return out

def parse_gift_text(txt: str) -> dict:
    out = {"questions": [], "phrases": Counter(), "keywords": Counter()}
    blocks = re.split(r"\n\s*\n", txt.strip())
    for block in blocks:
        if "{" not in block or "}" not in block:
            continue
        name = ""
        qtext = block
        m = re.match(r"\s*([^{]+?)::", block)
        if m:
            name = m.group(1).strip()
            qtext = block[m.end():]
        if "{" not in qtext or "}" not in qtext:
            continue
        qpart, apos = qtext.split("{", 1)
        answers_part = apos.rsplit("}", 1)[0]
        text = re.sub(r"\s+", " ", qpart).strip()
        answers = []
        for piece in re.finditer(r"([=~])([^=~]+)", answers_part):
            corr = (piece.group(1) == "=")
            a_text = re.sub(r"\s+", " ", piece.group(2)).strip()
            answers.append((a_text, corr))
        out["questions"].append({"name": name, "text": text, "answers": answers, "topic": ""})

        if text:
            m = re.match(r"(?i)(which|what|when|why|how|identify|select|choose)\b[^\n]{0,80}", text)
            if m: out["phrases"][m.group(0).lower()] += 1
            for tok in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text):
                out["keywords"][tok.lower()] += 1
        for (a_text, _) in answers:
            for tok in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", a_text):
                out["keywords"][tok.lower()] += 1
    return out

def bank_to_course_pack(bank: dict, name: str) -> dict:
    STOP = set("the a an and or for with from by to of on in at is are was were be as it its this that these those which who whom whose".split())
    kw = [k for k, _ in bank.get("keywords", {}).most_common(200)]
    glossary = [k for k in kw if k not in STOP and len(k) > 2][:40]
    pack = {
        "name": name,
        "glossary": glossary,
        "activities": {
            "Low": [
                ["Terminology Match (from bank)", [
                    "Match bank keywords to definitions written by peers.",
                    "Whole-class check; refine unclear definitions."
                ], ["Term cards"], "≥90% correct mappings."]
            ],
            "Medium": [
                ["Rebuild a Question", [
                    "Take a bank question and alter one parameter or context.",
                    "Swap with another pair and critique differences."
                ], ["Question slips"], "New item remains valid and non-ambiguous."]
            ],
            "High": [
                ["Misconception Hunt", [
                    "Collect 3 common wrong options from the bank; explain why each is plausible but wrong.",
                    "Write 1 improved distractor."
                ], ["Bank printouts"], "Clear misconceptions + better distractor."]
            ]
        }
    }
    return pack

def save_pack_json(pack: dict, folder: str = "packs") -> str:
    os.makedirs(folder, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9\-\_\(\)\s]+", "", pack.get("name","New Course")).strip() or "New Course"
    fname = safe_name.replace(" ", "_") + ".json"
    path = os.path.join(folder, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, indent=2)
    return path

def bank_summary_docx(bank: dict, title: str = "Imported Question Bank Summary") -> bytes:
    doc = DocxDocument()
    doc.add_heading(title, level=1)
    qs = bank.get("questions", [])
    doc.add_paragraph(f"Total questions parsed: {len(qs)}")

    topic_counts = Counter(q.get("topic","") or "Unspecified" for q in qs)
    if topic_counts:
        doc.add_heading("Topics", level=2)
        for t, c in topic_counts.most_common(12):
            doc.add_paragraph(f"{t}: {c}", style="List Bullet")

    phrases = bank.get("phrases", Counter())
    if phrases:
        doc.add_heading("Common stem openers", level=2)
        for p, c in phrases.most_common(10):
            doc.add_paragraph(f"{p} — {c}", style="List Bullet")

    keywords = bank.get("keywords", Counter())
    if keywords:
        doc.add_heading("Top keywords", level=2)
        for k, c in keywords.most_common(30):
            doc.add_paragraph(f"{k} — {c}", style="List Bullet")

    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

# ──────────────────────────────────────────────────────────────────────────────
# MCQ generator (API-free)
# ──────────────────────────────────────────────────────────────────────────────

class MCQ:
    def __init__(self, stem: str, options: List[str], answer: int):
        self.stem = stem
        self.options = options
        self.answer = answer

def build_mcqs(text: str, n: int, bloom_focus: str,
               rng: Optional[random.Random]=None, course: str="General",
               partition_key: Optional[str]=None, partition_buckets: int = 3) -> List[MCQ]:
    rng = rng or random
    text = (text or "").strip()
    if not text:
        return []
    sents = sentences(text)
    if not sents:
        return []

    # Partition to minimize overlap across instructors
    if partition_key:
        sents = partition_view(sents, partition_key, partition_buckets)

    keyterms = tfidf_keyterms(text, top_k=40)
    keyterms = apply_glossary_bias(keyterms, course)
    rng.shuffle(sents)

    out = []
    for s in sents:
        term = None
        for t in keyterms[:20]:
            if re.search(rf"\b{re.escape(t)}\b", s, re.I):
                term = t; break
        if not term:
            continue
        stem = f"What best describes '{term}' in this lesson?"
        correct = re.sub(r"\s+", " ", s)
        correct = re.sub(rf".*?\b{re.escape(term)}\b", term, correct, flags=re.I)
        correct = correct[:120].strip(" .")

        pool = [k for k in keyterms[5:30] if k.lower() != term.lower()]
        rng.shuffle(pool)
        distractors = []
        for p in pool:
            p2 = p.strip().capitalize()
            if p2 and p2.lower() != correct.lower():
                distractors.append(p2[:80])
            if len(distractors) >= 3: break
        while len(distractors) < 3:
            filler = (term[::-1] + " concept")[: max(8, min(14, len(term)+7))]
            distractors.append(filler)

        options = [correct] + distractors
        rng.shuffle(options)
        out.append(MCQ(stem=stem, options=options, answer=options.index(correct)))
        if len(out) >= n:
            break

    while len(out) < n and keyterms:
        t = keyterms.pop(0)
        stem = f"Which statement relates most closely to '{t}'?"
        correct = f"{t.capitalize()} is relevant to this topic."
        pool = keyterms[:]
        rng.shuffle(pool)
        distractors = []
        for p in pool:
            if p.lower() != t.lower():
                distractors.append(p.capitalize()[:80])
            if len(distractors) >= 3: break
        while len(distractors) < 3:
            distractors.append((t[::-1] + " term")[:12])
        options = [correct] + distractors
        rng.shuffle(options)
        out.append(MCQ(stem, options, options.index(correct)))
    return out[:n]

# ──────────────────────────────────────────────────────────────────────────────
# Activities + Revision
# ──────────────────────────────────────────────────────────────────────────────

def build_activities(topic: str, focus: str, count: int, minutes: int,
                     rng: Optional[random.Random]=None, course: str="General",
                     partition_key: Optional[str]=None, partition_buckets: int = 3) -> List[dict]:
    rng = rng or random
    course_bank = COURSE_PACKS.get(course, {}).get("activities", {}).get(focus, [])
    global_bank = TEMPLATES.get(focus, [])
    bank = (course_bank + global_bank)[:] or global_bank[:]
    if not bank:
        return []

    # Partition by title for minimal overlap
    if partition_key and len(bank) > 1:
        titles = [b[0] for b in bank]
        keep_titles = set(partition_view(titles, partition_key, partition_buckets))
        bank = [b for b in bank if b[0] in keep_titles] or bank

    rng.shuffle(bank)
    out = []
    for i in range(count):
        title, steps, materials, assess = bank[i % len(bank)]
        varied_steps = []
        for s in steps:
            varied = re.sub(r"(\d+)\s*°\s*C", lambda m: f"{int(m.group(1))+rng.choice([-2,-1,0,1,2])} °C", s)
            varied_steps.append(varied)
        out.append({
            "title": f"{title} — {topic or 'Lesson'}",
            "minutes": minutes,
            "objective": f"{focus} focus activity for {topic or 'the topic'}.",
            "steps": varied_steps,
            "materials": materials,
            "assessment": assess
        })
    return out

def build_revision_plan(focus: str, topic: str) -> List[str]:
    return [
        "## Day 1 – Fundamentals (45–60 min)",
        f"• Read key notes for {topic or 'the topic'}; summarise each section in one line.",
        "• Self-quiz with 3 MCQs.",
        "## Day 2 – Apply (45–60 min)",
        "• Re-work a short example; create 2 new practice items.",
        "## Day 3 – Analyse (45–60 min)",
        "• Draw a concept/process map; annotate assumptions.",
        "## Day 4 – Evaluate (45–60 min)",
        "• Critique a case or sample answer; propose 2 improvements.",
        "## Day 5 – Create (45–60 min)",
        "• Produce a one-page cheat-sheet + 5 MCQs with answers."
    ]

# ──────────────────────────────────────────────────────────────────────────────
# Exports (.docx)
# ──────────────────────────────────────────────────────────────────────────────

def mcqs_docx(mcqs: List[MCQ]) -> bytes:
    doc = DocxDocument()
    doc.add_heading("Knowledge MCQs", level=1)
    instr = st.session_state.get("instructor","").strip()
    if instr:
        doc.add_paragraph(f"Instructor: {instr}")
    topic = st.session_state.get("topic",""); course = st.session_state.get("course","")
    if topic or course:
        doc.add_paragraph("Context: " + " • ".join([p for p in [course, topic] if p]))
    doc.add_paragraph("")
    for i, q in enumerate(mcqs or [], 1):
        doc.add_paragraph(f"{i}. {q.stem}")
        for j, opt in enumerate(q.options, 1):
            doc.add_paragraph(f"{chr(64+j)}. {opt}", style="List Bullet")
        doc.add_paragraph(f"Answer: {chr(65+q.answer)}")
        doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def activities_docx(acts: List[dict]) -> bytes:
    doc = DocxDocument()
    doc.add_heading("Skills Activities", level=1)
    instr = st.session_state.get("instructor","").strip()
    if instr:
        doc.add_paragraph(f"Instructor: {instr}")
    topic = st.session_state.get("topic",""); course = st.session_state.get("course","")
    if topic or course:
        doc.add_paragraph("Context: " + " • ".join([p for p in [course, topic] if p]))
    doc.add_paragraph("")
    for i, a in enumerate(acts or [], 1):
        doc.add_heading(f"{i}. {a['title']} — {a['minutes']} mins", level=2)
        doc.add_paragraph(f"Objective: {a['objective']}")
        doc.add_paragraph("Steps:")
        for s in a["steps"]:
            doc.add_paragraph(s, style="List Number")
        if a["materials"]:
            doc.add_paragraph("Materials: " + ", ".join(a["materials"]))
        doc.add_paragraph("Check: " + a["assessment"])
        doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def revision_docx(plan: List[str], title: str = "1-Week Revision Plan") -> bytes:
    doc = DocxDocument()
    doc.add_heading(title, level=1)
    instr = st.session_state.get("instructor","").strip()
    if instr:
        doc.add_paragraph(f"Instructor: {instr}")
    topic = st.session_state.get("topic",""); course = st.session_state.get("course","")
    if topic or course:
        doc.add_paragraph("Context: " + " • ".join([p for p in [course, topic] if p]))
    doc.add_paragraph("")
    for line in plan:
        if line.startswith("## "):
            doc.add_heading(line.replace("## ",""), level=2)
        elif line.startswith("• "):
            doc.add_paragraph(line[2:], style="List Bullet")
        else:
            doc.add_paragraph(line)
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def bundle_docx(mcqs: List[MCQ], acts: List[dict], rev_lines: List[str], topic: str) -> bytes:
    doc = DocxDocument()
    doc.add_heading("ADI Lesson Pack", level=0)
    instr = st.session_state.get("instructor","").strip()
    if instr:
        doc.add_paragraph(f"Instructor: {instr}")
    course = st.session_state.get("course","")
    doc.add_paragraph("Context: " + " • ".join([p for p in [course, topic] if p]))
    doc.add_page_break()

    if mcqs:
        doc.add_heading("Knowledge MCQs", level=1)
        for i, q in enumerate(mcqs or [], 1):
            doc.add_paragraph(f"{i}. {q.stem}")
            for j, opt in enumerate(q.options, 1):
                doc.add_paragraph(f"{chr(64+j)}. {opt}", style="List Bullet")
            doc.add_paragraph(f"Answer: {chr(65+q.answer)}")
            doc.add_paragraph("")
        doc.add_page_break()

    if acts:
        doc.add_heading("Skills Activities", level=1)
        for i,a in enumerate(acts,1):
            doc.add_heading(f"{i}. {a['title']} — {a['minutes']} mins", level=2)
            doc.add_paragraph(f"Objective: {a['objective']}")
            doc.add_paragraph("Steps:")
            for s in a["steps"]:
                doc.add_paragraph(s, style="List Number")
            if a["materials"]:
                doc.add_paragraph("Materials: " + ", ".join(a["materials"]))
            doc.add_paragraph("Check: " + a["assessment"])
            doc.add_paragraph("")
        doc.add_page_break()

    if rev_lines:
        doc.add_heading("1-Week Revision Plan", level=1)
        for line in rev_lines:
            if line.startswith("## "):
                doc.add_heading(line.replace("## ",""), level=2)
            elif line.startswith("• "):
                doc.add_paragraph(line[2:], style="List Bullet")
            else:
                doc.add_paragraph(line)
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

# ──────────────────────────────────────────────────────────────────────────────
# UI — Sidebar
# ──────────────────────────────────────────────────────────────────────────────

st.sidebar.header("Upload (optional)")
uploaded = st.sidebar.file_uploader(
    "Drag and drop file here", type=["pdf","docx","pptx"],
    help="Limit ~200MB per file • PDF, DOCX, PPTX"
)

deep_scan = st.sidebar.checkbox("Deep scan (all pages, slower)", value=False, help="Tries more pages and engines under a time budget.")

# Course packs (hybrid)
with st.sidebar.expander("Course packs", expanded=False):
    st.caption(f"Built-in: {len(BUILTIN_COURSE_PACKS)} • External loaded: {len(load_external_packs())}")
    if st.button("🔄 Reload packs"):
        st.session_state["__packs_reload__"] = time.time()
        COURSE_PACKS = get_course_packs()
        st.experimental_rerun()

course_names = sorted(list(COURSE_PACKS.keys()))
st.session_state.course = st.sidebar.selectbox(
    "Course",
    course_names,
    index=course_names.index(st.session_state.get("course", course_names[0])) if st.session_state.get("course") in course_names else 0
)

# Instructor selection
instructor_options = ["— Select —"] + STAFF + ["Custom / Other"]
chosen_instructor = st.sidebar.selectbox("Instructor", instructor_options, index=0)
if chosen_instructor not in ("— Select —", "Custom / Other"):
    st.session_state.instructor = chosen_instructor
    default_variant = "".join([p[0] for p in chosen_instructor.split() if p]).upper()
    if not st.session_state.get("variant_tag"):
        st.session_state.variant_tag = default_variant
else:
    st.session_state.instructor = st.session_state.get("instructor", "")

variant_tag = st.sidebar.text_input("Instructor / variant (optional)", value=st.session_state.get("variant_tag",""))
st.session_state.variant_tag = variant_tag

st.sidebar.markdown("---")
st.sidebar.subheader("Course context")
st.session_state.lesson = st.sidebar.selectbox("Lesson", [1,2,3,4,5,6,7,8,9,10], index=(st.session_state.get("lesson",1)-1))
st.session_state.week   = st.sidebar.selectbox("Week", list(range(1,15)), index=(st.session_state.get("week",7)-1))

st.sidebar.markdown("---")
st.sidebar.subheader("Number of MCQs")
st.session_state.mcq_count = st.sidebar.selectbox("How many questions?", [5,10,15,20,30], index=[5,10,15,20,30].index(st.session_state.get("mcq_count",10)))

st.sidebar.markdown("---")
st.sidebar.subheader("Activities")
st.session_state.act_count = st.sidebar.selectbox("How many activities?", [1,2,3,4], index=[1,2,3,4].index(st.session_state.get("act_count",2)))
st.session_state.act_minutes = st.sidebar.selectbox("Time each (mins)", [5,10,15,20,30,45,60], index=[5,10,15,20,30,45,60].index(st.session_state.get("act_minutes",30)))

st.sidebar.markdown("---")
use_lesson_plan = st.sidebar.checkbox("Use lesson plan (DOCX) to pre-fill", value=False)

# Variation controls
st.sidebar.markdown("---")
st.sidebar.subheader("Variation controls")
partition_on = st.sidebar.checkbox(
    "Guarantee different sets across instructors (3-way partition)",
    value=True,
    help="Ensures disjoint question/activity pools when multiple instructors teach the same course/week."
)
st.session_state["partition_on"] = partition_on

variation_mode = st.sidebar.radio(
    "Variation mode",
    ["Per instructor / per day (default)", "Per instructor + per click", "Custom fixed seed"],
    index=0,
    help="Choose if sets should refresh daily, on each click, or stay fixed."
)

if "nonce" not in st.session_state: st.session_state["nonce"] = 0
if variation_mode == "Per instructor + per click":
    if st.sidebar.button("🔄 New set now"):
        st.session_state["nonce"] += 1

fixed_seed = None
if variation_mode == "Custom fixed seed":
    fixed_seed = st.sidebar.text_input("Fixed seed (e.g., 42 or ABC123)", value=st.session_state.get("fixed_seed",""))
    st.session_state["fixed_seed"] = fixed_seed

# Simple Mode
st.sidebar.markdown("---")
st.sidebar.subheader("Simple mode")
simple_mode = st.sidebar.toggle("Make it one-click (recommended for staff)", value=True)
if simple_mode:
    st.session_state.mcq_count   = st.session_state.get("mcq_count", 10) or 10
    st.session_state.act_count   = st.session_state.get("act_count", 2) or 2
    st.session_state.act_minutes = st.session_state.get("act_minutes", 30) or 30

# LMS importer
st.sidebar.markdown("---")
st.sidebar.subheader("Import LMS question bank → Course Pack")
bank_file = st.sidebar.file_uploader(
    "Upload Moodle XML / GIFT / CSV",
    type=["xml","gift","txt","csv"],
    accept_multiple_files=False,
    help="We’ll parse it and create a pluggable course pack JSON in /packs"
)
pack_name = st.sidebar.text_input("New Course Pack name", value="My Imported Course")
import_btn = st.sidebar.button("📦 Build Course Pack from Bank")

if import_btn and bank_file is not None:
    data = bank_file.read()
    bank = {"questions": [], "phrases": Counter(), "keywords": Counter()}
    ext = os.path.splitext(bank_file.name)[1].lower()
    try:
        if ext == ".xml":
            bank = parse_moodle_xml_bytes(data)
        elif ext in (".gift", ".txt"):
            bank = parse_gift_text(data.decode("utf-8", errors="ignore"))
        elif ext == ".csv":
            txt = data.decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(txt))
            qs = []; kw = Counter(); phr = Counter()
            for row in reader:
                qtext = (row.get("question","") or "").strip()
                topic = (row.get("topic","") or "").strip()
                answers = []
                for col in ["option_a","option_b","option_c","option_d"]:
                    opt = (row.get(col,"") or "").strip()
                    if not opt: continue
                    correct = (row.get("correct","").strip().lower() == col.split("_")[-1])
                    answers.append((opt, correct))
                qs.append({"name":"", "text":qtext, "answers":answers, "topic":topic})
                for tok in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", qtext):
                    kw[tok.lower()] += 1
                m = re.match(r"(?i)(which|what|when|why|how|identify|select|choose)\b[^\n]{0,80}", qtext)
                if m: phr[m.group(0).lower()] += 1
            bank = {"questions": qs, "phrases": phr, "keywords": kw}
        else:
            st.sidebar.error("Unsupported file type.")
            bank = None
    except Exception as e:
        bank = None
        st.sidebar.error(f"Import failed: {e}")

    if bank is not None:
        pn = (pack_name.strip() or "Imported Course")
        pack = bank_to_course_pack(bank, pn)
        path = save_pack_json(pack)
        st.sidebar.success(f"Pack saved: {path}")

        summary = bank_summary_docx(bank, title=f"{pack['name']} — Bank Summary")
        st.sidebar.download_button(
            "⬇️ Download Bank Summary (.docx)",
            data=summary,
            file_name=f"{pack['name'].replace(' ','_')}_bank_summary.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        st.sidebar.download_button(
            "⬇️ Download Course Pack (.json)",
            data=json.dumps(pack, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"{pack['name'].replace(' ','_')}.json",
            mime="application/json"
        )
        try:
            COURSE_PACKS = get_course_packs()
        except Exception:
            pass
        st.experimental_rerun()

# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="adi-banner">
  <div><strong>ADI Builder — Lesson Activities & Questions</strong></div>
  <div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
</div>
""", unsafe_allow_html=True)

# Variation seed
base = (
    f"{st.session_state.get('topic','')}"
    f"|{st.session_state.get('course','')}"
    f"|L{st.session_state.lesson}"
    f"|W{st.session_state.week}"
    f"|{st.session_state.get('instructor','')}"
    f"|{st.session_state.variant_tag}"
)
if variation_mode == "Per instructor / per day (default)":
    base += f"|{time.strftime('%Y-%m-%d')}"
elif variation_mode == "Per instructor + per click":
    base += f"|click:{st.session_state['nonce']}"
elif variation_mode == "Custom fixed seed":
    base += f"|fixed:{st.session_state.get('fixed_seed') or '0'}"

seed = hash_seed(base)
rng = random.Random(seed)
set_id = hashlib.sha1(str(seed).encode()).hexdigest()[:6].upper()
st.sidebar.caption(f"Set ID: **{set_id}**")

# Tabs
tab1, tab2, tab3 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

# Auto Bloom focus
bloom_focus = bloom_from_week(int(st.session_state.week))

# Topic + badge
colA, colB = st.columns([4,1.4], gap="large")
with colA:
    st.session_state.topic = st.text_input("Topic / Outcome (optional)", value=st.session_state.get("topic",""))
with colB:
    st.markdown(f"<span class='badge'>Week {st.session_state.week}: {bloom_focus}</span>", unsafe_allow_html=True)

use_sample = st.checkbox("Use sample text (for a quick test)", value=False, help="Adds a small sample to generate quickly.")
source_default = st.session_state.get("source_text","")
source_area = st.text_area("Source text (editable)", value=source_default, height=180, help="Paste or jot key notes, vocab, facts here…")

# Upload parsing + lesson plan ingest
uploaded_text = ""
parse_notes = ""
if uploaded is not None:
    tmp_path = os.path.join(".", uploaded.name)
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())
    kind = uploaded.name.split(".")[-1].lower()
    if use_lesson_plan and kind == "docx":
        info = parse_lesson_plan_docx(tmp_path)
        if info.get("topic"):
            st.session_state.topic = info["topic"]
        los_text = "\n".join(info.get("los", []))
        uploaded_text = los_text
        parse_notes = f"Lesson plan parsed • topic='{info.get('topic','')}' • LOs={len(info.get('los',[]))} • times={info.get('times', [])}"
    else:
        if kind == "pdf":
            uploaded_text, parse_notes = parse_pdf(tmp_path, deep=deep_scan, time_budget=120 if deep_scan else 25)
        elif kind == "docx":
            uploaded_text, parse_notes = parse_docx(tmp_path)
        elif kind == "pptx":
            uploaded_text, parse_notes = parse_pptx(tmp_path)

    with st.expander("Upload status", expanded=True):
        st.success("Parsed successfully" if "Parsed successfully" in parse_notes else "Parsed with notes")
        st.write(parse_notes)
        if uploaded_text.strip():
            if st.button("Insert extracted text"):
                st.session_state.source_text = (source_area + "\n\n" + uploaded_text).strip() if source_area else uploaded_text
                st.success("✅ Text inserted. You can now generate with one click.")
                st.experimental_rerun()

# Update source_text
if use_sample:
    st.session_state.source_text = (
        "Bearings reduce friction and support rotating elements. "
        "Actuators convert control signals into motion. "
        "Maintenance strategies include repair, reconditioning, and renovation. "
        "Documentation ensures traceability and safety compliance for life-extension programmes."
    )
else:
    st.session_state.source_text = source_area

# Verb pills
def render_bloom_row(level: str, verbs: List[str], active: bool):
    cls = {"Low":"low", "Medium":"med", "High":"high"}[level]
    st.markdown(f"<div class='bloom-row {cls}'>", unsafe_allow_html=True)
    st.caption(f"**{level}** (Weeks { '1–4' if level=='Low' else ('5–9' if level=='Medium' else '10–14') }): " + \
               ("Remember / Understand" if level=="Low" else ("Apply / Analyse" if level=="Medium" else "Evaluate / Create")))
    row = ""
    for v in verbs:
        row += f"<span class='verb-pill {'active' if active else ''}'>{v}</span>"
    st.markdown(row, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

render_bloom_row("Low",    ["define","identify","list","recall","describe","label"], bloom_focus=="Low")
render_bloom_row("Medium", ["apply","demonstrate","solve","illustrate","classify","compare"], bloom_focus=="Medium")
render_bloom_row("High",   ["evaluate","synthesize","design","justify","critique","create"], bloom_focus=="High")

# ──────────────────────────────────────────────────────────────────────────────
# Simple Mode: three big buttons (MCQs / Activities / Revision) + optional Bundle
# ──────────────────────────────────────────────────────────────────────────────

if simple_mode:
    st.info("Simple Mode: choose exactly what you need. Each button generates and offers a Word download.")
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    who = (st.session_state.get("instructor","") or "Instructor").replace(" ", "")
    course_slug = re.sub(r"[^A-Za-z0-9]+","_", st.session_state.course)

    with c1:
        if st.button("✨ MCQs only", use_container_width=True):
            mcqs = build_mcqs(
                st.session_state.get("source_text",""),
                st.session_state.mcq_count,
                bloom_focus,
                rng=rng,
                course=st.session_state.course,
                partition_key=(st.session_state.get("instructor","") if st.session_state.get("partition_on", True) else None),
                partition_buckets=3
            )
            st.session_state.mcqs = mcqs
            if mcqs:
                st.success("MCQs ready. Download below.")
                st.download_button(
                    "⬇️ Download MCQs (.docx)",
                    data=mcqs_docx(mcqs),
                    file_name=f"{course_slug}_MCQs_{who}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

    with c2:
        if st.button("🛠️ Activities only", use_container_width=True):
            acts = build_activities(
                st.session_state.get("topic",""), bloom_focus,
                st.session_state.act_count, st.session_state.act_minutes,
                rng=rng, course=st.session_state.course,
                partition_key=(st.session_state.get("instructor","") if st.session_state.get("partition_on", True) else None),
                partition_buckets=3
            )
            st.session_state.acts = acts
            if acts:
                st.success("Activities ready. Download below.")
                st.download_button(
                    "⬇️ Download Activities (.docx)",
                    data=activities_docx(acts),
                    file_name=f"{course_slug}_Activities_{who}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

    with c3:
        if st.button("📚 Revision only", use_container_width=True):
            rev_lines = build_revision_plan(bloom_focus, st.session_state.get("topic",""))
            st.session_state.rev_lines = rev_lines
            st.success("Revision plan ready. Download below.")
            st.download_button(
                "⬇️ Download Revision Plan (.docx)",
                data=revision_docx(rev_lines),
                file_name=f"{course_slug}_Revision_{who}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

    with c4:
        if st.button("✅ All-in-one (optional)", use_container_width=True):
            mcqs = st.session_state.get("mcqs") or build_mcqs(
                st.session_state.get("source_text",""),
                st.session_state.mcq_count,
                bloom_focus,
                rng=rng,
                course=st.session_state.course,
                partition_key=(st.session_state.get("instructor","") if st.session_state.get("partition_on", True) else None),
                partition_buckets=3
            )
            acts = st.session_state.get("acts") or build_activities(
                st.session_state.get("topic",""), bloom_focus,
                st.session_state.act_count, st.session_state.act_minutes,
                rng=rng, course=st.session_state.course,
                partition_key=(st.session_state.get("instructor","") if st.session_state.get("partition_on", True) else None),
                partition_buckets=3
            )
            rev_lines = st.session_state.get("rev_lines") or build_revision_plan(bloom_focus, st.session_state.get("topic",""))

            bundle = bundle_docx(mcqs or [], acts or [], rev_lines or [], st.session_state.get("topic",""))
            st.success("Lesson Pack ready. Download below.")
            st.download_button(
                "⬇️ Download Lesson Pack (.docx)",
                data=bundle,
                file_name=f"{course_slug}_LessonPack_{who}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Tabs (advanced mode remains unchanged)
# ──────────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = tab1, tab2, tab3  # already created above

with tab1:
    st.markdown("#### ")
    if st.button("✨ Generate MCQs", type="primary", disabled=simple_mode):
        mcqs = build_mcqs(
            st.session_state.get("source_text",""),
            st.session_state.mcq_count,
            bloom_focus,
            rng=rng,
            course=st.session_state.course,
            partition_key=(st.session_state.get("instructor","") if partition_on else None),
            partition_buckets=3
        )
        st.session_state.mcqs = mcqs

    for i, q in enumerate(st.session_state.get("mcqs", []), 1):
        with st.expander(f"{i}. {q.stem}"):
            for j, opt in enumerate(q.options):
                st.write(f"{chr(65+j)}. {opt}")
            st.write(f"**Answer:** {chr(65+q.answer)}")

    if st.session_state.get("mcqs") and not simple_mode:
        who = (st.session_state.get("instructor","") or "Instructor").replace(" ", "")
        course_slug = re.sub(r"[^A-Za-z0-9]+","_", st.session_state.course)
        doc = mcqs_docx(st.session_state.mcqs)
        st.download_button("⬇️ Download MCQs (.docx)", data=doc,
                           file_name=f"{course_slug}_MCQs_{who}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        rev_lines = build_revision_plan(bloom_focus, st.session_state.get("topic",""))
        bundle = bundle_docx(st.session_state.mcqs, st.session_state.get("acts", []), rev_lines, st.session_state.get("topic",""))
        st.download_button("⬇️ Download Lesson Pack (.docx)", data=bundle,
                           file_name=f"{course_slug}_LessonPack_{who}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

with tab2:
    if st.button("🛠️ Generate activities", disabled=simple_mode):
        acts = build_activities(
            st.session_state.get("topic",""), bloom_focus,
            st.session_state.act_count, st.session_state.act_minutes,
            rng=rng, course=st.session_state.course,
            partition_key=(st.session_state.get("instructor","") if partition_on else None),
            partition_buckets=3
        )
        st.session_state.acts = acts

    for i, a in enumerate(st.session_state.get("acts", []), 1):
        with st.expander(f"{i}. {a['title']} — {a['minutes']} mins"):
            st.write("**Objective:**", a["objective"])
            st.write("**Steps:**")
            for s in a["steps"]:
                st.write(f"- {s}")
            if a["materials"]:
                st.write("**Materials:**", ", ".join(a["materials"]))
            st.write("**Check:**", a["assessment"])

    if st.session_state.get("acts") and not simple_mode:
        who = (st.session_state.get("instructor","") or "Instructor").replace(" ", "")
        course_slug = re.sub(r"[^A-Za-z0-9]+","_", st.session_state.course)
        doc = activities_docx(st.session_state.acts)
        st.download_button("⬇️ Download Activities (.docx)", data=doc,
                           file_name=f"{course_slug}_Activities_{who}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        rev_lines = build_revision_plan(bloom_focus, st.session_state.get("topic",""))
        rev_doc = revision_docx(rev_lines)
        st.download_button("⬇️ Download Revision Plan (.docx)", data=rev_doc,
                           file_name=f"{course_slug}_Revision_{who}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        bundle = bundle_docx(st.session_state.get("mcqs", []), st.session_state.acts, rev_lines, st.session_state.get("topic",""))
        st.download_button("⬇️ Download Lesson Pack (.docx)", data=bundle,
                           file_name=f"{course_slug}_LessonPack_{who}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

with tab3:
    rev_lines = build_revision_plan(bloom_focus, st.session_state.get("topic",""))
    st.write("### 1-Week Revision Plan")
    for line in rev_lines:
        if line.startswith("## "):
            st.subheader(line.replace("## ",""))
        elif line.startswith("• "):
            st.write(line)
        else:
            st.write(line)

    if not simple_mode:
        who = (st.session_state.get("instructor","") or "Instructor").replace(" ", "")
        course_slug = re.sub(r"[^A-Za-z0-9]+","_", st.session_state.course)
        rev_doc = revision_docx(rev_lines)
        st.download_button("⬇️ Download Revision Plan (.docx)", data=rev_doc,
                           file_name=f"{course_slug}_Revision_{who}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
