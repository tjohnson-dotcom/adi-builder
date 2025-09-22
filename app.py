import streamlit as st
import random, re
from io import BytesIO

# Optional dependencies
try:
    from docx import Document
except Exception:
    Document = None
try:
    from pptx import Presentation
except Exception:
    Presentation = None
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# -------------------------------
# Page & Styling
# -------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="🧩", layout="wide")

st.markdown("""
<style>
  :root{
    --adi-green:#15563d;
    --adi-accent:#b79e82;
    --adi-bg:#f6f4f1;
    --adi-ink:#1d2724;
    --adi-soft:#efeae3;
  }
  html, body, .stApp {background: var(--adi-bg); color: var(--adi-ink);}
  .block-container {max-width: 1040px; padding-top: 1.1rem; padding-bottom: 3.2rem;}

  h1,h2,h3{color:var(--adi-green); font-weight:800; letter-spacing:.2px;}
  .hero{margin:-.4rem 0 1rem 0; padding:16px 18px; border-radius:14px;
    background: linear-gradient(90deg, var(--adi-green), #0e3d2a 60%, var(--adi-accent));
    color:#fff; box-shadow: 0 10px 24px rgba(0,0,0,.08);}

  .toolbar{display:flex; gap:.75rem; flex-wrap:wrap; align-items:end;
    background:#fff; border:1px solid var(--adi-accent); padding:.75rem .8rem; border-radius:14px;
    box-shadow: 0 6px 16px rgba(0,0,0,.05); margin-bottom:.7rem;}

  .card{border:2px solid var(--adi-accent); border-radius:14px; padding:14px 16px; background:#fff;
    box-shadow:0 6px 18px rgba(0,0,0,.05); margin-bottom:12px;}

  /* Tabs */
  .stTabs [data-baseweb="tab"]{background:#e8e4df; color:#2e2e2e; border-radius:12px 12px 0 0;
    padding:.55rem .9rem; font-weight:800;}
  .stTabs [aria-selected="true"]{background:#fff; color:var(--adi-green); border-bottom:3px solid var(--adi-green);}

  /* Buttons */
  .stButton>button{background:var(--adi-green); color:#fff; font-weight:800; border:0; border-radius:12px; padding:.65rem 1rem;
    box-shadow:0 8px 18px rgba(21,86,61,.20);}
  .stButton>button:hover{filter:brightness(.96); transform: translateY(-1px);}
  .stButton>button:active{transform: translateY(0);}

  /* Inputs */
  .stSelectbox > div > div,
  .stMultiSelect > div > div,
  .stTextInput > div > div > input,
  .stNumberInput input,
  .stTextArea textarea{
    border-radius:12px !important;
    border:2px solid var(--adi-accent) !important;
    box-shadow:none !important;
    margin-bottom:4px !important;
  }

  /* FIX: Drag & drop file uploader (all states) */
  .stFileUploader div[data-testid="stFileDropzone"],
  .stFileUploader div[data-testid="stFileUploader"],
  .stFileUploader > div > div{
    border:2px dashed var(--adi-green) !important;
    border-radius:12px !important;
    background:#fff;
  }

  /* Verb multiselect compact */
  .stMultiSelect{margin-bottom:0.25rem !important;}
  .stMultiSelect label{font-weight:600; margin-bottom:0.15rem; color:var(--adi-green);}
  .stMultiSelect [data-baseweb="tag"]{
    background: var(--adi-soft) !important; color: #2b2b2b !important; border-radius: 999px !important;
    margin:1px 3px 1px 0 !important; padding:0.15rem 0.5rem !important; font-size:0.83rem !important;
  }

  /* Slider */
  .stSlider [data-baseweb="slider"]>div>div{background:var(--adi-green);}
  .stSlider [role="slider"]{ box-shadow:0 0 0 4px rgba(21,86,61,.15) !important; }

  /* Section headers with green underline */
  .section-header{
    border-bottom:3px solid var(--adi-green);
    padding-bottom:0.25rem;
    margin-bottom:0.75rem;
  }

  /* Footer */
  .adi-footer{position: fixed; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, var(--adi-accent), var(--adi-green));
    color:#fff; padding:.55rem .9rem; text-align:center; font-weight:700;
    box-shadow: 0 -6px 20px rgba(0,0,0,.10); z-index:999;}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero">
  <b>ADI Builder</b><br>
  Generate crisp <u>Knowledge MCQs</u> or practical <u>Skills Activities</u> directly from lesson files.
</div>""", unsafe_allow_html=True)

