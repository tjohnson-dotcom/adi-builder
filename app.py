
# ADI Builder — v2.3 (stable)
# - ADI colors & hover effects
# - Logo width compatibility
# - Week-band pills
# - Policy Mode (3 Qs: Low→Medium→High)
# - Safe multiselect defaults (no crash)
# - MCQ/Activities/Revision + downloads

from io import BytesIO
from pathlib import Path
from typing import List, Tuple
import random, pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from docx import Document
from pptx import Presentation
from pypdf import PdfReader

APP_NAME = "ADI Builder — Lesson Activities & Questions"
STRAPLINE = "Professional, branded, editable and export-ready."
st.set_page_config(page_title=APP_NAME, page_icon="✅", layout="wide")

ADI_GREEN = "#245a34"
ADI_AMBER = "#b87b1e"
ADI_SLATE = "#40514a"
BG = "#f6f5f2"

# ===== CSS =====
CSS_REPL = """
<style>
  .stApp {{ background:{BG}; }}
  .adi-hero {{ background:{ADI_GREEN}; color:#fff; padding:18px 22px; border-radius:22px; }}
  .subtle {{ color:#e6efe9; opacity:.95 }}
  .stButton > button {{
    background:{ADI_GREEN}; color:#fff; border:0; border-radius:12px; padding:10px 16px; font-weight:700;
    box-shadow:0 2px 0 rgba(0,0,0,.06); transition:transform .04s, box-shadow .08s, filter .08s;
  }}
  .stButton > button:hover {{ filter:brightness(0.96); box-shadow:0 3px 0 rgba(0,0,0,.08); }}
  .stButton > button:active {{ transform:translateY(1px); box-shadow:0 0 0 rgba(0,0,0,0); }}
  div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
    border-radius:12px !important; border:1px solid #cfd8d2 !important;
  }}
  textarea.bigbox {{ min-height:180px !important; font-size:16px !important; line-height:1.4; }}
  .helper {{ color:#5a6c62; font-size:12px; margin-top:4px }}
  [data-baseweb="tab-list"] { border-bottom:3px solid #c6d6ce; gap:10px; }
[data-baseweb="tab"] { padding:10px 14px; border-radius:12px 12px 0 0; font-weight:700; color:#2b3b33; }
[data-baseweb="tab"]:hover { background:#eaf4ee; color:#1f3b2a; }
[data-baseweb="tab"][aria-selected="true"] { background:#e7f2ea; color:__ADI_GREEN__; box-shadow:0 2px 0 __ADI_GREEN__ inset, 0 -2px 0 #00000005 inset; }
[data-baseweb="tab"] svg { margin-right:8px; }
div[data-testid="stAlert"] {{ border-left:5px solid {ADI_GREEN}; background:#eef5ef; color:#1f3b2a;
    border-radius:10px; padding:12px 14px; }}
  div[data-testid="stAlert"] svg {{ color:{ADI_GREEN}; }}
  div[data-baseweb="tag"], .stChip {{ background:#e7f2ea !important; color:#143a28 !important; border:1px solid #c6e0cf !important; }}
  div[data-baseweb="tag"]:hover, .stChip:hover {{ background:#e1f0e6 !important; }}
  div[data-baseweb="tag"] svg, .stChip svg { color:#245a34 !important; }
  div[data-testid="stFileUploader"] > div:first-child {{
    border:2px dashed {ADI_GREEN}; background:#f0f7f2; border-radius:16px; padding:10px; transition: background .12s;
  }}
  div[data-testid="stFileUploader"]:hover > div:first-child {{ background:#e8f3ea; }}
  .band {{ display:inline-block; padding:6px 10px; border-radius:999px; font-weight:700; margin-right:8px }}
  .band.low {{ background:#e7f2ea; color:{ADI_GREEN}; border:1px solid #c6e0cf; }}
  .band.med {{ background:#fbefdd; color:{ADI_AMBER}; border:1px solid #efd4a3; }}
  .band.high {{ background:#e9eef2; color:{ADI_SLATE}; border:1px solid #cfd8df; }}
</style>
"""
CSS_REPL = CSS_REPL.replace("__ADI_GREEN__", ADI_GREEN)
st.markdown(CSS_REPL, unsafe_allow_html=True)

