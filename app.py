# app.py — ADI Builder (clean, pill-based UI + Word/Moodle/CSV export)

import base64
import io
import os
from textwrap import dedent

import pandas as pd
import streamlit as st
from docx import Document
from docx.shared import Pt

# ──────────────────────────────────────────────────────────────────────────────
# Page & Brand
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

def _logo_data_uri(path="logo.png"):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return None

LOGO_URI = _logo_data_uri()

ADI_CSS = """
<style>
:root{
  --adi-green:#245a34;
  --adi-green-600:#1f4c2c;
  --adi-green-50:#eef5f0;
  --adi-gold:#C8A85A;
  --card:#ffffff;
  --border:#d9dfda;
  --muted:#6b7280;
  --shadow:0 10px 24px rgba(0,0,0,.06);
}

html, body { background:#FAFAF7; }
main .block-container{ max-width:1200px; padding-top:1rem; }

.adi-hero{
  background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));
  color:#fff; border-radius:20px; padding:16px 18px; box-shadow:var(--shadow);
  display:flex; align-items:center; gap:12px; margin-bottom:10px;
}
.adi-hero .logo{
  width:44px; height:44px; border-radius:10px; background:rgba(0,0,0,.08);
  display:flex; align-items:center; justify-content:center; overflow:hidden;
}
.adi-hero .logo img{ width:100%; height:100%; object-fit:contain; }
.adi-hero .title{ font-weight:800; font-size:20px; line-height:1.2; }
.adi-hero .sub{ font-size:12px; opacity:.9; margin-top:2px }

.adi-card{
  background:var(--card); border:1px solid var(--border); border-radius:16px;
  padding:14px; box-shadow:var(--shadow);
}

h3.section{
  margin:0 0 8px 0; color:var(--adi-green); font-size:13px; letter-spacing:.05em;
  text-transform:uppercase;
}

/* Pills */
.pills{ display:flex; flex-wrap:wrap; gap:8px; }
.pill{
  padding:8px 14px; border-radius:999px; border:1.5px solid var(--border);
  background:#f7faf7; cursor:pointer; user-select:none; font-weight:600;
  transition:all .15s; color:#243b2a; font-size:13px;
}
.pill:hover{ border-color:var(--adi-green); background:#eff6f1; }
.pill.active{
  background:var(--adi-green); color:#fff; border-color:var(--adi-green);
  box-shadow:0 6px 14px rgba(36,90,52,.25);
}

/* Upload box */
.upload-box{
  border:2px dashed var(--adi-green); background:var(--adi-green-50);
  border-radius:14px; padding:12px 14px; display:flex; align-items:center; gap:10px;
}
.upload-badge{
  width:36px; height:36px; border-radius:10px; background:var(--adi-green);
  color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800;
}

/* Inputs / textareas */
textarea, input, select{
  border:2px solid var(--adi-green) !important; border-radius:12px !important;
}
textarea:focus, input:focus, select:focus{
  outline:none !important; border-color:var(--adi-green-600) !important;
  box-shadow:0 0 0 3px rgba(36,90,52,.25) !important;
}

/* Buttons */
div.stButton > button{
  background:var(--adi-green); color:#fff; border:none; border-radius:999px;
  padding:.65rem 1.1rem; font-weight:700; box-shadow:0 4px 12px rgba(31,76,44,.20);
}
div.stButton > button:hover{ filter:brightness(.97); box-shadow:0 0 0 3px rgba(200,168,90,.35); }

/* Minor tabs spacing */
.stTabs [data-baseweb="tab-list"]{ gap:10px }
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

with st.container():
    st.markdown(
        f"""
        <div class="adi-hero">
          <div class="logo">{('<img src="'+LOGO_URI+'" />') if LOGO_URI else '<div style="color:#fff;font-weight:800">A</div>'}</div>
          <div>
            <div class="title">ADI Builder – Lesson Activities & Questions</div>
            <div class="sub">Professional, branded, editable and export-ready.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def bloom_for_week(w: int) -> str:
    if 1 <= w <= 4:  return "Low"
    if 5 <= w <= 9:  return "Medium"
    return "High"