# -------------------------------
# Bloom’s levels & verbs
# -------------------------------
BLOOMS = {
    "Remember":   ["define", "list", "recall", "identify"],
    "Understand": ["explain", "summarise", "describe", "classify"],
    "Apply":      ["apply", "demonstrate", "use", "illustrate"],
    "Analyse":    ["analyse", "compare", "differentiate", "categorise"],
    "Evaluate":   ["evaluate", "justify", "critique", "assess"],
    "Create":     ["design", "develop", "construct", "propose"]
}
LEVELS = list(BLOOMS.keys())
DEFAULT_MIX = ["Understand", "Apply", "Analyse"]

# -------------------------------
# File parsing
# -------------------------------
def extract_text_from_pdf(data: bytes) -> str:
    if not fitz: return ""
    return "\n".join(p.get_text("text") for p in fitz.open(stream=data, filetype="pdf"))

def extract_text_from_docx(data: bytes) -> str:
    if not Document: return ""
    bio = BytesIO(data); doc = Document(bio)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_pptx(data: bytes) -> str:
    if not Presentation: return ""
    bio = BytesIO(data); prs = Presentation(bio)
    return "\n".join(shp.text for slide in prs.slides for shp in slide.shapes if hasattr(shp, "text") and shp.text)

def extract_text(uploaded) -> str:
    if not uploaded: return ""
    data = uploaded.read(); name = uploaded.name.lower()
    if name.endswith(".pdf"): return extract_text_from_pdf(data)
    if name.endswith(".docx"): return extract_text_from_docx(data)
    if name.endswith(".pptx"): return extract_text_from_pptx(data)
    return ""

# -------------------------------
# Topic carving
# -------------------------------
def carve_topics(raw_text: str, want: int = 30) -> list[str]:
    if not raw_text: return []
    lines = [re.sub(r"\s+", " ", L).strip() for L in raw_text.splitlines()]
    lines = [L for L in lines if 6 <= len(L) <= 140 and re.search(r"[A-Za-z]", L)]
    seen, out = set(), []
    for L in lines:
        if L.lower() not in seen: seen.add(L.lower()); out.append(L)
    random.shuffle(out)
    return out[:want]

# -------------------------------
# MCQ builder
# -------------------------------
def build_mcq(topic: str, verb: str, distractor_pool: list[str]) -> dict:
    stem = f"{verb.capitalize()} the key idea: **{topic}**."
    correct = f"A concise {verb} of {topic}"
    d = [f"{verb.capitalize()} of {t}" for t in distractor_pool if t != topic][:3]
    while len(d) < 3: d.append("A plausible but incorrect statement")
    options = [correct] + d; random.shuffle(options)
    return {"stem": stem, "options": options, "correct": "abcd"[options.index(correct)]}

# -------------------------------
# Activity builder
# -------------------------------
ACTIVITY_TEMPLATES = [
    ("Guided Practice","Individually complete a short, authentic task.",
     ["Read the brief and success criteria.","Complete the task step-by-step.","Self-check against the criteria.","Submit for quick feedback."]),
    ("Pair & Share","Work in pairs to apply knowledge.",
     ["Agree roles (Speaker / Notetaker).","Discuss the prompt and capture key points.","Swap roles and refine the output.","Share one insight with another pair."]),
    ("Mini Case","Analyse a short scenario and recommend actions.",
     ["Read the case and highlight key facts.","Identify risks or constraints.","Recommend two actions and justify them.","Prepare a 60-second summary."]),
    ("Procedure Drill","Follow a procedure safely and accurately.",
     ["Review the SOP steps together.","Perform steps in order while a peer observes.","Record deviations and fix them.","Reflect on one improvement."]),
    ("Reflect & Improve","Evaluate your output and plan improvements.",
     ["Compare against the success criteria.","Identify one strength and one area to improve.","Write a short improvement plan.","Share your plan with the group."]),
]