components.html("""
<!doctype html><html><head><meta charset='utf-8'></head><body>
<script>
(function(){
  function applyADI(){
    const d = window.parent && window.parent.document ? window.parent.document : document;
    d.querySelectorAll('div[data-baseweb="tag"]').forEach(el => {
      el.style.setProperty('background', '#e7f2ea', 'important');
      el.style.setProperty('border', '1px solid #c6e0cf', 'important');
      el.style.setProperty('color', '#143a28', 'important');
    });
  }
  function start(){
    try{ applyADI(); }catch(e){}
    try{
      const d = window.parent && window.parent.document ? window.parent.document : document;
      new MutationObserver(applyADI).observe(d.body, {subtree:true, childList:true, attributes:true});
    }catch(e){}
  }
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(start, 0);
  } else {
    document.addEventListener('DOMContentLoaded', start, {once:true});
  }
})();
</script>
</body></html>
""", height=0)

ROOT = Path(__file__).parent
LOGO = ROOT / "Logo.png"

def show_logo():
    if LOGO.exists():
        try:
            st.image(str(LOGO), use_container_width=True)
        except TypeError:
            try:
                st.image(str(LOGO), use_column_width=True)
            except TypeError:
                st.image(str(LOGO), width=140)
    else:
        st.markdown("**ADI**")

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

def big_text_area(label:str, key:str, placeholder:str="", value:str="")->str:
    st.markdown(f"<label style='font-weight:700'>{label}</label>", unsafe_allow_html=True)
    txt = st.text_area("", key=key, value=value, placeholder=placeholder, label_visibility="collapsed")
    st.markdown(f"<div class='helper'>Characters: {len(txt)}</div>", unsafe_allow_html=True)
    st.markdown("<script>document.querySelectorAll('textarea').forEach(t=>t.classList.add('bigbox'));</script>", unsafe_allow_html=True)
    return txt

# ---- File reading ----
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

def extract_text(upload):
    if not upload: return "", "", 0
    name = upload.name.lower()
    size = upload.size if hasattr(upload, "size") else 0
    if name.endswith(".pdf"): return read_pdf(upload), "pdf", size
    if name.endswith(".docx"): return read_docx(upload), "docx", size
    if name.endswith(".pptx"): return read_pptx(upload), "pptx", size
    return "", "", size

# ---- Generators ----
def seed_for(week:int, lesson:int)->int:
    return (week * 100) + lesson

def rand_words(n:int, rng:random.Random)->List[str]:
    corpus = ["system","network","policy","process","safety","ethics","design","testing","controls","risk",
              "audience","quality","evidence","impact","role","model","function","flow","goal","method",
              "data","analysis","outcome","security","module","topic","lesson","practice","standard","criteria"]
    return [rng.choice(corpus) for _ in range(n)]

def generate_mcqs_random(topic, verbs, week, lesson, blocks, spice=0, policy_mode=False):
    rng = random.Random(seed_for(week, lesson) + spice)
    rows = []
    if policy_mode:
        seq = ["Low","Medium","High"]
        blocks = 3
        tiers = [BLOOM[t] for t in seq]
        for i in range(3):
            v = rng.choice(tiers[i])
            subject = topic or " ".join(rand_words(2, rng))
            q = f"{v.capitalize()} {subject}: which option is most correct?"
            correct = " ".join(rand_words(3, rng))
            distractors = [" ".join(rand_words(3, rng)) for _ in range(3)]
            options = [correct] + distractors
            rng.shuffle(options)
            rows.append({"Question": q, "A": options[0], "B": options[1], "C": options[2], "D": options[3],
                         "Answer": ["A","B","C","D"][options.index(correct)]})
        return pd.DataFrame(rows)

    for i in range(blocks):
        v = verbs[i % max(1, len(verbs))] if verbs else rng.choice(sum(BLOOM.values(), []))
        subject = topic or " ".join(rand_words(2, rng))
        q = f"{v.capitalize()} {subject}: which option is most correct?"
        correct = " ".join(rand_words(3, rng))
        distractors = [" ".join(rand_words(3, rng)) for _ in range(3)]
        options = [correct] + distractors
        rng.shuffle(options)
        rows.append({"Question": q, "A": options[0], "B": options[1], "C": options[2], "D": options[3],
                     "Answer": ["A","B","C","D"][options.index(correct)]})
    return pd.DataFrame(rows)

