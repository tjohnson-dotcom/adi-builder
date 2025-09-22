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
# Page & Styling (ADI colours)
# -------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="🧩", layout="wide")

st.markdown("""
<style>
  :root{
    --adi-green:#15563d;      /* deep green */
    --adi-accent:#b79e82;     /* light brown */
    --adi-bg:#f6f4f1;         /* soft beige bg */
    --adi-text:#1d2724;
  }
  html, body, .stApp {background: var(--adi-bg); color: var(--adi-text);}
  .block-container {max-width: 1020px; padding-top: 1.2rem; padding-bottom: 3.2rem;}

  h1,h2,h3{color:var(--adi-green); font-weight:800; letter-spacing:.2px;}
  .hero{
    margin:-.6rem 0 1rem 0; padding:18px 18px; border-radius:14px;
    background: linear-gradient(90deg, var(--adi-green), #0e3d2a 60%, var(--adi-accent));
    color:#fff; box-shadow: 0 10px 24px rgba(0,0,0,.08);
  }

  .toolbar{
    display:flex; gap:.75rem; flex-wrap:wrap; align-items:end;
    background:#fff; border:1px solid rgba(0,0,0,.08); padding:.75rem .8rem; border-radius:14px;
    box-shadow: 0 6px 16px rgba(0,0,0,.05);
    margin-bottom: .6rem;
  }

  .card{
    border:1px solid rgba(0,0,0,.08); border-radius:14px; padding:14px 16px; background:#fff;
    box-shadow:0 6px 18px rgba(0,0,0,.05); margin-bottom:12px;
  }

  .stTabs [data-baseweb="tab"]{
    background:#e8e4df; color:#2e2e2e; border-radius:12px 12px 0 0; padding:.55rem .9rem; font-weight:800;
  }
  .stTabs [aria-selected="true"]{
    background:#fff; color:var(--adi-green); border-bottom:3px solid var(--adi-accent);
  }

  .stButton>button{
    background:var(--adi-green); color:#fff; font-weight:800; border:0; border-radius:12px; padding:.65rem 1rem;
    box-shadow:0 8px 18px rgba(21,86,61,.20);
  }
  .stButton>button:hover{filter:brightness(.96); transform: translateY(-1px);}
  .stButton>button:active{transform: translateY(0);}

  .muted{color:#6a7370}

  /* Footer bar */
  .adi-footer{
    position: fixed; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, var(--adi-accent), var(--adi-green));
    color:#fff; padding:.55rem .9rem; text-align:center; font-weight:700;
    box-shadow: 0 -6px 20px rgba(0,0,0,.10);
    z-index:999;
  }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero">
  <b>ADI Builder</b><br>
  Create crisp <u>Knowledge MCQs</u> or practical <u>Skills Activities</u> directly from lesson files.
</div>""", unsafe_allow_html=True)

# -------------------------------
# Bloom levels & verbs
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
FORBIDDEN = {"all of the above","none of the above","true","false"}

# -------------------------------
# File parsing
# -------------------------------
def extract_text_from_pdf(data: bytes) -> str:
    if not fitz: return ""
    out = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for p in doc:
            out.append(p.get_text("text"))
    return "\n".join(out)

def extract_text_from_docx(data: bytes) -> str:
    if not Document: return ""
    bio = BytesIO(data)
    doc = Document(bio)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_pptx(data: bytes) -> str:
    if not Presentation: return ""
    bio = BytesIO(data)
    prs = Presentation(bio)
    lines = []
    for slide in prs.slides:
        for shp in slide.shapes:
            if hasattr(shp, "text") and shp.text:
                lines.append(shp.text)
    return "\n".join(lines)

def extract_text(uploaded) -> str:
    if not uploaded: return ""
    data = uploaded.read()
    name = uploaded.name.lower()
    if   name.endswith(".pdf"):  return extract_text_from_pdf(data)
    elif name.endswith(".docx"): return extract_text_from_docx(data)
    elif name.endswith(".pptx"): return extract_text_from_pptx(data)
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
        k = L.lower()
        if k not in seen:
            seen.add(k); out.append(L)
    random.shuffle(out)
    return out[:want]

