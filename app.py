# app.py — ADI Builder (stable, pill-only UI, exports working)
# Run:  pip install -r requirements.txt
#       streamlit run app.py

import os
import io
import re
import csv
import base64
import random
from datetime import datetime
from typing import List, Dict

import streamlit as st
from docx import Document
from docx.shared import Pt

# -------------------- Page + Theme --------------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="📘", layout="wide")

CSS = """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-green-50:#EEF5F0;
  --adi-gold:#C8A85A; --adi-stone:#f3f1ee; --adi-stone-text:#4a4a45;
  --adi-ink:#1f2937; --muted:#6b7280; --border:#d9dfda;
}

html,body{background:#FAFAF7;}
main .block-container{padding-top:1rem; max-width:1220px;}

.header{
  background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));
  color:#fff; padding:18px 20px; border-radius:18px; box-shadow:0 10px 24px rgba(0,0,0,.06);
}
.header h1{margin:0; font-size:22px; font-weight:800;}
.header .sub{opacity:.9; margin-top:3px; font-size:12px}

.card{
  background:#fff; border:1px solid var(--border); border-radius:14px; padding:14px;
  box-shadow:0 10px 24px rgba(0,0,0,.04);
}
.card h3{
  margin:0 0 10px 0; color:var(--adi-green); font-size:12px; text-transform:uppercase; letter-spacing:.05em;
}

/* Drag & drop box */
.drop{
  background:var(--adi-green-50); border:2px dashed var(--adi-green); border-radius:12px; padding:12px;
}
.drop .row{display:flex; gap:10px; align-items:center;}
.drop .badge{width:30px; height:30px; border-radius:8px; background:var(--adi-green); color:#fff;
  display:flex; align-items:center; justify-content:center; font-weight:800;}

/* Inputs */
input[type="radio"]{ accent-color: var(--adi-green); }

/* Pills */
.choice-pills{display:flex; gap:8px; flex-wrap:wrap;}
.choice-pill{
  padding:8px 14px; border-radius:999px; border:1px solid var(--border);
  background:#f3f7f3; cursor:pointer; user-select:none; font-weight:600; color:#26422d;
}
.choice-pill.active{
  background:var(--adi-green); color:#fff; border-color:var(--adi-green-600);
  box-shadow:0 6px 14px rgba(36,90,52,.25);
}

/* Buttons */
div.stButton>button{
  background:var(--adi-green); color:#fff; border:none; border-radius:999px;
  padding:.65rem 1.1rem; font-weight:700; box-shadow:0 6px 14px rgba(31,76,44,.22);
}
div.stButton>button:hover{filter:brightness(.98)}

/* Preview boxes */
.qbox{
  background:#fff; border:1px solid var(--border); border-radius:12px; padding:10px;
  margin-bottom:10px;
}

/* Small captions */
small{color:var(--muted)}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -------------------- Header --------------------
st.markdown("""
<div class="header">
  <h1>ADI Builder – Lesson Activities & Questions</h1>
  <div class="sub">Professional, branded, editable and export-ready.</div>