def generate_activities_random(topic, verbs, week, lesson, n, mins, spice=0):
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

def generate_revision(topic, text, week, lesson):
    wb = week_band(week)
    base = topic or (text.split("\n")[0] if text else "the module")
    plan = [
        f"{wb} — quick recall quiz on {base}.",
        f"Make a 1-page summary of key terms from {base}.",
        f"Create 5 flashcards: definitions, examples, and misconceptions.",
        f"Self-check: write 3 outcomes for lesson {lesson} and verify with a peer.",
        f"Practice question bank: 5 MCQs and 2 short answers derived from {base}.",
    ]
    return plan

# ---- Exports ----
def docx_from_df(df, title):
    d = Document(); d.add_heading(title, 1)
    letters = ["A","B","C","D"]
    for i, row in df.iterrows():
        d.add_paragraph(f"{i+1}. {row['Question']}")
        for L in letters: d.add_paragraph(f"   {L}) {row[L]}")
    bio = BytesIO(); d.save(bio); return bio.getvalue()

def docx_answer_key_from_df(df):
    d = Document(); d.add_heading("Answer Key", 1)
    for i, row in df.iterrows(): d.add_paragraph(f"Q{i+1}: {row['Answer']}")
    bio = BytesIO(); d.save(bio); return bio.getvalue()

def gift_from_df(df):
    lines = []
    for _, row in df.iterrows():
        parts = []
        for L in ["A","B","C","D"]:
            parts.append(("= " if row['Answer']==L else "~ ")+str(row[L]))
        lines.append(f"::{row['Question'][:40]}:: {row['Question']} {{ {' '.join(parts)} }}")
    return ("\n\n".join(lines)).encode("utf-8")

def docx_from_lines(title, lines):
    d = Document(); d.add_heading(title, 1)
    for i, a in enumerate(lines, 1): d.add_paragraph(f"{i}. {a}")
    bio = BytesIO(); d.save(bio); return bio.getvalue()

# ---- Session ----
if "week" not in st.session_state: st.session_state["week"] = 1
if "lesson" not in st.session_state: st.session_state["lesson"] = 1
if "bloom" not in st.session_state: st.session_state["bloom"] = policy_for_week(st.session_state["week"])
if "verbs_mcq" not in st.session_state: st.session_state["verbs_mcq"] = BLOOM[st.session_state["bloom"]][:4]
if "mcq_df" not in st.session_state: st.session_state["mcq_df"] = pd.DataFrame()
if "activities" not in st.session_state: st.session_state["activities"] = []
if "revision" not in st.session_state: st.session_state["revision"] = []
if "spice" not in st.session_state: st.session_state["spice"] = 0

