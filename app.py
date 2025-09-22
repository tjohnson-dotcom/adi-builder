import streamlit as st
import random, re
from io import BytesIO

# Optional dependencies (app still runs if some are missing)
try:
    from docx import Document            # for DOCX export and reading .docx
except Exception:
    Document = None
try:
    from pptx import Presentation        # read .pptx
except Exception:
    Presentation = None
try:
    import fitz                          # PyMuPDF: read .pdf
except Exception:
    fitz = None

# -------------------------------
# Page & Styling (ADI palette)
# -------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="🧩", layout="wide")

st.markdown("""
<style>
  :root{
    --adi:#15563d;          /* deep green */
    --adi-ink:#1d2724;      /* body text */
    --adi-soft:#f6f8f7;     /* soft bg */
    --adi-accent:#b79e82;   /* warm accent */
  }
  .block-container {max-width: 1020px; padding-top: 1.2rem; padding-bottom: 2rem;}
  html, body, .stApp {background: var(--adi-soft); color: var(--adi-ink);}

  h1,h2,h3{color:var(--adi); font-weight:800; letter-spacing:.2px;}
  h1{font-size:2.05rem} h2{font-size:1.45rem} h3{font-size:1.15rem}

  .hero{
    margin:-.6rem 0 1rem 0; padding:18px 18px; border-radius:14px;
    background: linear-gradient(90deg, var(--adi), #0e3d2a 60%, var(--adi-accent));
    color:#fff; box-shadow: 0 10px 24px rgba(0,0,0,.09);
  }
  .hero b{font-size:1.2rem}
  .subtle{color:#6a7471}

  .toolbar{
    display:flex; gap:.75rem; flex-wrap:wrap; align-items:end;
    background:#ffffff; border:1px solid rgba(0,0,0,.08); padding:.75rem .8rem; border-radius:14px;
    box-shadow: 0 6px 16px rgba(0,0,0,.05);
  }
  .toolbar .cell{min-width:210px;}
  .divider{height:1px; background:rgba(0,0,0,.08); margin:12px 0 16px;}

  .card{
    border:1px solid rgba(0,0,0,.08); border-radius:14px; padding:14px 16px; background:#fff;
    box-shadow:0 6px 18px rgba(0,0,0,.06); margin-bottom:12px;
  }

  .stTabs [data-baseweb="tab-list"]{gap:.25rem;}
  .stTabs [data-baseweb="tab"]{
    background:#eaf0ec; color:#0f2f24; border-radius:12px 12px 0 0; padding:.55rem .9rem; font-weight:800;
  }
  .stTabs [aria-selected="true"]{background:#fff; color:var(--adi); border-bottom:3px solid var(--adi-accent);}

  .stButton>button{
    background:var(--adi); color:#fff; font-weight:800; border:0; border-radius:12px; padding:.65rem 1rem;
    box-shadow:0 8px 18px rgba(21,86,61,.20);
  }
  .stButton>button:hover{filter:brightness(.96); transform: translateY(-1px);}
  .stButton>button:active{transform: translateY(0);}

  .stSelectbox > div > div,
  .stMultiSelect > div > div,
  .stTextInput > div > div > input,
  .stNumberInput input,
  .stTextArea textarea{
    border-radius:12px !important; border-color: rgba(0,0,0,.18) !important;
  }
  .stSlider [data-baseweb="slider"]>div>div{background:var(--adi);}
  .stSlider [role="slider"]{ box-shadow:0 0 0 4px rgba(21,86,61,.15) !important; }

  .hint{display:inline-block; background:#eef2ef; color:#2c3f37; padding:.28rem .6rem; border-radius:999px; font-size:.88rem;}
  .muted{color:#64706d}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero">
  <b>ADI Builder</b><br>
  Create crisp <u>Knowledge MCQs</u> or simple, practical <u>Skills Activities</u> from a lesson file.
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
    # normalise spaces and keep mid-length lines with letters
    lines = [re.sub(r"\s+", " ", L).strip() for L in raw_text.splitlines()]
    lines = [L for L in lines if 6 <= len(L) <= 140 and re.search(r"[A-Za-z]", L)]
    # de-duplicate preserving order
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
    # build distractors from other topics; fallback to safe generics
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
    ("Guided Practice", "Individually complete a short, authentic task linked to the lesson.",
     ["Read the brief and success criteria.",
      "Complete the task step-by-step.",
      "Self-check against the criteria.",
      "Submit for quick feedback."]),
    ("Pair & Share", "Work in pairs to apply knowledge and explain decisions.",
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
      "Record any deviations and fix them.",
      "Reflect: one improvement for next time."]),
    ("Reflect & Improve", "Evaluate your output and plan a small improvement.",
     ["Compare against the success criteria.",
      "Identify one strength and one area to improve.",
      "Write a short improvement plan.",
      "Share your plan with the group."]),
]

def build_activity(level: str, verbs: list[str], topic: str, minutes: int) -> dict:
    name, brief, steps = random.choice(ACTIVITY_TEMPLATES)
    v = random.choice(verbs) if verbs else "apply"
    outcome = {
        "Remember":   f"Identify and {v} key facts related to {topic}.",
        "Understand": f"{v.capitalize()} main ideas and explain relevance for {topic}.",
        "Apply":      f"{v.capitalize()} the concept in a practical task about {topic}.",
        "Analyse":    f"{v.capitalize()} components and relationships within {topic}.",
        "Evaluate":   f"{v.capitalize()} options and justify decisions for {topic}.",
        "Create":     f"{v.capitalize()} a clear output or solution based on {topic}."
    }.get(level, f"{v.capitalize()} core ideas about {topic}.")
    return {
        "title": f"{name} — {level}",
        "brief": brief,
        "outcome": outcome,
        "steps": steps,
        "resources": ["Slides/eBook extract", "Worksheet/template", "Pens"],
        "assessment": random.choice(["Tutor walk-by check", "Peer two-stars-and-a-wish", "Self checklist"]),
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
# Toolbar (sleek, minimal)
# -------------------------------
st.markdown(
    "<div class='toolbar'>"
    "<div class='cell'>", unsafe_allow_html=True
)
uploaded = st.file_uploader("Upload PDF / DOCX / PPTX", type=["pdf","docx","pptx"], help="Drag & drop your lesson or eBook file here.")
st.markdown("</div><div class='cell'>", unsafe_allow_html=True)
week = st.selectbox("Week", list(range(1,15)), index=0)
st.markdown("</div><div class='cell'>", unsafe_allow_html=True)
lesson = st.selectbox("Lesson", list(range(1,5)), index=0)
st.markdown("</div></div>", unsafe_allow_html=True)

raw_text = extract_text(uploaded) if uploaded else ""
topics_pool = carve_topics(raw_text, want=40)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# -------------------------------
# Tabs: MCQs | Activities
# -------------------------------
tab_mcq, tab_act = st.tabs(["🧠 Knowledge MCQs", "🛠 Skills Activities"])

# ===== MCQs =====
with tab_mcq:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Knowledge MCQs")
    st.caption("Choose level(s) and verbs; we’ll rotate verbs so stems feel varied and stay crisp.")

    # Level multiselect + verbs checkboxes (visible, but tidy)
    colL, colQ = st.columns([1.2, 1])
    with colL:
        chosen_levels = st.multiselect("Bloom’s levels", LEVELS, default=DEFAULT_MIX)
        if not chosen_levels:
            chosen_levels = DEFAULT_MIX
    with colQ:
        total_mcqs = st.slider("Number of questions", 5, 10, 6)

    verb_bank = []
    # show compact verb pickers for the chosen levels
    for lvl in chosen_levels:
        default = BLOOMS[lvl][:2]  # two per level preselected
        picks = st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=default, key=f"verbs_{lvl}_mcq")
        verb_bank.extend(picks)
    if not verb_bank:
        verb_bank = sum((BLOOMS[l] for l in chosen_levels), [])

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Generate MCQs", type="primary"):
        if not topics_pool:
            st.warning("Please upload a lesson file (PDF/DOCX/PPTX) with readable text.")
        else:
            random.shuffle(topics_pool)
            topics = topics_pool[:total_mcqs]
            mcqs = []
            for i, t in enumerate(topics):
                verb = verb_bank[i % len(verb_bank)]
                mcqs.append(build_mcq(t, verb, topics_pool))

            # Render
            letters = "abcd"
            for i, q in enumerate(mcqs, 1):
                st.markdown(f"<div class='card'><b>Q{i}.</b> {q['stem']}<br>", unsafe_allow_html=True)
                for j, opt in enumerate(q["options"]):
                    st.markdown(f"&nbsp;&nbsp;&nbsp;{letters[j]}) {opt}")
                st.markdown(f"<span class='muted'>Correct: {q['correct']}</span></div>", unsafe_allow_html=True)

            # Download
            title = f"ADI MCQs — Week {week}, Lesson {lesson}"
            docx = export_docx_mcqs(mcqs, title)
            if docx:
                st.download_button(
                    "⬇ Download MCQs (DOCX)",
                    data=docx,
                    file_name=f"ADI_MCQs_W{week}_L{lesson}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# ===== Activities =====
with tab_act:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Skills Activities")
    st.caption("Pick timing and how many activities to build. Choose levels & verbs to shape the outcome line.")

    cA, cB, cC = st.columns([1,1,1.2])
    with cA:
        timing = st.selectbox("Activity timing (minutes)", list(range(10, 65, 5)), index=2)
    with cB:
        num_acts = st.slider("Number of activities", 1, 4, 2)
    with cC:
        chosen_levels_act = st.multiselect("Bloom’s levels", LEVELS, default=["Apply", "Understand"])
        if not chosen_levels_act:
            chosen_levels_act = ["Apply", "Understand"]

    # verbs per selected level
    verb_bank_act = []
    for lvl in chosen_levels_act:
        default = BLOOMS[lvl][:1]
        picks = st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=default, key=f"verbs_{lvl}_act")
        verb_bank_act.extend(picks)
    if not verb_bank_act:
        verb_bank_act = sum((BLOOMS[l] for l in chosen_levels_act), [])

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Generate Activities", type="primary", key="gen_act"):
        if not topics_pool:
            st.warning("Please upload a lesson file (PDF/DOCX/PPTX) with readable text.")
        else:
            random.shuffle(topics_pool)
            topics = topics_pool[:num_acts]
            acts = []
            for i in range(num_acts):
                lvl = chosen_levels_act[i % len(chosen_levels_act)]
                acts.append(build_activity(lvl, verb_bank_act, topics[i], timing))

            # Render
            for i, a in enumerate(acts, 1):
                st.markdown(f"<div class='card'><b>Activity {i}: {a['title']}</b><br>", unsafe_allow_html=True)
                st.markdown(f"**Brief:** {a['brief']}")
                st.markdown(f"**Outcome:** {a['outcome']}")
                st.markdown("**Steps:**")
                for step in a["steps"]:
                    st.markdown(f"- {step}")
                st.markdown(f"**Resources:** {', '.join(a['resources'])}")
                st.markdown(f"<span class='muted'>Assessment: {a['assessment']}  •  Timing: {a['timing']} min</span></div>", unsafe_allow_html=True)

            # Download
            title = f"ADI Activities — Week {week}, Lesson {lesson}"
            docx = export_docx_activities(acts, title)
            if docx:
                st.download_button(
                    "⬇ Download Activities (DOCX)",
                    data=docx,
                    file_name=f"ADI_Activities_W{week}_L{lesson}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
