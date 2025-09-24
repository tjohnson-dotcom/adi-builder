# app.py — ADI Builder (MCQs + Activities, polished ADI look & exports)
# Run:  streamlit run app.py

import re
import textwrap
from io import BytesIO
from datetime import datetime
from typing import List, Tuple

import streamlit as st
from docx import Document
from docx.shared import Pt, Inches
from lxml import etree

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    page_icon="📘",
    layout="wide",
)

# =========================
# Theme / CSS
# =========================
ADI_CSS = """
<style>
:root{
  --adi-green:#245a34;
  --adi-green-600:#1f4c2c;
  --adi-green-50:#eef5f0;
  --adi-stone:#f5f4f2;
  --adi-stone-600:#6a6a63;
  --adi-gold:#c8a85a;
  --border:#dfe6e2;
  --card:#ffffff;
  --shadow:0 10px 24px rgba(0,0,0,.06);
  --radius:18px;
  --pill:999px;
}

/* Page container */
main .block-container{max-width:1260px; padding-top:16px;}

/* Hero bar */
.adi-hero{
  background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));
  color:#fff; border-radius:18px; padding:14px 18px; box-shadow:var(--shadow);
  display:flex; align-items:center; gap:12px; margin-bottom:10px;
}
.adi-hero .title{font-weight:800; font-size:18px;}
.adi-hero .sub{opacity:.95; font-size:12px;}

/* Cards */
.adi-card{
  background:var(--card); border:1px solid var(--border); border-radius:16px;
  box-shadow:var(--shadow); padding:12px 14px; margin-bottom:12px;
}
.adi-card h3{
  margin:0 0 8px 0; color:var(--adi-green); font-size:12px;
  text-transform:uppercase; letter-spacing:.05em;
}

/* Upload box */
.adi-upload{
  border:2px dashed var(--adi-green); background:var(--adi-green-50);
  border-radius:14px; padding:12px 14px;
}

/* Inputs */
.stTextInput>div>div>input,
.stTextArea textarea,
.stNumberInput input{
  border:2px solid var(--adi-green) !important; border-radius:12px !important;
}
.stTextInput>div>div>input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus{
  outline:none !important; border-color:var(--adi-green-600) !important;
  box-shadow:0 0 0 3px rgba(36,90,52,.25) !important;
}

/* Pill selectors (buttons) */
.pill-row{display:flex; gap:8px; flex-wrap:wrap;}
.pill{
  border-radius:999px; padding:8px 14px; border:1px solid var(--border);
  background:var(--stone, var(--adi-stone)); cursor:pointer; user-select:none;
  transition:all .15s; color:#1e1e1b;
}
.pill:hover{filter:brightness(.98)}
.pill.selected{ background:var(--adi-green); color:#fff; border-color:var(--adi-green-600)}

/* Two styles: lesson (solid green), week (stone until active) */
.pill-lesson{ background:var(--adi-green); color:#fff; border:1px solid var(--adi-green-600); }
.pill-lesson.selected{ background:var(--adi-green);}

.pill-week{ background:var(--adi-stone); color:#1e1e1b; }
.pill-week.selected{ background:var(--adi-green); color:#fff; }

/* Bloom chips */
.chips{ display:flex; gap:8px; flex-wrap:wrap; margin-top:6px;}
.chip{ padding:6px 10px; border-radius:999px; font-size:12px; border:1px solid #e0e2df;}
.chip.low{ background:#eaf5ec; color:#1f4c2c;}
.chip.med{ background:#f8f3e8; color:#6a4b2d;}
.chip.high{ background:#f3f1ee; color:#4a4a45;}
.chip.active{ outline:3px solid rgba(36,90,52,.25); }

/* Buttons */
div.stButton>button{
  background:var(--adi-green); color:#fff; border:none;
  border-radius:999px; padding:.6rem 1.1rem; font-weight:600;
  box-shadow:0 4px 12px rgba(31,76,44,.18); transition:all .2s;
}
div.stButton>button:hover{ filter:brightness(.97); box-shadow:0 0 0 3px rgba(200,168,90,.35); }

.small-note{ font-size:12px; color:#5d655e; margin-top:4px;}
.card-subtle{ padding:10px; background:#fafaf8; border:1px solid var(--border); border-radius:12px;}
.hr{ height:1px; background:#ecefeb; margin:8px 0 12px 0;}
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# =========================
# Helpers
# =========================
LOW_VERBS   = ["define","identify","list","recall","describe","label"]
MED_VERBS   = ["apply","demonstrate","solve","illustrate"]
HIGH_VERBS  = ["evaluate","synthesize","design","justify"]

def bloom_tier_for_week(week:int)->str:
    if week<=4: return "low"
    if week<=9: return "med"
    return "high"

def split_sentences(text:str)->List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text: return []
    # very simple sentence split
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]

def make_mcq_from_sentence(s:str, tier:str, idx:int)->Tuple[str,List[str],int]:
    """
    Extremely lightweight MCQ builder to make the app usable offline.
    """
    stem = s
    if len(stem)<50:
        stem = f"Based on the material, which option best fits: {s}"
    verb_pool = {"low":LOW_VERBS,"med":MED_VERBS,"high":HIGH_VERBS}[tier]
    correct = f"{verb_pool[idx%len(verb_pool)].capitalize()} — {stem[:60]}…"
    distractors = [
        f"{verb_pool[(idx+1)%len(verb_pool)].capitalize()} something else",
        f"{verb_pool[(idx+2)%len(verb_pool)].capitalize()} alternative",
        f"{verb_pool[(idx+3)%len(verb_pool)].capitalize()} unrelated"
    ]
    options = [correct] + distractors
    answer_index = 0
    return stem, options, answer_index

def build_blocks(n_blocks:int, week:int, source_text:str)->List[dict]:
    sentences = split_sentences(source_text) or [
        "Policies set the expectations and boundaries for acceptable use.",
        "Skills are demonstrated through applied tasks and performance.",
        "Knowledge provides the foundation for judgement and action."
    ]
    tier = bloom_tier_for_week(week)
    blocks=[]
    s_idx=0
    for b in range(n_blocks):
        q=[]
        for i in range(3):
            s = sentences[s_idx%len(sentences)]
            stem, options, correct = make_mcq_from_sentence(s,tier, i+b*3)
            q.append({"stem":stem, "options":options, "answer":correct})
            s_idx+=1
        blocks.append({"tier":tier, "questions":q})
    return blocks

def export_docx(blocks:List[dict], topic:str, week:int)->bytes:
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.add_heading('ADI — MCQ Pack', level=1)
    if topic:
        p = doc.add_paragraph()
        p.add_run('Topic: ').bold=True
        p.add_run(topic)
    p = doc.add_paragraph()
    p.add_run('Week: ').bold=True
    p.add_run(str(week))
    doc.add_paragraph()
    qn=1
    for bi,block in enumerate(blocks, start=1):
        doc.add_heading(f"Block {bi}  (Bloom: {block['tier'].capitalize()})", level=2)
        for q in block["questions"]:
            doc.add_paragraph(f"{qn}. {q['stem']}")
            letters=["A","B","C","D"]
            for i,opt in enumerate(q["options"]):
                doc.add_paragraph(f"   {letters[i]}. {opt}")
            # answer
            correct_letter = letters[q['answer']]
            doc.add_paragraph(f"   Answer: {correct_letter}")
            doc.add_paragraph()
            qn+=1
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()

def export_moodle_xml(blocks:List[dict], topic:str)->bytes:
    """
    Minimal Moodle XML for MCQs (multichoice, single).
    """
    quiz = etree.Element("quiz")
    qid = 1
    for block in blocks:
        for q in block["questions"]:
            q_el = etree.SubElement(quiz, "question", type="multichoice")
            name = etree.SubElement(q_el, "name")
            text = etree.SubElement(name, "text")
            text.text = f"Q{qid}: {topic or 'MCQ'}"

            qt = etree.SubElement(q_el, "questiontext", format="html")
            qt_text = etree.SubElement(qt, "text")
            qt_text.text = etree.CDATA(q["stem"])

            etree.SubElement(q_el,"single").text = "true"
            etree.SubElement(q_el,"shuffleanswers").text = "true"
            etree.SubElement(q_el,"answernumbering").text = "abc"

            for i,opt in enumerate(q["options"]):
                fraction = "100" if i==q["answer"] else "0"
                ans = etree.SubElement(q_el, "answer", fraction=fraction", format="html")
                atext = etree.SubElement(ans,"text")
                atext.text = etree.CDATA(opt)
            qid+=1

    xml_bytes = etree.tostring(quiz, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return xml_bytes

# =========================
# Header
# =========================
st.markdown("""
<div class="adi-hero">
  <div class="title">ADI Builder — Lesson Activities & Questions</div>
  <div class="sub">Professional, branded, editable and export-ready.</div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab_choice = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])[0]

