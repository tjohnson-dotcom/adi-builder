# streamlit_app.py — ADI Builder (Counts + Time per item + MCQs + Activity Planner)
import os, io, random
from datetime import datetime
import streamlit as st
from docx import Document
from docx.shared import Pt

st.set_page_config(page_title="ADI Builder", page_icon="📚", layout="wide")

ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
STONE_BG  = "#f5f5f4"
INK       = "#1f2937"

st.markdown(f"""
<style>
:root {{ --adi-font-base: 18px; --adi-font-ui: 17px; }}
html, body, [data-testid="stAppViewContainer"] {{
  background:{STONE_BG}; color:{INK};
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, 'Helvetica Neue', Arial;
  font-size: var(--adi-font-base);
}}
.main .block-container {{ max-width: 1360px; margin:0 auto; padding-top:.8rem; padding-bottom:2rem; }}

.stButton>button {{
  background:{ADI_GREEN} !important; color:white !important;
  border:0; border-radius:16px; padding:.75rem 1.2rem; font-weight:600;
  font-size:var(--adi-font-ui);
}}
.stButton>button:hover {{ filter:brightness(1.05); }}

.adi-card {{ background:white; border-radius:16px; padding:1.2rem; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
.bloom-chip {{ display:inline-flex; align-items:center; gap:.5rem; padding:.4rem .8rem; border-radius:999px;
  background:linear-gradient(90deg,{ADI_GOLD},{ADI_GREEN}); color:white; font-weight:700; font-size:.95rem; }}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "uploads" not in st.session_state:
    st.session_state["uploads"] = {}

# ---- Sidebar ----
with st.sidebar:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_container_width=True)
    else:
        st.markdown("### **ADI Builder**")

    modes = ["Knowledge", "Skills", "Activities", "Revision"]
    icons = {"Knowledge":"📘","Skills":"🛠️","Activities":"🎯","Revision":"📝"}
    labels = [f"{icons[m]} {m}" for m in modes]
    picked = st.radio("Pick a mode", labels, index=0, label_visibility="collapsed")
    mode = modes[labels.index(picked)]

    week   = st.selectbox("Week", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson", list(range(1,6)), index=0)

    # Global controls you asked for
    count  = st.selectbox("Number of items", [3,4,5,6,8,10,12,15,20], index=4)  # default 8
    time_per = st.selectbox("Time per item (minutes)", [5,10,15,20,25,30,40,45,50,60], index=2)

    st.markdown("### 📎 Resources (drag & drop)")
    with st.expander("📥 Drag & drop files or click to browse"):
        ebook_file = st.file_uploader("📖 eBook (PDF)", type=["pdf"], key="ebook")
        plan_file  = st.file_uploader("📄 Lesson Plan (DOCX/PDF)", type=["docx","pdf"], key="plan")
        ppt_file   = st.file_uploader("📊 Slides (PPTX)", type=["pptx"], key="ppt")

    # Persist visible upload status
    def _remember(tag,f):
        if f: st.session_state["uploads"][tag] = {"name":f.name, "size":round(getattr(f,"size",0)/1024/1024,2)}
    _remember("ebook", ebook_file); _remember("plan", plan_file); _remember("ppt", ppt_file)

    if st.session_state["uploads"]:
        st.markdown("#### ✅ Uploaded")
        for tag,meta in st.session_state["uploads"].items():
            icon={"ebook":"📖","plan":"📄","ppt":"📊"}[tag]
            st.markdown(f"- {icon} **{meta['name']}** · {meta['size']} MB")

    run = st.button("✨ Generate for staff")

def bloom_level(w:int)->str:
    if 1<=w<=4: return "LOW — Remember/Understand"
    if 5<=w<=9: return "MEDIUM — Apply/Analyse"
    return "HIGH — Evaluate/Create"

def _bloom_band(w:int)->str:
    return "LOW" if w<=4 else ("MEDIUM" if w<=9 else "HIGH")

# --- Knowledge (MCQs) helpers ---
def make_mcq_stems(n:int, topic:str, week:int):
    topic_txt = topic.strip() if topic else "the topic"
    level = _bloom_band(week)
    pools = {
        "LOW":[
            "Identify the correct term for {T}.",
            "Select the best definition of {T}.",
            "Recognize the main idea of {T}.",
            "Match the concept that describes {T}.",
            "Choose the statement that correctly describes {T}.",
        ],
        "MEDIUM":[
            "Apply the concept of {T} to the scenario.",
            "Select the step that should occur next in {T}.",
            "Determine which approach best solves a problem in {T}.",
            "Classify the example according to {T}.",
            "Select the most appropriate use of {T}.",
        ],
        "HIGH":[
            "Evaluate which option best justifies {T}.",
            "Decide which solution most improves {T}.",
            "Critique the argument about {T} and pick the most valid claim.",
            "Prioritize the factors for {T} and choose the top priority.",
            "Design choice: select the option that best develops {T}.",
        ],
    }
    pool = pools[level]
    return [pool[i % len(pool)].replace("{T}", topic_txt) for i in range(n)]

def make_mcq_options(stem:str, week:int):
    level=_bloom_band(week)
    correct = f"Best answer aligned to: {stem}"
    distractors = [
        f"Partly correct but misses a key detail of: {stem}",
        f"Plausible wording that conflicts with: {stem}",
        f"Irrelevant detail not required for: {stem}",
    ]
    if level=="MEDIUM":
        distractors[0]=f"Correct step but wrong order for: {stem}"
        distractors[1]=f"Mixes two concepts related to: {stem}"
    elif level=="HIGH":
        distractors[0]=f"Reasonable yet lacks justification for: {stem}"
        distractors[1]=f"Claim without evidence about: {stem}"
    opts=[("A",correct,True),("B",distractors[0],False),("C",distractors[1],False),("D",distractors[2],False)]
    random.shuffle(opts)
    return opts

# --- Activity library (Skills/Activities/Revision) ---
def seed_activities(mode:str, topic:str, week:int, count:int):
    topic_txt = topic or "the topic"
    if mode=="Skills":
        base=[
            f"Demonstrate the core procedure for {topic_txt} and record observations.",
            f"Peer-check a partner using the provided rubric for {topic_txt}.",
            f"Complete a worked example of {topic_txt} and annotate decisions.",
            f"Perform a quick diagnostic on {topic_txt} and note faults.",
            f"Reflect on one improvement for next session on {topic_txt}.",
        ]
    elif mode=="Activities":
        base=[
            f"Think–Pair–Share: 3 facts, 2 connections, 1 question about {topic_txt}.",
            f"Jigsaw: split subtopics of {topic_txt}, teach-back in groups.",
            f"Gallery walk: poster notes on misconceptions about {topic_txt}.",
            f"Case vignette: small-group solution applying {topic_txt}.",
            f"Concept map: connect key terms around {topic_txt}.",
        ]
    else: # Revision
        base=[
            f"Create a one-page cheat sheet for {topic_txt}.",
            f"Write 5 short-answer questions covering {topic_txt}.",
            f"Flashcard set: 10 key terms from {topic_txt}.",
            f"Past-paper style question on {topic_txt} (timed).",
            f"Exit ticket: 2 things learned, 1 question on {topic_txt}.",
        ]
    return (base * ((count // len(base)) + 1))[:count]

# ---- Main ----
left, right = st.columns([1,1], gap="large")

with left:
    st.subheader(f"{mode} — Week {week}, Lesson {lesson}")
    st.caption("ADI-aligned prompts and activities. Zero sliders. Easy picks.")
    st.markdown(f"<span class='bloom-chip'>Bloom: {bloom_level(week)}</span>", unsafe_allow_html=True)
    topic = st.text_input("Topic / Objective (short)")
    notes = st.text_area("Key notes (optional)", height=120)

with right:
    st.markdown("### 📤 Draft outputs")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    if run:
        if mode=="Knowledge":
            stems = make_mcq_stems(count, topic, week)
            answer_key = []
            for i, stem in enumerate(stems, start=1):
                st.write(f"**Q{i}.** {stem}")
                for letter, text, is_correct in make_mcq_options(stem, week):
                    st.write(f"\u2003{letter}. {text}")
                    if is_correct: answer_key.append((i, letter))
                st.write("")
            st.markdown("**Answer Key**")
            st.write(", ".join([f"Q{q} → {a}" for q,a in answer_key]))

            def export_docx_mcq():
                doc=Document()
                doc.add_heading(f"ADI Knowledge — W{week} L{lesson}", level=1)
                if topic: doc.add_paragraph(f"Topic: {topic}")
                if notes: doc.add_paragraph(f"Notes: {notes}")
                for i, stem in enumerate(stems, 1):
                    doc.add_paragraph(f"Q{i}. {stem}")
                    for letter, text, is_correct in make_mcq_options(stem, week):
                        p=doc.add_paragraph(f"   {letter}. {text}")
                        for run in p.runs: run.font.size=Pt(11)
                doc.add_heading("Answer Key", level=2)
                doc.add_paragraph(", ".join([f"Q{q} → {a}" for q,a in answer_key]))
                bio=io.BytesIO(); doc.save(bio); bio.seek(0); return bio
            st.download_button("⬇️ Export MCQs (DOCX)", data=export_docx_mcq(),
                               file_name=f"ADI_Knowledge_W{week}_L{lesson}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True)
        else:
            items = seed_activities(mode, topic, week, count)
            for i, s in enumerate(items, start=1):
                st.write(f"**{mode[:-1] if mode.endswith('s') else mode} {i} ({time_per} min):** {s}")
            def export_docx_plan():
                doc=Document()
                doc.add_heading(f"ADI {mode} Plan — W{week} L{lesson}", level=1)
                if topic: doc.add_paragraph(f"Topic: {topic}")
                if notes: doc.add_paragraph(f"Notes: {notes}")
                for i, s in enumerate(items, 1):
                    doc.add_paragraph(f"{mode[:-1] if mode.endswith('s') else mode} {i} ({time_per} min): {s}")
                bio=io.BytesIO(); doc.save(bio); bio.seek(0); return bio
            st.download_button(f"⬇️ Export {mode} Plan (DOCX)", data=export_docx_plan(),
                               file_name=f"ADI_{mode}_W{week}_L{lesson}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True)
    else:
        st.info("Upload resources, set Week/Lesson, choose mode, number of items, and time per item. Then click **Generate**.")
    st.markdown("</div>", unsafe_allow_html=True)

# Chat
st.markdown("### 💬 Conversation")
st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])
if prompt := st.chat_input("Ask ADI Builder…"):
    st.session_state["messages"].append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(prompt)
    reply = "Got it. Use **Generate** for drafts, then export to DOCX. Time per item and counts are in the sidebar."
    st.session_state["messages"].append({"role":"assistant","content":reply})
    with st.chat_message("assistant"): st.markdown(reply)
st.markdown("</div>", unsafe_allow_html=True)

# Guards
problems=[]
if run:
    if ebook_file and getattr(ebook_file,"size",0) > 25*1024*1024: problems.append("eBook exceeds 25MB.")
    if ppt_file and not ppt_file.name.lower().endswith(".pptx"): problems.append("Slides must be .pptx.")
if problems: st.warning("\n".join([f"• {p}" for p in problems]))
