

# ADI Builder — Lesson Activities & Questions (v2.5.5, stable build)
# Streamlit 1.35+ ; no JS/HTML injection; safe session handling.

import os, io, random
from typing import List, Tuple
import streamlit as st
from docx import Document

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="✅", layout="wide")

ADI_GREEN = "#245a34"

CSS = """
<style>
html, body, .stApp { background: #f6f5f2; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
.adi-banner { background:#244a34; color:#fff; border-radius:18px; padding:20px 24px; }
.adi-subtle { color:#dfeee6; font-size:0.92rem; }
.adi-pill { display:inline-block; padding:6px 12px; border-radius:10px; margin-right:10px; font-weight:700; }
.adi-pill.low { background:#e7f2ea; color:#143a28; }
.adi-pill.med { background:#fdecd6; color:#6a4b14; }
.adi-pill.high { background:#e8ecef; color:#2d3940; }
[data-baseweb="tab-list"] { border-bottom:3px solid #c6d6ce; gap:10px; }
[data-baseweb="tab"] { padding:10px 14px; border-radius:12px 12px 0 0; font-weight:700; color:#2b3b33; }
[data-baseweb="tab"]:hover { background:#eaf4ee; color:#1f3b2a; }
[data-baseweb="tab"][aria-selected="true"] { background:#e7f2ea; color:#245a34; box-shadow:0 2px 0 #245a34 inset; }
div[data-baseweb="tag"] { background:#e7f2ea; color:#143a28; border:1px solid #c6e0cf; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

LOW_VERBS = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate", "compare"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify"]
ALL_VERBS = sorted(set(LOW_VERBS + MED_VERBS + HIGH_VERBS))

st.markdown("""
<style>
/* Buttons (use ADI green, never Streamlit red) */
.stButton>button, .stDownloadButton>button {
  background: #245a34 !important;
  color: #fff !important;
  border: 1px solid #1e4c2b !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  transition: transform .02s ease-in-out, box-shadow .2s ease;
  border-radius: 10px;
}
.stButton>button:hover, .stDownloadButton>button:hover {
  filter: brightness(1.02);
  transform: translateY(-1px);
}

/* Pills / chips (verbs, week tags) */
[data-baseweb="tag"] {
  background: #eaf3ed !important;
  color: #245a34 !important;
  border: 1px solid #cfe3d6 !important;
}
[data-baseweb="tag"][aria-selected="true"] {
  background: #245a34 !important; color: #fff !important; border-color:#1e4c2b !important;
}

