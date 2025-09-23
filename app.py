# ADI Builder – Trainer-friendly UI (MCQs + Activities, editable + export)
# Run:
#   pip install -r requirements.txt
#   streamlit run app.py

import io
import os
import random
from datetime import datetime

import pandas as pd
import streamlit as st
from docx import Document
from docx.shared import Pt, Inches

# ------------------------------
# Branding / Theme
# ------------------------------
ADI_GREEN = "#245a34"
ADI_GREEN_600 = "#1f4c2c"
ADI_GREEN_50 = "#EEF5F0"
ADI_GOLD = "#C8A85A"
STONE = "#f3f1ee"

st.set_page_config(
    page_title="ADI Builder",
    page_icon="📘",
    layout="wide",
)

CSS = f"""
<style>
:root {{
  --adi-green:{ADI_GREEN};
  --adi-green-600:{ADI_GREEN_600};
  --adi-green-50:{ADI_GREEN_50};
  --adi-gold:{ADI_GOLD};
  --stone:{STONE};
}}

html, body {{
  background:#FAFAF7;
}}

main .block-container {{
  padding-top: 0.8rem;
  max-width: 1200px;
}}

.adi-hero {{
  background: linear-gradient(90deg, var(--adi-green), var(--adi-green-600));
  color:#fff;
  padding: 16px 18px;
  border-radius: 18px;
  box-shadow: 0 8px 22px rgba(0,0,0,.12);
  margin-bottom: 12px;
}}
.adi-title {{ font-weight: 800; font-size: 22px; }}
.adi-sub {{ opacity:.95; font-size:12px; margin-top:2px; }}

.adi-card {{
  background:#fff;
  border: 1px solid #dde3de;
  border-radius:16px;
  box-shadow: 0 8px 22px rgba(0,0,0,.06);
  padding:14px 14px 4px 14px;
}}

.quick-pills {{
  display:flex; gap:8px; flex-wrap:wrap;
}}
.quick-pill {{
  padding:6px 12px; border-radius:999px; border:1px solid #d8dfda;
  background:#f3f7f3; cursor:pointer; user-select:none;
  font-weight:600; color:#26422d;
}}
.quick-pill.active {{
  background: var(--adi-green); color:#fff; border-color:var(--adi-green-600);
  box-shadow:0 6px 14px rgba(36,90,52,.25);
}}

div.stButton>button {{
  background: var(--adi-green);
  color:#fff; border:none; border-radius:999px;
  padding:.6rem 1.1rem; font-weight:600;
  box-shadow:0 6px 16px rgba(31,76,44,.24);
}}
div.stButton>button:hover {{
  filter:brightness(.96);
  box-shadow:0 0 0 3px rgba(200,168,90,.35);
}}

.badge {{
  display:inline-block; font-size:12px; padding:4px 8px; border-radius:999px;
  background:var(--adi-green-50); color:#1f4c2c; border:1px solid #d8e3da;
}}

.radio-wrap {{
  display:flex; gap:12px; align-items:center; flex-wrap:wrap;
  padding:8px 12px; border:1px dashed #cfd7d1; border-radius:12px; background:#fff;
}}

.bloom-pill {{
  padding:6px 10px; border-radius:999px; border:1px solid #e5e5e0;
  background:#f8f6f3; color:#5b564f; font-size:12px; margin-right:6px;
}}
.bloom-pill.active.low {{ background:#eaf5ec; color:#154224; }}
.bloom-pill.active.med {{ background:#f8f1df; color:#6a4b2d; }}
.bloom-pill.active.high {{ background:#eee; color:#333; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------
# Simple heuristic Bloom tiers
# ------------------------------
BLOOMS = {
    "low": ["define", "identify", "list", "recall", "describe", "label"],
    "med": ["apply", "demonstrate", "solve", "illustrate"],
    "high": ["evaluate", "synthesize", "design", "justify"],
}
def bloom_tier_from_week(week:int)->str:
    if 1 <= week <= 4:
        return "low"
    if 5 <= week <= 9:
        return "med"
    return "high"  # 10-14

# ------------------------------
# MCQ generation (placeholder logic)
# Replace with your real generator if available
# ------------------------------
def generate_mcqs(topic: str, source_text: str, n_questions: int, tier: str):
    """Return list of dicts: question, A,B,C,D, answer, bloom"""
    verbs = BLOOMS.get(tier, BLOOMS["low"])
    out = []
    for i in range(1, n_questions+1):
        verb = random.choice(verbs).capitalize()
        q = f"{verb} – {topic or 'Topic'} (Q{i})"
        options = [f"Option {c} for Q{i}" for c in ["A","B","C","D"]]
        ans = "A"
        out.append({
            "Bloom": verb,
            "Question": q,
            "A": options[0],
            "B": options[1],
            "C": options[2],
            "D": options[3],
            "Answer": ans
        })
    return out

# ------------------------------
# Activities generation (placeholder)
# ------------------------------
def generate_activities(n: int, week: int, duration_min: int):
    tier = bloom_tier_from_week(week)
    templates = {
        "low": "Short knowledge check on {topic}. Pair up and {verb}.",
        "med": "Small group task to {verb} a scenario from {topic}.",
        "high": "Team design challenge: {verb} a solution for a complex case in {topic}."
    }
    verbs = BLOOMS[tier]
    topic = "module content"
    out = []
    for i in range(1, n+1):
        verb = random.choice(verbs)
        text = templates[tier].format(topic=topic, verb=verb)
        out.append({
            "Activity": f"Activity {i}",
            "Description": text,
            "Duration (mins)": duration_min
        })
    return out

# ------------------------------
# Export helpers
# ------------------------------
def mcqs_to_docx(df: pd.DataFrame, filename: str) -> bytes:
    doc = Document()
    doc.add_heading('ADI – MCQs', level=1)
    doc.add_paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"))
    doc.add_paragraph('')

    for idx, row in df.iterrows():
        p = doc.add_paragraph()
        run = p.add_run(f"Q{idx+1}. {row.get('Question','')}")
        run.bold = True
        doc.add_paragraph(f"A. {row.get('A','')}")
        doc.add_paragraph(f"B. {row.get('B','')}")
        doc.add_paragraph(f"C. {row.get('C','')}")
        doc.add_paragraph(f"D. {row.get('D','')}")
        doc.add_paragraph(f"Answer: {row.get('Answer','')}")
        doc.add_paragraph(f"(Bloom: {row.get('Bloom','')})")
        doc.add_paragraph('')

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.read()

def mcqs_to_gift(df: pd.DataFrame) -> bytes:
    # Minimal Moodle GIFT
    lines = []
    for idx, row in df.iterrows():
        q = row.get("Question","").replace("\n"," ")
        a = row.get("A","")
        b = row.get("B","")
        c = row.get("C","")
        d = row.get("D","")
        correct = row.get("Answer","A").strip().upper()
        options = {"A":a,"B":b,"C":c,"D":d}
        correct_text = options.get(correct, a)
        gift = f"::{idx+1}::{q} {{ = {correct_text} ~ {a if correct!='A' else b} ~ {c} ~ {d} }}\n"
        lines.append(gift)
    return ("\n".join(lines)).encode("utf-8")

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def activities_to_docx(df: pd.DataFrame) -> bytes:
    doc = Document()
    doc.add_heading('ADI – Activities', level=1)
    doc.add_paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"))
    doc.add_paragraph('')

    for idx, row in df.iterrows():
        doc.add_heading(row.get("Activity", f"Activity {idx+1}"), level=2)
        doc.add_paragraph(row.get("Description",""))
        doc.add_paragraph(f"Duration: {row.get('Duration (mins)',0)} minutes")
        doc.add_paragraph('')

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.read()

# ------------------------------
# Header
# ------------------------------
st.markdown(
    """
    <div class="adi-hero">
      <div class="adi-title">ADI Builder – Lesson Activities & Questions</div>
      <div class="adi-sub">Professional, branded, editable and export-ready.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# Tabs
