# ADI Builder — streamlined UI (MCQs + Activities)
# ------------------------------------------------
# Run:
#   pip install streamlit pandas python-docx
#   streamlit run app.py

import io
import base64
import os
from html import escape as xml_escape

import pandas as pd
import streamlit as st
from docx import Document
from docx.shared import Pt

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ---------------------- Theme (light touch) ----------------------
CSS = """
<style>
:root{
  --green:#245a34; --green-600:#1f4c2c; --stone:#f3f1ee; --edge:#d9dfda;
}
html,body{ background:#fafaf7;}
main .block-container {max-width:1180px;}
.adi-hero{background:linear-gradient(90deg,var(--green),var(--green-600)); color:#fff;
  border-radius:18px; padding:16px 18px; margin-bottom:12px; box-shadow:0 8px 20px rgba(0,0,0,.08);}
.adi-title{font-weight:800; font-size:20px; margin:0;}
.adi-sub{opacity:.92; font-size:12px; margin-top:4px;}
.badge{display:inline-block; padding:6px 10px; border-radius:999px; background:#eef5ef; color:#1f4c2c; border:1px solid #d9e6db; margin-right:6px; margin-bottom:6px; font-size:12px;}
.card{background:#fff; border:1px solid var(--edge); border-radius:14px; padding:14px; box-shadow:0 8px 20px rgba(0,0,0,.04);}
h3{margin:0 0 10px 0; color:#2b2f2a;}
.small{color:#6b7280; font-size:12px;}
div.stButton>button{ background:var(--green); color:#fff; border:none; border-radius:999px; padding:.65rem 1rem; font-weight:600;}
div.stButton>button:hover{ filter:brightness(.96);}
.tribar{display:flex; gap:10px; flex-wrap:wrap;}
.tribar .badge.low{ background:#eaf5ec;}
.tribar .badge.med{ background:#fff6e6; color:#6a4b2d; border-color:#f0e2c7;}
.tribar .badge.hi { background:#f3f1ee; color:#45433f; }
a.muted{color:#6b7280; text-decoration:none;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------- Header ----------------------
st.markdown(
    """
    <div class="adi-hero">
      <div class="adi-title">ADI Builder – Lesson Activities & Questions</div>
      <div class="adi-sub">Professional, branded, editable, export-ready.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------- Bloom banner ----------------------
