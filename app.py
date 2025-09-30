

# ADI Builder — Streamlit (Render-ready v3)
from io import BytesIO
from typing import List, Dict, Tuple
import streamlit as st
from docx import Document
from pptx import Presentation
from pypdf import PdfReader

st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="✅", layout="wide")

ADI_GREEN = "#245a34"
CHIP_BG = "#e8efe9"
CHIP_TXT = "#1f3b2a"
SECTION_BG = "#f6f5f2"
st.markdown(f"""
<style>
.stApp {{ background: {SECTION_BG}; }}
.adi-hero {{ background:{ADI_GREEN}; color:#fff; padding:24px; border-radius:24px; font-weight:700; font-size:28px; }}
.chip {{ display:inline-block; padding:8px 14px; margin:6px 8px 0 0; border-radius:999px; background:{CHIP_BG}; color:{CHIP_TXT};
         border:1px solid rgba(0,0,0,0.05); font-weight:600 }}
.subtle {{ color:#666 }}
.card {{ padding:16px; border:1px solid #e6e6e6; border-radius:14px; background:#fff }}
</style>
""", unsafe_allow_html=True)

BLOOM = {
    "Low": ["define", "identify", "list", "recall", "describe", "label"],
    "Medium": ["apply", "demonstrate", "solve", "illustrate"],
    "High": ["evaluate", "synthesize", "design", "justify"],
}

def policy_for_week(week:int)->str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    return "High"

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

def extract_text(upload)->Tuple[str,str]:
    if not upload: return "", ""
    name = upload.name.lower()
    if name.endswith(".pdf"): return read_pdf(upload), "pdf"
    if name.endswith(".docx"): return read_docx(upload), "docx"
    if name.endswith(".pptx"): return read_pptx(upload), "pptx"
    return "", ""

def generate_mcqs(topic:str, verbs:List[str], blocks:int=5)->List[Dict]:
    t = topic or "the lesson topic"
    out = []
    for i in range(blocks):
        v = verbs[i % max(1,len(verbs))] if verbs else "explain"
        out.append({
            "question": f"{v.capitalize()} {t}: Which option best fits?",
            "options": [
                f"Correct {v} response about {t}",
                f"Irrelevant detail about {t}",
                f"Common misconception about {t}",
                f"Partially true but incomplete about {t}",
            ],
            "answer_index": 0,
        })
    return out

def gift_from_mcqs(mcqs:List[Dict])->bytes:
    lines = []
    for i, q in enumerate(mcqs, 1):
        correct = q["options"][q["answer_index"]]
        distractors = [o for j,o in enumerate(q["options"]) if j!=q["answer_index"]]
        lines.append(f"::Q{i}:: {q['question']} {{ = {correct} ~ {distractors[0]} ~ {distractors[1]} ~ {distractors[2]} }}")
    return ("\n\n".join(lines)).encode("utf-8")

def docx_mcq(mcqs:List[Dict], title:str)->bytes:
    d = Document(); d.add_heading(title, 1)
    letters = ["A","B","C","D"]
    for i, q in enumerate(mcqs, 1):
        d.add_paragraph(f"{i}. {q['question']}")
        for j,opt in enumerate(q["options"]):
            d.add_paragraph(f"   {letters[j]}) {opt}")
    bio=BytesIO(); d.save(bio); return bio.getvalue()

def docx_answer_key(mcqs:List[Dict])->bytes:
    d = Document(); d.add_heading("Answer Key", 1)
    letters = ["A","B","C","D"]
    for i, q in enumerate(mcqs, 1):
        d.add_paragraph(f"Q{i}: {letters[q['answer_index']]}")
    bio=BytesIO(); d.save(bio); return bio.getvalue()

def generate_activities(topic:str, verbs:List[str], n:int=3, mins:int=45)->List[str]:
    t = topic or "the lesson topic"
    bank = [
        "Think-Pair-Share explaining {}.",
        "Create an infographic comparing aspects of {}.",
        "Solve a case applying {} to a real scenario.",
        "Critique a sample answer about {} and suggest improvements.",
        "Design a short quiz to assess {}.",
        "Construct a concept map of {}."
    ]
    out = []
    for i in range(n):
        base = bank[i % len(bank)].format(t)
        verb = (verbs[i % max(1,len(verbs))] if verbs else "explain")
        out.append(f"{base} (Use verb: {verb}; ~{mins} min)")
    return out

def docx_activities(acts:List[str])->bytes:
    d = Document(); d.add_heading("Activity Sheet", 1)
    for i, a in enumerate(acts, 1): d.add_paragraph(f"{i}. {a}")
    bio=BytesIO(); d.save(bio); return bio.getvalue()

# Session defaults BEFORE widgets
if "week" not in st.session_state: st.session_state["week"]=1
if "lesson" not in st.session_state: st.session_state["lesson"]=1
if "bloom_tier" not in st.session_state: st.session_state["bloom_tier"]=policy_for_week(st.session_state["week"])
if "verbs_sel" not in st.session_state: st.session_state["verbs_sel"]=BLOOM[st.session_state["bloom_tier"]][:4]
if "mcqs" not in st.session_state: st.session_state["mcqs"]=[]
if "acts" not in st.session_state: st.session_state["acts"]=[]
if "acts_count" not in st.session_state: st.session_state["acts_count"]=3
if "act_mins" not in st.session_state: st.session_state["act_mins"]=45