# ------------------------------
tab1, tab2 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# =======================================
# TAB 1 – MCQs
# =======================================
with tab1:
    left, right = st.columns([1.1, 1.9], gap="large")

    with left:
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("#### Upload eBook / Lesson Plan / PPT")
        st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
        uploaded = st.file_uploader("Drag and drop your file (optional)", type=["pdf","docx","pptx"])
        if uploaded is not None:
            st.success(f"Uploaded: {uploaded.name}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("#### Pick from eBook / Plan / PPT")
        st.write("**Lesson**")
        lesson = st.radio("lesson", [1,2,3,4,5], index=0, horizontal=True, label_visibility="collapsed")
        st.write("**Week**")
        week = st.radio("week", list(range(1,15)), index=0, horizontal=True, label_visibility="collapsed")
        tier = bloom_tier_from_week(week)
        st.caption("**ADI policy:** Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. Tier is auto-highlighted below.")
        # Bloom badges
        st.write(
            f'<span class="bloom-pill {"active low" if tier=="low" else ""}">Low: {", ".join(BLOOMS["low"][:3])}…</span> '
            f'<span class="bloom-pill {"active med" if tier=="med" else ""}">Medium: {", ".join(BLOOMS["med"][:2])}…</span> '
            f'<span class="bloom-pill {"active high" if tier=="high" else ""}">High: {", ".join(BLOOMS["high"][:2])}…</span>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("#### Generate MCQs — Policy Blocks (Low → Medium → High)")
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        src_text = st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here...")

        # Quick pick pills
        st.write("**How many MCQs?**")
        if "mcq_target" not in st.session_state:
            st.session_state.mcq_target = 10
        cols = st.columns([.9,.9,.9,3])
        with cols[0]:
            if st.button("5", key="q5", use_container_width=True):
                st.session_state.mcq_target = 5
        with cols[1]:
            if st.button("10", key="q10", use_container_width=True):
                st.session_state.mcq_target = 10
        with cols[2]:
            if st.button("20", key="q20", use_container_width=True):
                st.session_state.mcq_target = 20
        with cols[3]:
            mcq_count = st.slider(" ", min_value=5, max_value=30, value=st.session_state.mcq_target, step=1, label_visibility="collapsed")
            st.session_state.mcq_target = mcq_count

        if st.button("Generate MCQ Blocks"):
            data = generate_mcqs(topic, src_text, st.session_state.mcq_target, tier)
            st.session_state.mcq_df = pd.DataFrame(data)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("#### Preview & Edit")
        mcq_df = st.session_state.get("mcq_df", pd.DataFrame(columns=["Bloom","Question","A","B","C","D","Answer"]))
        edited = st.data_editor(
            mcq_df,
            num_rows="dynamic",
            use_container_width=True,
            key="mcq_editor",
            column_config={
                "Answer": st.column_config.SelectboxColumn("Answer", options=["A","B","C","D"]),
            }
        )
        st.session_state.mcq_df = edited

        colA, colB, colC = st.columns(3)
        with colA:
            docx_bytes = mcqs_to_docx(edited, "adi_mcqs.docx") if not edited.empty else None
            st.download_button(
                "Download Word (.docx)",
                data=docx_bytes or b"",
                file_name=f"adi_mcqs_w{week}_{len(edited)}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                disabled=edited.empty,
                use_container_width=True
            )
        with colB:
            csv_bytes = df_to_csv_bytes(edited) if not edited.empty else None
            st.download_button(
                "Download CSV",
                data=csv_bytes or b"",
                file_name=f"adi_mcqs_w{week}_{len(edited)}.csv",
                mime="text/csv",
                disabled=edited.empty,
                use_container_width=True
            )
        with colC:
            gift_bytes = mcqs_to_gift(edited) if not edited.empty else None
            st.download_button(
                "Download Moodle (GIFT)",
                data=gift_bytes or b"",
                file_name=f"adi_mcqs_w{week}_{len(edited)}.gift",
                mime="text/plain",
                disabled=edited.empty,
                use_container_width=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

# =======================================
# TAB 2 – Activities
# =======================================
with tab2:
    c1, c2 = st.columns([1.1, 1.9], gap="large")

    with c1:
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("#### Pick parameters")
        week2 = st.radio("Week (activities)", list(range(1,15)), index=0, horizontal=True, label_visibility="collapsed", key="wk2")
        tier2 = bloom_tier_from_week(week2)
        st.write(
            f'<span class="bloom-pill {"active low" if tier2=="low" else ""}">Low</span> '
            f'<span class="bloom-pill {"active med" if tier2=="med" else ""}">Medium</span> '
            f'<span class="bloom-pill {"active high" if tier2=="high" else ""}">High</span>',
            unsafe_allow_html=True
        )
        n_acts = st.slider("Number of activities", 1, 8, 3)
        duration = st.slider("Duration (mins) (per activity)", 10, 120, 45, step=5)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("#### Generate Activities")
        if st.button("Generate Activity Plan"):
            acts = generate_activities(n_acts, week2, duration)
            st.session_state.act_df = pd.DataFrame(acts)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.markdown("#### Preview & Edit")
        act_df = st.session_state.get("act_df", pd.DataFrame(columns=["Activity","Description","Duration (mins)"]))
        act_edit = st.data_editor(act_df, num_rows="dynamic", use_container_width=True, key="act_editor")
        st.session_state.act_df = act_edit

        col1, col2 = st.columns(2)
        with col1:
            bytes_doc = activities_to_docx(act_edit) if not act_edit.empty else None
            st.download_button(
                "Download Word (.docx)",
                data=bytes_doc or b"",
                file_name=f"adi_activities_w{week2}_{len(act_edit)}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                disabled=act_edit.empty,
                use_container_width=True
            )
        with col2:
            bytes_csv = df_to_csv_bytes(act_edit) if not act_edit.empty else None
            st.download_button(
                "Download CSV",
                data=bytes_csv or b"",
                file_name=f"adi_activities_w{week2}_{len(act_edit)}.csv",
                mime="text/csv",
                disabled=act_edit.empty,
                use_container_width=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
