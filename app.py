# ADI Builder — Lesson Activities & Questions (Streamlit, single-file)
# Run:   pip install -r requirements.txt
#        streamlit run app.py

import os
import base64
from io import BytesIO
from typing import List, Dict

import streamlit as st
import pandas as pd

# Optional parsers
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    from pptx import Presentation
except Exception:
    Presentation = None

# Word export
try:
    from docx import Document
    from docx.shared import Pt
except Exception:
    Document = None


# -------------------------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------------------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions",
                   page_icon="📘", layout="wide")

# -------------------------------------------------------------------------------------
# THEME / CSS
# -------------------------------------------------------------------------------------
ADI_CSS = """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-green-50:#EEF5F0;
  --adi-gold:#C8A85A; --bg:#FAFAF7; --card:#ffffff; --border:#d9dfda;
  --ink:#1f2937; --muted:#6b7280; --radius:18px; --pill:999px;
}
html,body{background:var(--bg)}
main .block-container{padding-top:0.8rem; padding-bottom:2rem; max-width:1220px;}
/* Header */
.adi-hero{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));
 color:#fff; border-radius:20px; padding:18px 20px; margin:8px 0 16px; box-shadow:0 10px 24px rgba(0,0,0,.06);}
.adi-hero-row{display:flex; align-items:center; gap:14px;}
.logo-box{width:48px; height:48px; border-radius:12px; background:rgba(0,0,0,.08);
 display:flex; align-items:center; justify-content:center; overflow:hidden}
.logo-fallback{font-weight:800; font-size:20px;}
.adi-title{font-weight:800; font-size:22px; margin:0}
.adi-sub{opacity:.92; font-size:12px; margin-top:2px}

/* Tabs */
.adi-tabs [role="radiogroup"]{ gap:10px; display:flex; flex-wrap:wrap; }
.adi-tabs label{ background:#f3f7f3; border:2px solid var(--adi-green-50);
 color:var(--adi-green-600); border-radius:14px; padding:10px 18px; cursor:pointer;
 font-weight:600; transition:all .2s; }
.adi-tabs label:hover{ background:#eaf5ec; }
.adi-tabs label[aria-checked="true"]{ background:var(--adi-green); color:#fff;
 border-color:var(--adi-green-600); box-shadow:0 6px 14px rgba(36,90,52,.25); }

/* Cards */
.adi-card{ background:var(--card); border:1px solid var(--border); border-radius:16px;
 box-shadow:0 10px 24px rgba(0,0,0,.06); padding:14px 14px 10px; }

/* Upload block */
.adi-upload{ border:2px dashed var(--adi-green); background:var(--adi-green-50);
 border-radius:14px; padding:12px; display:flex; gap:10px; align-items:center; }
.adi-upload .icon{ width:28px; height:28px; border-radius:7px; background:var(--adi-green);
 color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; }

/* Pills */
.pills{ display:flex; flex-wrap:wrap; gap:8px; }
.pill{ padding:8px 14px; border-radius:999px; border:1px solid #e3e7e3; background:#f3f7f3; font-size:13px; color:#25402b; cursor:pointer;}
.pill.active{ background:var(--adi-green); color:#fff; border-color:var(--adi-green-600); }

/* Inputs */
input, textarea, select{ border-radius:12px !important; }
input:focus, textarea:focus, select:focus{
  outline:none !important; border-color:var(--adi-green-600) !important;
  box-shadow:0 0 0 3px rgba(36,90,52,.25) !important; }

/* Buttons */
div.stButton>button{ background:var(--adi-green); color:#fff; border:none;
 border-radius:999px; padding:.7rem 1.1rem; font-weight:600;
 box-shadow:0 4px 12px rgba(31,76,44,.22); transition:all .25s; }
div.stButton>button:hover{ filter:brightness(.97);
 box-shadow:0 0 0 3px rgba(200,168,90,.45); }

/* Thin HR */
hr{ border:none; border-top:1px solid #e6e6e6; margin:8px 0; }

/* table-like header labels */
.smallhdr{font-size:12px; color:#6b7280; text-transform:uppercase; letter-spacing:.05em; margin-top:6px;}
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------------------------------
# LOGO (optional)
# -------------------------------------------------------------------------------------
LOGO_PATH = "logo.png"  # if you upload a logo.png in repo root
logo_data_uri = None
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_data_uri = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

# -------------------------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------------------------
with st.container():
    st.markdown(
        f"""
        <div class="adi-hero">
          <div class="adi-hero-row">
            <div class="logo-box">{('<img src="'+logo_data_uri+'" alt="ADI"/>') if logo_data_uri else '<div class="logo-fallback">A</div>'}</div>
            <div>
              <div class="adi-title">ADI Builder – Lesson Activities & Questions</div>
              <div class="adi-sub">Professional, branded, editable and export-ready.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------------------------
