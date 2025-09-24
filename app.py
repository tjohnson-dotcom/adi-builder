# app.py — ADI Builder: Lesson Activities & Questions (Word + Moodle GIFT)
# ----------------------------------------------------------------------
# Run locally:
#   pip install -r requirements.txt
#   streamlit run app.py
#
# Optional: place a logo at repo root as: logo.png

import base64
import io
import os
from datetime import datetime

from typing import List, Dict, Any

import pandas as pd
import streamlit as st
from docx import Document

# -----------------------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ADI Builder",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# Branding / colors / CSS
# -----------------------------------------------------------------------------
LOGO_PATH = "logo.png"  # change if you use a different filename

def _read_logo_data_uri(path: str) -> str | None:
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                uri = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
            return uri
    except Exception:
        pass
    return None

logo_uri = _read_logo_data_uri(LOGO_PATH)

ADI_CSS = f"""
<style>
:root {{
  --adi-green: #245a34;
  --adi-green-600: #1f4c2c;
  --adi-green-50: #EEF5F0;
  --adi-gold: #C8A85A;
  --adi-ink: #1f2937;
  --border: #d9dfda;
  --card: #ffffff;
  --bg: #FAFAF7;
  --shadow: 0 10px 26px rgba(0,0,0,.08);
  --radius: 16px;
  --radius-pill: 999px;
}}

html,body {{ background: var(--bg); }}
main .block-container {{ padding-top: 0.75rem; padding-bottom: 2rem; max-width: 1220px; }}

.adi-hero {{ background: linear-gradient(90deg, var(--adi-green), var(--adi-green-600)); color: #fff; border-radius: 22px; padding: 18px 20px; box-shadow: var(--shadow); margin-bottom: 10px; }}
.adi-hero-row {{ display: flex; align-items: center; gap: 14px; }}
.logo-box {{ width: 44px; height: 44px; border-radius: 10px; background: rgba(0,0,0,.08); display:flex; align-items:center; justify-content:center; overflow: hidden; }}
.logo-box img {{ width:100%; height:100%; object-fit:contain; }}
.logo-fallback {{ font-weight:800; font-size:20px; }}

.adi-title {{ font-weight:800; font-size:20px; margin:0; }}
.adi-sub {{ opacity:.95; font-size:12px; margin-top:2px; }}

.adi-card {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); padding: 14px; margin-bottom: 12px; }}

h3.adi-cap {{ margin: 0 0 8px 0; color: var(--adi-green); font-size: 12px; text-transform: uppercase; letter-spacing: .05em; }}

input, textarea, select, .stTextArea textarea {{ border: 2px solid var(--adi-green) !important; border-radius: 12px !important; }}
input:focus, textarea:focus, select:focus {{ outline: none !important; border-color: var(--adi-green-600) !important; box-shadow: 0 0 0 3px rgba(36,90,52,.22) !important; }}

div.stButton>button {{ background: var(--adi-green); color:#fff; border:none; border-radius: var(--radius-pill); padding: .6rem 1rem; font-weight:600; box-shadow: 0 6px 16px rgba(31,76,44,.20); transition: all .2s; }}
div.stButton>button:hover {{ filter: brightness(.98); box-shadow: 0 0 0 3px rgba(200,168,90,.40); }}

.btn-gold button {{ background: var(--adi-gold) !important; color: #1f2a1f !important; box-shadow: 0 6px 16px rgba(200,168,90,.32) !important; }}

.pill {{ display:inline-flex; align-items:center; justify-content:center; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--border); background: #f6f8f6; color: #1f2a1f; font-weight:600; cursor:pointer; }}
.pill:hover {{ background: #eef5ef; }}
.pill.active {{ background: var(--adi-green); color:#fff; border-color: var(--adi-green-600); }}

.small-pills .pill {{ padding: 4px 10px; font-size: 12px; margin: 2px 6px 2px 0; }}

.bloom-legend {{ display:flex; gap:14px; flex-wrap:wrap; }}
.badge-low {{ background:#eaf5ec; color:#245a34; border:1px solid #d2e5d7; }}
.badge-med {{ background:#f8f3e8; color:#6a4b2d; border:1px solid #e7dbc7; }}
.badge-high{{ background:#f3f1ee; color:#4a4a45; border:1px solid #e2e1df; }}

.upload-hint {{ border: 2px dashed var(--adi-green); background: var(--adi-green-50); border-radius: 14px; padding: 10px; display:flex; gap:10px; align-items:center; }}
.upload-hint .icon {{ width:28px; height:28px; border-radius:7px; background:var(--adi-green); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; }}

hr.soft {{ border:0; height:1px; background: var(--border); margin: 6px 0 10px 0; }}
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Helpers & session state
# -----------------------------------------------------------------------------

def ensure_state():
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Knowledge MCQs (ADI Policy)"
    if "mcq_blocks" not in st.session_state:
        st.session_state.mcq_blocks = 10
    if "lesson" not in st.session_state:
        st.session_state.lesson = 1
    if "week" not in st.session_state:
        st.session_state.week = 1
    if "mcq_df" not in st.session_state:
        st.session_state.mcq_df = None
    if "act_df" not in st.session_state:
        st.session_state.act_df = None

ensure_state()

LOW_VERBS = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify"]


def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    if 5 <= week <= 9:
        return "Medium"
    return "High"


def _fallback(text: str, default: str) -> str:
    return text.strip() if text and text.strip() else default

# -----------------------------------------------------------------------------
# MCQ generation (deterministic scaffold)
# -----------------------------------------------------------------------------

def generate_mcq_blocks(topic: str, source: str, num_blocks: int, week: int) -> pd.DataFrame:
    """Create num_blocks * 3 MCQs (each block has 3: Low/Medium/High)."""
    topic = _fallback(topic, "Module topic")
    src_snip = _fallback(source, "Key concepts and policy points.")

    rows: List[Dict[str, Any]] = []
    for b in range(1, num_blocks + 1):
        for tier in ["Low", "Medium", "High"]:
            if tier == "Low":
                verb = LOW_VERBS[b % len(LOW_VERBS)]
                stem = f"{verb.capitalize()} a basic fact about: {topic}."
            elif tier == "Medium":
                verb = MED_VERBS[b % len(MED_VERBS)]
                stem = f"{verb.capitalize()} this concept from {topic} in a practical case."
            else:
                verb = HIGH_VERBS[b % len(HIGH_VERBS)]
                stem = f"{verb.capitalize()} a policy implication of {topic} given: {src_snip[:80]}"

            options = [
                f"Option A ({tier})",
                f"Option B ({tier})",
                f"Option C ({tier})",
                f"Option D ({tier})",
            ]
            answer_idx = (b + ["Low","Medium","High"].index(tier)) % 4
            rows.append({
                "Block": b,
                "Tier": tier,
                "Question": stem,
                "Option A": options[0],
                "Option B": options[1],
                "Option C": options[2],
                "Option D": options[3],
                "Answer": ["A","B","C","D"][answer_idx],
                "Explanation": f"This is a placeholder rationale linked to {topic}.",
            })
    return pd.DataFrame(rows)

# -----------------------------------------------------------------------------
# Activities generation (simple scaffold)
# -----------------------------------------------------------------------------

def generate_activities(count: int, duration: int, tier: str, topic: str) -> pd.DataFrame:
    if tier == "Low":
        verbs = LOW_VERBS
        pattern = "Warm-up: {verb} the core terms in {topic}; Pair-check; Short recap."
    elif tier == "Medium":
        verbs = MED_VERBS
        pattern = "Case task: {verb} key ideas from {topic} in groups; Peer review; Gallery walk."
    else:
        verbs = HIGH_VERBS
        pattern = "Design task: {verb} a solution for {topic}; Present; Critique and refine."

    rows = []
    for i in range(1, count + 1):
        v = verbs[i % len(verbs)]
        title = f"Module: Activity {i}"
        objective = f"Students will {v} key content from {topic}."
        steps = pattern.format(verb=v.capitalize(), topic=_fallback(topic, "the module"))
        materials = "Projector, handouts, whiteboard"
        assessment = "Participation rubric; brief exit ticket"
        rows.append({
            "Tier": tier,
            "Title": title,
            "Objective": objective,
            "Steps": steps,
            "Materials": materials,
            "Assessment": assessment,
            "Duration (mins)": duration
        })
    return pd.DataFrame(rows)

# -----------------------------------------------------------------------------
# Exporters (DOCX, GIFT, CSV)
# -----------------------------------------------------------------------------

def mcq_to_docx(df: pd.DataFrame, topic: str) -> bytes:
    doc = Document()
    doc.add_heading(f"ADI MCQs — {topic}", level=1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    p = doc.add_paragraph("Each block: Low → Medium → High")
    p.runs[0].italic = True

    for b in sorted(df["Block"].unique()):
        doc.add_heading(f"Block {b}", level=2)
        block_df = df[df["Block"] == b]
        for _, row in block_df.iterrows():
            p = doc.add_paragraph()
            run = p.add_run(f"[{row['Tier']}] {row['Question']}")
            run.bold = True
            doc.add_paragraph(f"A. {row['Option A']}")
            doc.add_paragraph(f"B. {row['Option B']}")
            doc.add_paragraph(f"C. {row['Option C']}")
            doc.add_paragraph(f"D. {row['Option D']}")
            doc.add_paragraph(f"Answer: {row['Answer']}")
            doc.add_paragraph(f"Explanation: {row['Explanation']}")
            doc.add_paragraph("")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def mcq_to_gift(df: pd.DataFrame, topic: str) -> bytes:
    """Moodle GIFT export for single-correct MCQs."""
    out_lines = [f"// ADI MCQs — {topic}", f"// Exported {datetime.now():%Y-%m-%d %H:%M}", ""]
    for i, row in df.reset_index(drop=True).iterrows():
        qname = f"Block{row['Block']}-{row['Tier']}-{i+1}"
        stem = row["Question"].replace("\n", " ").strip()
        opts = [row["Option A"], row["Option B"], row["Option C"], row["Option D"]]
        ans_letter = row["Answer"].strip().upper()
        ans_idx = {"A":0,"B":1,"C":2,"D":3}.get(ans_letter, 0)

        def esc(s: str) -> str:
            return s.replace("{", "\\{").replace("}", "\\}")

        opts_esc = [esc(o) for o in opts]
        stem_esc = esc(stem)

        gift = []
        gift.append(f"::{qname}:: {stem_esc} {{")
        for j, opt in enumerate(opts_esc):
            gift.append(f"={'=' if j == ans_idx else '~'}{opt}" if j == ans_idx else f"~{opt}")
        gift.append("}")
        gift.append("")
        out_lines.extend(gift)
    return "\n".join(out_lines).encode("utf-8")


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO()
    df.to_csv(bio, index=False)
    return bio.getvalue()


def activities_to_docx(df: pd.DataFrame, topic: str) -> bytes:
    doc = Document()
    doc.add_heading(f"ADI Activities — {topic}", level=1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")

    for _, row in df.iterrows():
        doc.add_heading(row["Title"], level=2)
        doc.add_paragraph(f"Tier: {row['Tier']}")
        doc.add_paragraph(f"Objective: {row['Objective']}")
        doc.add_paragraph(f"Steps: {row['Steps']}")
        doc.add_paragraph(f"Materials: {row['Materials']}")
        doc.add_paragraph(f"Assessment: {row['Assessment']}")
        doc.add_paragraph(f"Duration: {row['Duration (mins)']} mins")
        doc.add_paragraph("")
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# -----------------------------------------------------------------------------
# Header UI
# -----------------------------------------------------------------------------
with st.container():
    st.markdown(
        f"""
        <div class="adi-hero">
          <div class="adi-hero-row">
            <div class="logo-box">
              {('<img src="'+logo_uri+'" alt="ADI"/>') if logo_uri else '<div class="logo-fallback">A</div>'}
            </div>
            <div>
              <div class="adi-title">ADI Builder – Lesson Activities & Questions</div>
              <div class="adi-sub">Professional, branded, editable, and export-ready.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Bloom legend