def bloom_banner():
    st.markdown("**ADI Bloom tiers (used by policy):**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Low**")
        st.markdown(
            '<div class="tribar">'
            + "".join(f'<span class="badge low">{w}</span>' for w in ["define","identify","list","recall","describe","label"])
            + "</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("**Medium**")
        st.markdown(
            '<div class="tribar">'
            + "".join(f'<span class="badge med">{w}</span>' for w in ["apply","demonstrate","solve","illustrate"])
            + "</div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown("**High**")
        st.markdown(
            '<div class="tribar">'
            + "".join(f'<span class="badge hi">{w}</span>' for w in ["evaluate","synthesize","design","justify"])
            + "</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div class="small">ADI policy: Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High.</div>',
        unsafe_allow_html=True,
    )

# ---------------------- Simple Generators (replace later) ----------------------
def generate_mcqs(source_text: str, topic: str, total_questions: int, week: int) -> pd.DataFrame:
    """
    Deterministic placeholder: creates MCQs from topic/source snippets.
    Replace this with your real generator when ready.
    """
    # Choose Bloom tier by week (policy)
    if week <= 4: tier, verbs = "Low", ["define","identify","list","recall","describe","label"]
    elif week <= 9: tier, verbs = "Medium", ["apply","demonstrate","solve","illustrate"]
    else: tier, verbs = "High", ["evaluate","synthesize","design","justify"]

    src = (source_text or topic or "policy").strip()
    if not src: src = "policy"

    rows = []
    for i in range(total_questions):
        verb = verbs[i % len(verbs)]
        stem = f"{verb.title()} — {src} (Q{i+1})"
        # A simple 4-option pattern; correct cycles A/B/C/D
        options = [f"Option {x} for {verb}" for x in ["A","B","C","D"]]
        answer = "ABCD"[i % 4]
        rows.append({
            "Tier": tier,
            "Verb": verb,
            "Question": stem,
            "A": options[0],
            "B": options[1],
            "C": options[2],
            "D": options[3],
            "Answer": answer
        })
    return pd.DataFrame(rows)

def generate_activities(source_text: str, topic: str, count: int, week: int) -> pd.DataFrame:
    """
    Simple placeholder for activities. Replace with your real activity builder later.
    """
    if week <= 4: tier = "Low"
    elif week <= 9: tier = "Medium"
    else: tier = "High"
    base = (topic or source_text or "Module").strip() or "Module"

    rows = []
    for i in range(count):
        rows.append({
            "Tier": tier,
            "Title": f"{base}: Activity {i+1}",
            "Objective": f"Students will {['define','apply','evaluate'][min(2, (week-1)//5)]} the core concept of {base}.",
            "Steps": "1) Briefing (5m)\n2) Main task (25m)\n3) Share-out (10m)",
            "Materials": "Projector, handout, whiteboard",
            "Assessment": "Participation and brief reflection",
            "Duration (mins)": 45
        })
    return pd.DataFrame(rows)

# ---------------------- Export helpers ----------------------
def mcq_docx_bytes(df: pd.DataFrame) -> bytes:
    doc = Document()
    doc.styles['Normal'].font.size = Pt(11)
    for i, r in df.iterrows():
        qn = i + 1
        doc.add_paragraph(f"Q{qn}. {r['Question']}")
        doc.add_paragraph(f"   A) {r['A']}")
        doc.add_paragraph(f"   B) {r['B']}")
        doc.add_paragraph(f"   C) {r['C']}")
        doc.add_paragraph(f"   D) {r['D']}")
        doc.add_paragraph(f"   Answer: {r['Answer']}")
        doc.add_paragraph("")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()

def activity_docx_bytes(df: pd.DataFrame) -> bytes:
    doc = Document()
    doc.styles['Normal'].font.size = Pt(11)
    for i, r in df.iterrows():
        doc.add_paragraph(f"Activity {i+1}: {r['Title']}")
        doc.add_paragraph(f"Tier: {r.get('Tier','')}")
        doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph("Steps:")
        for line in str(r["Steps"]).splitlines():
            doc.add_paragraph(line, style=None)
        doc.add_paragraph(f"Materials: {r['Materials']}")
        doc.add_paragraph(f"Assessment: {r['Assessment']}")
        doc.add_paragraph(f"Duration (mins): {r.get('Duration (mins)', '')}")
        doc.add_paragraph("")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()

def moodle_xml_bytes(df: pd.DataFrame) -> bytes:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']
    for _, r in df.iterrows():
        correct = str(r['Answer']).strip().upper()[:1]
        answers = [('A', r['A']), ('B', r['B']), ('C', r['C']), ('D', r['D'])]
        parts.append('<question type="multichoice">')
        parts.append(f'<name><text>{xml_escape(str(r["Question"])[:80])}</text></name>')
        parts.append(f'<questiontext format="html"><text><![CDATA[{xml_escape(r["Question"])}]]></text></questiontext>')
        parts.append('<defaultgrade>1</defaultgrade><single>true</single><shuffleanswers>true</shuffleanswers>')
        parts.append('<answernumbering>abc</answernumbering>')
        for letter, text in answers:
            fraction = '100' if letter == correct else '0'
            parts.append(f'<answer fraction="{fraction}" format="html"><text><![CDATA[{xml_escape(text)}]]></text>')
            parts.append('<feedback><text></text></feedback></answer>')
        parts.append('</question>')
    parts.append('</quiz>')
    return "\n".join(parts).encode("utf-8")

# ---------------------- Tabs ----------------------
tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# Keep Bloom banner always visible
bloom_banner()
st.divider()

# ---------------------- Shared inputs (left) ----------------------
with st.sidebar:
    st.markdown("### Upload eBook / Lesson Plan / PPT")
    st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
    uploaded = st.file_uploader("Drag & drop or Browse", type=["pdf","docx","pptx"], label_visibility="collapsed")
    if uploaded:
        st.success(f"Uploaded: **{uploaded.name}**")
    st.markdown("— or —")
    st.text_input("Topic / Outcome (optional)", key="topic_sidebar", placeholder="Module description, knowledge & skills outcomes")
    st.text_area("Source text (optional, editable)", key="source_sidebar", height=120, placeholder="Paste or edit source text here...")

    st.markdown("### Pick from eBook / Plan / PPT")
    col_l, col_w = st.columns(2)
    with col_l:
        lesson = st.radio("Lesson", options=[1,2,3,4,5], horizontal=True, index=0)
    with col_w:
        week = st.radio("Week", options=list(range(1,15)), horizontal=True, index=0)

    st.caption("ADI policy auto-sets Bloom tier by week.")

# ---------------------- MCQs tab ----------------------
with tab[0]:
    st.markdown("### Generate MCQs — Policy Blocks (Low → Medium → High)")

    topic = st.session_state.get("topic_sidebar","")
    src = st.session_state.get("source_sidebar","")

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        total_mcq = st.number_input("How many MCQs? (×3 questions per block not enforced here)", min_value=5, max_value=30, step=1, value=10)
    with col2:
        st.write("")
    with col3:
        gen_mcq = st.button("Generate MCQ Blocks", use_container_width=True)

    if gen_mcq:
        mcq_df = generate_mcqs(src, topic, total_mcq, week)
        st.session_state["mcq_df"] = mcq_df

    if "mcq_df" in st.session_state:
        st.markdown("#### Edit MCQs")
        st.caption("You can edit any cell (Question, A–D, Answer). Add rows if needed.")
        edited_df = st.data_editor(
            st.session_state["mcq_df"],
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Tier": st.column_config.SelectboxColumn(options=["Low","Medium","High"]),
                "Verb": st.column_config.TextColumn(),
                "Question": st.column_config.TextColumn(width="large"),
                "A": st.column_config.TextColumn(),
                "B": st.column_config.TextColumn(),
                "C": st.column_config.TextColumn(),
                "D": st.column_config.TextColumn(),
                "Answer": st.column_config.SelectboxColumn(options=["A","B","C","D"]),
            },
        )
        st.session_state["mcq_df"] = edited_df

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "Download CSV",
                edited_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"adi_mcqs_w{week}_{len(edited_df)}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "Download Word (.docx)",
                mcq_docx_bytes(edited_df),
                file_name=f"adi_mcqs_w{week}_{len(edited_df)}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with c3:
            st.download_button(
                "Download Moodle XML",
                moodle_xml_bytes(edited_df),
                file_name=f"adi_mcqs_w{week}_{len(edited_df)}.xml",
                mime="application/xml",
                use_container_width=True,
            )

# ---------------------- Activities tab ----------------------
with tab[1]:
    st.markdown("### Build Skills Activities")
    topic = st.session_state.get("topic_sidebar","")
    src = st.session_state.get("source_sidebar","")

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        num_acts = st.number_input("How many activities?", min_value=1, max_value=10, step=1, value=3)
    with col2:
        default_dur = st.number_input("Default duration (mins)", min_value=10, max_value=180, step=5, value=45)
    with col3:
        gen_act = st.button("Generate Activity Plan", use_container_width=True)

    if gen_act:
        act_df = generate_activities(src, topic, num_acts, week)
        # apply default duration
        if "Duration (mins)" in act_df.columns:
            act_df["Duration (mins)"] = default_dur
        st.session_state["act_df"] = act_df

    if "act_df" in st.session_state:
        st.markdown("#### Edit Activities")
        st.caption("Edit any field. Use the table as the final plan before export.")
        edited_acts = st.data_editor(
            st.session_state["act_df"],
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Tier": st.column_config.SelectboxColumn(options=["Low","Medium","High"]),
                "Title": st.column_config.TextColumn(width="medium"),
                "Objective": st.column_config.TextColumn(width="large"),
                "Steps": st.column_config.TextColumn(width="large"),
                "Materials": st.column_config.TextColumn(width="medium"),
                "Assessment": st.column_config.TextColumn(width="medium"),
                "Duration (mins)": st.column_config.NumberColumn(min_value=5, max_value=240, step=5),
            },
            height=420
        )
        st.session_state["act_df"] = edited_acts

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download Activities (CSV)",
                edited_acts.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"adi_activities_w{week}_{len(edited_acts)}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "Download Activities Word (.docx)",
                activity_docx_bytes(edited_acts),
                file_name=f"adi_activities_w{week}_{len(edited_acts)}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