def bloom_by_week(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    elif 5 <= week <= 9:
        return "Medium"
    else:
        return "High"

def best_effort_text_from_upload(file) -> str:
    """
    Extract text if optional libs available. Always safe.
    """
    if file is None:
        return ""
    name = file.name.lower()
    if name.endswith(".pdf") and PyPDF2 is not None:
        try:
            reader = PyPDF2.PdfReader(file)
            text = []
            for page in reader.pages:
                t = page.extract_text() or ""
                text.append(t)
            return "\n".join(text).strip()
        except Exception:
            return ""
    elif name.endswith(".pptx") and Presentation is not None:
        try:
            prs = Presentation(file)
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return "\n".join(text).strip()
        except Exception:
            return ""
    elif name.endswith(".docx") and Document is not None:
        try:
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs]).strip()
        except Exception:
            return ""
    # fallback (unknown/unsupported)
    return ""

def export_docx(title: str, blocks: List[Dict]) -> bytes:
    if Document is None:
        return b""
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.add_heading(title, level=1)
    for b in blocks:
        doc.add_heading(b["heading"], level=2)
        for q in b["questions"]:
            doc.add_paragraph(q, style="List Number")
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.read()

def export_activities_docx(df: pd.DataFrame) -> bytes:
    if Document is None:
        return b""
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.add_heading('ADI Activities Plan', level=1)
    for idx, row in df.iterrows():
        doc.add_heading(f"Activity {idx+1}: {row.get('title','')}", level=2)
        doc.add_paragraph(f"Tier: {row.get('tier','')}")
        doc.add_paragraph(f"Objective: {row.get('objective','')}")
        doc.add_paragraph("Steps:")
        for step in str(row.get('steps','')).split(";"):
            step = step.strip()
            if step:
                doc.add_paragraph(step, style='List Bullet')
        doc.add_paragraph(f"Materials: {row.get('materials','')}")
        doc.add_paragraph(f"Assessment: {row.get('assessment','')}")
        if 'duration' in row:
            doc.add_paragraph(f"Duration: {row.get('duration')} mins")
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.read()

def mcq_templates(low_topic, med_topic, high_topic) -> List[str]:
    """
    Simple templates to avoid LLM; safe placeholders that staff can edit.
    """
    low = f"Define the term related to: {low_topic}. (A) ... (B) ... (C) ... (D) ..."
    med = f"Apply the concept of {med_topic} to this scenario: _____. (A) ... (B) ... (C) ... (D) ..."
    high = f"Evaluate the approach for {high_topic}. Which option is best and why? (A) ... (B) ... (C) ... (D) ..."
    return [low, med, high]