# -----------------------------------------------------------------------------

def render_bloom_panel():
    st.markdown("### Bloom’s focus")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.markdown("**Low** (Remember/Understand)")
        for w in LOW_VERBS:
            st.markdown(f"<span class='pill badge-low'>{w}</span>", unsafe_allow_html=True)
    with col2:
        st.markdown("**Medium** (Apply/Analyze)")
        for w in MED_VERBS:
            st.markdown(f"<span class='pill badge-med'>{w}</span>", unsafe_allow_html=True)
    with col3:
        st.markdown("**High** (Evaluate/Create)")
        for w in HIGH_VERBS:
            st.markdown(f"<span class='pill badge-high'>{w}</span>", unsafe_allow_html=True)
    st.markdown("<hr class='soft'/>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------

tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# ---------------------------------------------------------------- MCQ TAB ---
with tab[0]:
    left, right = st.columns([1,2], gap="large")

    with left:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='adi-cap'>Upload eBook / Lesson Plan / PPT</h3>", unsafe_allow_html=True)
        st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
        st.markdown(
            "<div class='upload-hint'><div class='icon'>UP</div>"
            "<div><strong>Drag and drop</strong> your file here, or use the button below.<br>"
            "<small>We recommend eBooks (PDF) as source for best results.</small></div></div>",
            unsafe_allow_html=True,
        )
        _ = st.file_uploader(" ", type=["pdf","docx","pptx"], label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='adi-cap'>Pick from eBook / Plan / PPT</h3>", unsafe_allow_html=True)

        st.markdown("**Lesson**")
        lcols = st.columns(6)
        for i,c in enumerate(lcols, start=1):
            with c:
                if st.button(f"{i}", key=f"lesson_{i}"):
                    st.session_state.lesson = i
                st.markdown(f"<div class='small-pills'></div>", unsafe_allow_html=True)

        st.markdown("**Week**")
        for row in range(2):
            cols = st.columns(7)
            for j,c in enumerate(cols, start=1):
                idx = j + row*7
                if idx>14: break
                with c:
                    if st.button(f"{idx}", key=f"week_{idx}"):
                        st.session_state.week = idx

        st.caption("ADI policy: Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. Bloom auto-highlights in generator.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='adi-cap'>Activity Parameters (reference)</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Activities (for Activities tab)", min_value=1, value=3, step=1, key="ref_act_n")
        with c2:
            st.number_input("Duration mins (for Activities tab)", min_value=5, value=45, step=5, key="ref_act_d")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='adi-cap'>Generate MCQs — Policy Blocks (Low → Medium → High)</h3>", unsafe_allow_html=True)
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source = st.text_area("Source text (optional, editable)", placeholder="Paste or edit source text here...", height=130)

        bloom = bloom_focus_for_week(st.session_state.week)
        st.text_input("Bloom focus", value=f"Week {st.session_state.week}: {bloom}", disabled=True, label_visibility="collapsed")
        st.caption(f"Bloom focus for Week {st.session_state.week}: **{bloom}**")

        render_bloom_panel()

        st.markdown("#### Quick pick")
        qp1, qp2, qp3, qp4 = st.columns(4)
        with qp1:
            if st.button("5"):
                st.session_state.mcq_blocks = 5
        with qp2:
            if st.button("10"):
                st.session_state.mcq_blocks = 10
        with qp3:
            if st.button("20"):
                st.session_state.mcq_blocks = 20
        with qp4:
            if st.button("30"):
                st.session_state.mcq_blocks = 30

        st.number_input("Or enter a custom number of blocks", min_value=1, value=st.session_state.mcq_blocks, step=1, key="mcq_blocks")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Generate MCQ Blocks"):
            with st.spinner("Building MCQ blocks…"):
                st.session_state.mcq_df = generate_mcq_blocks(topic, source, st.session_state.mcq_blocks, st.session_state.week)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='adi-cap'>Preview & Edit</h3>", unsafe_allow_html=True)
        if st.session_state.mcq_df is None:
            st.info("No MCQs yet. Generate blocks above to preview and edit.")
        else:
            edited = st.data_editor(
                st.session_state.mcq_df,
                num_rows="dynamic",
                use_container_width=True,
                key="mcq_editor",
            )
            st.session_state.mcq_df = edited

            cdoc, cgift, ccsv = st.columns(3)
            with cdoc:
                st.download_button(
                    "Download Word (.docx)",
                    mcq_to_docx(edited, _fallback(topic, "Module")),
                    file_name="adi_mcqs.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            with cgift:
                st.download_button(
                    "Download Moodle (GIFT)",
                    mcq_to_gift(edited, _fallback(topic, "Module")),
                    file_name="adi_mcqs_gift.txt",
                    mime="text/plain",
                )
            with ccsv:
                st.download_button(
                    "Download CSV",
                    df_to_csv_bytes(edited),
                    file_name="adi_mcqs.csv",
                    mime="text/csv",
                )
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------- ACTIVITIES TAB ---
with tab[1]:
    left, right = st.columns([1,2], gap="large")

    with left:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='adi-cap'>Parameters</h3>", unsafe_allow_html=True)
        n = st.number_input("Number of activities", min_value=1, value=st.session_state.get("ref_act_n", 3), step=1)
        d = st.number_input("Duration (mins) per activity", min_value=5, value=st.session_state.get("ref_act_d", 45), step=5)
        tier = st.radio("Emphasis", ["Low","Medium","High"], horizontal=True, index=1)
        topic2 = st.text_input("Topic (optional)", value="", placeholder="Module or unit focus")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Generate Activity Plan", key="gen_act"):
            with st.spinner("Assembling activities…"):
                st.session_state.act_df = generate_activities(n, d, tier, topic2)

    with right:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='adi-cap'>Preview & Edit</h3>", unsafe_allow_html=True)
        if st.session_state.act_df is None:
            st.info("No activities yet. Generate a plan on the left to preview and edit.")
        else:
            act_edit = st.data_editor(
                st.session_state.act_df,
                num_rows="dynamic",
                use_container_width=True,
                key="act_editor",
            )
            st.session_state.act_df = act_edit

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "Download Word (.docx)",
                    activities_to_docx(act_edit, _fallback(topic2, "Module")),
                    file_name="adi_activities.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            with c2:
                st.download_button(
                    "Download CSV",
                    df_to_csv_bytes(act_edit),
                    file_name="adi_activities.csv",
                    mime="text/csv",
                )
        st.markdown("</div>", unsafe_allow_html=True)