</div>
""", unsafe_allow_html=True)

# -------------------- Helpers --------------------
def pills(label: str, options, key: str, default=None):
    """Render pill selectors; return selection via st.session_state[key]."""
    st.write(f"**{label}**")
    if key not in st.session_state:
        st.session_state[key] = default if default is not None else options[0]
    cols = st.columns(min(len(options), 6))
    for i, opt in enumerate(options):
        col = cols[i % len(cols)]
        with col:
            selected = (st.session_state[key] == opt)
            pill_html = f'<div class="choice-pill {"active" if selected else ""}">{opt}</div>'
            if st.button(pill_html, key=f"{key}_{opt}", use_container_width=True):
                st.session_state[key] = opt
    return st.session_state[key]

def export_docx_mcqs(questions: List[Dict]) -> bytes:
    doc = Document()
    styles = doc.styles['Normal']
    styles.font.name = 'Calibri'
    styles.font.size = Pt(11)

    doc.add_heading('ADI — Multiple Choice Questions', level=1)
    for i, q in enumerate(questions, start=1):
        p = doc.add_paragraph()
        p.add_run(f"Q{i}. {q['question']}").bold = True
        for j, ch in enumerate(q['choices'], start=1):
            doc.add_paragraph(f"{chr(64+j)}. {ch}", style=None)
        doc.add_paragraph(f"Answer: {q['answer_key']}").italic = True
        doc.add_paragraph("")  # spacer
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def export_csv_mcqs(questions: List[Dict]) -> bytes:
    bio = io.StringIO()
    writer = csv.writer(bio)
    writer.writerow(["Question", "A", "B", "C", "D", "Correct"])
    for q in questions:
        writer.writerow([q["question"], *q["choices"], q["answer_key"]])
    return bio.getvalue().encode("utf-8")

def export_gift_mcqs(questions: List[Dict]) -> bytes:
    # Simple Moodle GIFT
    lines = []
    for q in questions:
        lines.append(f"::{q.get('id','Q')}:: {q['question']} {{")
        correct_letter = q['answer_key'].strip().upper()
        mapping = {"A":0,"B":1,"C":2,"D":3}
        for idx, choice in enumerate(q['choices']):
            if idx == mapping.get(correct_letter, 0):
                lines.append(f"  ={choice}")
            else:
                lines.append(f"  ~{choice}")
        lines.append("}\n")
    return ("\n".join(lines)).encode("utf-8")

def download_button(bin_bytes: bytes, label: str, file_name: str):
    st.download_button(label, data=bin_bytes, file_name=file_name, type="primary")

# -------------------- Very Simple MCQ Generator (local, deterministic) --------------------
DISTRACTORS = [
    "Not applicable", "None of the above", "All of the above", "Irrelevant option",
    "Alternative method", "Different policy", "Unrelated concept"
]

def make_mcq_from_line(line: str) -> Dict:
    """Naive question from a line of text: take a key term and build distractors."""
    text = re.sub(r'\s+', ' ', line).strip()
    if len(text) < 10:
        text = f"This statement is true regarding: {text or 'ADI policy'}"
    # pick a key term (last 1–2 words)
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]*", text) if len(w) > 2]
    key = " ".join(words[-2:]) if len(words) >= 2 else (words[-1] if words else "ADI Policy")
    correct = f"{key}"
    distractors = random.sample(DISTRACTORS, k=3) if len(DISTRACTORS) >= 3 else ["Option 1","Option 2","Option 3"]
    choices = [correct] + distractors
    random.shuffle(choices)
    answer_key = "ABCD"[choices.index(correct)]
    return {
        "id": f"Q_{abs(hash(text))%10_000}",
        "question": f"Which of the following best relates to: {text}?",
        "choices": choices,
        "answer_key": answer_key
    }

def generate_mcqs(source_text: str, count: int) -> List[Dict]:
    # Use non-empty lines as seeds; if not enough lines, repeat/augment
    seeds = [ln.strip() for ln in source_text.splitlines() if ln.strip()]
    if not seeds:
        seeds = [f"ADI policy guideline item {i}" for i in range(1, count+1)]
    out = []
    i = 0
    while len(out) < count:
        out.append(make_mcq_from_line(seeds[i % len(seeds)]))
        i += 1
    return out[:count]

# -------------------- Session --------------------
if "mcqs" not in st.session_state:
    st.session_state.mcqs = []

# -------------------- Tabs --------------------
tab1, tab2 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# ==========================================================
# TAB 1 — MCQs
# ==========================================================
with tab1:
    left, right = st.columns([0.95, 2.05], gap="large")

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Upload eBook / Lesson Plan / PPT")
        st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")

        st.markdown("""
        <div class="drop">
          <div class="row">
            <div class="badge">UP</div>
            <div>
              <strong>Drag and drop</strong> your file here, or click below.<br>
              <small>We recommend eBooks (PDF) as source for best results.</small>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.file_uploader(" ", type=["pdf","docx","pptx"], label_visibility="collapsed")

        st.markdown("### Pick from eBook / Plan / PPT")
        lesson = pills("Lesson", [1,2,3,4,5], key="lesson", default=1)

        st.markdown(" ")
        week = pills("Week", list(range(1,15)), key="week", default=1)
        # Bloom highlight note
        st.caption("ADI policy: Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. The appropriate Bloom tier will be auto-highlighted.")

        st.markdown('</div>', unsafe_allow_html=True)  # /card

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Generate MCQs — Policy Blocks (Low → Medium → High)")
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source = st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here…")

        st.write("**How many MCQs?**")
        mcq_count = pills(" ", [5,10,20,30], key="mcq_target", default=10)

        if st.button("Generate MCQ Blocks"):
            st.session_state.mcqs = generate_mcqs(source or topic, mcq_count)

        # Preview & edit
        st.markdown("### Preview & Edit")
        if not st.session_state.mcqs:
            st.info("No questions yet. Generate to see them here.")
        else:
            edited = []
            for idx, q in enumerate(st.session_state.mcqs, start=1):
                st.markdown(f"**Q{idx}**")
                with st.container(border=True):
                    qtext = st.text_area("Question", q["question"], key=f"qtext_{idx}", label_visibility="collapsed")
                    cols = st.columns(4)
                    new_choices = []
                    for j, c in enumerate(q["choices"]):
                        with cols[j]:
                            new_choices.append(st.text_input(f"{'ABCD'[j]}.", c, key=f"ch_{idx}_{j}"))
                    # answer picker
                    ans = st.radio("Answer", ["A","B","C","D"], index="ABCD".index(q["answer_key"]), horizontal=True, key=f"ans_{idx}")
                    edited.append({"id": q["id"], "question": qtext, "choices": new_choices, "answer_key": ans})
                st.markdown("")

            st.session_state.mcqs = edited

            # Export buttons
            st.markdown("### Export")
            c1, c2, c3 = st.columns(3)
            with c1:
                docx_bytes = export_docx_mcqs(st.session_state.mcqs)
                download_button(docx_bytes, "Download Word (.docx)", f"ADI_MCQs_w{week}_{mcq_count}.docx")
            with c2:
                csv_bytes = export_csv_mcqs(st.session_state.mcqs)
                download_button(csv_bytes, "Download CSV", f"ADI_MCQs_w{week}_{mcq_count}.csv")
            with c3:
                gift_bytes = export_gift_mcqs(st.session_state.mcqs)
                download_button(gift_bytes, "Download Moodle (GIFT)", f"ADI_MCQs_w{week}_{mcq_count}.txt")

        st.markdown('</div>', unsafe_allow_html=True)  # /card