# Sidebar
with st.sidebar:
    st.markdown('<div class="card"><strong>Upload eBook / Lesson Plan / PPT</strong><br>'
                '<span class="subtle">PDF · DOCX · PPTX (≤200MB)</span></div>', unsafe_allow_html=True)
    upload = st.file_uploader(" ", type=["pdf","docx","pptx"], label_visibility="collapsed")
    st.markdown('<div class="card"><strong>Pick from eBook / Plan / PPT</strong></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        lesson = st.selectbox("Lesson", [1,2,3,4,5], index=st.session_state["lesson"]-1)
    with c2:
        week = st.selectbox("Week", list(range(1,15)), index=st.session_state["week"]-1)
    if lesson != st.session_state["lesson"] or week != st.session_state["week"]:
        st.session_state["lesson"]=lesson
        st.session_state["week"]=week
        st.session_state["bloom_tier"]=policy_for_week(week)
        st.session_state["verbs_sel"]=BLOOM[st.session_state["bloom_tier"]][:4]
        st.rerun()
    st.markdown('<div class="card"><strong>Activity Parameters</strong></div>', unsafe_allow_html=True)
    a1,a2 = st.columns(2)
    with a1:
        st.session_state["acts_count"]=st.number_input("Activities",1,10,st.session_state["acts_count"],1)
    with a2:
        st.session_state["act_mins"]=st.number_input("Duration (mins)",10,120,st.session_state["act_mins"],5)

# Hero
st.markdown('<div class="adi-hero">ADI Builder — Lesson Activities & Questions'
            '<span class="subtle" style="font-weight:400;font-size:14px;margin-left:10px">Professional, branded, export‑ready.</span>'
            '</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

extracted, kind = extract_text(upload)
topic_hint = (extracted.split("\n")[0][:120] if extracted else "")

with tab1:
    st.subheader("Generate MCQs — Policy Blocks (Low → Medium → High)")
    topic = st.text_input("Topic / Outcome (optional)", value="Module description, knowledge & skills outcomes")
    st.caption(f"Bloom focus for Week {st.session_state['week']}: **{st.session_state['bloom_tier']}**")
    src = st.text_area("Source text (optional, editable)", value="", height=180,
                       placeholder="Paste or edit source text here...")
    st.markdown("**Bloom’s verbs (ADI Policy)**")
    chips = []
    for tier in ["Low","Medium","High"]:
        for v in BLOOM[tier]:
            chips.append(f'<span class="chip">{v}</span>')
        chips.append("<br/>")
    st.markdown("".join(chips), unsafe_allow_html=True)
    blocks = st.number_input("How many MCQ blocks? (×3 questions)", 1, 30, 1, 1)
    verbs = st.multiselect("Choose options", options=sorted(set(sum(BLOOM.values(), []))),
                           default=st.session_state["verbs_sel"], key="verbs_sel")
    if st.button("Generate MCQ Blocks"):
        st.session_state["mcqs"] = generate_mcqs(topic or topic_hint or "topic", verbs, blocks=int(blocks)*3)
        st.success("MCQs generated.")
    mcqs = st.session_state["mcqs"]
    if mcqs:
        letters = ["A","B","C","D"]
        for i,q in enumerate(mcqs[:10],1):
            st.markdown(f"**Q{i}.** {q['question']}")
            for j,opt in enumerate(q["options"]):
                st.write(f"- {letters[j]}) {opt}")
        d1,d2,d3 = st.columns(3)
        with d1:
            st.download_button("⬇️ MCQ Paper (.docx)", data=docx_mcq(mcqs,"MCQ Paper"), file_name="mcq_paper.docx")
        with d2:
            st.download_button("⬇️ Answer Key (.docx)", data=docx_answer_key(mcqs), file_name="answer_key.docx")
        with d3:
            st.download_button("⬇️ Moodle GIFT (.gift)", data=gift_from_mcqs(mcqs), file_name="mcq_questions.gift")

with tab2:
    st.subheader("Skills Activities")
    verbs_for_acts = st.multiselect("Preferred action verbs",
                                    BLOOM["Medium"] + BLOOM["High"],
                                    default=["apply","demonstrate","evaluate","design"],
                                    key="verbs_for_acts")
    if st.button("Pull → Activities"):
        st.session_state["acts"] = generate_activities(topic_hint or topic, verbs_for_acts,
                                                       n=int(st.session_state["acts_count"]),
                                                       mins=int(st.session_state["act_mins"]))
        st.success("Activities generated.")
    acts = st.session_state["acts"]
    if acts:
        for i,a in enumerate(acts,1): st.write(f"{i}. {a}")
        st.download_button("⬇️ Activity Sheet (.docx)",
                           data=docx_activities(acts), file_name="activity_sheet.docx")
