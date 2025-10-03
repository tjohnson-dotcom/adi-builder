# app.py — ADI Builder (Lessons, MCQs, Activities, Revision)
# Streamlit 1.29+; Zero external LLM/API; on-prem friendly

import os, io, json, time, random, hashlib, re
from datetime import datetime

import streamlit as st

# -------------------------------------------------------------------
# Streamlit rerun compatibility (experimental_rerun → rerun)
# -------------------------------------------------------------------
if not hasattr(st, "experimental_rerun"):
    st.experimental_rerun = st.rerun

# ------------------------- File parsing libs ------------------------
import fitz                      # PyMuPDF (PDF)
from docx import Document as DocxDocument
from pptx import Presentation

# -------------------------- NLTK bootstrap --------------------------
# Robust, race-safe bootstrap that works on Render/containers without errors
import nltk
NLTK_DIR = os.environ.get("NLTK_DATA", "/opt/render/nltk_data")
os.environ["NLTK_DATA"] = NLTK_DIR
os.makedirs(NLTK_DIR, exist_ok=True)

def _ensure_nltk(pkg_path: str, name_candidates: list[str]):
    """Ensure an NLTK resource exists (safe if multiple workers init at once)."""
    try:
        nltk.data.find(pkg_path)
        return
    except LookupError:
        pass
    for nm in name_candidates:
        try:
            nltk.download(nm, download_dir=NLTK_DIR, quiet=True, raise_on_error=False)
            nltk.data.find(pkg_path)
            return
        except Exception:
            continue

# Support classic & new names across NLTK versions
_ensure_nltk("tokenizers/punkt", ["punkt", "punkt_tab"])
_ensure_nltk("taggers/averaged_perceptron_tagger",
             ["averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"])
_ensure_nltk("corpora/wordnet", ["wordnet"])

from nltk.corpus import wordnet as wn
from nltk import word_tokenize, pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer

# ----------------------- ADI catalog & staff ------------------------
COURSE_CATALOG = {
    "Cohort 1: T3-24-25 (D1)": [
        ("GE4-EPM", "Defense Technology Practices: Experimentation, Quality Management and Inspection"),
        ("GE4-IPM", "Integrated Project and Materials Management in Defense Technology"),
        ("GE4-MRO", "Military Vehicle and Aircraft MRO: Principles & Applications"),
        ("CT4-COM", "Computation for Chemical Technologists"),
        ("CT4-EMG", "Explosives Manufacturing"),
        ("CT4-TFL", "Thermofluids"),
        ("MT4-CMG", "Composite Manufacturing"),
        ("MT4-CAD", "Computer Aided Design"),
        ("MT4-MAE", "Machine Elements"),
        ("EE4-MFC", "Electrical Materials"),
        ("EE4-PMG", "PCB Manufacturing"),
        ("EE4-PCT", "Power Circuits & Transmission"),
    ],
    "Cohort 2: T3-24-25 (D1)": [
        ("MT5-MPD", "Mechanical Product Dissection"),
        ("MT5-AST", "Assembly Technology"),
        ("MT5-AVM", "Aviation Maintenance"),
        ("MT5-HYP", "Hydraulics and Pneumatics"),
        ("MT5-CAD", "Computer Aided Design and Additive Manufacturing"),
        ("MT5-CNC", "Industrial Machining"),
        ("CT5-TCE", "Thermochemistry of Explosives"),
        ("CT5-SET", "Separation Technologies 1"),
        ("CT5-POT", "Explosives Plant Operations and Troubleshooting"),
        ("CT5-COT", "Coating Technologies"),
        ("CT5-LAB", "Chemical Technology Laboratory Techniques"),
        ("CT5-CPT", "Chemical Process Technology"),
    ],
}

STAFF_ROSTER = [
    "GHAMZA LABEEB KHADER","DANIEL JOSEPH LAMB","NARDEEN TARIQ","FAIZ LAZAM ALSHAMMARI",
    "DR. MASHAEL ALSHAMMARI","AHMED ALBADER","Noura Aldossari","Ahmed Gasem Alharbi",
    "Mohammed Saeed Alfarhan","Abdulmalik Halawani","Dari AlMutairi","Meshari AlMutrafi",
    "Myra Crawford","Meshal Alghurabi","Ibrahim Alrawili","Michail Mavroftas","Gerhard Van der Poel",
    "Khalil Razak","Mohammed Alwuthylah","Rana Ramadan","Salem Saleh Subaih","Barend Daniel Esterhuizen",
]