# -------------------------------
# MCQ builder/export
# -------------------------------
def clean_option(s: str) -> str:
    s2 = s
    for bad in FORBIDDEN:
        s2 = re.sub(rf"\b{re.escape(bad)}\b", "", s2, flags=re.I)
    s2 = re.sub(r"\s{2,}", " ", s2).strip()
    return s2 or "—"

def build_mcq(topic: str, verb: str, distractor_pool: list[str]) -> dict:
    stem = f"{verb.capitalize()} the key idea: **{topic}**."
    correct = clean_option(f"A concise {verb} of {topic}")
    d = []
    for t in distractor_pool:
        if t != topic and len(d) < 3:
            d.append(clean_option(f"{verb.capitalize()} of {t}"))
    while len(d) < 3:
        d.append("A plausible but incorrect statement")
    options = [correct] + d
    random.shuffle(options)
    letters = "abcd"
    return {"stem": stem, "options": options, "correct": letters[options.index(correct)]}

def export_docx_mcqs(mcqs, title):
    if not Document: return None
    doc = Document(); doc.add_heading(title, 1)
    letters = "abcd"
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{letters[j]}) {opt}", style="List Bullet")
        doc.add_paragraph(f"Correct: {q['correct']}"); doc.add_paragraph("")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# -------------------------------
# Activity builder/export
# -------------------------------
ACTIVITY_TEMPLATES = [
    ("Guided Practice", "Individually complete a short, authentic task.",
     ["Read the brief and success criteria.",
      "Complete the task step-by-step.",
      "Self-check against the criteria.",
      "Submit for quick feedback."]),
    ("Pair & Share", "Work in pairs to apply knowledge.",
     ["Agree roles (Speaker / Notetaker).",
      "Discuss the prompt and capture key points.",
      "Swap roles and refine the output.",
      "Share one insight with another pair."]),
    ("Mini Case", "Analyse a short scenario and recommend actions.",
     ["Read the case and highlight key facts.",
      "Identify risks or constraints.",
      "Recommend two actions and justify them.",
      "Prepare a 60-second summary."]),
    ("Procedure Drill", "Follow a procedure safely and accurately.",
     ["Review the SOP steps together.",
      "Perform steps in order while a peer observes.",
      "Record deviations and fix them.",
      "Reflect on one improvement."]),
    ("Reflect & Improve", "Evaluate your output and plan improvements.",
     ["Compare against the success criteria.",
      "Identify one strength and one area to improve.",
      "Write a short improvement plan.",
      "Share your plan with the group."]),
]

def build_activity(level: str, verbs: list[str], topic: str, minutes: int) -> dict:
    name, brief, steps = random.choice(ACTIVITY_TEMPLATES)
    v = random.choice(verbs) if verbs else "apply"
    outcome = f"{v.capitalize()} learning about {topic} at {level} level."
    return {
        "title": f"{name} — {level}",
        "brief": brief,
        "outcome": outcome,
        "steps": steps,
        "resources": ["Slides/eBook extract", "Worksheet/template", "Pens"],
        "assessment": random.choice(["Tutor check", "Peer feedback", "Self checklist"]),
        "timing": minutes
    }

def export_docx_activities(acts, title):
    if not Document: return None
    doc = Document(); doc.add_heading(title, 1)
    for i, a in enumerate(acts, 1):
        doc.add_heading(f"Activity {i}: {a['title']}", 2)
        doc.add_paragraph(a["brief"])
        doc.add_paragraph(f"Outcome: {a['outcome']}")
        doc.add_paragraph("Steps:")
        for s in a["steps"]:
            doc.add_paragraph(s, style="List Number")
        doc.add_paragraph("Resources: " + ", ".join(a["resources"]))
        doc.add_paragraph(f"Assessment: {a['assessment']}")
        doc.add_paragraph(f"Timing: {a['timing']} minutes")
        doc.add_paragraph("")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

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