# ---- Header ----
c_logo, c_title = st.columns([1,6], vertical_alignment="center")
with c_logo: show_logo()
with c_title:
    st.markdown(f'<div class="adi-hero"><div style="font-size:28px;font-weight:800;">{APP_NAME}</div>'
                f'<div class="subtle" style="margin-top:4px;">{STRAPLINE}</div></div>',
                unsafe_allow_html=True)
    colA, colB, colC = st.columns([1,1,1])
    with colA:
        if st.button("Weeks 1–3", key="band_low"):
            st.session_state["week"] = 1; st.session_state["bloom"] = "Low"; st.rerun()
        st.markdown('<span class="band low">Low focus</span>', unsafe_allow_html=True)
    with colB:
        if st.button("Weeks 4–8", key="band_med"):
            st.session_state["week"] = 4; st.session_state["bloom"] = "Medium"; st.rerun()
        st.markdown('<span class="band med">Medium focus</span>', unsafe_allow_html=True)
    with colC:
        if st.button("Weeks 9–14", key="band_high"):
            st.session_state["week"] = 9; st.session_state["bloom"] = "High"; st.rerun()
        st.markdown('<span class="band high">High focus</span>', unsafe_allow_html=True)

# ---- Sidebar ----
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
    st.caption(f"Policy: {st.session_state['bloom']} • {week_band(st.session_state['week'])}")

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs(["🧠 Knowledge MCQs", "🛠️ Skills Activities", "📘 Revision"])

extracted, kind, size = extract_text(upload)
topic_hint = (extracted.split("\n")[0][:160] if extracted else "")

# ---- Helper: safe multiselect ----
def safe_multiselect_verbs(label, pool, session_key="verbs_mcq", disabled=False):
    options = sorted(set(pool))
    prev = st.session_state.get(session_key, [])
    safe_default = [v for v in prev if v in options]
    if not safe_default and options:
        safe_default = options[: min(4, len(options))]
    return st.multiselect(label, options, default=safe_default, key=session_key, disabled=disabled)

# ---- Tab 1: MCQs ----
with tab1:
    st.subheader("Knowledge MCQs")
    st.toggle("ADI 3-question policy mode (Low ➜ Medium ➜ High)", key="policy_mode",
              help="Exactly 3 questions that follow the ADI Bloom policy progression.")
    levels = st.multiselect("Bloom’s levels",
                            ["Understand","Apply","Analyse","Evaluate","Create"],
                            default=["Understand","Apply","Analyse"],
                            disabled=st.session_state["policy_mode"])
    with st.expander("Verbs per level", expanded=True):
        chosen_tiers = []
        for lvl in levels:
            if lvl in {"Understand"}: chosen_tiers.append("Low")
            elif lvl in {"Apply","Analyse"}: chosen_tiers.append("Medium")
            else: chosen_tiers.append("High")
        pool = []
        for tier in chosen_tiers or ["Low","Medium"]:
            pool.extend(BLOOM[tier])
        verbs = safe_multiselect_verbs("Choose options", pool, "verbs_mcq",
                                       disabled=st.session_state["policy_mode"])
    topic = st.text_input("Topic (optional)", value=topic_hint)
    quick = st.radio("Quick pick", [5,10,20,30], index=1, horizontal=True,
                     disabled=st.session_state["policy_mode"])
    blocks = st.number_input("Or custom number of MCQ blocks", 1, 100, int(quick), 1, key="mcq_blocks",
                             disabled=st.session_state["policy_mode"])

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⚡ Generate MCQ Blocks", type="primary"):
            st.session_state["mcq_df"] = generate_mcqs_random(
                topic,
                verbs,
                st.session_state["week"],
                st.session_state["lesson"],
                int(3 if st.session_state["policy_mode"] else blocks),
                st.session_state["spice"],
                policy_mode=st.session_state["policy_mode"]
            )
    with c2:
        if st.button("🎲 Regenerate (new random set)"):
            st.session_state["spice"] += 1
            st.session_state["mcq_df"] = generate_mcqs_random(
                topic,
                verbs,
                st.session_state["week"],
                st.session_state["lesson"],
                int(3 if st.session_state["policy_mode"] else blocks),
                st.session_state["spice"],
                policy_mode=st.session_state["policy_mode"]
            )
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
        st.info("Upload (optional), pick verbs (or use policy mode), set blocks, then **Generate MCQ Blocks**.")

# ---- Tab 2: Activities ----
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

# ---- Tab 3: Revision ----
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