/* Tab bar underline & icons – make them pop */
div[data-testid="stHorizontalBlock"] .stMarkdown a {
  color: #245a34 !important;
}
.stTabs [data-baseweb="tab"] {
  font-weight: 600;
  color: #1f3b27;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: #245a34 !important;
  border-bottom: 3px solid #245a34 !important;
}
st.markdown("""
<style>
/* Buttons (use ADI green, never Streamlit red) */
.stButton>button, .stDownloadButton>button {
  background: #245a34 !important;
  color: #fff !important;
  border: 1px solid #1e4c2b !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  transition: transform .02s ease-in-out, box-shadow .2s ease;
  border-radius: 10px;
}
.stButton>button:hover, .stDownloadButton>button:hover {
  filter: brightness(1.02);
  transform: translateY(-1px);
}

/* Pills / chips (verbs, week tags) */
[data-baseweb="tag"] {
  background: #eaf3ed !important;
  color: #245a34 !important;
  border: 1px solid #cfe3d6 !important;
}
[data-baseweb="tag"][aria-selected="true"] {
  background: #245a34 !important; color: #fff !important; border-color:#1e4c2b !important;
}

/* Tab bar underline & icons – make them pop */
div[data-testid="stHorizontalBlock"] .stMarkdown a {
  color: #245a34 !important;
}
.stTabs [data-baseweb="tab"] {
  font-weight: 600;
  color: #1f3b27;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: #245a34 !important;
  border-bottom: 3px solid #245a34 !important;
}

/* Card-ish sections */
.block-container { padding-top: 1rem; }
.section-card {
  background:#fff; border:1px solid #e8ece9; border-radius:14px; padding:1rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}

/* Subtle help text */
.small-note { color:#687a70; font-size:.86rem; }

/* Hide the aggressive red alert boxes Streamlit shows by default */
.stAlert { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Buttons (use ADI green, never Streamlit red) */
.stButton>button, .stDownloadButton>button {
  background: #245a34 !important;
  color: #fff !important;
  border: 1px solid #1e4c2b !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  transition: transform .02s ease-in-out, box-shadow .2s ease;
  border-radius: 10px;
}
.stButton>button:hover, .stDownloadButton>button:hover {
  filter: brightness(1.02);
  transform: translateY(-1px);
}

/* Pills / chips (verbs, week tags) */
[data-baseweb="tag"] {
  background: #eaf3ed !important;
  color: #245a34 !important;
  border: 1px solid #cfe3d6 !important;
}
[data-baseweb="tag"][aria-selected="true"] {
  background: #245a34 !important; color: #fff !important; border-color:#1e4c2b !important;
}

/* Tab bar underline & icons – make them pop */
div[data-testid="stHorizontalBlock"] .stMarkdown a {
  color: #245a34 !important;
}
.stTabs [data-baseweb="tab"] {
  font-weight: 600;
  color: #1f3b27;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: #245a34 !important;
  border-bottom: 3px solid #245a34 !important;
}

/* Card-ish sections */
.block-container { padding-top: 1rem; }
.section-card {
  background:#fff; border:1px solid #e8ece9; border-radius:14px; padding:1rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}

/* Subtle help text */
.small-note { color:#687a70; font-size:.86rem; }

/* Hide the aggressive red alert boxes Streamlit shows by default */
.stAlert { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)


/* Card-ish sections */
.block-container { padding-top: 1rem; }
.section-card {
  background:#fff; border:1px solid #e8ece9; border-radius:14px; padding:1rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}

/* Subtle help text */
.small-note { color:#687a70; font-size:.86rem; }

/* Hide the aggressive red alert boxes Streamlit shows by default */
.stAlert { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)


def init_state():
    s = st.session_state
    s.setdefault("week", 1)
    s.setdefault("lesson", 1)
    s.setdefault("policy_mode", False)
    s.setdefault("verbs_mcq", ["define","identify","list","recall"])
    s.setdefault("verbs_act", ["apply","demonstrate","evaluate","design"])
    s.setdefault("blocks", 10)
    s.setdefault("mcq_rows", [])
    s.setdefault("act_rows", [])
    s.setdefault("rev_rows", [])
    s.setdefault("topic", "")
    s.setdefault("upload_name", "")
init_state()

def safe_file_uploader(label, types):
    f = st.file_uploader(label, type=types, accept_multiple_files=False)
    if f is None:
        return None
    # sanity check: avoid flicker re-runs killing state
    if not hasattr(st.session_state, "_upload_seen"):
        st.session_state._upload_seen = set()
    key = (f.name, f.size)
    if key in st.session_state._upload_seen:
        return f
    st.session_state._upload_seen.add(key)
    return f

upload = safe_file_uploader("Upload PDF / DOCX / PPTX", ["pdf","docx","pptx"])


def band_for_week(week:int)->Tuple[str,str]:
    if week<=3: return ("Weeks 1–3", "Low focus")
    if week<=8: return ("Weeks 4–8", "Medium focus")
    return ("Weeks 9–14", "High focus")

def stable_seed(week:int, lesson:int, spice:int=0)->int:
    return week*100 + lesson + spice*9973

def pick_topic_hint(upload_name:str, topic_text:str)->str:
    if topic_text.strip():
        return topic_text.strip()
    if upload_name:
        base = os.path.splitext(os.path.basename(upload_name))[0]
        base = base.replace("_"," ").replace("-"," ").strip()
        return f"Based on: {base}"
    return "General module concepts"

def rand_words(n:int)->str:
    bank = ["system","process","energy","security","signal","design","network","analysis","quality","safety",
            "resource","model","standard","strategy","policy","control","testing","planning","risk","theory"]
    return " ".join(random.choice(bank) for _ in range(n))

def generate_mcqs(n:int, verbs:List[str], topic:str, seed:int)->List[dict]:
    random.seed(seed)
    rows = []
    for i in range(n):
        verb = random.choice(verbs) if verbs else "understand"
        stem = f"{verb.title()} {topic.lower()} — {rand_words(5)}?"
        correct_letter = random.choice(["A","B","C","D"])
        options = {}
        letters = ["A","B","C","D"]
        for L in letters:
            if L==correct_letter:
                options[L] = f"{verb.title()} the key aspect of {topic.lower()}"
            else:
                options[L] = f"{rand_words(4).title()}"
        rows.append({
            "No": i+1, "Question": stem,
            "A": options["A"], "B": options["B"], "C": options["C"], "D": options["D"],
            "Answer": correct_letter
        })
    return rows

def generate_activities(count:int, mins:int, verbs:List[str], topic:str, seed:int)->List[dict]:
    random.seed(seed+4242)
    templates = {
        "apply": "In pairs, apply the concept of {topic} to a real-world scenario and present findings.",
        "demonstrate": "Demonstrate a step-by-step procedure related to {topic} with a quick demo.",
        "evaluate": "Evaluate the strengths and weaknesses of two approaches to {topic}.",
        "design": "Design a {topic}-focused mini project with goals, tasks, and success criteria.",
        "solve": "Solve a short case related to {topic} and justify your choices.",
        "illustrate": "Illustrate a workflow/map detailing how {topic} operates in practice.",
        "compare": "Compare two methods for achieving {topic} and recommend one."
    }
    rows = []
    for i in range(count):
        verb = random.choice(verbs) if verbs else "apply"
        text = templates.get(verb, "Plan a brief activity related to {topic}.").format(topic=topic)
        rows.append({"No": i+1, "Verb": verb, "Activity": text, "Duration (mins)": mins})
    return rows

def to_docx_mcq(rows:List[dict], title:str)->bytes:
    doc = Document(); doc.add_heading(title, level=1)
    for r in rows:
        _ = doc.add_paragraph(f"{r['No']}. {r['Question']}")
        doc.add_paragraph(f"A. {r['A']}"); doc.add_paragraph(f"B. {r['B']}")
        doc.add_paragraph(f"C. {r['C']}"); doc.add_paragraph(f"D. {r['D']}"); doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

def to_docx_answer_key(rows:List[dict], title:str)->bytes:
    doc = Document(); doc.add_heading(title, level=1)
    t = doc.add_table(rows=1, cols=2)
    hdr = t.rows[0].cells; hdr[0].text = "Q#"; hdr[1].text = "Answer"
    for r in rows:
        row = t.add_row().cells; row[0].text = str(r["No"]); row[1].text = r["Answer"]
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

def to_gift(rows:List[dict], title:str)->bytes:
    lines = [f"// {title}"]
    for r in rows:
        q = r["Question"].replace("\\n"," ")
        options = [("A", r["A"]), ("B", r["B"]), ("C", r["C"]), ("D", r["D"])]
        gift_opts = []
        for letter, text in options:
            gift_opts.append(("="+text) if letter==r["Answer"] else ("~"+text))
        lines.append(f"{q}{{{''.join(gift_opts)}}}")
    return ("\\n\\n".join(lines)).encode("utf-8")

def to_docx_activities(rows:List[dict], title:str)->bytes:
    doc = Document(); doc.add_heading(title, level=1)
    t = doc.add_table(rows=1, cols=3)
    hdr = t.rows[0].cells; hdr[0].text = "No"; hdr[1].text = "Activity"; hdr[2].text = "Duration (mins)"
    for r in rows:
        row = t.add_row().cells
        row[0].text = str(r["No"]); row[1].text = r["Activity"]; row[2].text = str(r["Duration (mins)"])
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()
[theme]
primaryColor = "#245a34"          # ADI green (buttons, sliders, etc)
backgroundColor = "#f6f5f2"       # soft page background
secondaryBackgroundColor = "#ffffff"
textColor = "#0f2316"
font = "sans serif"

[server]
headless = true
maxUploadSize = 200               # MB – matches your UI copy
fileWatcherType = "none"
enableXsrfProtection = true

[browser]
gatherUsageStats = false

active_tab = st.session_state.get("tab", "MCQs")
title_map = {
  "MCQs": "🧠 Knowledge MCQs",
  "Activities": "🛠️ Skills Activities",
  "Revision": "📘 Revision"
}
st.subheader(title_map.get(active_tab, "🧠 Knowledge MCQs"))


def to_docx_revision(rows:List[str], title:str)->bytes:
    doc = Document(); doc.add_heading(title, level=1)
    for i, line in enumerate(rows, 1):
        doc.add_paragraph(f"{i}. {line}")
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

with st.sidebar:
    st.header("Upload PDF / DOCX / PPTX")
    up = st.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"], label_visibility="collapsed")
    if up is not None:
        st.session_state["upload_name"] = up.name
        st.session_state["upload_bytes"] = up.getbuffer().tobytes()
        st.success(f"Uploaded ✓ {up.name}")
    st.write(""); st.write("Week")
    st.session_state["week"] = st.selectbox("", list(range(1,15)), index=0, label_visibility="collapsed")
    st.write("Lesson")
    st.session_state["lesson"] = st.selectbox("", list(range(1,11)), index=0, label_visibility="collapsed")

band = "Weeks 1–3" if st.session_state["week"]<=3 else "Weeks 4–8" if st.session_state["week"]<=8 else "Weeks 9–14"
focus = "Low focus" if "1–3" in band else ("Medium focus" if "4–8" in band else "High focus")
st.markdown(f"""
<div class="adi-banner">
  <div style="font-size:1.35rem; font-weight:800;">ADI Builder — Lesson Activities & Questions</div>
  <div class="adi-subtle">Professional, branded, editable and export-ready.</div>
  <div style="margin-top:10px;">
    <span class="adi-pill {'low' if '1–3' in band else 'med' if '4–8' in band else 'high'}">{band}</span>
    <span class="adi-pill {'low' if '1–3' in band else 'med' if '4–8' in band else 'high'}">{focus}</span>
  </div>
</div>
""", unsafe_allow_html=True)
st.write("")

tab_mcq, tab_act, tab_rev = st.tabs(["🧠 Knowledge MCQs", "🛠️ Skills Activities", "📘 Revision"])

with tab_mcq:
    st.subheader("Knowledge MCQs")
    st.session_state["policy_mode"] = st.toggle("ADI 3-question policy mode (Low ➜ Medium ➜ High)", value=st.session_state["policy_mode"])

    levels = st.multiselect("Bloom’s levels",
        options=["Understand","Apply","Analyse","Evaluate","Create"],
        default=["Understand","Apply","Analyse"]
    )

    pool = []
    if "Understand" in levels: pool += LOW_VERBS
    if "Apply" in levels or "Analyse" in levels: pool += MED_VERBS
    if "Evaluate" in levels or "Create" in levels: pool += HIGH_VERBS
    pool = sorted(set(pool)) or ALL_VERBS
    def_mcq = [v for v in st.session_state["verbs_mcq"] if v in pool] or pool[:4]
    st.session_state["verbs_mcq"] = def_mcq
    verbs = st.multiselect("Choose options", pool, default=def_mcq)

    topic = st.text_input("Topic (optional)", value=st.session_state["topic"])
    st.session_state["topic"] = topic

    quick = st.radio("Quick pick", [5,10,20,30], horizontal=True, index=1)
    blocks = st.number_input("Or custom number of MCQ blocks", min_value=1, max_value=50, value=st.session_state["blocks"], step=1)
    st.session_state["blocks"] = blocks

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        gen = st.button("⚡ Generate MCQ Blocks", use_container_width=True, type="primary")
    with c2:
        regen = st.button("🔁 Regenerate (new random set)", use_container_width=True)
    with c3:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state["mcq_rows"] = []

    n_blocks = blocks if blocks != 10 else quick
    if gen or regen:
        t = (st.session_state["topic"].strip() or
             (os.path.splitext(os.path.basename(st.session_state.get("upload_name","")))[0].replace("_"," ").replace("-"," ").strip() or "General module concepts"))
        seed = st.session_state["week"]*100 + st.session_state["lesson"] + (9973 if regen else 0)
        if st.session_state["policy_mode"]:
            tiers = [LOW_VERBS, MED_VERBS, HIGH_VERBS]
            rows = []
            for i, tv in enumerate(tiers, 1):
                rows += generate_mcqs(1, [v for v in verbs if v in tv] or tv[:4], t, seed+i*17)
        else:
            rows = generate_mcqs(n_blocks, verbs, t, seed)
        st.session_state["mcq_rows"] = rows

    rows = st.session_state.get("mcq_rows", [])
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)

        title = f"MCQ Paper — Week {st.session_state['week']} Lesson {st.session_state['lesson']}"
        key_title = f"Answer Key — Week {st.session_state['week']} Lesson {st.session_state['lesson']}"
        gift_title = f"Moodle GIFT — Week {st.session_state['week']} Lesson {st.session_state['lesson']}"

        colA, colB, colC = st.columns(3)
        with colA:
            st.download_button("📄 Download MCQ Paper (.docx)", data=to_docx_mcq(rows, title),
                               file_name="mcq_paper.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with colB:
            st.download_button("🗝️ Download Answer Key (.docx)", data=to_docx_answer_key(rows, key_title),
                               file_name="answer_key.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with colC:
            st.download_button("🎓 Download Moodle GIFT (.gift)", data=to_gift(rows, gift_title),
                               file_name="mcq.gift", mime="text/plain", use_container_width=True)
    else:
        st.info("Upload (optional), pick verbs, set blocks, then **Generate MCQ Blocks**.")

with tab_act:
    st.subheader("Skills Activities")
    col1, col2 = st.columns([3,2], gap="large")
    with col1:
        count = st.number_input("Activities", min_value=1, max_value=12, value=3, step=1)
    with col2:
        mins = st.number_input("Duration per activity (mins)", min_value=10, max_value=180, value=45, step=5)

    act_pool = MED_VERBS + HIGH_VERBS
    def_act = [v for v in st.session_state["verbs_act"] if v in act_pool] or ["apply","demonstrate","evaluate","design"]
    st.session_state["verbs_act"] = def_act
    act_verbs = st.multiselect("Preferred action verbs", act_pool, default=def_act)

    c1, c2 = st.columns([1,1])
    with c1:
        genA = st.button("✅ Generate Activities", use_container_width=True, type="primary")
    with c2:
        regenA = st.button("🔁 Regenerate Activities", use_container_width=True)

    if genA or regenA:
        t = (st.session_state.get("topic","").strip() or
             (os.path.splitext(os.path.basename(st.session_state.get("upload_name","")))[0].replace("_"," ").replace("-"," ").strip() or "General module concepts"))
        seed = st.session_state["week"]*100 + st.session_state["lesson"] + (9973 if regenA else 0)
        st.session_state["act_rows"] = generate_activities(count, mins, act_verbs, t, seed)

    arows = st.session_state.get("act_rows", [])
    if arows:
        st.dataframe(arows, use_container_width=True, hide_index=True)
        title = f"Activity Sheet — Week {st.session_state['week']} Lesson {st.session_state['lesson']}"
        st.download_button("📄 Download Activity Sheet (.docx)", data=to_docx_activities(arows, title),
                           file_name="activities.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else:
        st.info("Pick count/duration and verbs, then **Generate Activities**.")

with tab_rev:
    st.subheader("Revision planner by week band")
    t = (st.session_state.get("topic","").strip() or
         (os.path.splitext(os.path.basename(st.session_state.get("upload_name","")))[0].replace("_"," ").replace("-"," ").strip() or "General module concepts"))
    txt = st.text_area("Source text (editable)", height=160, placeholder="Paste the key concepts or summaries here…")
    topic_title = st.text_input("Topic / unit title", value=t)

    if st.button("📘 Build revision plan", type="primary"):
        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        if not lines:
            lines = [f"Revise {t}: key terms", f"Revise {t}: short answer practice", f"Revise {t}: example tasks"]
        st.session_state["rev_rows"] = lines

    rrows = st.session_state.get("rev_rows", [])
    if rrows:
        st.write("Revision items")
        for i, line in enumerate(rrows, 1):
            st.write(f"{i}. {line}")
        title = f"Revision Plan — Week {st.session_state['week']} Lesson {st.session_state['lesson']}"
        st.download_button("📄 Download Revision Pack (.docx)", data=to_docx_revision(rrows, title),
                           file_name="revision.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else:
        st.info("Paste or upload content, set Week/Lesson, then **Build revision plan**.")