def make_mcq_blocks(n_blocks: int, topic: str, source: str, week: int) -> List[Dict]:
    """
    Each block has 3 Qs: Low/Medium/High.
    We seed them with topic/source to keep relevant; staff can edit afterward.
    """
    blocks = []
    for i in range(n_blocks):
        # Simple heuristic to vary text a touch
        t_low = topic or "module key term"
        t_med = topic or "module concept"
        t_high = topic or "module approach"
        qs = mcq_templates(t_low, t_med, t_high)
        blocks.append({"heading": f"Block {i+1}", "questions": qs})
    return blocks

def to_blocks_df(blocks: List[Dict]) -> pd.DataFrame:
    # Flatten to show/edit
    rows = []
    for b in blocks:
        q1, q2, q3 = b["questions"]
        rows.append({"block": b["heading"], "LOW": q1, "MEDIUM": q2, "HIGH": q3})
    return pd.DataFrame(rows)

def from_blocks_df(df: pd.DataFrame) -> List[Dict]:
    out = []
    for _, r in df.iterrows():
        out.append({"heading": r["block"],
                    "questions": [r["LOW"], r["MEDIUM"], r["HIGH"]]})
    return out

def ensure_activities_df(seed_df: pd.DataFrame):
    if "activities_df" not in st.session_state:
        st.session_state.activities_df = seed_df.copy()
    return st.session_state.activities_df

# -------------------------------------------------------------------------------------
# TABS NAV
# -------------------------------------------------------------------------------------
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Knowledge MCQs (ADI Policy)"