# We will focus MCQ tab (as requested)
with tab_choice:
    left, right = st.columns([1,1.4], gap="large")

    with left:
        # Upload card
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("### Upload eBook / Lesson Plan / PPT")
        st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
        st.markdown('<div class="adi-upload">Drag and drop your file here, or use the button below.<br><span class="small-note">We recommend eBooks (PDF) as source for best results.</span></div>', unsafe_allow_html=True)
        st.file_uploader(" ", type=["pdf","docx","pptx"], label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        # Lesson/Week pick
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("### Pick from eBook / Plan / PPT")
        st.markdown("**Lesson**")
        if "lesson" not in st.session_state: st.session_state.lesson=1
        cols = st.columns(6)
        for i,c in enumerate(cols, start=1):
            with c:
                btn = st.button(str(i),
                                key=f"lesson_{i}",
                                use_container_width=True,
                                help="Select lesson")
                if btn:
                    st.session_state.lesson = i
        # turn the lesson buttons into pills via CSS-ish: we'll just show current
        st.caption(f"Selected lesson: **{st.session_state.lesson}**")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown("**Week**")
        if "week" not in st.session_state: st.session_state.week=1
        row1 = st.columns(7)
        row2 = st.columns(7)
        for i in range(1,8):
            with row1[i-1]:
                if st.button(str(i), key=f"week_{i}", use_container_width=True):
                    st.session_state.week=i
        for i in range(8,15):
            with row2[i-8]:
                if st.button(str(i), key=f"week_{i}", use_container_width=True):
                    st.session_state.week=i
        st.caption("ADI policy: Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. Bloom auto-highlights in generator.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Reference parameters (used for skills later; we keep here as a tidy card)
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("### Activity Parameters (reference)")
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Activities (for Activities tab)", min_value=1, value=3, step=1, key="act_cnt")
        with c2:
            st.number_input("Duration mins (for Activities tab)", min_value=5, value=45, step=5, key="act_dur")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        # Generator card
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("### Generate MCQs — Policy Blocks (Low → Medium → High)")
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source_text = st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here…")
        st.markdown(f'<div class="card-subtle">Bloom focus for Week {st.session_state.week}: <b>{bloom_tier_for_week(st.session_state.week).capitalize()}</b></div>', unsafe_allow_html=True)

        # Bloom focus chips
        st.markdown("#### Bloom’s focus")
        bcols = st.columns(3)
        active_tier = bloom_tier_for_week(st.session_state.week)
        with bcols[0]:
            st.caption("Low (Remember/Understand)")
            st.markdown(
                '<div class="chips">' +
                ''.join([f'<span class="chip low {"active" if active_tier=="low" else ""}">{v}</span>' for v in LOW_VERBS]) +
                '</div>', unsafe_allow_html=True
            )
        with bcols[1]:
            st.caption("Medium (Apply/Analyze)")
            st.markdown(
                '<div class="chips">' +
                ''.join([f'<span class="chip med {"active" if active_tier=="med" else ""}">{v}</span>' for v in MED_VERBS]) +
                '</div>', unsafe_allow_html=True
            )
        with bcols[2]:
            st.caption("High (Evaluate/Create)")
            st.markdown(
                '<div class="chips">' +
                ''.join([f'<span class="chip high {"active" if active_tier=="high" else ""}">{v}</span>' for v in HIGH_VERBS]) +
                '</div>', unsafe_allow_html=True
            )

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown("#### Quick pick")

        q1,q2,q3,q4 = st.columns(4)
        if q1.button("5"): st.session_state["mcq_blocks"]=5
        if q2.button("10"): st.session_state["mcq_blocks"]=10
        if q3.button("20"): st.session_state["mcq_blocks"]=20
        if q4.button("30"): st.session_state["mcq_blocks"]=30
        n_blocks = st.number_input("Or enter a custom number of blocks", min_value=1, value=st.session_state.get("mcq_blocks", 10), step=1, key="mcq_blocks")

        gen = st.button("Generate MCQ Blocks")
        st.markdown('</div>', unsafe_allow_html=True)

        # Preview & downloads
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("### Preview & Download")
        if gen:
            blocks = build_blocks(n_blocks, st.session_state.week, source_text)
            st.session_state["blocks"] = blocks

        blocks = st.session_state.get("blocks")
        if not blocks:
            st.info("No MCQs yet. Choose lesson/week, select number of blocks, then click **Generate MCQ Blocks**.")
        else:
            # Show a compact preview
            for bi,block in enumerate(blocks, start=1):
                with st.expander(f"Block {bi} — Bloom: {block['tier'].capitalize()}"):
                    for qi,q in enumerate(block["questions"], start=1):
                        st.write(f"**Q{qi}.** {q['stem']}")
                        letters = ["A","B","C","D"]
                        for i,opt in enumerate(q["options"]):
                            st.write(f"- {letters[i]}. {opt}")
                        st.write(f"*Answer: {letters[q['answer']]}*")
                        st.write("---")

            # Downloads
            _, dmid, _ = st.columns([1,2,1])
            with dmid:
                docx_bytes = export_docx(blocks, topic, st.session_state.week)
                st.download_button(
                    "Download Word (.docx)",
                    data=docx_bytes,
                    file_name=f"adi_mcqs_w{st.session_state.week}_{n_blocks}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

                moodle_bytes = export_moodle_xml(blocks, topic)
                st.download_button(
                    "Download Moodle XML",
                    data=moodle_bytes,
                    file_name=f"adi_mcqs_w{st.session_state.week}_{n_blocks}.xml",
                    mime="application/xml",
                    use_container_width=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------
# (Optional) Activities tab – placeholder
# ------------------------------------------
# You can flesh this out later using the same palette/components.