# ----------------------------- Theme --------------------------------
ADI_GREEN = "#245a34"
SHADE_LOW  = "rgba(36,90,52,0.06)"
SHADE_MED  = "rgba(36,90,52,0.08)"
SHADE_HIGH = "rgba(36,90,52,0.06)"

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="🧰", layout="wide")

CUSTOM_CSS = f"""
<style>
/* Banner + tabs */
.adi-banner {{
  background:{ADI_GREEN}; color:#fff; border-radius:10px; padding:16px 18px; font-weight:600;
}}
.stTabs [data-baseweb="tab-highlight"] {{
  background: linear-gradient(90deg,{ADI_GREEN} 0%, {ADI_GREEN} 100%);
}}
.badge {{ display:inline-block; background:#e5d4a3; color:#3b2f14; padding:5px 10px; border-radius:999px; font-size:12px; }}

/* Shaded bands */
.band-low  {{ background:{SHADE_LOW};  border-radius:10px; padding:10px 14px; }}
.band-med  {{ background:{SHADE_MED};  border-radius:10px; padding:10px 14px; }}
.band-high {{ background:{SHADE_HIGH}; border-radius:10px; padding:10px 14px; }}

/* Upload parse status */
.parse-ok   {{ border-left:4px solid {ADI_GREEN}; background:#f1f7f3; padding:10px 12px; border-radius:6px; }}
.parse-warn {{ border-left:4px solid #c07d00;  background:#fff9e8; padding:10px 12px; border-radius:6px; }}

/* Buttons */
.stButton > button {{ border-radius:10px; padding:10px 16px; font-weight:600; }}

/* --- Pill checkboxes (robust across Streamlit versions) --- */
#verbs [role="checkbox"]{{
  display:inline-block; margin:8px 10px 6px 0;
}}
#verbs [role="checkbox"] input{{ display:none; }}   /* hide square box */
#verbs [role="checkbox"] label{{
  display:inline-block; border:1px solid #e8e8e8; background:#f8f8f7; color:#333;
  padding:10px 18px; border-radius:999px; font-weight:600; cursor:pointer; transition:all .12s;
}}
#verbs [role="checkbox"]:hover label{{ background:#efefee; }}
#verbs [role="checkbox"][aria-checked="true"] label{{
  background:{ADI_GREEN}; color:#fff; border-color:{ADI_GREEN};
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------- Helpers -------------------------------
def stable_seed(*parts, jitter_minutes=0):
    base = "|".join(map(str, parts))
    if jitter_minutes:
        base += f"|{int(time.time()//(60*jitter_minutes))}"
    return int(hashlib.sha256(base.encode("utf-8")).hexdigest()[:10], 16)

def split_chunks(text, max_chars=1200):
    chunks, cur, n = [], [], 0
    for line in text.splitlines():
        line = line if line.strip() else " "
        if n + len(line) > max_chars and cur:
            chunks.append(" ".join(cur)); cur, n = [line], len(line)
        else:
            cur.append(line); n += len(line)
    if cur: chunks.append(" ".join(cur))
    return chunks

def normalise_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def tfidf_keyphrases(text, top_k=25):
    docs = split_chunks(text, 1000) or [" "]
    vect = TfidfVectorizer(ngram_range=(1,2), max_features=6000, stop_words="english")
    X = vect.fit_transform(docs if len(docs)>1 else docs+[" "])
    scores = X.toarray().sum(axis=0)
    terms = vect.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda x:x[1], reverse=True)
    return [t for t,_ in ranked[:top_k]]

def noun_verb_terms(text, limit=40):
    try:
        toks = word_tokenize(text)
        tagged = pos_tag(toks)
    except Exception:
        return []
    keep = [w for (w,p) in tagged if (p.startswith("NN") or p.startswith("VB")) and w.isalpha() and len(w)>2]
    out, seen = [], set()
    for w in keep:
        lw = w.lower()
        if lw not in seen:
            seen.add(lw); out.append(lw)
        if len(out) >= limit: break
    return out

# ----------------------------- Parsing ------------------------------
def parse_pdf(file_buf, deep=False, max_pages=60, timeout_s=20):
    start = time.time(); text=[]; parsed=0; total=0
    with fitz.open(stream=file_buf.read(), filetype="pdf") as d:
        total = d.page_count
        step = 1 if deep else max(1, total//max_pages or 1)
        for i in range(0, total, step):
            if time.time()-start > timeout_s: break
            try:
                t = d.load_page(i).get_text("text")
                if t: text.append(t); parsed += 1
            except Exception:
                continue
    return "\n".join(text), {"pages_scanned": parsed, "total_pages": total}

def parse_docx(file_buf):
    doc = DocxDocument(file_buf); out=[]
    for p in doc.paragraphs:
        if p.text: out.append(p.text)
    for t in doc.tables:
        for r in t.rows:
            row = " ".join(normalise_spaces(c.text) for c in r.cells if c.text)
            if row: out.append(row)
    return "\n".join(out)

def parse_pptx(file_buf):
    prs = Presentation(file_buf); out=[]
    for s in prs.slides:
        for sh in s.shapes:
            if hasattr(sh,"text") and sh.text:
                out.append(sh.text)
    return "\n".join(out)

# ---------------------- MCQ QUALITY UPGRADE ------------------------
def _noun_phrases(text, cap=60):
    # lightweight noun phrase finder using POS tags
    try:
        toks = word_tokenize(text)
        tags = pos_tag(toks)
    except Exception:
        return []
    keep, cur = [], []
    for w,p in tags:
        if p.startswith("JJ") or p.startswith("NN"):
            cur.append(w)
        else:
            if cur:
                np = " ".join(cur).strip()
                if 2 < len(np) < 80 and len(np.split()) <= 6:
                    keep.append(np.lower())
                cur = []
    if cur:
        np = " ".join(cur).strip()
        if 2 < len(np) < 80 and len(np.split()) <= 6:
            keep.append(np.lower())
    # de-dup while preserving order
    out, seen = [], set()
    for k in keep:
        if k not in seen:
            seen.add(k); out.append(k)
        if len(out) >= cap: break
    return out

def antonyms(word):
    ants = set()
    for s in wn.synsets(word):
        for l in s.lemmas():
            for a in l.antonyms():
                ants.add(a.name().replace("_"," "))
    return list(ants)

def _near_length_pool(answer, bank):
    alen = len(answer)
    cand = []
    for w in bank:
        lw = w.lower().strip()
        if lw == answer.lower().strip(): 
            continue
        if abs(len(lw) - alen) <= 4:
            cand.append(lw)
    # Prefer multi-word look-alikes first
    multi = [c for c in cand if len(c.split())>=2]
    single= [c for c in cand if len(c.split())<2]
    cand = multi + single
    return list(dict.fromkeys(cand))  # unique, keep order

def _wordnet_siblings(term):
    sib = set()
    for s in wn.synsets(term.replace(" ", "_")):
        for rel in (s.hypernyms() + s.hyponyms()):
            for l in rel.lemmas():
                sib.add(l.name().replace("_"," "))
    return list(sib)

def plausible_distractors(answer, pool, max_n=10):
    s = set()
    s.update(a for a in antonyms(answer))
    s.update(_wordnet_siblings(answer))
    s.update(_near_length_pool(answer, pool))
    s = [w for w in s if w.lower()!=answer.lower() and 2 < len(w) < 60]
    s = [w for w in s if len(w.split()) <= 8]
    # Avoid overly generic distractors
    ban = {"none of the above","all of the above","both a and b","neither a nor b"}
    s = [w for w in s if w.lower() not in ban]
    return s[:max_n]

def _clean_fact(s):
    s = s.strip().replace("\u00ad", "")  # soft hyphen
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" .;:")
    return s

def _candidate_facts(source_text, want=120):
    # TF-IDF + noun phrases + short sentences → candidates
    keys = tfidf_keyphrases(source_text, top_k=want//2 + 30)
    nps  = _noun_phrases(source_text, cap=want)
    facts = []
    for t in keys + nps:
        t = _clean_fact(t)
        if len(t) < 3: continue
        if t not in facts:
            facts.append(t)
        if len(facts) >= want: break
    # also pull short sentences as fallbacks
    for s in [x.strip() for x in re.split(r"[\.!?]\s+", source_text)]:
        if 6 <= len(s.split()) <= 18 and s not in facts:
            facts.append(s)
            if len(facts) >= want + 40: break
    return facts

def _stem_templates(term, context_keys, focus_tier="MED"):
    ck = ", ".join(context_keys[:4]) if context_keys else "the topic"
    t  = term
    # Difficulty nudged by focus tier
    if focus_tier == "LOW":
        return [
            (f"Select the **best definition** of **{t}**:",
             lambda ans: (ans, f"A concept unrelated to {ck}", f"An opposite of {ans}", f"A vague example without structure")),
            (f"Which statement about **{t}** is **TRUE**?",
             lambda ans: (ans, f"{t} is unrelated to {ck}", f"{t} always contradicts best practice", f"{t} is purely hypothetical")),
        ]
    if focus_tier == "HIGH":
        return [
            (f"Which option **best justifies** using **{t}** in practice?",
             lambda ans: (ans, f"It replaces all checks with guesswork", f"It ignores constraints about {ck}", f"It randomises decisions")),
            (f"Which statement is the **most accurate critique** of poor use of **{t}**?",
             lambda ans: (ans, f"It proves {t} is unnecessary", f"It shows {t} should never be planned", f"It means outcomes are always optimal")),
        ]
    # MED default
    return [
        (f"Which statement about **{t}** is **TRUE**?",
         lambda ans: (ans, f"{t} is unrelated to {ck}", f"{t} is purely theoretical with no use", f"{t} always means the opposite")),
        (f"What is the **primary purpose** of **{t}** in this module?",
         lambda ans: (ans, f"To minimise {t}", f"To randomise {t}", f"To remove the need for {t}")),
        (f"Which option **best completes** the statement: *In practice, {t} helps to…*",
         lambda ans: (ans, f"…avoid all planning for {t}", f"…ignore {ck}", f"…replace checks with guesswork")),
        (f"Select the **best definition** of **{t}**:",
         lambda ans: (ans, f"A concept unrelated to {ck}", f"An opposite of {ans}", f"A random example without structure")),
    ]

def build_mcq_from_term(term, distractor_bank, rng, context_keys, focus_tier="MED"):
    term = _clean_fact(term)
    answer = term
    templates = _stem_templates(term, context_keys, focus_tier)
    stem, make_options = templates[rng.randrange(len(templates))]
    base_choices = list(make_options(answer))
    extra = plausible_distractors(answer, distractor_bank, max_n=10)
    # Merge and de-duplicate while keeping first as correct
    seen = set()
    merged = []
    for ch in base_choices + extra:
        c = normalise_spaces(ch)
        if not c or c.lower() in seen:
            continue
        seen.add(c.lower()); merged.append(c)
        if len(merged) >= 8: break
    # Ensure at least 4 options
    if len(merged) < 4:
        for w in distractor_bank:
            w = normalise_spaces(w)
            if w.lower() == answer.lower(): 
                continue
            if w.lower() not in seen and len(w.split()) <= 8:
                seen.add(w.lower()); merged.append(w)
            if len(merged) >= 4: break
    rng.shuffle(merged)
    # Guarantee answer present; if not, swap in
    if answer not in merged:
        merged[0] = answer
        rng.shuffle(merged)
    choices = merged[:4]
    key = "ABCD"[choices.index(answer)] if answer in choices else "A"
    # Guardrails: keep options concise & distinct
    choices = [c[:120] for c in choices]
    if len(set([c.lower() for c in choices])) < 4:
        # backfill uniqueness
        fill = [w for w in distractor_bank if w.lower() not in [c.lower() for c in choices] and 2 < len(w) <= 60]
        for i in range(4):
            if sum(1 for _ in [choices[j] for j in range(4) if j!=i and choices[j].lower()==choices[i].lower()])>0 and fill:
                choices[i] = fill.pop(0)
        if answer not in choices:
            choices[0] = answer
            rng.shuffle(choices)
            key = "ABCD"[choices.index(answer)]
    return {"stem": stem, "choices": choices, "key": key}

def generate_mcqs(source_text, num_qs, seed_tuple, focus_tier="MED"):
    rng = random.Random(stable_seed(*seed_tuple, jitter_minutes=0))
    facts = _candidate_facts(source_text, want=max(120, num_qs*10))
    context_keys = tfidf_keyphrases(source_text, top_k=12)
    mcqs, used = [], set()
    for term in facts:
        tnorm = term.lower()
        if tnorm in used: 
            continue
        q = build_mcq_from_term(term, facts, rng, context_keys, focus_tier)
        # Filters
        if any(len(c.split())>16 for c in q["choices"]): 
            continue
        if re.search(rf"\b{re.escape(term)}\b", q["stem"], re.I) and q["stem"].lower().count(term.lower())>1:
            continue
        used.add(tnorm); mcqs.append(q)
        if len(mcqs) >= num_qs: break
    # Safety backfill
    while len(mcqs) < num_qs and facts:
        t = facts.pop(0)
        mcqs.append(build_mcq_from_term(t, facts, rng, context_keys, focus_tier))
    return mcqs

# --------------------------- Activities / Revision -------------------
def generate_activities(topic, verbs, minutes_list, source_text):
    acts=[]
    mats = ["whiteboard","markers","laptop","handout"]
    def prompt_for(verb, lvl):
        if lvl=="LOW":
            return f"Quick check: **{verb}** the key idea(s) for **{topic or 'this lesson'}**."
        if lvl=="MED":
            return f"Pair task: **use {verb}** on a short scenario about **{topic or 'this lesson'}**."
        return f"Mini-project: **{verb}** a solution and justify choices for **{topic or 'this lesson'}**."
    for minutes in minutes_list:
        level = "LOW" if minutes<=15 else ("MED" if minutes<=30 else "HIGH")
        verb = (verbs.get(level) or ["identify","apply","design"])[0]
        acts.append({
            "title": f"{verb.title()} — {minutes} min",
            "minutes": minutes,
            "task": prompt_for(verb, level),
            "materials": mats[:2] if level!="HIGH" else mats,
            "deliverable": "1-slide summary" if level!="HIGH" else "Short design brief"
        })
    return acts

def generate_revision(topic, source_text, k=6):
    keys = tfidf_keyphrases(source_text, top_k=12)
    anchors = ", ".join(keys[:6]) if keys else (topic or "the lesson")
    prompts = [
        f"Summarise **{topic or 'the lesson'}** in ≤120 words. Include: {anchors}.",
        f"Define 5 key terms from **{topic or 'the lesson'}** and give a 1-line example each.",
        f"Create a 6-step checklist for applying **{topic or 'the lesson'}** in practice.",
        f"Contrast two closely related ideas from the lesson and provide one worked example.",
        f"Draft 3 exam-style questions (with answers) covering: {anchors}.",
        f"Draw a quick flow or mind-map linking: {anchors}."
    ]
    return prompts[:k]

# ---------------------------- UI pieces -----------------------------
def header():
    st.markdown(f"""
    <div class="adi-banner">
      ADI Builder — Lesson Activities & Questions
      <div style="font-weight:400;margin-top:4px">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
    </div>
    """, unsafe_allow_html=True)

def band(title, level_key):
    css = {"LOW":"band-low","MED":"band-med","HIGH":"band-high"}[level_key]
    st.markdown(f"""<div class="{css}"><b>{title}</b>""", unsafe_allow_html=True)

def endband():
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------- State --------------------------------
if "parsed_text" not in st.session_state: st.session_state.parsed_text = ""
if "parse_meta"  not in st.session_state: st.session_state.parse_meta  = {}
if "selected_verbs" not in st.session_state:
    st.session_state.selected_verbs = {"LOW":[], "MED":[], "HIGH":[]}
if "last_mcqs" not in st.session_state: st.session_state["last_mcqs"]=[]
if "last_acts" not in st.session_state: st.session_state["last_acts"]=[]
if "last_rev"  not in st.session_state: st.session_state["last_rev"]=[]

# ---------------------------- Layout -------------------------------
header()
tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

# ---------------------------- Sidebar ------------------------------
with st.sidebar:
    st.subheader("Upload (optional)")
    upload = st.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"], label_visibility="collapsed")
    deep   = st.checkbox("Deep scan (all pages, slower)", value=True, help="Scans more pages with timeouts")
    if upload is not None:
        stat = st.empty()
        try:
            if upload.name.lower().endswith(".pdf"):
                with st.spinner("Parsing PDF..."):
                    fb = io.BytesIO(upload.getbuffer())
                    text, meta = parse_pdf(fb, deep=deep, timeout_s=38 if deep else 16)
            elif upload.name.lower().endswith(".docx"):
                with st.spinner("Parsing Word..."):
                    fb = io.BytesIO(upload.getbuffer()); text = parse_docx(fb); meta={}
            else:
                with st.spinner("Parsing PowerPoint..."):
                    fb = io.BytesIO(upload.getbuffer()); text = parse_pptx(fb); meta={}
            st.session_state.parsed_text = text; st.session_state.parse_meta = meta
            stat.markdown(
                f"""<div class="parse-ok"><b>Parsed successfully</b><br/>
                <small>{meta.get('pages_scanned','')} / {meta.get('total_pages','')} pages (PDF) · Source length: {len(text):,} chars</small></div>""",
                unsafe_allow_html=True,
            )
        except Exception as e:
            stat.markdown(f"""<div class="parse-warn"><b>Could not parse file</b><br/><small>{e}</small></div>""",
                          unsafe_allow_html=True)

    st.subheader("Course context")

    cohort_names = list(COURSE_CATALOG.keys())
    cohort = st.selectbox("Cohort", cohort_names, index=0)

    course_codes = [f"{c[0]} — {c[1]}" for c in COURSE_CATALOG.get(cohort, [])]
    course_choice = st.selectbox("Course", course_codes, index=0) if course_codes else ""

    if course_choice:
        sel_code, sel_title = course_choice.split(" — ", 1)
    else:
        sel_code, sel_title = "", ""

    lesson = st.selectbox("Lesson", list(range(1,15)), index=0)
    week   = st.selectbox("Week",   list(range(1,15)), index=0)

    default_topic = f"{sel_code}: {sel_title}" if sel_code else ""
    topic  = st.text_input("Topic / outcome", value=default_topic,
                           placeholder="Module description, knowledge & skills outcomes")

    st.subheader("Number of MCQs")
    num_mcqs = st.selectbox("How many questions?", [5,10,15,20,30], index=1)

    st.subheader("Activities duration (mins)")
    act_times = st.multiselect("Pick durations", [5,10,15,20,30,45,60], default=[10,20,30,60])

    st.subheader("Instructor (for unique seed)")
    instructor_sel = st.selectbox("Your name", ["(not set)"] + STAFF_ROSTER, index=0)
    instructor = "" if instructor_sel == "(not set)" else instructor_sel

    st.subheader("Export")
    export_pack = st.checkbox("Include Course Pack JSON", value=False)

# Auto Bloom focus
focus_map = {1:"LOW",2:"LOW",3:"LOW",4:"LOW",5:"MED",6:"MED",7:"MED",8:"MED",9:"MED",10:"HIGH",11:"HIGH",12:"HIGH",13:"HIGH",14:"HIGH"}
focus_tier = focus_map.get(week,"LOW")
st.write(f"**Bloom focus (auto)**  <span class='badge'>Week {week}: {focus_tier.title()}</span>", unsafe_allow_html=True)

# Source text editor on MCQ tab
with tabs[0]:
    st.caption("Paste or jot key notes, vocab, facts here…")
    src = st.text_area("Source text (editable)", value=st.session_state.parsed_text, height=200, label_visibility="collapsed")

# Verbs UI (pills)
VERBS = {
    "LOW":["define","identify","list","recall","describe","label"],
    "MED":["apply","demonstrate","solve","illustrate","classify","compare"],
    "HIGH":["evaluate","synthesize","design","justify","critique","create"]
}

def render_verb_band(level):
    title = {
        "LOW":"LOW (Weeks 1–4): Remember / Understand",
        "MED":"MEDIUM (Weeks 5–9): Apply / Analyse",
        "HIGH":"HIGH (Weeks 10–14): Evaluate / Create"
    }[level]
    band(title, level)
    for v in VERBS[level]:
        key = f"verb_{level}_{v}"
        default = v in st.session_state.selected_verbs[level]
        checked = st.checkbox(v.title(), value=default, key=key, label_visibility="visible")
        if checked and v not in st.session_state.selected_verbs[level]:
            st.session_state.selected_verbs[level].append(v)
        if not checked and v in st.session_state.selected_verbs[level]:
            st.session_state.selected_verbs[level].remove(v)
    endband()

st.markdown('<div id="verbs">', unsafe_allow_html=True)
render_verb_band("LOW")
render_verb_band("MED")
render_verb_band("HIGH")
st.markdown('</div>', unsafe_allow_html=True)

# Outline current focus tier subtly
st.markdown(
    f"""<script>