with st.container():
    st.markdown('<div class="adi-tabs">', unsafe_allow_html=True)
    tab_choice = st.radio(
        "choose",
        options=["Knowledge MCQs (ADI Policy)", "Skills Activities"],
        index=0 if st.session_state.active_tab.startswith("Knowledge") else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="adi_tabs_radio",
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.session_state.active_tab = tab_choice

# -------------------------------------------------------------------------------------
# PAGE LAYOUT
# -------------------------------------------------------------------------------------
left, right = st.columns([0.95, 2.05], gap="large")

# -------------------------
# LEFT PANEL (UPLOAD + PICKERS)
# -------------------------
with left:
    # Upload card
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Upload eBook / Lesson Plan / PPT")
    st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
    st.markdown(
        '<div class="adi-upload"><div class="icon">UP</div>'
        '<div><strong>Drag and drop</strong> your file here, or <u>Browse</u><br>'
        '<small>We recommend eBooks (PDF) as source for best results.</small></div></div>',
        unsafe_allow_html=True,
    )
    upload = st.file_uploader(" ", type=["pdf", "docx", "pptx"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # Pickers
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Pick from eBook / Plan / PPT")

    # Lesson pills
    st.markdown("**Lesson**")
    if "lesson" not in st.session_state: st.session_state.lesson = 1
    cols = st.columns(6)
    for i, c in enumerate(cols, start=1):
        with c:
            active = (st.session_state.lesson == i)
            if st.button(f"{i}", key=f"lesson_{i}", use_container_width=True):
                st.session_state.lesson = i
            st.markdown(
                f"<div class='pill {'active' if active else ''}'></div>",
                unsafe_allow_html=True
            )

    # Week pills (1..14)
    st.markdown("**Week**")
    if "week" not in st.session_state: st.session_state.week = 1
    row1 = st.columns(7)
    row2 = st.columns(7)
    for i in range(1, 8):
        with row1[i-1]:
            active = (st.session_state.week == i)
            if st.button(f"{i}", key=f"week_{i}", use_container_width=True):
                st.session_state.week = i
            st.markdown(f"<div class='pill {'active' if active else ''}'></div>",
                        unsafe_allow_html=True)
    for i in range(8, 15):
        with row2[i-8]:
            active = (st.session_state.week == i)
            if st.button(f"{i}", key=f"week_{i}", use_container_width=True):
                st.session_state.week = i
            st.markdown(f"<div class='pill {'active' if active else ''}'></div>",
                        unsafe_allow_html=True)

    st.caption("**ADI policy:** Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. The appropriate Bloom tier will be auto-highlighted below.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Activity Parameters (used on Activities tab)
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Activity Parameters")
    c1, c2 = st.columns(2)
    with c1:
        activities_count = st.number_input("Number of activities", min_value=1, max_value=10, value=3, step=1)
    with c2:
        duration_mins = st.number_input("Duration (mins) (per activity)", min_value=5, max_value=120, value=45, step=5)
    st.caption("ADI Bloom tiers used for MCQs are shown on the right.")
    st.markdown('</div>', unsafe_allow_html=True)


# -------------------------
# RIGHT PANEL (CONTENT)
# -------------------------
with right:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)

    if st.session_state.active_tab.startswith("Knowledge"):
        # ----------------- MCQs -----------------
        st.markdown("### Generate MCQs — Policy Blocks (Low → Medium → High)")

        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source_text = st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here...")

        # Auto-fill from upload if empty and user wants
        if upload and st.button("Pull → MCQs from Upload"):
            with st.spinner("Reading file..."):
                txt = best_effort_text_from_upload(upload)
                if txt:
                    source_text = txt
                    st.session_state["source_text"] = txt
                    st.success("Pulled text from uploaded file.")
                else:
                    st.warning("Could not extract text (unsupported or empty). You can paste text manually.")

        st.caption("How many MCQ blocks? (×3 questions)")
        n_blocks = st.number_input(" ", min_value=1, max_value=30, value=10, step=1, key="mcq_blocks")

        if st.button("Generate MCQ Blocks"):
            with st.spinner("Generating blocks..."):
                # Use session copy of source text if we pulled earlier
                if "source_text" in st.session_state and not source_text:
                    source_text = st.session_state["source_text"]

                blocks = make_mcq_blocks(n_blocks, topic, source_text, st.session_state.week)
                st.session_state["mcq_blocks"] = blocks
                st.session_state["mcq_df"] = to_blocks_df(blocks)
            st.success("MCQ blocks generated.")

        # Show editor if exists
        if "mcq_df" in st.session_state:
            st.markdown("#### Preview & Edit (each block contains Low/Medium/High)")
            mcq_df = st.session_state["mcq_df"].copy()
            edited = st.data_editor(
                mcq_df,
                use_container_width=True,
                hide_index=True,
                key="mcq_editor"
            )
            if st.button("Apply MCQ Edits"):
                st.session_state["mcq_df"] = edited
                st.session_state["mcq_blocks"] = from_blocks_df(edited)
                st.success("Edits applied.")

            dl1, dl2 = st.columns(2)
            with dl1:
                data = edited.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", data=data, file_name="adi_mcqs.csv", mime="text/csv", use_container_width=True)
            with dl2:
                doc_bytes = export_docx("ADI MCQ Blocks", st.session_state["mcq_blocks"])
                st.download_button("Download Word (.docx)", data=doc_bytes, file_name="adi_mcqs.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   use_container_width=True)

        # Bloom hint
        st.markdown("---")
        st.caption(f"**Bloom focus for Week {st.session_state.week}:** {bloom_by_week(st.session_state.week)}")

    else:
        # ----------------- ACTIVITIES -----------------
        st.markdown("### Generate Activities")

        # Quick pill pick for tier (based on week, default):
        default_tier = bloom_by_week(st.session_state.week)
        tiers = ["Low", "Medium", "High"]
        tier_idx = tiers.index(default_tier)

        c_t1, c_t2, c_t3 = st.columns(3)
        chosen_tier = default_tier
        with c_t1:
            if st.button("Low", use_container_width=True):
                chosen_tier = "Low"
        with c_t2:
            if st.button("Medium", use_container_width=True):
                chosen_tier = "Medium"
        with c_t3:
            if st.button("High", use_container_width=True):
                chosen_tier = "High"
        st.caption(f"Default tier from Week {st.session_state.week}: **{default_tier}** (override above if needed)")

        def seed_activities(n: int, mins: int, tier: str) -> pd.DataFrame:
            rows = []
            for i in range(1, n+1):
                rows.append({
                    "tier": tier,
                    "title": f"Module: Activity {i}",
                    "objective": "Students will apply the core concept of Module.",
                    "steps": "Briefing (5m); Main task (25m); Share-out (10m)",
                    "materials": "Projector, handout, whiteboard",
                    "assessment": "Participation + short reflection",
                    "duration": mins
                })
            return pd.DataFrame(rows)

        if st.button("Generate Activity Plan"):
            with st.spinner("Generating plan..."):
                seed_df = seed_activities(activities_count, duration_mins, chosen_tier)
                st.session_state["activities_df"] = seed_df
            st.success("Activities generated.")

        if "activities_df" in st.session_state:
            st.markdown("#### Preview & Edit")
            df = st.session_state["activities_df"]

            # headers
            h1, h2, h3, h4, h5, h6 = st.columns([0.9, 1.2, 1.4, 2.2, 1.2, 1.3])
            with h1: st.markdown("<div class='smallhdr'>Tier</div>", unsafe_allow_html=True)
            with h2: st.markdown("<div class='smallhdr'>Title</div>", unsafe_allow_html=True)
            with h3: st.markdown("<div class='smallhdr'>Objective</div>", unsafe_allow_html=True)
            with h4: st.markdown("<div class='smallhdr'>Steps</div>", unsafe_allow_html=True)
            with h5: st.markdown("<div class='smallhdr'>Materials</div>", unsafe_allow_html=True)
            with h6: st.markdown("<div class='smallhdr'>Assessment</div>", unsafe_allow_html=True)

            tiers_list = ["Low", "Medium", "High"]
            edited_rows = []

            with st.form("activities_editor_form", clear_on_submit=False):
                for i, row in df.reset_index(drop=True).iterrows():
                    c1, c2, c3, c4, c5, c6 = st.columns([0.9, 1.2, 1.4, 2.2, 1.2, 1.3])
                    with c1:
                        tier_v = st.selectbox(
                            label=f"Tier_{i}",
                            options=tiers_list,
                            index=(tiers_list.index(row.get('tier','Medium')) if row.get('tier','Medium') in tiers_list else 1),
                            key=f"tier_{i}"
                        )
                    with c2:
                        title_v = st.text_input(" ", value=row.get('title',''), key=f"title_{i}")
                    with c3:
                        obj_v = st.text_input("  ", value=row.get('objective',''), key=f"obj_{i}")
                    with c4:
                        steps_v = st.text_area("   ", value=row.get('steps',''), key=f"steps_{i}", height=80,
                                               help="Use ; to separate steps, e.g. 'Briefing (5m); Main task (25m); Share-out (10m)'")
                    with c5:
                        mats_v = st.text_input("    ", value=row.get('materials',''), key=f"mats_{i}")
                    with c6:
                        assess_v = st.text_input("     ", value=row.get('assessment',''), key=f"assess_{i}")

                    edited_rows.append({
                        "tier": tier_v, "title": title_v, "objective": obj_v, "steps": steps_v,
                        "materials": mats_v, "assessment": assess_v, "duration": row.get("duration", duration_mins)
                    })
                    st.markdown("<hr/>", unsafe_allow_html=True)

                applied = st.form_submit_button("Apply edits")

            if applied:
                st.session_state["activities_df"] = pd.DataFrame(edited_rows)
                st.success("Edits applied.")

            # Downloads
            d1, d2 = st.columns(2)
            with d1:
                csv_bytes = st.session_state["activities_df"].to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", data=csv_bytes, file_name="adi_activities_plan.csv",
                                   mime="text/csv", use_container_width=True)
            with d2:
                docx_bytes = export_activities_docx(st.session_state["activities_df"])
                st.download_button("Download Word (.docx)", data=docx_bytes, file_name="adi_activities_plan.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

  