# ===== MCQs =====
with tab_mcq:
    st.subheader("Knowledge MCQs")
    chosen_levels = st.multiselect("Bloom’s levels", LEVELS, default=DEFAULT_MIX)
    if not chosen_levels: chosen_levels = DEFAULT_MIX
    total_mcqs = st.slider("Number of questions", 5, 10, 6)

    auto_verbs_mcq = st.checkbox("Automatically choose suitable verbs for me (recommended)", value=True)

    verb_bank = []
    if auto_verbs_mcq:
        # Balanced selection: first 2 verbs from each chosen level
        for lvl in chosen_levels:
            verb_bank.extend(BLOOMS[lvl][:2])
    else:
        # Manual per-level selection
        for lvl in chosen_levels:
            default = BLOOMS[lvl][:2]
            picks = st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=default, key=f"verbs_{lvl}_mcq")
            verb_bank.extend(picks)

    if not verb_bank:
        verb_bank = sum((BLOOMS[l] for l in chosen_levels), [])

    if st.button("Generate MCQs", type="primary"):
        if not topics_pool:
            st.warning("Please upload a lesson file.")
        else:
            random.shuffle(topics_pool)
            topics = topics_pool[:total_mcqs]
            mcqs = [build_mcq(t, verb_bank[i % len(verb_bank)], topics_pool) for i, t in enumerate(topics)]
            for i, q in enumerate(mcqs, 1):
                st.markdown(f"<div class='card'><b>Q{i}.</b> {q['stem']}<br>", unsafe_allow_html=True)
                for j, opt in enumerate(q["options"]): st.markdown(f"&nbsp;&nbsp;&nbsp;{chr(97+j)}) {opt}")
                st.markdown(f"<span class='muted'>Correct: {q['correct']}</span></div>", unsafe_allow_html=True)
            docx = export_docx_mcqs(mcqs, f"ADI MCQs — Week {week}, Lesson {lesson}")
            if docx:
                st.download_button("⬇ Download MCQs (DOCX)", data=docx,
                    file_name=f"ADI_MCQs_W{week}_L{lesson}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ===== Activities =====
with tab_act:
    st.subheader("Skills Activities")
    chosen_levels_act = st.multiselect("Bloom’s levels", LEVELS, default=["Apply", "Understand"])
    if not chosen_levels_act: chosen_levels_act = ["Apply", "Understand"]
    timing = st.selectbox("Activity timing (minutes)", list(range(10, 65, 5)), index=2)
    num_acts = st.slider("Number of activities", 1, 4, 2)

    auto_verbs_act = st.checkbox("Automatically choose suitable verbs for me (recommended)", value=True, key="auto_act")

    verb_bank_act = []
    if auto_verbs_act:
        for lvl in chosen_levels_act:
            verb_bank_act.extend(BLOOMS[lvl][:2])
    else:
        for lvl in chosen_levels_act:
            default = BLOOMS[lvl][:1]
            picks = st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=default, key=f"verbs_{lvl}_act")
            verb_bank_act.extend(picks)

    if not verb_bank_act:
        verb_bank_act = sum((BLOOMS[l] for l in chosen_levels_act), [])

    if st.button("Generate Activities", type="primary"):
        if not topics_pool:
            st.warning("Please upload a lesson file.")
        else:
            random.shuffle(topics_pool)
            topics = topics_pool[:num_acts]
            acts = [build_activity(chosen_levels_act[i % len(chosen_levels_act)], verb_bank_act, topics[i], timing) for i in range(num_acts)]
            for i, a in enumerate(acts, 1):
                st.markdown(f"<div class='card'><b>Activity {i}: {a['title']}</b><br>", unsafe_allow_html=True)
                st.markdown(f"**Brief:** {a['brief']}")
                st.markdown(f"**Outcome:** {a['outcome']}")
                st.markdown("**Steps:**")
                for s in a["steps"]: st.markdown(f"- {s}")
                st.markdown(f"**Resources:** {', '.join(a['resources'])}")
                st.markdown(f"<span class='muted'>Assessment: {a['assessment']} • Timing: {a['timing']} min</span></div>", unsafe_allow_html=True)
            docx = export_docx_activities(acts, f"ADI Activities — Week {week}, Lesson {lesson}")
            if docx:
                st.download_button("⬇ Download Activities (DOCX)", data=docx,
                    file_name=f"ADI_Activities_W{week}_L{lesson}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# -------------------------------
# Footer
# -------------------------------
st.markdown(
    "<div class='adi-footer'>ADI | Teaching & Learning Tools</div>",
    unsafe_allow_html=True
)