const tier="{focus_tier}";
for(const el of window.parent.document.querySelectorAll('.band-low,.band-med,.band-high')){{
  if((tier==='LOW' && el.classList.contains('band-low'))||
     (tier==='MED' && el.classList.contains('band-med'))||
     (tier==='HIGH'&& el.classList.contains('band-high'))){{
       el.style.boxShadow='inset 0 0 0 2px {ADI_GREEN}';
  }}
}}
</script>""",
    unsafe_allow_html=True,
)

# Actions
colL, colR = st.columns([1,1])
with colL:
    gen_btn = st.button("✨ Generate MCQs", type="primary", use_container_width=True)
with colR:
    regen_btn = st.button("↻ Regenerate", use_container_width=True)

if gen_btn or regen_btn:
    if not (src or st.session_state.parsed_text):
        st.warning("Please add source text (or upload a file) to generate MCQs.")
    else:
        tier_verbs = {
            "LOW":  st.session_state.selected_verbs["LOW"]  or VERBS["LOW"],
            "MED":  st.session_state.selected_verbs["MED"]  or VERBS["MED"],
            "HIGH": st.session_state.selected_verbs["HIGH"] or VERBS["HIGH"],
        }
        seed_parts = (instructor or "anon", week, lesson, topic or "topic")
        mcqs = generate_mcqs(src, num_mcqs, seed_parts, focus_tier=focus_tier)
        acts = generate_activities(topic, tier_verbs, act_times, src)
        rev  = generate_revision(topic or "this lesson", src)
        st.session_state["last_mcqs"]=mcqs
        st.session_state["last_acts"]=acts
        st.session_state["last_rev"]=rev

# Output
mcqs_out = st.session_state.get("last_mcqs", [])
acts_out  = st.session_state.get("last_acts", [])
rev_out   = st.session_state.get("last_rev",  [])

st.divider(); st.subheader("Preview")
col1, col2 = st.columns([1.2,0.8], gap="large")

with col1:
    st.markdown("#### MCQs")
    if not mcqs_out:
        st.info("No questions yet. Click **Generate MCQs** to create a set.")
    else:
        for i,q in enumerate(mcqs_out,1):
            st.markdown(f"**{i}. {q['stem']}**")
            st.markdown("<ul>"+ "".join([f"<li>{li}. {opt}</li>" for li,opt in zip('ABCD', q['choices'])]) +"</ul>", unsafe_allow_html=True)
            st.caption(f"Answer: **{q['key']}**")

with col2:
    st.markdown("#### Activities")
    if not acts_out: st.info("Pick durations in the sidebar to propose activities.")
    else:
        for a in acts_out: st.markdown(f"- **{a['title']}** – {a['task']}")
    st.markdown("#### Revision")
    if not rev_out: st.info("Revision prompts will appear here.")
    else:
        st.markdown("<ul>"+ "".join([f"<li>{r}</li>" for r in rev_out]) +"</ul>", unsafe_allow_html=True)

# ----------------------------- Downloads ----------------------------
st.divider(); st.subheader("Download")
def text_to_docx(title, mcqs=None, activities=None, revision=None):
    doc = DocxDocument()
    doc.add_heading(title, level=1)
    if mcqs:
        doc.add_heading("Multiple-choice questions", level=2)
        for i,q in enumerate(mcqs,1):
            doc.add_paragraph(f"{i}. {q['stem']}")
            for li,opt in zip("ABCD", q["choices"]):
                doc.add_paragraph(f"{li}. {opt}")
            doc.add_paragraph(f"Answer: {q['key']}"); doc.add_paragraph("")
    if activities:
        doc.add_heading("Skills Activities", level=2)
        for i,a in enumerate(activities,1):
            doc.add_paragraph(f"{i}. {a['title']} ({a['minutes']} min)")
            doc.add_paragraph(a["task"])
            if a.get("materials"):   doc.add_paragraph("Materials: "+", ".join(a["materials"]))
            if a.get("deliverable"): doc.add_paragraph("Deliverable: "+a["deliverable"])
            doc.add_paragraph("")
    if revision:
        doc.add_heading("Revision", level=2)
        for i,r in enumerate(revision,1): doc.add_paragraph(f"{i}. {r}")
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

def mcqs_to_gift(mcqs):
    lines = []
    for q in mcqs:
        stem = q["stem"].replace("\n"," ").strip()
        lines.append(f"::{stem}:: {stem} {{")
        for li,opt in zip("ABCD", q["choices"]):
            lines.append((" = " if li==q["key"] else " ~ ")+opt)
        lines.append("}")
    return "\n".join(lines)

def mcqs_to_moodle_xml(mcqs, quiz_name="ADI Quiz"):
    from xml.sax.saxutils import escape
    lines = ['<?xml version="1.0" encoding="UTF-8"?>','<quiz>']
    for q in mcqs:
        lines.append('<question type="multichoice">')
        lines.append(f"<name><text>{escape(q['stem'][:60])}</text></name>")
        lines.append(f"<questiontext format=\"html\"><text><![CDATA[{escape(q['stem'])}]]></text></questiontext>")
        lines.append("<shuffleanswers>1</shuffleanswers><single>true</single>")
        # correct
        lines.append(f"<answer fraction=\"100\"><text>{escape(q['choices']['ABCD'.index(q['key'])])}</text></answer>")
        # distractors
        for li,opt in zip("ABCD", q["choices"]):
            if li==q["key"]: continue
            lines.append(f"<answer fraction=\"0\"><text>{escape(opt)}</text></answer>")
        lines.append("</question>")
    lines.append("</quiz>")
    return "\n".join(lines)

title = lambda: f"ADI_{week:02d}_W{week}_L{lesson}_{(topic or 'Lesson').strip().replace(' ','_')}"
dl = st.columns([1,1,1,1])

with dl[0]:
    if mcqs_out:
        docx_buf = text_to_docx(title(), mcqs_out, acts_out, rev_out)
        st.download_button("📄 Download DOCX", data=docx_buf, file_name=f"{title()}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True)
    else: st.button("📄 Download DOCX", disabled=True, use_container_width=True)

with dl[1]:
    if mcqs_out:
        gift = mcqs_to_gift(mcqs_out)
        st.download_button("🎯 Download GIFT", data=gift, file_name=f"{title()}.gift",
                           mime="text/plain", use_container_width=True)
    else: st.button("🎯 Download GIFT", disabled=True, use_container_width=True)

with dl[2]:
    if mcqs_out:
        xml = mcqs_to_moodle_xml(mcqs_out, quiz_name=title())
        st.download_button("🧩 Moodle XML", data=xml, file_name=f"{title()}.xml",
                           mime="application/xml", use_container_width=True)
    else: st.button("🧩 Moodle XML", disabled=True, use_container_width=True)

with dl[3]:
    if export_pack and (mcqs_out or acts_out or rev_out):
        pack = {
            "meta":{"title":title(),"week":week,"lesson":lesson,"topic":topic,
                    "generated_at":datetime.utcnow().isoformat()+"Z","instructor":instructor},
            "mcqs":mcqs_out,"activities":acts_out,"revision":rev_out
        }
        js = json.dumps(pack, ensure_ascii=False, indent=2)
        st.download_button("📦 Course Pack JSON", data=js, file_name=f"{title()}_pack.json",
                           mime="application/json", use_container_width=True)
    else: st.button("📦 Course Pack JSON", disabled=True, use_container_width=True)

# Activities & Revision tabs (read-only mirrors)
with tabs[1]:
    st.caption("Activities reflect durations chosen in the sidebar.")
    if acts_out:
        for a in acts_out:
            st.markdown(f"- **{a['title']}** – {a['task']}  \n  _Deliverable: {a['deliverable']}_")
    else: st.info("Pick durations and click Generate on the MCQ tab first.")

with tabs[2]:
    if rev_out:
        st.markdown("<ol>"+ "".join([f"<li>{r}</li>" for r in rev_out]) +"</ol>", unsafe_allow_html=True)
    else: st.info("Generate once from the MCQ tab to populate revision prompts.")
