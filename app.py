
# ADI Builder — Full Streamlit App v2 (with logo compatibility fix)
# Features:
# - ADI theme and CSS (no red alerts, green accents)
# - Logo + strapline header (compatible with older/newer Streamlit: use_container_width fallback)
# - Highlighted uploader with "Uploaded ✓ filename (size)"
# - Week & Lesson selectors drive policy tier and randomness
# - Random MCQs (A/B/C/D), inline editing, downloads: MCQ Paper (.docx), Answer Key (.docx), Moodle GIFT (.gift)
# - Random Activities, inline editing, download Activity Sheet (.docx)
# - Revision tab for week bands (1–3, 4–8, 9–14) with DOCX export
# - Safe session_state usage

from io import BytesIO
from typing import List, Dict, Tuple
from pathlib import Path
import random, pandas as pd
import streamlit as st
from docx import Document
from pptx import Presentation
from pypdf import PdfReader

APP_NAME = "ADI Builder — Lesson Activities & Questions"
STRAPLINE = "Professional, branded, editable and export-ready."
st.set_page_config(page_title=APP_NAME, page_icon="✅", layout="wide")

# ---------- Theme & CSS ----------
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
  textarea.bigbox {{ min-height:180px !important; font-size:16px !important; line-height:1.4; }}
  .helper {{ color:#5a6c62; font-size:12px; margin-top:4px }}
  /* Tabs underline/active */
  [data-baseweb="tab-list"] {{ border-bottom:2px solid #dfe6e2; }}
  [data-baseweb="tab"][aria-selected="true"] {{ color:{ADI_GREEN}; font-weight:700; }}
  /* Alerts recolor */
  div[data-testid="stAlert"] {{ border-left:5px solid {ADI_GREEN}; background:#eef5ef; color:#1f3b2a;
    border-radius:10px; padding:12px 14px; }}
  div[data-testid="stAlert"] svg {{ color:{ADI_GREEN}; }}
  /* Tag "chips" recolor */
  div[data-baseweb="tag"] {{ background:#e8efe9; color:#1f3b2a; border:1px solid #cfd8d2; }}
  /* Uploader highlight */
  div[data-testid="stFileUploader"] > div:first-child {{ 
    border:2px dashed {ADI_GREEN}; background:#f0f7f2; border-radius:16px; padding:10px;
  }}
  div[data-testid="stFileUploader"]:hover > div:first-child {{ background:#e8f3ea; }}
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).parent
LOGO = ROOT / "Logo.png"  # put Logo.png in repo root to show it

# ---------- Logo helper (compat for older/newer Streamlit) ----------
def show_logo():
    if LOGO.exists():
        try:
            st.image(str(LOGO), use_container_width=True)
        except TypeError:
            # Older Streamlit versions
            try:
                st.image(str(LOGO), use_column_width=True)
            except TypeError:
                st.image(str(LOGO), width=140)
    else:
        st.markdown("**ADI**")

# ---------- Data & helpers ----------
BLOOM = {
    "Low": ["define", "identify", "list", "recall", "describe", "label"],
    "Medium": ["apply", "demonstrate", "solve", "illustrate"],
    "High": ["evaluate", "synthesize", "design", "justify"],
}

def policy_for_week(week:int)->str:
    if 1 <= week <= 3: return "Low"
    if 4 <= week <= 8: return "Medium"
    return "High"

def week_band(week:int)->str:
    if 1 <= week <= 3: return "Weeks 1–3"
    if 4 <= week <= 8: return "Weeks 4–8"
    return "Weeks 9–14"

# Enhanced textarea with live counter
def big_text_area(label:str, key:str, placeholder:str="", value:str="")->str:
    st.markdown(f"<label style='font-weight:600'>{label}</label>", unsafe_allow_html=True)
    txt = st.text_area("", key=key, value=value, placeholder=placeholder, label_visibility="collapsed")
    st.markdown(f"<div class='helper'>Characters: {len(txt)}</div>", unsafe_allow_html=True)
    st.markdown("<script>document.querySelectorAll('textarea').forEach(t=>t.classList.add('bigbox'));</script>", unsafe_allow_html=True)
    return txt

# ---------- File readers ----------
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

def extract_text(upload)->Tuple[str,str,int]:
    if not upload: return "", "", 0
    name = upload.name.lower()
    size = upload.size if hasattr(upload, "size") else 0
    if name.endswith(".pdf"): return read_pdf(upload), "pdf", size
    if name.endswith(".docx"): return read_docx(upload), "docx", size
    if name.endswith(".pptx"): return read_pptx(upload), "pptx", size
    return "", "", size

# ---------- Random content generators ----------
def seed_for(week:int, lesson:int)->int:
    return (week * 100) + lesson

def rand_words(n:int, rng:random.Random)->List[str]:
    corpus = ["system","network","policy","process","safety","ethics","design","testing","controls","risk",
              "audience","quality","evidence","impact","role","model","function","flow","goal","method",
              "data","analysis","outcome","security","module","topic","lesson","practice","standard","criteria"]
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
        rng.shuffle(options)
        answer_letter = letters[options.index(correct)]
        rows.append({"Question": q, "A": options[0], "B": options[1], "C": options[2], "D": options[3], "Answer": answer_letter})
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

# ---------- Revision generator ----------
def week_band(week:int)->str:
    if 1 <= week <= 3: return "Weeks 1–3"
    if 4 <= week <= 8: return "Weeks 4–8"
    return "Weeks 9–14"

def generate_revision(topic:str, text:str, week:int, lesson:int)->List[str]:
    band = week_band(week)
    base = topic or (text.split("\n")[0] if text else "the module")
    plan = [
        f"{band} — quick recall quiz on {base}.",
        f"Make a 1-page summary of key terms from {base}.",
        f"Create 5 flashcards: definitions, examples, and misconceptions.",
        f"Self-check: write 3 outcomes for lesson {lesson} and verify with a peer.",
        f"Practice question bank: 5 MCQs and 2 short answers derived from {base}.",
    ]
    return plan

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
        opts = [(row['A'], 'A'), (row['B'],'B'), (row['C'],'C'), (row['D'],'D')]
        parts = []
        for text, letter in opts:
            parts.append(("= " if row['Answer']==letter else "~ ") + str(text))
        body = f"::{row['Question'][:40]}:: {row['Question']} {{ {' '.join(parts)} }}"
        lines.append(body)
    return ("\n\n".join(lines)).encode("utf-8")

def docx_from_lines(title:str, lines:List[str])->bytes:
    d = Document(); d.add_heading(title, 1)
    for i, a in enumerate(lines, 1): d.add_paragraph(f"{i}. {a}")
    bio = BytesIO(); d.save(bio); return bio.getvalue()

# ---------- Session ----------
if "week" not in st.session_state: st.session_state["week"] = 1
if "lesson" not in st.session_state: st.session_state["lesson"] = 1
if "bloom" not in st.session_state: st.session_state["bloom"] = policy_for_week(st.session_state["week"])
if "verbs_mcq" not in st.session_state: st.session_state["verbs_mcq"] = BLOOM[st.session_state["bloom"]][:4]
if "mcq_df" not in st.session_state: st.session_state["mcq_df"] = pd.DataFrame()
if "activities" not in st.session_state: st.session_state["activities"] = []
if "revision" not in st.session_state: st.session_state["revision"] = []
if "spice" not in st.session_state: st.session_state["spice"] = 0

# ---------- Header ----------
c_logo, c_title = st.columns([1,5], vertical_alignment="center")
with c_logo:
    show_logo()
with c_title:
    st.markdown(f'<div class="adi-hero"><div style="font-size:28px;font-weight:800;">{APP_NAME}</div>'
                f'<div class="subtle" style="margin-top:4px;">{STRAPLINE}</div></div>',
                unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("**Upload PDF / DOCX / PPTX**")
    upload = st.file_uploader(" ", type=["pdf","docx","pptx"], label_visibility="collapsed")
    if upload is not None:
        size_kb = (upload.size // 1024) if hasattr(upload, "size") else 0
        st.success(f"Uploaded ✓  {upload.name}  ({size_kb} KB)")
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
        st.session_state["revision"] = []
        st.rerun()
    band = week_band(st.session_state['week'])
    st.caption(f"Policy: {st.session_state['bloom']} • {band}")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["🧠 Knowledge MCQs", "🛠️ Skills Activities", "📘 Revision"])

extracted, kind, size = extract_text(upload)
topic_hint = (extracted.split("\n")[0][:160] if extracted else "")

# ---------- Tab 1: MCQs ----------
with tab1:
    st.subheader("Knowledge MCQs")
    levels = st.multiselect("Bloom’s levels", ["Understand","Apply","Analyse","Evaluate","Create"],
                            default=["Understand","Apply","Analyse"])
    with st.expander("Verbs per level", expanded=True):
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
    c1, c2, c3 = st.columns(3)
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
        st.success(f"Generated {len(df)} questions. Edit below if needed.")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="mcq_editor")
        st.session_state["mcq_df"] = edited
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("⬇️ MCQ Paper (.docx)", data=docx_from_df(edited, "MCQ Paper"),
                               file_name="mcq_paper.docx")
        with d2:
            st.download_button("⬇️ Answer Key (.docx)", data=docx_answer_key_from_df(edited),
                               file_name="answer_key.docx")
        with d3:
            st.download_button("⬇️ Moodle GIFT (.gift)", data=gift_from_df(edited),
                               file_name="mcq_questions.gift")
    else:
        st.info("Upload (optional), pick verbs, set blocks, then **Generate MCQ Blocks**.")

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
        acts_df = pd.DataFrame({"Activity": acts})
        edited_acts = st.data_editor(acts_df, num_rows="dynamic", use_container_width=True, key="acts_editor")
        st.session_state["activities"] = list(edited_acts["Activity"].fillna(""))
        st.download_button("⬇️ Activity Sheet (.docx)",
                           data=docx_from_lines("Activity Sheet", st.session_state["activities"]),
                           file_name="activity_sheet.docx")
    else:
        st.info("Pick count/duration and verbs, then **Generate Activities**.")

# ---------- Tab 3: Revision ----------
with tab3:
    st.subheader("Revision planner by week band")
    src = big_text_area("Source text (editable)", key="rev_src",
                        value=extracted[:3000] if extracted else "",
                        placeholder="Paste the key concepts or summaries here…")
    topic_rev = st.text_input("Topic / unit title", value=(topic_hint or "Module / Unit"))
    if st.button("📘 Build revision plan", type="primary"):
        st.session_state["revision"] = generate_revision(topic_rev, src, st.session_state["week"], st.session_state["lesson"])
    rev = st.session_state["revision"]
    if rev:
        st.write("**Generated plan:**")
        for i, line in enumerate(rev, 1): st.write(f"{i}. {line}")
        st.download_button("⬇️ Revision Pack (.docx)",
                           data=docx_from_lines("Revision Pack", rev),
                           file_name="revision_pack.docx")
    else:
        st.info("Paste or upload content, set Week/Lesson, then **Build revision plan**.")