def safe_text(x: str) -> str:
    return (x or "").strip()

def generate_mcqs(topic: str, src: str, total_questions: int, bloom: str):
    """Placeholder generator. Replace with your LLM later."""
    qs = []
    base = safe_text(topic) or "Module"
    info = safe_text(src)[:120] or "policy content"
    for i in range(1, total_questions + 1):
        stem = f"[{bloom}] {base}: Q{i} — based on {info}"
        correct = f"Correct answer {i}"
        opts = [correct, f"Option {i}-B", f"Option {i}-C", f"Option {i}-D"]
        shift = i % 4
        rotated = opts[shift:] + opts[:shift]
        correct_letter = ["A", "B", "C", "D"][(4 - shift) % 4]
        qs.append({"question":stem, "A":rotated[0], "B":rotated[1], "C":rotated[2], "D":rotated[3], "correct":correct_letter})
    return qs

def mcqs_to_docx(mcqs, title="ADI MCQs"):
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)
    doc.add_heading(title, level=1)
    for i, q in enumerate(mcqs, start=1):
        p = doc.add_paragraph()
        p.add_run(f"{i}. {q['question']}").bold = True
        doc.add_paragraph(f"A) {q['A']}")
        doc.add_paragraph(f"B) {q['B']}")
        doc.add_paragraph(f"C) {q['C']}")
        doc.add_paragraph(f"D) {q['D']}")
        doc.add_paragraph(f"Answer: {q['correct']}").italic = True
        doc.add_paragraph()
    buf = io.BytesIO(); doc.save(buf); buf.seek(0); return buf

def mcqs_to_gift(mcqs):
    lines = []
    for q in mcqs:
        opts = []
        for letter in ["A","B","C","D"]:
            prefix = "=" if letter == q["correct"] else "~"
            opts.append(f"{prefix}{q[letter]}")
        gift = f"::{q['question']}:: {{\n  " + "\n  ".join(opts) + "\n}\n"
        lines.append(gift)
    return "\n".join(lines).encode("utf-8")

def mcqs_to_csv(mcqs):
    return pd.DataFrame(mcqs).to_csv(index=False).encode("utf-8")

def activity_plan(week: int, n: int, dur: int, topic: str):
    focus = bloom_for_week(week)
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "Tier": focus,
            "Title": f"Module: Activity {i}",
            "Objective": f"Learners will {('apply' if focus!='Low' else 'recall')} key ideas from {topic or 'the module'}.",
            "Steps": f"1) Briefing ({min(5, dur//6)}m)  2) Main task ({dur-10}m)  3) Share-out (5m)",
            "Materials": "Projector, handout, whiteboard",
            "Assessment": "Participation rubric / quick check",
            "Duration (mins)": dur,
        })
    return rows

def activities_to_docx(rows, title="ADI Activities"):
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)
    doc.add_heading(title, level=1)
    for i, r in enumerate(rows, start=1):
        doc.add_heading(f"{i}. {r['Title']}", level=2)
        doc.add_paragraph(f"Tier: {r['Tier']}")
        doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph(f"Steps: {r['Steps']}")
        doc.add_paragraph(f"Materials: {r['Materials']}")
        doc.add_paragraph(f"Assessment: {r['Assessment']}")
        doc.add_paragraph(f"Duration: {r['Duration (mins)']} mins")
        doc.add_paragraph()
    buf = io.BytesIO(); doc.save(buf); buf.seek(0); return buf

def df_to_csv(df: pd.DataFrame):
    return df.to_csv(index=False).encode("utf-8")