def build_activity(level: str, verbs: list[str], topic: str, minutes: int) -> dict:
    name, brief, steps = random.choice(ACTIVITY_TEMPLATES)
    v = random.choice(verbs) if verbs else "apply"
    return {"title": f"{name} — {level}","brief": brief,
            "outcome": f"{v.capitalize()} learning about {topic} at {level} level.","steps": steps,
            "resources": ["Slides/eBook extract","Worksheet/template","Pens"],
            "assessment": random.choice(["Tutor check","Peer feedback","Self checklist"]),
            "timing": minutes}

# -------------------------------
# Toolbar
# -------------------------------
st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
uploaded = st.file_uploader("Upload PDF / DOCX / PPTX", type=["pdf","docx","pptx"])
col1, col2 = st.columns(2)
with col1: week = st.selectbox("Week", list(range(1,15)), index=0)
with col2: lesson = st.selectbox("Lesson", list(range(1,5)), index=0)
st.markdown("</div>", unsafe_allow_html=True)

raw_text = extract_text(uploaded) if uploaded else ""
topics_pool = carve_topics(raw_text, want=40)

# -------------------------------
# Tabs
# -------------------------------
tab_mcq, tab_act = st.tabs(["🧠 Knowledge MCQs", "🛠 Skills Activities"])

with tab_mcq:
    st.markdown("<h2 class='section-header'>Knowledge MCQs</h2>", unsafe_allow_html=True)
    chosen_levels = st.multiselect("Bloom’s levels", LEVELS, default=DEFAULT_MIX)
    auto_verbs_mcq = st.checkbox("Auto-select verbs (balanced)", value=False)
    verb_bank = []
    if auto_verbs_mcq:
        for lvl in chosen_levels: verb_bank.extend(BLOOMS[lvl][:2])
    else:
        for lvl in chosen_levels:
            picks = st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=BLOOMS[lvl][:2], key=f"verbs_{lvl}_mcq")
            verb_bank.extend(picks)
    total_mcqs = st.slider("Number of questions", 5, 10, 6)
    if st.button("Generate MCQs", type="primary"):
        if not topics_pool: st.info("Please upload a lesson file.")
        else:
            for i,t in enumerate(topics_pool[:total_mcqs],1):
                q = build_mcq(t, verb_bank[i % len(verb_bank)], topics_pool)
                st.markdown(f"<div class='card'><b>Q{i}.</b> {q['stem']}<br>", unsafe_allow_html=True)
                for j,opt in enumerate(q["options"]): st.markdown(f"&nbsp;&nbsp;&nbsp;{'abcd'[j]}) {opt}")
                st.markdown(f"<span class='muted'>Correct: {q['correct']}</span></div>", unsafe_allow_html=True)

with tab_act:
    st.markdown("<h2 class='section-header'>Skills Activities</h2>", unsafe_allow_html=True)
    chosen_levels_act = st.multiselect("Bloom’s levels", LEVELS, default=["Apply","Understand"])
    auto_verbs_act = st.checkbox("Auto-select verbs (balanced)", value=False, key="auto_act")
    verb_bank_act = []
    if auto_verbs_act:
        for lvl in chosen_levels_act: verb_bank_act.extend(BLOOMS[lvl][:2])
    else:
        for lvl in chosen_levels_act:
            picks = st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=BLOOMS[lvl][:1], key=f"verbs_{lvl}_act")
            verb_bank_act.extend(picks)
    timing = st.selectbox("Activity timing (minutes)", list(range(10,65,5)), index=2)
    num_acts = st.slider("Number of activities", 1, 4, 2)
    if st.button("Generate Activities", type="primary"):
        if not topics_pool: st.info("Please upload a lesson file.")
        else:
            for i,t in enumerate(topics_pool[:num_acts],1):
                a = build_activity(chosen_levels_act[i % len(chosen_levels_act)], verb_bank_act, t, timing)
                st.markdown(f"<div class='card'><b>Activity {i}: {a['title']}</b><br>", unsafe_allow_html=True)
                st.markdown(f"**Brief:** {a['brief']}"); st.markdown(f"**Outcome:** {a['outcome']}"); st.markdown("**Steps:**")
                for s in a["steps"]: st.markdown(f"- {s}")
                st.markdown(f"**Resources:** {', '.join(a['resources'])}")
                st.markdown(f"<span class='muted'>Assessment: {a['assessment']} • Timing: {a['timing']} min</span></div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='adi-footer'>ADI | Teaching & Learning Tools</div>", unsafe_allow_html=True)