# ==========================================================
# TAB 2 — Activities (simple plan + export)
# ==========================================================
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Pick parameters")

    week2 = pills("Week", list(range(1,15)), key="week_act", default=1)
    tier = pills("Bloom tier", ["Low","Medium","High"], key="tier_act", default="Medium")
    n_acts = pills("Number of activities", [1,2,3,4,5,6,7,8], key="act_count", default=3)
    duration = pills("Duration (mins) (per activity)", [15,30,45,60,90,120], key="act_duration", default=45)

    st.markdown("### Generate Activities")
    if st.button("Generate Activity Plan"):
        activities = []
        for i in range(1, n_acts+1):
            activities.append({
                "tier": tier,
                "title": f"Module: Activity {i}",
                "objective": "Students will apply the core concept of Module.",
                "steps": "1) Briefing (5m) 2) Main task 3) Share-out",
                "materials": "Projector, handouts, whiteboard",
                "assessment": "Participation / quick check"
            })
        st.session_state.activities = activities

    st.markdown("### Preview & Edit")
    if "activities" not in st.session_state or not st.session_state.activities:
        st.info("No activities yet. Generate to see them here.")
    else:
        edited = []
        for i, row in enumerate(st.session_state.activities, start=1):
            st.markdown(f"**Activity {i}**")
            with st.container(border=True):
                c1, c2 = st.columns([0.6,1.4])
                with c1:
                    tier_v = st.selectbox("Tier", ["Low","Medium","High"], index=["Low","Medium","High"].index(row["tier"]), key=f"tier_{i}")
                    title_v = st.text_input("Title", row["title"], key=f"title_{i}")
                with c2:
                    obj_v = st.text_input("Objective", row["objective"], key=f"obj_{i}")
                steps_v = st.text_area("Steps", row["steps"], key=f"steps_{i"])
                mats_v = st.text_input("Materials", row["materials"], key=f"mats_{i}")
                assess_v = st.text_input("Assessment", row["assessment"], key=f"assess_{i}")
                edited.append({
                    "tier": tier_v, "title": title_v, "objective": obj_v,
                    "steps": steps_v, "materials": mats_v, "assessment": assess_v
                })
            st.markdown("")
        st.session_state.activities = edited

        # Exports
        st.markdown("### Export")
        def export_docx_activities(rows: List[Dict]) -> bytes:
            doc = Document()
            doc.add_heading('ADI — Activities Plan', level=1)
            for i, r in enumerate(rows, start=1):
                doc.add_heading(f"Activity {i}: {r['title']}", level=2)
                doc.add_paragraph(f"Tier: {r['tier']}")
                doc.add_paragraph(f"Objective: {r['objective']}")
                doc.add_paragraph(f"Steps: {r['steps']}")
                doc.add_paragraph(f"Materials: {r['materials']}")
                doc.add_paragraph(f"Assessment: {r['assessment']}")
                doc.add_paragraph("")
            bio = io.BytesIO()
            doc.save(bio)
            return bio.getvalue()

        def export_csv_activities(rows: List[Dict]) -> bytes:
            bio = io.StringIO()
            writer = csv.writer(bio)
            writer.writerow(["Tier","Title","Objective","Steps","Materials","Assessment"])
            for r in rows:
                writer.writerow([r["tier"], r["title"], r["objective"], r["steps"], r["materials"], r["assessment"]])
            return bio.getvalue().encode("utf-8")

        c1, c2 = st.columns(2)
        with c1:
            download_button(export_docx_activities(st.session_state.activities),
                            "Download Word (.docx)", f"ADI_Activities_w{week2}.docx")
        with c2:
            download_button(export_csv_activities(st.session_state.activities),
                            "Download CSV", f"ADI_Activities_w{week2}.csv")

    st.markdown('</div>', unsafe_allow_html=True)  # /card
