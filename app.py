# ADI Builder — Lesson Activities & Questions
# Final build: compact sidebar, bold pickers, gold tabs, Bloom tiers emphasized.
# Features: Upload (PDF/DOCX/PPTX) → prefill source, generate/edit MCQs & Activities,
# export Word/CSV/GIFT. Clean, professional UI.

import base64
import io
import os
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation

# ----------------------------- Page config -----------------------------
st.set_page_config(
    page_title="ADI Builder",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Theme & CSS -----------------------------
st.markdown(
    """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-gold:#C8A85A;
  --ink:#1f2937; --muted:#6b7280; --bg:#F5F4EE; --card:#ffffff; --border:#E3E8E3;
  --shadow:0 12px 28px rgba(0,0,0,.07);
  --low-bg:#eaf5ec; --med-bg:#f8f3e8; --high-bg:#f3f1ee;
}

/* Layout */
html,body{background:var(--bg);} 
main .block-container{max-width:1180px; padding-top:0.6rem}

/* HERO header */
.adi-hero{display:flex; align-items:center; gap:14px; padding:18px 20px; border-radius:22px; color:#fff;
  background:linear-gradient(95deg,var(--adi-green),var(--adi-green-600)); box-shadow:var(--shadow); margin-bottom:14px}
.logo{width:48px;height:48px;border-radius:12px;background:rgba(0,0,0,.12);display:flex;align-items:center;justify-content:center;overflow:hidden}
.logo img{width:100%;height:100%;object-fit:contain}
.h-title{font-size:22px;font-weight:800;margin:0}
.h-sub{font-size:12px;opacity:.95;margin:2px 0 0 0}

/* ---------------- Sidebar ---------------- */
section[data-testid="stSidebar"]>div{background:#F5F4EE}

/* Sidebar cards (outer) */
.side-card{
  background:linear-gradient(180deg,#fff,#f6f6f2);
  border:1.6px solid #d8ddd8;
  border-radius:14px;
  padding:10px 12px 12px;
  margin:12px 6px;
  box-shadow:0 6px 14px rgba(0,0,0,.05), inset 0 1px 0 #ffffff;
}
.side-card.upload{border-color:#C8A85A}
.side-card.context{border-color:#245a34}
.side-card.mcqs{border-color:#C8A85A}
.side-card.skills{border-color:#245a34}

/* Compact section headers */
.side-cap{
  display:flex; align-items:center; gap:6px;
  font-size:12.5px; line-height:1.18; font-weight:800;
  color:var(--adi-green); text-transform:uppercase; letter-spacing:.04em;
  margin:0 0 4px; padding:3px 6px; background:#fafaf7; border-radius:6px;
}
.side-cap i{font-style:normal; width:14px; text-align:center; color:var(--adi-gold)}
.rule{height:.5px; border:0; margin:2px 0 6px; background:linear-gradient(90deg,var(--adi-gold),transparent)}

/* Sidebar labels + pickers pop */
section[data-testid='stSidebar'] label{font-size:14px!important; font-weight:800; color:var(--adi-green)}
section[data-testid='stSidebar'] .stSelectbox div[role='combobox'],
section[data-testid='stSidebar'] .stNumberInput input{
  border:2px solid var(--adi-green)!important; border-radius:10px!important;
  background:#fafaf7!important; font-weight:900; font-size:15px; color:#1d3a27;
  text-align:center;
}
section[data-testid='stSidebar'] .stSelectbox div[role='combobox']:focus,
section[data-testid='stSidebar'] .stNumberInput input:focus{
  box-shadow:0 0 0 3px rgba(36,90,52,.22)!important;
}

/* Quick pick outlined panel */
.qp{border:1.6px solid var(--adi-gold); border-radius:12px; padding:8px 10px; background:#fffef9; box-shadow:inset 0 1px 0 #fff}
.qp [role='radiogroup']{gap:10px}
.qp [role='radiogroup'] label{font-weight:800; color:#2b2f28}

/* Upload dropzone style */
div[data-testid="stFileUploaderDropzone"]{border-radius:14px; border:1.5px dashed #c8d1c8; background:#ffffff}
div[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--adi-green); box-shadow:0 0 0 3px rgba(36,90,52,.12)}

/* ---------------- Main panels ---------------- */
.card{background:var(--card); border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow); padding:18px 18px; margin:12px 0}
.cap{color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; font-size:12px; margin:0 0 12px}
h3.hsharp{margin:6px 0 6px; font-size:18px; color:#2a2f28}
h4.hsub{margin:2px 0 10px; font-size:13px; color:#6b7280}

/* Inputs on right */
.stTextArea textarea, .stTextInput input{border:2px solid var(--adi-green)!important; border-radius:12px!important}
.stTextArea textarea:focus, .stTextInput input:focus{box-shadow:0 0 0 3px rgba(36,90,52,.18)!important}
main .block-container .stTextInput input::placeholder,
main .block-container .stTextArea textarea::placeholder{color:#4b5563; opacity:.9}

/* Tabs — gold underline on active */
[data-testid='stTabs'] button{font-weight:750; text-transform:uppercase; letter-spacing:.02em; color:#3e4a3e}
[data-testid='stTabs'] button[aria-selected='true']{color:var(--adi-green)!important; font-weight:900!important; border-bottom:3px solid var(--adi-gold)!important}

/* Bloom grid */
.bloom-grid{display:grid; grid-template-columns:repeat(3,1fr); gap:16px}
.bloom-col{background:#fff; border:1px solid var(--border); border-radius:14px; padding:0; overflow:hidden; box-shadow:var(--shadow)}
.tier-head{display:flex; align-items:center; gap:10px; padding:10px 12px; font-weight:900; letter-spacing:.02em; border-bottom:1px solid var(--border)}
.tier-low{background:linear-gradient(180deg,var(--low-bg),#fff); color:#1f4c2c}
.tier-med{background:linear-gradient(180deg,var(--med-bg),#fff); color:#5b3a1d}
.tier-high{background:linear-gradient(180deg,var(--high-bg),#fff); color:#2f2f2f}
.tier-pill{width:10px;height:10px;border-radius:999px; box-shadow:0 0 0 3px rgba(0,0,0,.04)}
.tier-pill.low{background:#2f6f46}.tier-pill.med{background:#8b5a2b}.tier-pill.high{background:#555}
.tier-sub{font-size:12px; color:inherit; margin-left:auto; opacity:.85; text-transform:uppercase; letter-spacing:.04em}
.bloom-body{padding:12px}

/* Bloom badges */
.badge{display:inline-flex; align-items:center; justify-content:center; padding:10px 16px; border-radius:999px; border:2px solid #cfd6cf; margin:6px 10px 10px 0; font-weight:800}
.low{background:var(--low-bg); color:#245a34}
.med{background:var(--med-bg); color:#6a4b2d}
.high{background:var(--high-bg); color:#4a4a45}
.active-glow{box-shadow:0 0 0 4px rgba(36,90,52,.22)}
.active-amber{box-shadow:0 0 0 4px rgba(200,168,90,.26)}
.active-gray{box-shadow:0 0 0 4px rgba(120,120,120,.22)}

/* Policy chip */
.policy-chip{display:inline-flex; align-items:center; gap:6px; padding:6px 10px; border-radius:999px; font-weight:700; background:#f4f6f3; color:#1f3a27; border:1px solid #dfe6df}
.policy-chip .pill{width:8px;height:8px;border-radius:999px;background:#245a34}

/* Sharper tables/editors */
[data-testid="stDataFrame"] {border-radius:14px; border:1px solid var(--border); box-shadow:var(--shadow)}

/* Ensure right-side labels are bold green */
main .block-container label{font-weight:800; color:var(--adi-green); font-size:13.5px}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------- Helpers & State -----------------------------
def ensure_state():
    ss = st.session_state
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("mcq_blocks", 10)
    ss.setdefault("mcq_df", None)
    ss.setdefault("act_df", None)
    ss.setdefault("upload_text", "")

ensure_state()

LOW_VERBS = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify"]

def _fallback(text: str, default: str) -> str:
    return text.strip() if text and str(text).strip() else default

def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    if 5 <= week <= 9:
        return "Medium"
    return "High"

# ----------------------------- Upload parsing -----------------------------
def extract_text_from_upload(up_file) -> str:
    """Extract a short snippet of text from PDF/DOCX/PPTX to seed the source box."""
    if up_file is None:
        return ""
    name = up_file.name.lower()
    text = ""
    try:
        if name.endswith(".pdf"):
            reader = PdfReader(up_file)
            for page in reader.pages[:6]:
                txt = page.extract_text() or ""
                text += txt + "\n"
        elif name.endswith(".docx"):
            doc = Document(up_file)
            for p in doc.paragraphs[:60]:
                text += p.text + "\n"
        elif name.endswith(".pptx"):
            prs = Presentation(up_file)
            for slide in prs.slides[:15]:
                for shp in slide.shapes:
                    if hasattr(shp, "text") and shp.text:
                        text += shp.text + "\n"
        return text.strip()[:1000]
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ----------------------------- Generators -----------------------------
def generate_mcq_blocks(topic: str, source: str, num_blocks: int, week: int) -> pd.DataFrame:
    topic = _fallback(topic, "Module topic")
    src_snip = _fallback(source, "Key concepts and policy points.")
    rows: List[Dict[str, Any]] = []
    for b in range(1, num_blocks + 1):
        for tier in ("Low", "Medium", "High"):
            if tier == "Low":
                verb = LOW_VERBS[b % len(LOW_VERBS)]
                stem = f"{verb.capitalize()} a basic fact about: {topic}."
            elif tier == "Medium":
                verb = MED_VERBS[b % len(MED_VERBS)]
                stem = f"{verb.capitalize()} this concept from {topic} in a practical case."
            else:
                verb = HIGH_VERBS[b % len(HIGH_VERBS)]
                stem = f"{verb.capitalize()} a policy implication of {topic} given: {src_snip[:80]}"
            opts = [f"Option A ({tier})", f"Option B ({tier})", f"Option C ({tier})", f"Option D ({tier})"]
            answer_idx = (b + ["Low", "Medium", "High"].index(tier)) % 4
            rows.append(
                {
                    "Block": b,
                    "Tier": tier,
                    "Question": stem,
                    "Option A": opts[0],
                    "Option B": opts[1],
                    "Option C": opts[2],
                    "Option D": opts[3],
                    "Answer": ["A", "B", "C", "D"][answer_idx],
                    "Explanation": f"This is a placeholder rationale linked to {topic}.",
                }
            )
    return pd.DataFrame(rows)

def generate_activities(count: int, duration: int, tier: str, topic: str) -> pd.DataFrame:
    if tier == "Low":
        verbs, pattern = LOW_VERBS, "Warm-up: {verb} the core terms in {topic}; Pair-check; Short recap."
    elif tier == "Medium":
        verbs, pattern = MED_VERBS, "Case task: {verb} key ideas from {topic} in groups; Peer review; Gallery walk."
    else:
        verbs, pattern = HIGH_VERBS, "Design task: {verb} a solution for {topic}; Present; Critique and refine."
    rows = []
    for i in range(1, count + 1):
        v = verbs[i % len(verbs)]
        rows.append(
            {
                "Tier": tier,
                "Title": f"Module: Activity {i}",
                "Objective": f"Students will {v} key content from {topic}.",
                "Steps": pattern.format(verb=v.capitalize(), topic=_fallback(topic, "the module")),
                "Materials": "Projector, handouts, whiteboard",
                "Assessment": "Participation rubric; brief exit ticket",
                "Duration (mins)": duration,
            }
        )
    return pd.DataFrame(rows)

# ----------------------------- Exporters -----------------------------
def mcq_to_docx(df: pd.DataFrame, topic: str) -> bytes:
    doc = Document()
    doc.add_heading(f"ADI MCQs — {topic}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    p = doc.add_paragraph("Each block: Low → Medium → High")
    p.runs[0].italic = True
    for b in sorted(df["Block"].unique()):
        doc.add_heading(f"Block {b}", 2)
        for _, row in df[df["Block"] == b].iterrows():
            pr = doc.add_paragraph().add_run(f"[{row['Tier']}] {row['Question']}")
            pr.bold = True
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
    lines = [f"// ADI MCQs — {topic}", f"// Exported {datetime.now():%Y-%m-%d %H:%M}", ""]
    for i, row in df.reset_index(drop=True).iterrows():
        qname = f"Block{row['Block']}-{row['Tier']}-{i+1}"
        stem = row["Question"].replace("\n", " ").strip()
        opts = [row["Option A"], row["Option B"], row["Option C"], row["Option D"]]
        ans_idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(row["Answer"].strip().upper(), 0)

        def esc(s: str) -> str:
            return s.replace("{", "\\{").replace("}", "\\}")

        lines.append(f"::{qname}:: {esc(stem)} {{")
        for j, o in enumerate(opts):
            lines.append(f"={esc(o)}" if j == ans_idx else f"~{esc(o)}")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO()
    df.to_csv(bio, index=False)
    return bio.getvalue()

def activities_to_docx(df: pd.DataFrame, topic: str) -> bytes:
    doc = Document()
    doc.add_heading(f"ADI Activities — {topic}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    for _, row in df.iterrows():
        doc.add_heading(row["Title"], 2)
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

# ----------------------------- Header -----------------------------
def _read_logo_data_uri(path: str) -> str | None:
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass
    return None

logo_uri = _read_logo_data_uri("logo.png")

with st.container():
    st.markdown(
        f"""
        <div class='adi-hero'>
          <div class='logo'>{('<img src="'+logo_uri+'" alt="ADI"/>') if logo_uri else 'ADI'}</div>
          <div>
            <div class='h-title'>ADI Builder — Lesson Activities & Questions</div>
            <div class='h-sub'>Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    # Upload
    st.markdown("<div class='side-card upload'><div class='side-cap'><i>📂</i> UPLOAD (OPTIONAL)</div><hr class='rule'/>", unsafe_allow_html=True)
    up_file = st.file_uploader("Drag and drop file here", type=["pdf", "docx", "pptx"])
    st.markdown("</div>", unsafe_allow_html=True)

    # Course context
    st.markdown("<div class='side-card context'><div class='side-cap'><i>📘</i> COURSE CONTEXT</div><hr class='rule'/>", unsafe_allow_html=True)
    st.session_state.lesson = st.selectbox("Lesson", list(range(1, 7)), index=st.session_state.lesson - 1)
    st.session_state.week = st.selectbox("Week", list(range(1, 15)), index=st.session_state.week - 1)
    bloom = bloom_focus_for_week(st.session_state.week)
    st.markdown(
        f"<span class='policy-chip'><span class='pill'></span> Week {st.session_state.week} • <strong class='bloom-focus'>{bloom}</strong> focus</span>"
        "<div style='font-size:11px;color:#6b7280;margin-top:6px'>ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # MCQs quick pick
    st.markdown("<div class='side-card mcqs'><div class='side-cap'><i>🎯</i> KNOWLEDGE MCQs (ADI POLICY)</div><hr class='rule'/>", unsafe_allow_html=True)
    st.markdown("<div class='qp'>", unsafe_allow_html=True)
    quick_list = [5, 10, 20, 30]
    default_idx = quick_list.index(st.session_state.mcq_blocks) if st.session_state.mcq_blocks in quick_list else 1
    pick = st.radio("Quick pick blocks", quick_list, horizontal=True, index=default_idx)
    st.session_state.mcq_blocks = pick
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Activities controls
    st.markdown("<div class='side-card skills'><div class='side-cap'><i>🛠</i> SKILLS ACTIVITIES</div><hr class='rule'/>", unsafe_allow_html=True)
    st.session_state.setdefault("ref_act_n", 3)
    st.session_state.setdefault("ref_act_d", 45)
    st.session_state.ref_act_n = st.number_input("Activities count", min_value=1, value=st.session_state.ref_act_n, step=1)
    st.session_state.ref_act_d = st.number_input("Duration (mins)", min_value=5, value=st.session_state.ref_act_d, step=5)
    st.markdown("</div>", unsafe_allow_html=True)

    # Prefill source from upload
    if up_file:
        st.session_state.upload_text = extract_text_from_upload(up_file)

# ----------------------------- Bloom grid render -----------------------------
def render_bloom_grid(current_focus: str):
    low_class = "badge low " + ("active-glow" if current_focus == "Low" else "")
    med_class = "badge med " + ("active-amber" if current_focus == "Medium" else "")
    high_class = "badge high " + ("active-gray" if current_focus == "High" else "")
    st.markdown("<h3 class='hsharp'>Bloom’s verbs (ADI Policy)</h3><h4 class='hsub'>Grouped by policy tiers and week ranges</h4>", unsafe_allow_html=True)
    st.markdown("<div class='bloom-grid'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='bloom-col'>"
        "<div class='tier-head tier-low'><span class='tier-pill low'></span> Low (Weeks 1–4)"
        "<span class='tier-sub'>Remember / Understand</span></div>"
        "<div class='bloom-body'>" + " ".join([f"<span class='{low_class}'>{w}</span>" for w in LOW_VERBS]) + "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='bloom-col'>"
        "<div class='tier-head tier-med'><span class='tier-pill med'></span> Medium (Weeks 5–9)"
        "<span class='tier-sub'>Apply / Analyze</span></div>"
        "<div class='bloom-body'>" + " ".join([f"<span class='{med_class}'>{w}</span>" for w in MED_VERBS]) + "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='bloom-col'>"
        "<div class='tier-head tier-high'><span class='tier-pill high'></span> High (Weeks 10–14)"
        "<span class='tier-sub'>Evaluate / Create</span></div>"
        "<div class='bloom-body'>" + " ".join([f"<span class='{high_class}'>{w}</span>" for w in HIGH_VERBS]) + "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- Tabs & main content -----------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

with mcq_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>MCQ Generator</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with col2:
        st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom}", disabled=True)

    source = st.text_area("Source text (editable)", value=st.session_state.upload_text, height=140)

    render_bloom_grid(bloom)

    if st.button("Generate MCQ Blocks"):
        with st.spinner("Building MCQ blocks…"):
            st.session_state.mcq_df = generate_mcq_blocks(topic, source, st.session_state.mcq_blocks, st.session_state.week)

    if st.session_state.mcq_df is None:
        st.info("No MCQs yet. Use the button above to generate.")
    else:
        edited = st.data_editor(st.session_state.mcq_df, num_rows="dynamic", use_container_width=True, key="mcq_editor")
        st.session_state.mcq_df = edited
        st.download_button(
            "Download Word (.docx)",
            mcq_to_docx(edited, _fallback(topic, "Module")),
            file_name="adi_mcqs.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.download_button(
            "Download Moodle (GIFT)",
            mcq_to_gift(edited, _fallback(topic, "Module")),
            file_name="adi_mcqs_gift.txt",
            mime="text/plain",
        )
        st.download_button("Download CSV", df_to_csv_bytes(edited), file_name="adi_mcqs.csv", mime="text/csv")
    st.markdown("</div>", unsafe_allow_html=True)

with act_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>Activities Planner</p>", unsafe_allow_html=True)

    default_idx = ["Low", "Medium", "High"].index(bloom if bloom in ["Low", "Medium", "High"] else "Medium")
    tier = st.radio("Emphasis", ["Low", "Medium", "High"], horizontal=True, index=default_idx)
    topic2 = st.text_input("Topic (optional)", value="", placeholder="Module or unit focus")

    if st.button("Generate Activities"):
        with st.spinner("Assembling activities…"):
            st.session_state.act_df = generate_activities(
                int(st.session_state.ref_act_n),
                int(st.session_state.ref_act_d),
                tier,
                topic2,
            )

    if st.session_state.act_df is None:
        st.info("No activities yet. Use the button above to generate.")
    else:
        act_edit = st.data_editor(st.session_state.act_df, num_rows="dynamic", use_container_width=True, key="act_editor")
        st.session_state.act_df = act_edit
        st.download_button(
            "Download Word (.docx)",
            activities_to_docx(act_edit, _fallback(topic2, "Module")),
            file_name="adi_activities.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.download_button("Download CSV", df_to_csv_bytes(act_edit), file_name="adi_activities.csv", mime="text/csv")
    st.markdown("</div>", unsafe_allow_html=True)
