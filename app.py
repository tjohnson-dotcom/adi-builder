
# ADI Builder — Full Streamlit App (Render-ready)
# - ADI colors & logo
# - Randomized MCQs (A/B/C/D) and Activities (week/lesson-aware)
# - Inline editing (st.data_editor)
# - Exports: .docx (paper, key, activities) and .gift (Moodle)
# - Safe session_state

from io import BytesIO
from typing import List, Dict, Tuple
from pathlib import Path
import random
import pandas as pd
import streamlit as st
from docx import Document
from pptx import Presentation
from pypdf import PdfReader

# ---------- Page & Theme ----------
APP_NAME = "ADI Builder — Lesson Activities & Questions"
STRAPLINE = "Professional, branded, editable and export-ready."
st.set_page_config(page_title=APP_NAME, page_icon="✅", layout="wide")

ADI_GREEN = "#245a34"
BG = "#f6f5f2"
st.markdown(f"""
<style>
  .stApp {{ background:{BG}; }}
  .adi-hero {{ background:{ADI_GREEN}; color:#fff; padding:18px 22px; border-radius:22px; }}
  .subtle {{ color:#e6efe9; opacity:.95 }}
  /* Buttons */
  .stButton > button {{ background:{ADI_GREEN}; color:#fff; border:0; border-radius:12px; padding:10px 16px; font-weight:600; }}
  .stButton > button:hover {{ filter:brightness(.95); }}
  /* Inputs border radius */
  div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
    border-radius:12px !important; border:1px solid #cfd8d2 !important;
  }}
  /* Tabs underline/active */
  [data-baseweb="tab-list"] {{ border-bottom:2px solid #dfe6e2; }}
  [data-baseweb="tab"][aria-selected="true"] {{ color:{ADI_GREEN}; font-weight:700; }}
  /* Alert cards recolor (no red) */
  div[data-testid="stAlert"] {{ border-left:5px solid {ADI_GREEN}; background:#eef5ef; color:#1f3b2a;
    border-radius:10px; padding:12px 14px; }}
  div[data-testid="stAlert"] svg {{ color:{ADI_GREEN}; }}
  /* Multi-select "chips" recolor (BaseWeb tags) */
  div[data-baseweb="tag"] {{ background:#e8efe9; color:#1f3b2a; border:1px solid #cfd8d2; }}
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).parent
LOGO = ROOT / "Logo.png"  # optional

# ---------- Data ----------
BLOOM = {
    "Low": ["define", "identify", "list", "recall", "describe", "label"],
    "Medium": ["apply", "demonstrate", "solve", "illustrate"],
    "High": ["evaluate", "synthesize", "design", "justify"],
}

def policy_for_week(week:int)->str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    return "High"

# ---------- File readers (optional source extraction) ----------
def read_pdf(file)->str:
    try:
        data = file.read()
        reader = PdfReader(BytesIO(data))
        texts = []
        for i, page in enumerate(reader.pages):
            if i >= 10: break
            t = (page.extract_text() or "").strip()
            if t: texts.append(t)
        return "\n".join(texts)
    except Exception:
        return ""

def read_docx(file)->str:
    try:
        from docx import Document
        d = Document(file)
        return "\n".join(p.text for p in d.paragraphs if p.text.strip())
    except Exception:
        return ""

def read_pptx(file)->str:
    try:
        prs = Presentation(file)
        chunks = []
        for i, slide in enumerate(prs.slides):
            if i >= 20: break
            buf = []
            for sh in slide.shapes:
                if hasattr(sh, "text"):
                    t = sh.text.strip()
                    if t: buf.append(t)
            if buf: chunks.append("\n".join(buf))
        return "\n\n".join(chunks)
    except Exception:
        return ""

def extract_text(upload)->Tuple[str,str]:
    if not upload: return "", ""
    name = upload.name.lower()
    if name.endswith(".pdf"): return read_pdf(upload), "pdf"
    if name.endswith(".docx"): return read_docx(upload), "docx"
    if name.endswith(".pptx"): return read_pptx(upload), "pptx"
    return "", ""

# ---------- Random content generators ----------
def seed_for(week:int, lesson:int)->int:
    # Stable seed per week/lesson but varies when "Regenerate" is pressed.
    return (week * 100) + lesson

def rand_words(n:int, rng:random.Random)->List[str]:
    corpus = ["system", "network", "policy", "process", "safety", "ethics", "design", "testing",
              "controls", "risk", "audience", "quality", "evidence", "impact", "role", "model",
              "function", "flow", "goal", "method", "data", "analysis", "outcome", "security",
              "module", "topic", "lesson", "practice", "standard", "criteria"]
    return [rng.choice(corpus) for _ in range(n)]

def generate_mcqs_random(topic:str, verbs:List[str], week:int, lesson:int, blocks:int, spice:int=0)->pd.DataFrame:
    rng = random.Random(seed_for(week, lesson) + spice)
    rows = []
    letters = ["A","B","C","D"]
    for i in range(blocks):
        v = verbs[i % max(1, len(verbs))] if verbs else rng.choice(sum(BLOOM.values(), []))
        subject = topic or " ".join(rand_words(2, rng))
        q = f"{v.capitalize()} {subject}: which option is most correct?"
        correct = " ".join(rand_words(3, rng))
        distractors = [" ".join(rand_words(3, rng)) for _ in range(3)]
        options = [correct] + distractors
        rng.shuffle(options)  # randomize option order
        answer_letter = letters[options.index(correct)]
        rows.append({
            "Question": q,
            "A": options[0],
            "B": options[1],
            "C": options[2],
            "D": options[3],
            "Answer": answer_letter
        })
    return pd.DataFrame(rows)

def generate_activities_random(topic:str, verbs:List[str], week:int, lesson:int, n:int, mins:int, spice:int=0)->List[str]:
    rng = random.Random(seed_for(week, lesson) + spice + 999)
    t = topic or "the lesson topic"
    frames = [
        "Think-Pair-Share explaining {}.",
        "Create an infographic comparing aspects of {}.",
        "Solve a case applying {} to a real scenario.",
        "Critique a sample answer about {} and suggest improvements.",
        "Design a short quiz to assess {}.",
        "Construct a concept map of {}."
    ]
    acts = []
    for i in range(n):
        base = rng.choice(frames).format(t)
        v = (verbs[i % max(1,len(verbs))] if verbs else rng.choice(BLOOM[policy_for_week(week)]))
        acts.append(f"{base} (Use verb: {v}; ~{mins} min)")
    return acts

# ---------- Exporters ----------
def docx_from_df(df:pd.DataFrame, title:str)->bytes:
    d = Document(); d.add_heading(title, 1)
    letters = ["A","B","C","D"]
    for i, row in df.iterrows():
        d.add_paragraph(f"{i+1}. {row['Question']}")
        for j, L in enumerate(letters):
            d.add_paragraph(f"   {L}) {row[L]}")
    bio = BytesIO(); d.save(bio); return bio.getvalue()

def docx_answer_key_from_df(df:pd.DataFrame)->bytes:
    d = Document(); d.add_heading("Answer Key", 1)
    for i, row in df.iterrows():
        d.add_paragraph(f"Q{i+1}: {row['Answer']}")
    bio = BytesIO(); d.save(bio); return bio.getvalue()

def gift_from_df(df:pd.DataFrame)->bytes:
    lines = []
    for _, row in df.iterrows():
        # GIFT format: correct starts with "="; distractors with "~"
        opts = [(row['A'], 'A'), (row['B'],'B'), (row['C'],'C'), (row['D'],'D')]
        parts = []
        for text, letter in opts:
            if row['Answer'] == letter:
                parts.append(f"= {text}")
            else:
                parts.append(f"~ {text}")
        body = f"::{row['Question'][:40]}:: {row['Question']} {{ {' '.join(parts)} }}"
        lines.append(body)
    return ("\n\n".join(lines)).encode("utf-8")

def docx_from_activities(acts:List[str])->bytes:
    d = Document(); d.add_heading("Activity Sheet", 1)
    for i, a in enumerate(acts, 1):
        d.add_paragraph(f"{i}. {a}")
    bio = BytesIO(); d.save(bio); return bio.getvalue()

# ---------- Session defaults ----------
if "week" not in st.session_state: st.session_state["week"] = 1
if "lesson" not in st.session_state: st.session_state["lesson"] = 1
if "bloom" not in st.session_state: st.session_state["bloom"] = policy_for_week(st.session_state["week"])
if "verbs_mcq" not in st.session_state: st.session_state["verbs_mcq"] = BLOOM[st.session_state["bloom"]][:4]
if "mcq_df" not in st.session_state: st.session_state["mcq_df"] = pd.DataFrame()
if "activities" not in st.session_state: st.session_state["activities"] = []
if "spice" not in st.session_state: st.session_state["spice"] = 0  # increments to regenerate randomness

# ---------- Header (logo + strapline) ----------
c_logo, c_title = st.columns([1,5], vertical_alignment="center")
with c_logo:
    if LOGO.exists():
        st.image(str(LOGO), use_container_width=True)
    else:
        st.markdown("**ADI**")
with c_title:
    st.markdown(f'<div class="adi-hero"><div style="font-size:28px;font-weight:800;">{APP_NAME}</div>'
                f'<div class="subtle" style="margin-top:4px;">{STRAPLINE}</div></div>',
                unsafe_allow_html=True)

# ---------- Sidebar controls ----------
with st.sidebar:
    st.markdown("**Upload PDF / DOCX / PPTX**")
    upload = st.file_uploader(" ", type=["pdf","docx","pptx"], label_visibility="collapsed")
    st.caption("Limit 200MB per file • PDF, DOCX, PPTX")
    week = st.selectbox("Week", list(range(1,15)), index=st.session_state["week"]-1)
    lesson = st.selectbox("Lesson", [1,2,3,4,5], index=st.session_state["lesson"]-1)
    if week != st.session_state["week"] or lesson != st.session_state["lesson"]:
        st.session_state["week"] = week
        st.session_state["lesson"] = lesson
        st.session_state["bloom"] = policy_for_week(week)
        st.session_state["verbs_mcq"] = BLOOM[st.session_state["bloom"]][:4]
        st.session_state["spice"] = 0
        st.session_state["mcq_df"] = pd.DataFrame()
        st.session_state["activities"] = []
        st.rerun()
    st.caption(f"Policy: {st.session_state['bloom']}")

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["🧠 Knowledge MCQs", "🛠️ Skills Activities"])

extracted, kind = extract_text(upload)
topic_hint = (extracted.split("\n")[0][:120] if extracted else "")

# ---------- Tab 1: MCQs ----------
with tab1:
    st.subheader("Knowledge MCQs")
    col1, col2 = st.columns([2,1])
    with col1:
        levels = st.multiselect("Bloom’s levels", ["Understand","Apply","Analyse","Evaluate","Create"],
                                default=["Understand","Apply","Analyse"])
    with col2:
        auto = st.checkbox("Auto-select verbs (balanced)", value=False)
    verbs = []
    if auto:
        for tier in ["Low","Medium","High"]:
            verbs.extend(BLOOM[tier][:2])
    else:
        with st.expander("Verbs per level", expanded=True):
            # map chosen levels to tiers
            chosen_tiers = []
            for lvl in levels:
                if lvl in {"Understand"}: chosen_tiers.append("Low")
                elif lvl in {"Apply","Analyse"}: chosen_tiers.append("Medium")
                else: chosen_tiers.append("High")
            pool = []
            for tier in chosen_tiers or ["Low","Medium"]:
                pool.extend(BLOOM[tier])
            verbs = st.multiselect("Choose options", sorted(set(pool)),
                                   default=st.session_state["verbs_mcq"], key="verbs_mcq")
    topic = st.text_input("Topic (optional)", value=topic_hint)
    quick = st.radio("Quick pick", [5,10,20,30], index=1, horizontal=True)
    blocks = st.number_input("Or custom number of MCQ blocks", 1, 100, int(quick), 1, key="mcq_blocks")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("⚡ Generate MCQ Blocks", type="primary"):
            st.session_state["mcq_df"] = generate_mcqs_random(topic, verbs, st.session_state["week"],
                                                              st.session_state["lesson"], int(blocks),
                                                              st.session_state["spice"])
    with c2:
        if st.button("🎲 Regenerate (new random set)"):
            st.session_state["spice"] += 1
            st.session_state["mcq_df"] = generate_mcqs_random(topic, verbs, st.session_state["week"],
                                                              st.session_state["lesson"], int(blocks),
                                                              st.session_state["spice"])
    with c3:
        if st.button("🧹 Clear"):
            st.session_state["mcq_df"] = pd.DataFrame()

    df = st.session_state["mcq_df"]
    if not df.empty:
        st.success(f"Generated {len(df)} questions.")
        st.caption("Edit directly below, then use the download buttons.")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="mcq_editor")
        st.session_state["mcq_df"] = edited
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("⬇️ MCQ Paper (.docx)",
                               data=docx_from_df(edited, "MCQ Paper"),
                               file_name="mcq_paper.docx")
        with d2:
            st.download_button("⬇️ Answer Key (.docx)",
                               data=docx_answer_key_from_df(edited),
                               file_name="answer_key.docx")
        with d3:
            st.download_button("⬇️ Moodle GIFT (.gift)",
                               data=gift_from_df(edited),
                               file_name="mcq_questions.gift")
    else:
        st.info("Upload a file (optional), choose verbs, set blocks, then **Generate MCQ Blocks**.")

# ---------- Tab 2: Activities ----------
with tab2:
    st.subheader("Skills Activities")
    a1, a2 = st.columns(2)
    with a1:
        n_acts = st.number_input("Activities", 1, 10, 3, 1)
    with a2:
        mins = st.number_input("Duration per activity (mins)", 10, 120, 45, 5)
    verbs_for_acts = st.multiselect("Preferred action verbs", BLOOM["Medium"] + BLOOM["High"],
                                    default=["apply","demonstrate","evaluate","design"],
                                    key="verbs_for_acts")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧩 Generate Activities", type="primary"):
            st.session_state["activities"] = generate_activities_random(
                topic_hint or topic, verbs_for_acts, st.session_state["week"], st.session_state["lesson"],
                int(n_acts), int(mins), st.session_state["spice"]
            )
    with c2:
        if st.button("🎲 Regenerate Activities"):
            st.session_state["spice"] += 7
            st.session_state["activities"] = generate_activities_random(
                topic_hint or topic, verbs_for_acts, st.session_state["week"], st.session_state["lesson"],
                int(n_acts), int(mins), st.session_state["spice"]
            )
    acts = st.session_state["activities"]
    if acts:
        st.caption("Edit any activity lines before downloading.")
        # simple editable list using data_editor
        acts_df = pd.DataFrame({"Activity": acts})
        edited_acts = st.data_editor(acts_df, num_rows="dynamic", use_container_width=True, key="acts_editor")
        st.session_state["activities"] = list(edited_acts["Activity"].fillna(""))
        st.download_button("⬇️ Activity Sheet (.docx)",
                           data=docx_from_activities(st.session_state["activities"]),
                           file_name="activity_sheet.docx")
    else:
        st.info("Pick count/duration and verbs, then **Generate Activities**.")
