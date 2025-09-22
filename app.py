import streamlit as st
import random
import re
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
    import fitz
except Exception:
    fitz = None

# -------------------------------
#   CUSTOM CSS (ADI colors, crisp)
# -------------------------------
CUSTOM_CSS = """
<style>
    .block-container {padding-top:2rem; padding-bottom:2rem; max-width:1040px;}
    h1, h2, h3 {color:#004d40; font-weight:800;}
    .stTabs [data-baseweb="tab"] p {font-weight:700;}
    .stButton>button {
        background:#004d40; color:white; font-weight:700;
        border-radius:10px; padding:.65rem 1.2rem; border:0;
    }
    .stButton>button:hover {background:#00695c;}
    .card {
        border:1px solid #e0e0e0; border-radius:12px; padding:1rem;
        background:#fafafa; box-shadow:0 2px 6px rgba(0,0,0,.05); margin-bottom:1rem;
    }
    .muted {color:#6f7a7a}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------
#   BLOOM LEVELS & VERBS
# -------------------------------
BLOOMS = {
    "Remember":   ["define", "list", "recall", "state", "identify"],
    "Understand": ["explain", "summarize", "describe", "classify", "discuss"],
    "Apply":      ["apply", "demonstrate", "use", "illustrate", "practice"],
    "Analyse":    ["analyze", "compare", "differentiate", "categorize", "examine"],
    "Evaluate":   ["evaluate", "justify", "critique", "assess", "defend"],
    "Create":     ["design", "compose", "construct", "propose", "develop"]
}
LEVEL_ORDER = list(BLOOMS.keys())

# -------------------------------
#   HELPERS
# -------------------------------
def carve_topics(raw_text: str, want: int = 10) -> list[str]:
    """Very simple text-to-topics filter."""
    lines = [re.sub(r"\s+", " ", L).strip() for L in raw_text.splitlines()]
    lines = [L for L in lines if 6 <= len(L) <= 140]
    if not lines:
        return [f"Topic {i}" for i in range(1, want+1)]
    random.shuffle(lines)
    return lines[:want]

def build_mcq(topic: str, verb: str) -> dict:
    stem = f"In one sentence, {verb} the key idea: **{topic}**."
    correct = f"A concise {verb} of {topic}"
    distractors = [
        "Unrelated example", "Motivational quote", "Unused resource"
    ]
    options = [correct] + random.sample(distractors, k=3)
    random.shuffle(options)
    letters = "abcd"
    return {
        "stem": stem,
        "options": options,
        "correct": letters[options.index(correct)]
    }

def export_docx_mcqs(mcqs, title):
    if not Document: return None
    doc = Document()
    doc.add_heading(title, 1)
    letters = "abcd"
    for i, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{i}. {q['stem']}")
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{letters[j]}) {opt}", style="List Bullet")
        doc.add_paragraph(f"Correct: {q['correct']}")
        doc.add_paragraph("")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# -------------------------------
#   ACTIVITIES
# -------------------------------
ACTIVITY_TEMPLATES = [
    ("Guided Practice", "Individually complete a short task.",
     ["Read the brief.", "Complete step-by-step.", "Check against criteria.", "Submit for feedback."]),
    ("Pair & Share", "Work in pairs to apply knowledge.",
     ["Agree roles.", "Discuss prompt.", "Swap roles.", "Share with group."]),
    ("Mini Case", "Analyse a short scenario.",
     ["Read case facts.", "Identify risks.", "Recommend actions.", "Prepare a summary."]),
    ("Procedure Drill", "Follow a procedure safely.",
     ["Review SOP.", "Perform steps.", "Record deviations.", "Reflect improvements."]),
    ("Reflect & Improve", "Evaluate your work.",
     ["Compare with criteria.", "Identify strengths/weaknesses.", "Plan improvements.", "Share insight."])
]

def build_activity(level, verbs, topic, timing):
    name, brief, steps = random.choice(ACTIVITY_TEMPLATES)
    verb = random.choice(verbs) if verbs else "apply"
    outcome = f"{verb.capitalize()} knowledge of {topic} at {level} level."
    return {
        "title": f"{name} — {level}",
        "brief": brief,
        "outcome": outcome,
        "steps": steps,
        "resources": ["Slides", "Worksheet", "Pen/marker"],
        "assessment": random.choice(["Tutor check", "Peer review", "Self checklist"]),
        "timing": timing
    }

def export_docx_activities(acts, title):
    if not Document: return None
    doc = Document()
    doc.add_heading(title, 1)
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
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# -------------------------------
#   PAGE
# -------------------------------
st.title("📘 ADI Builder")
st.caption("Generate **Knowledge MCQs** and **Skills Activities** quickly with ADI styling.")

tab_mcq, tab_skills = st.tabs(["🧠 Knowledge MCQs", "🛠 Skills Activities"])

# --- MCQs ---
with tab_mcq:
    st.subheader("Knowledge MCQs")
    mix_levels = st.checkbox("Mix levels", value=True)
    levels = LEVEL_ORDER if mix_levels else [st.selectbox("Level", LEVEL_ORDER, index=2)]
    verbs = []
    for lvl in levels:
        verbs.extend(st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=BLOOMS[lvl][:1]))
    num_qs = st.slider("Number of MCQs", 5, 10, 6)

    if st.button("Generate MCQs"):
        topics = carve_topics("Sample lesson text", want=num_qs)
        if not verbs: verbs = sum(BLOOMS.values(), [])
        mcqs = [build_mcq(topics[i], random.choice(verbs)) for i in range(num_qs)]
        for i, q in enumerate(mcqs, 1):
            st.markdown(f"**Q{i}. {q['stem']}**")
            for opt in q["options"]:
                st.write(f"- {opt}")
            st.write(f"✅ Correct: {q['correct']}")
            st.markdown("---")
        docx = export_docx_mcqs(mcqs, "ADI MCQs")
        if docx: st.download_button("⬇ Download DOCX", data=docx, file_name="ADI_MCQs.docx")

# --- Activities ---
with tab_skills:
    st.subheader("Skills Activities")
    mix_levels = st.checkbox("Mix levels ", value=True, key="acts_mix")
    levels = LEVEL_ORDER if mix_levels else [st.selectbox("Level", LEVEL_ORDER, index=2, key="acts_lvl")]
    verbs = []
    for lvl in levels:
        verbs.extend(st.multiselect(f"Verbs for {lvl}", BLOOMS[lvl], default=BLOOMS[lvl][:1], key=f"acts_{lvl}"))
    timing = st.selectbox("Activity timing (minutes)", list(range(10, 65, 5)), index=2)
    num_acts = st.slider("Number of activities", 1, 4, 2)

    if st.button("Generate Activities"):
        topics = carve_topics("Sample lesson text", want=num_acts)
        if not verbs: verbs = sum(BLOOMS.values(), [])
        acts = [build_activity(levels[i % len(levels)], verbs, topics[i], timing) for i in range(num_acts)]
        for i, a in enumerate(acts, 1):
            st.markdown(f"""
            <div class="card">
            <h3>Activity {i}: {a['title']}</h3>
            <p><b>Brief:</b> {a['brief']}</p>
            <p><b>Outcome:</b> {a['outcome']}</p>
            <p><b>Steps:</b></p>
            <ul>{"".join(f"<li>{s}</li>" for s in a['steps'])}</ul>
            <p><b>Resources:</b> {", ".join(a['resources'])}</p>
            <p><b>Assessment:</b> {a['assessment']} | <b>Timing:</b> {a['timing']} min</p>
            </div>
            """, unsafe_allow_html=True)
        docx = export_docx_activities(acts, "ADI Skills Activities")
        if docx: st.download_button("⬇ Download DOCX", data=docx, file_name="ADI_Activities.docx")