# Small pill row helper
def pill_row(label: str, options, selected, key_prefix):
    st.markdown(f"<h3 class='section'>{label}</h3>", unsafe_allow_html=True)
    cols = st.columns(len(options))
    for i, (val, txt) in enumerate(options):
        with cols[i]:
            if st.button(txt, key=f"{key_prefix}_{val}"):
                st.session_state[key_prefix] = val
            active = " active" if st.session_state.get(key_prefix, selected) == val else ""
            st.markdown(f"<div class='pill{active}'>{txt}</div>", unsafe_allow_html=True)
    return st.session_state.get(key_prefix, selected)

# ──────────────────────────────────────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────────────────────────────────────
tab_mcq, tab_act = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# Defaults
for k, v in {
    "lesson": 1, "week": 1, "mcq_quick": 10,
    "mcqs_generated": False, "mcqs_data": [],
    "acts_generated": False, "acts_data": [],
}.items():
    st.session_state.setdefault(k, v)

# ──────────────────────────────────────────────────────────────────────────────
# MCQs
# ──────────────────────────────────────────────────────────────────────────────
with tab_mcq:
    left, right = st.columns([0.95, 1.05], gap="large")

    with left:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section'>Upload eBook / Lesson Plan / PPT</h3>", unsafe_allow_html=True)
        st.markdown(
            '<div class="upload-box"><div class="upload-badge">UP</div>'
            '<div><strong>Drag and drop</strong> your file here, or use the button below.<br>'
            '<span style="color:var(--muted)">We recommend eBooks (PDF) as source for best results. (≤200MB)</span></div></div>',
            unsafe_allow_html=True,
        )
        st.file_uploader(" ", type=["pdf", "docx", "pptx"], label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section'>Pick from eBook / Plan / PPT</h3>", unsafe_allow_html=True)
        st.session_state.lesson = pill_row("Lesson", [(i, str(i)) for i in range(1, 7)], st.session_state.lesson, "lesson")
        st.session_state.week = pill_row("Week", [(i, str(i)) for i in range(1, 15)], st.session_state.week, "week")
        st.caption("ADI policy: Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. Bloom auto-highlights in generator.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section'>Generate MCQs — Policy Blocks (Low → Medium → High)</h3>", unsafe_allow_html=True)

        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        src = st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here...")

        st.markdown("<h3 class='section'>How many MCQs?</h3>", unsafe_allow_html=True)
        st.write("Quick pick")
        qp_cols = st.columns(4)
        for i, q in enumerate([5, 10, 20, 30]):
            if qp_cols[i].button(str(q), key=f"qp_{q}"):
                st.session_state.mcq_quick = q
        total_q = st.number_input("Or enter a custom number", min_value=3, max_value=100,
                                  value=int(st.session_state.mcq_quick), step=1)

        bloom = bloom_for_week(st.session_state.week)
        st.caption(f"Bloom focus for Week {st.session_state.week}: **{bloom}**")

        if st.button("Generate MCQ Blocks"):
            st.session_state.mcqs_data = generate_mcqs(topic, src, total_q, bloom)
            st.session_state.mcqs_generated = True

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.markdown("<h3 class='section'>Preview & Edit</h3>", unsafe_allow_html=True)
    if st.session_state.mcqs_generated and st.session_state.mcqs_data:
        edited = []
        for i, q in enumerate(st.session_state.mcqs_data, start=1):
            with st.expander(f"Q{i}: {q['question'][:80]}…", expanded=(i <= 3)):
                qtext = st.text_area("Question", value=q["question"], key=f"q_{i}")
                colA, colB = st.columns(2)
                with colA:
                    a = st.text_input("A", value=q["A"], key=f"a_{i}")
                    c = st.text_input("C", value=q["C"], key=f"c_{i}")
                with colB:
                    b = st.text_input("B", value=q["B"], key=f"b_{i}")
                    d = st.text_input("D", value=q["D"], key=f"d_{i}")
                correct = st.selectbox("Correct option", ["A","B","C","D"],
                                       index=["A","B","C","D"].index(q["correct"]),
                                       key=f"corr_{i}")
                edited.append({"question":qtext,"A":a,"B":b,"C":c,"D":d,"correct":correct})
        st.session_state.mcqs_data = edited

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("Download Word (.docx)",
                               data=mcqs_to_docx(st.session_state.mcqs_data, title="ADI MCQs"),
                               file_name="adi_mcqs.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with c2:
            st.download_button("Download Moodle (.txt)",
                               data=mcqs_to_gift(st.session_state.mcqs_data),
                               file_name="adi_mcqs_gift.txt",
                               mime="text/plain")
        with c3:
            st.download_button("Download CSV",
                               data=mcqs_to_csv(st.session_state.mcqs_data),
                               file_name="adi_mcqs.csv",
                               mime="text/csv")
    else:
        st.info("Generate MCQs to preview and export.")
    st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Activities
# ──────────────────────────────────────────────────────────────────────────────
with tab_act:
    left, right = st.columns([0.9, 1.1], gap="large")

    with left:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section'>Pick parameters</h3>", unsafe_allow_html=True)

        st.write("Week")
        wcols = st.columns(7)
        for idx, w in enumerate([1,2,3,4,5,6,7]):
            if wcols[idx].button(str(w), key=f"actw_{w}"):
                st.session_state.week = w

        st.write("Number of activities")
        n_acts = st.number_input("", min_value=1, max_value=10, value=3, step=1, key="n_acts")
        st.write("Duration (mins)")
        a_dur = st.number_input("", min_value=5, max_value=120, value=45, step=5, key="a_dur")
        st.caption(f"Bloom focus for Week {st.session_state.week}: **{bloom_for_week(st.session_state.week)}**")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section'>Generate Activities</h3>", unsafe_allow_html=True)
        a_topic = st.text_input("Module / Unit (optional)", value="", placeholder="Module/Unit name to appear in titles…")
        if st.button("Generate Activity Plan"):
            st.session_state.acts_data = activity_plan(st.session_state.week, n_acts, a_dur, a_topic)
            st.session_state.acts_generated = True
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.markdown("<h3 class='section'>Preview & Edit</h3>", unsafe_allow_html=True)
    if st.session_state.acts_generated and st.session_state.acts_data:
        edited = []
        for i, r in enumerate(st.session_state.acts_data, start=1):
            with st.expander(f"Activity {i}: {r['Title']}", expanded=(i <= 2)):
                tier = st.text_input("Tier", value=r["Tier"], key=f"tier_{i}")
                title = st.text_input("Title", value=r["Title"], key=f"title_{i}")
                obj = st.text_area("Objective", value=r["Objective"], key=f"obj_{i}")
                steps = st.text_area("Steps", value=r["Steps"], key=f"steps_{i}")
                mats = st.text_input("Materials", value=r["Materials"], key=f"mats_{i}")
                assess = st.text_input("Assessment", value=r["Assessment"], key=f"assess_{i}")
                durv = st.number_input("Duration (mins)", min_value=5, max_value=180,
                                       value=int(r["Duration (mins)"]), step=5, key=f"dur_{i}")
                edited.append({"Tier":tier,"Title":title,"Objective":obj,"Steps":steps,"Materials":mats,"Assessment":assess,"Duration (mins)":durv})
        st.session_state.acts_data = edited

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download Word (.docx)",
                               data=activities_to_docx(st.session_state.acts_data, title="ADI Activities"),
                               file_name="adi_activities.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with c2:
            df = pd.DataFrame(st.session_state.acts_data)
            st.download_button("Download CSV",
                               data=df_to_csv(df),
                               file_name="adi_activities.csv",
                               mime="text/csv")
    else:
        st.info("Generate activities to preview and export.")
    st.markdown("</div>", unsafe_allow_html=True)
