# streamlit_app.py — ADI Builder (MCQs + Upload Status + Bloom-aware)

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
html, body, [data-testid="stAppViewContainer"] {{
  background: {STONE_BG};
  color: {INK};
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, 'Helvetica Neue', Arial;
  font-size: 17px;
}}
.stButton>button {{ background:{ADI_GREEN} !important; color:white !important; border:0; border-radius:14px; padding:.7rem 1.2rem; font-weight:600; }}
.stButton>button:hover {{ filter:brightness(1.05); }}
.adi-card {{ background:white; border-radius:16px; padding:1.2rem; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
.bloom-chip {{ display:inline-flex; align-items:center; gap:.5rem; padding:.4rem .8rem; border-radius:999px; background:linear-gradient(90deg,{ADI_GOLD},{ADI_GREEN}); color:white; font-weight:700; font-size:.9rem; }}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "uploads" not in st.session_state:
    st.session_state["uploads"] = {}

# --- Sidebar ---
with st.sidebar:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_container_width=True)
    else:
        st.markdown("### **ADI Builder**")

    _options = ["Knowledge","Skills","Activities","Revision"]
    _icons   = {"Knowledge":"📘","Skills":"🛠️","Activities":"🎯","Revision":"📝"}
    _labels  = [f"{_icons[o]} {o}" for o in _options]
    _picked  = st.radio("Pick a workflow", _labels, index=0, label_visibility="collapsed")
    mode     = _options[_labels.index(_picked)]

    week   = st.selectbox("Week", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson", list(range(1,6)), index=0)
    count  = st.selectbox("Number of questions", [3,4,5,6,8,10,12,15,20], index=2)

    st.markdown("### 📎 Resources")
    with st.expander("📥 Drag & drop files"):
        ebook_file = st.file_uploader("📖 eBook (PDF)", type=["pdf"], key="ebook")
        plan_file  = st.file_uploader("📄 Lesson Plan (DOCX/PDF)", type=["docx","pdf"], key="plan")
        ppt_file   = st.file_uploader("📊 Slides (PPTX)", type=["pptx"], key="ppt")

    def _remember_upload(tag,f):
        if f:
            st.session_state["uploads"][tag] = {"name":f.name,"size":round(getattr(f,"size",0)/1024/1024,2)}
    _remember_upload("ebook",ebook_file)
    _remember_upload("plan",plan_file)
    _remember_upload("ppt",ppt_file)

    if st.session_state["uploads"]:
        st.markdown("#### ✅ Uploaded")
        for tag,meta in st.session_state["uploads"].items():
            icon={"ebook":"📖","plan":"📄","ppt":"📊"}[tag]
            st.markdown(f"- {icon} **{meta['name']}** · {meta['size']} MB")

    run = st.button("✨ Generate for staff")

# --- Helpers ---
def bloom_level(w:int):
    if 1<=w<=4: return "LOW — Remember/Understand"
    if 5<=w<=9: return "MEDIUM — Apply/Analyse"
    return "HIGH — Evaluate/Create"

def _bloom_level(w:int):
    return "LOW" if w<=4 else ("MEDIUM" if w<=9 else "HIGH")

def make_mcq_stems(n:int,topic:str,week:int):
    topic_txt = topic.strip() if topic else "the topic"
    level=_bloom_level(week)
    pools={
        "LOW":["Identify the correct term for {T}.","Select the best definition of {T}.","Recognize the main idea of {T}.","Match the concept that describes {T}.","Choose the statement that describes {T} correctly."],
        "MEDIUM":["Apply the concept of {T} to a scenario.","Select the step that should occur next in {T}.","Determine which approach best solves a problem in {T}.","Classify the example according to {T}.","Select the most appropriate use of {T}."],
        "HIGH":["Evaluate which option justifies {T}.","Decide which solution best improves {T}.","Critique the argument about {T} and pick the most valid.","Prioritize the factors for {T} and choose the top priority.","Design choice: select the option that best develops {T}."]
    }
    pool=pools[level]
    stems=[pool[i%len(pool)].replace("{T}",topic_txt) for i in range(n)]
    return stems

def make_mcq_options(stem:str,week:int):
    level=_bloom_level(week)
    correct=f"Best answer aligned to: {stem}"
    distractors=[f"Partly correct but misses detail of: {stem}",f"Plausible wording conflicting with: {stem}",f"Irrelevant detail not required for: {stem}"]
    if level=="MEDIUM":
        distractors[0]=f"Correct step but wrong order for: {stem}"
        distractors[1]=f"Mixes two concepts in: {stem}"
    if level=="HIGH":
        distractors[0]=f"Reasonable yet unjustified claim about: {stem}"
        distractors[1]=f"Evidence-free claim on: {stem}"
    options=[("A",correct,True),("B",distractors[0],False),("C",distractors[1],False),("D",distractors[2],False)]
    random.shuffle(options)
    return options

# --- Layout ---
left,right=st.columns([1,1])
with left:
    st.markdown("<div class='adi-topbar'><span class='brand'>📚 ADI Builder</span></div>", unsafe_allow_html=True)
    st.subheader(f"{mode} — Week {week}, Lesson {lesson}")
    st.caption("ADI-aligned prompts and activities. Zero sliders. Easy picks.")
    st.markdown(f"<span class='bloom-chip'>Bloom: {bloom_level(week)}</span>", unsafe_allow_html=True)
    topic=st.text_input("Topic / Objective (short)")
    notes=st.text_area("Key notes (optional)",height=100)

with right:
    st.markdown("### 📤 Draft outputs")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    if run:
        if mode=="Knowledge":
            stems=make_mcq_stems(count,topic,week)
            answer_key=[]
            for idx,stem in enumerate(stems,1):
                st.write(f"**Q{idx}.** {stem}")
                opts=make_mcq_options(stem,week)
                for letter,text,is_correct in opts:
                    st.write(f" {letter}. {text}")
                    if is_correct: answer_key.append((idx,letter))
                st.write("")
            st.markdown("**Answer Key**")
            st.write(", ".join([f"Q{q} → {a}" for q,a in answer_key]))
            def build_docx():
                doc=Document()
                doc.add_heading(f"ADI {mode} — Week {week} Lesson {lesson}",0)
                if topic: doc.add_paragraph(f"Topic: {topic}")
                if notes: doc.add_paragraph(f"Notes: {notes}")
                for idx,stem in enumerate(stems,1):
                    doc.add_paragraph(f"Q{idx}. {stem}")
                    opts=make_mcq_options(stem,week)
                    for letter,text,is_correct in opts:
                        p=doc.add_paragraph(f"   {letter}. {text}")
                        for run in p.runs: run.font.size=Pt(11)
                doc.add_heading("Answer Key",level=1)
                doc.add_paragraph(", ".join([f"Q{q} → {a}" for q,a in answer_key]))
                bio=io.BytesIO(); doc.save(bio); bio.seek(0); return bio
            st.download_button("⬇️ Export to Word (DOCX)",data=build_docx(),file_name=f"ADI_{mode}_W{week}_L{lesson}.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
        else:
            st.info("Other modes (Skills, Activities, Revision) output tasks instead of MCQs.")
    else:
        st.info("Upload resources, set Week/Lesson, pick a mode, then click Generate.")
    st.markdown("</div>", unsafe_allow_html=True)

# Conversation
st.markdown("### 💬 Conversation")
st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])
if prompt:=st.chat_input("Ask ADI Builder…"):
    st.session_state["messages"].append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(prompt)
    resp="Got it. Use Generate for structured drafts, or tell me what to refine."
    st.session_state["messages"].append({"role":"assistant","content":resp})
    with st.chat_message("assistant"): st.markdown(resp)
st.markdown("</div>", unsafe_allow_html=True)

# Crash guards
problems=[]
if run:
    if ebook_file and getattr(ebook_file,"size",0)>25*1024*1024: problems.append("eBook exceeds 25MB")
    if ppt_file and not ppt_file.name.lower().endswith(".pptx"): problems.append("Slides must be .pptx")
if problems: st.warning("\n".join([f"• {p}" for p in problems]))
