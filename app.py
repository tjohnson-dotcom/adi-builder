# app.py — ADI Builder (Streamlit, ADI Bloom Policy)
# MCQs: 3-question blocks (Low→Medium→High) with approved verbs; per-question Passage/Image
# Activities with steps; Exports: DOCX + RTF; Full Pack DOCX
# Branded UI (ADI green), safe file_uploader handling, Lesson/Week extract, PDF/DOCX/PPTX parsing

from __future__ import annotations
import os, re
from io import BytesIO
from datetime import datetime
import streamlit as st

# ---------- Optional libs ----------
try:
    from docx import Document
    from docx.shared import Pt, Inches
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except Exception:
    PPTX_AVAILABLE = False

# ---------- Page + Brand ----------
st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")
ADI_GREEN = "#006C35"; ADI_BEIGE = "#C8B697"; ADI_SAND = "#D9CFC2"; ADI_BROWN = "#6B4E3D"; ADI_GRAY = "#F5F5F5"

st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%); }}
html,body,[class*="css"] {{ font-family: 'Segoe UI', Inter, Roboto, system-ui, -apple-system, sans-serif; }}
h1,h2,h3 {{ color:{ADI_GREEN}; font-weight: 750; }}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  border-bottom: 4px solid {ADI_GREEN}; color:{ADI_GREEN}; font-weight: 650;
}}
.banner {{ background:{ADI_GREEN}; color:#fff; padding:18px 28px; border-radius:12px; margin: 12px 0 18px; }}
.badge {{ display:inline-block; background:{ADI_BEIGE}; color:#222; padding:3px 9px; border-radius:9px; font-size:.8rem; margin-left:8px; }}
.card {{ background:#fff; border-radius:16px; box-shadow:0 6px 18px rgba(0,0,0,.06); padding:18px; border-left:6px solid {ADI_GREEN}; margin:14px 0; }}
.card h4 {{ margin:0 0 8px 0; color:{ADI_GREEN}; }}
.card .meta {{ color:#666; font-size:.9rem; margin-bottom:8px; }}
.card .label {{ font-weight:650; color:{ADI_BROWN}; }}
.stButton>button {{ background:{ADI_GREEN}; color:#fff; border:none; border-radius:10px; padding:8px 14px; font-weight:600; }}
.stButton>button:hover {{ background:#0c5a2f; }}
textarea {{ border:1.4px solid #c7c7c7 !important; border-radius:10px !important; padding:10px !important; background:#fff !important; }}
textarea:focus {{ outline:none !important; border-color:{ADI_GREEN} !important; box-shadow:0 0 0 2px rgba(0,108,53,.15); }}
.chips {{ display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 0; }}
.chip {{ background:{ADI_SAND}; color:{ADI_BROWN}; border:1px solid #e9e0d6; padding:4px 8px; border-radius:999px; font-size:.8rem; }}
.chip.more {{ background:#eee; color:#555; }}
.answer-badge {{ background:{ADI_GREEN}; color:#fff; border-radius:999px; padding:2px 8px; font-size:.8rem; }}
.btnrow {{ display:flex; gap:8px; flex-wrap:wrap; margin:6px 0 8px; }}

/* Difficulty slider (bold centered label, green track/thumb) */
.stSlider label p {{
  text-align: center !important;
  font-weight: 700 !important;
  color: {ADI_GREEN} !important;
}}
.stSlider > div[data-baseweb="slider"] > div {{ background: {ADI_GREEN} !important; }}
.stSlider [role="slider"] {{
  background: white !important; border: 2px solid {ADI_GREEN} !important;
}}

/* Verb multiselect pills (beige/green) */
.stMultiSelect [data-baseweb="tag"] {{
  background: {ADI_BEIGE} !important; color: {ADI_GREEN} !important;
  border-radius: 999px !important; font-weight: 600 !important;
}}
.stMultiSelect [data-baseweb="tag"] svg {{ display:none; }}
.stMultiSelect div[role="option"] {{
  background: {ADI_BEIGE} !important; color: {ADI_GREEN} !important;
  border-radius: 12px !important; padding: 4px 8px !important; font-weight: 600 !important;
}}
.stMultiSelect div[role="option"]:hover {{ background: {ADI_GREEN} !important; color: white !important; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="banner">
  <h1>🎓 ADI Builder — Lesson Activities & Questions <span class="badge">Branded</span></h1>
</div>
""", unsafe_allow_html=True)
st.caption("Professional, branded, editable and export-ready.")

# ---------- Logo ----------
def sidebar_brand():
    path = "assets/adi-logo.png"
    if os.path.exists(path):
        st.sidebar.image(path, width=180)
    else:
        st.sidebar.markdown(
            f"<div style='font-weight:700;color:{ADI_GREEN};font-size:1.05rem;'>Academy of Defense Industries</div>",
            unsafe_allow_html=True
        )
sidebar_brand()

# ---------- RTF helper ----------
def to_rtf(title: str, body: str) -> bytes:
    def esc(s: str) -> str:
        s = s.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
        return s.replace("\r\n","\n").replace("\r","\n").replace("\n", r"\line ")
    parts = [r"{\rtf1\ansi\deff0", r"{\fonttbl{\f0 Calibri;}}", r"\fs22", r"\pard\f0 "]
    if title: parts.append(r"\b "+esc(title)+r"\b0\line\line ")
    parts.append(esc(body)); parts.append("}")
    return "\n".join(parts).encode("utf-8")

# ---------- ADI Bloom Policy (approved verbs per tier) ----------
ADI_LOW   = ["define","identify","list","recall","describe","label","recognize","state","name","select"]
ADI_MED   = ["apply","demonstrate","interpret","compare","classify","use","solve","illustrate","organize","explain"]
ADI_HIGH  = ["analyze","evaluate","justify","design","formulate","develop","critique","prioritize","propose","synthesize"]

# ---------- Upload + parse ----------
st.sidebar.header("Upload eBook / Lesson Plan / PPT")
upload = st.sidebar.file_uploader("PDF / DOCX / PPTX (≤200MB)", type=["pdf","docx","pptx"])

@st.cache_resource(show_spinner=False)
def parse_file(file):
    if file is None: return ""
    name = file.name.lower()
    if name.endswith(".pdf") and PDF_AVAILABLE:
        reader = PdfReader(file); return "\n".join((p.extract_text() or "") for p in reader.pages)
    if name.endswith(".docx") and DOCX_AVAILABLE:
        from docx import Document as _D
        doc = _D(file); return "\n".join(p.text for p in doc.paragraphs)
    if name.endswith(".pptx") and PPTX_AVAILABLE:
        prs = Presentation(file); parts=[]; 
        for s in prs.slides:
            for shp in s.shapes:
                if hasattr(shp, "text"): parts.append(shp.text)
        return "\n".join(parts)
    return ""

@st.cache_resource(show_spinner=False)
def index_sections(full_text: str):
    if not full_text: return {}, {}
    t = re.sub(r"\u00a0", " ", full_text)
    lm = list(re.finditer(r"(?im)^(lesson\s*(\d{1,2}))\b.*$", t))
    wm = list(re.finditer(r"(?im)^(week\s*(\d{1,2}))\b.*$", t))
    def slice_by(matches):
        sec = {}
        for i,m in enumerate(matches):
            start = m.start(); end = matches[i+1].start() if i+1<len(matches) else len(t)
            try: idx = int(m.group(2))
            except: continue
            sec[idx] = t[start:end].strip()
        return sec
    return slice_by(lm), slice_by(wm)

if upload is not None and "parsed_text_blob" not in st.session_state:
    blob = parse_file(upload)
    st.session_state.parsed_text_blob = blob
    st.session_state.lessons, st.session_state.weeks = index_sections(blob)

# ---------- Lesson/Week picker ----------
if st.session_state.get("parsed_text_blob"):
    st.sidebar.subheader("Pick from eBook/Plan/PPT")
    lkeys = sorted(st.session_state.lessons.keys()) or list(range(1,15))
    wkeys = sorted(st.session_state.weeks.keys()) or list(range(1,15))
    sel_l = st.sidebar.selectbox("📖 Lesson", options=["—"]+[str(k) for k in lkeys], index=0)
    sel_w = st.sidebar.selectbox("🗓️ Week",   options=["—"]+[str(k) for k in wkeys], index=0)
    c1,c2 = st.sidebar.columns(2)
    pull_mcq  = c1.button("Pull → MCQs")
    pull_acts = c2.button("Pull → Activities")

    def selected_text():
        parts=[]
        if sel_l.isdigit() and int(sel_l) in st.session_state.lessons: parts.append(st.session_state.lessons[int(sel_l)])
        if sel_w.isdigit() and int(sel_w) in st.session_state.weeks:   parts.append(st.session_state.weeks[int(sel_w)])
        return "\n\n".join(parts).strip()

    preview = selected_text()
    if preview:
        st.sidebar.caption("Preview of selection:")
        st.sidebar.text_area("", value=preview[:2000], height=140)
    else:
        st.sidebar.caption("No headings found — generic selectors shown.")
    if pull_mcq:  st.session_state.mcq_seed = preview
    if pull_acts: st.session_state.act_seed = preview

# ---------- Activity parameters ----------
st.sidebar.subheader("Activity Parameters")
col1,col2 = st.sidebar.columns(2)
num_activities = col1.number_input("Activities", 1, 10, 3)
duration       = col2.number_input("Duration (mins)", 5, 180, 45)

# Simple info chips for verbs (visual only)
st.sidebar.caption("ADI Bloom tiers used for MCQs:")
st.sidebar.markdown("<div class='chips'>"+"".join(f"<span class='chip'>{v}</span>" for v in ADI_LOW[:4])+ "<span class='chip more'>+low</span></div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='chips'>"+"".join(f"<span class='chip'>{v}</span>" for v in ADI_MED[:4])+ "<span class='chip more'>+med</span></div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='chips'>"+"".join(f"<span class='chip'>{v}</span>" for v in ADI_HIGH[:4])+ "<span class='chip more'>+high</span></div>", unsafe_allow_html=True)

# ---------- Tabs ----------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# ---------- MCQs (Policy: 3 per block) ----------
with mcq_tab:
    st.subheader("Generate MCQs (3 per block: Low → Medium → High)")
    if st.session_state.get("mcq_seed"): st.success("Lesson/Week text inserted into MCQ editor.")
    topic = st.text_input("Topic / Outcome (optional)", "Module description, knowledge & skills outcomes")
    base_text = st.text_area("Source text (optional, editable)", value=st.session_state.get("mcq_seed",""), height=160)
    blocks = st.number_input("How many MCQ blocks? (x3 questions)", 1, 20, 1)

    def make_low_q(t):
        stem = f"Which option best **{ADI_LOW[0]}s** or **{ADI_LOW[1]}** a key concept in {t}?"
        opts = ["A) A vague opinion","B) A precise statement with essential characteristics","C) An unrelated anecdote","D) A random number"]
        return stem, opts, "B"
    def make_med_q(t):
        stem = f"You need to **{ADI_MED[0]}** {t} in a new context. What is the **most appropriate** first step?"
        opts = ["A) Repeat the definition","B) Identify variables/constraints; choose a method to apply","C) Collect unrelated data","D) Ignore context and proceed"]
        return stem, opts, "B"
    def make_high_q(t):
        stem = f"Given constraints, **{ADI_HIGH[1]}** two approaches to {t}. Which choice **best justifies** the recommendation?"
        opts = ["A) Cites unrelated evidence","B) States assumptions and criteria, weighing trade-offs","C) Focuses on formatting over reasoning","D) Mentions outcomes without criteria"]
        return stem, opts, "B"

    if st.button("Generate MCQ Blocks"):
        all_q = []
        for b in range(int(blocks)):
            all_q.extend([make_low_q(topic), make_med_q(topic), make_high_q(topic)])

        edited_blocks=[]
        for i,(stem,opts,ans) in enumerate(all_q, start=1):
            st.markdown(f"""
            <div class='card'>
              <h4>📝 Question {i}</h4>
              <div class='meta'>Policy tier: {"Low" if i%3==1 else "Medium" if i%3==2 else "High"}</div>
              <div>{stem}</div>
              <div style='margin-top:6px;'>{'<br/>'.join(opts)}</div>
              <div style='margin-top:8px;'>Answer: <span class='answer-badge'>{ans}</span></div>
            </div>
            """, unsafe_allow_html=True)

            q_text = stem + "\n" + "\n".join(opts) + f"\nAnswer: {ans}"
            box = st.text_area(f"✏️ Edit Q{i}", q_text, key=f"mcq_edit_{i}", height=118)

            passage_key = f"mcq_passage_{i}"
            img_key     = f"mcq_img_{i}"
            st.text_area(f"📄 Passage (optional) for Q{i}", value=st.session_state.get(passage_key, ""), key=passage_key, height=80)
            st.file_uploader(f"🖼️ Image (optional) for Q{i}", type=["png","jpg","jpeg"], key=img_key)

            edited_blocks.append(box)

        # Exports
        def mcq_blocks_to_docx(blocks_text):
            if not DOCX_AVAILABLE: return None
            doc = Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Knowledge MCQs (Policy Blocks)', level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for idx, blk in enumerate(blocks_text,1):
                tier = "Low" if idx%3==1 else "Medium" if idx%3==2 else "High"
                lines=[l.rstrip() for l in blk.splitlines() if l.strip()]
                if not lines: continue
                stem=lines[0]; options=[l for l in lines[1:] if re.match(r"^[A-D]\)", l)]
                ans_line = next((l for l in lines if l.lower().startswith("answer:")), "")
                doc.add_heading(f"Question {idx} — {tier}", level=2)

                pkey=f"mcq_passage_{idx}"
                ptxt = st.session_state.get(pkey, "").strip()
                if ptxt:
                    doc.add_heading("Passage", level=3); doc.add_paragraph(ptxt)

                doc.add_paragraph(stem)

                ikey=f"mcq_img_{idx}"
                img = st.session_state.get(ikey)
                if img is not None:
                    try: img.seek(0); doc.add_picture(img, width=Inches(4.5))
                    except Exception: doc.add_paragraph("[Image could not be embedded]")

                for opt in options: doc.add_paragraph(opt, style="List Bullet")
                if ans_line:
                    p = doc.add_paragraph(ans_line); 
                    if p.runs: p.runs[0].italic = True
                doc.add_paragraph("")
            bio = BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

        txt_payload = "\n\n".join(edited_blocks)
        st.download_button("🗎 Word (.rtf)", to_rtf("ADI Builder — Knowledge MCQs (Policy Blocks)", txt_payload), file_name="mcqs_policy.rtf")
        docx_payload = mcq_blocks_to_docx(edited_blocks)
        if docx_payload:
            st.download_button("📝 Word (.docx)", docx_payload, file_name="mcqs_policy.docx")
        st.session_state["mcq_blocks"] = edited_blocks  # for Full Pack

# ---------- Activities ----------
with act_tab:
    st.subheader("Generate Skills Activities")
    context_text = st.text_area("Context from eBook / notes (editable)", value=st.session_state.get("act_seed",""), height=160)

    if "activity_duration" not in st.session_state: st.session_state.activity_duration = duration

    if st.button("Generate Activities", type="primary"):
        activities=[]
        for i in range(1, num_activities+1):
            t_intro = max(3, round(0.15*duration))
            t_work  = max(10, duration - t_intro - 5)
            t_share = max(2, duration - t_intro - t_work)

            step1 = f"Read/skim the provided context and highlight key terms related to the learning outcome. ({t_intro} min)"
            step2 = f"In pairs/small groups, apply the concept to the scenario: identify variables, assumptions, and constraints. ({t_work} min)"
            step3 = f"Create a concise output (diagram or 3–slide mini-deck). Prepare a 1-minute share-out. ({t_share} min)"

            checks = [
                "Output correctly applies the concept",
                "Assumptions and constraints are noted",
                "Visual is clear and labeled",
                "Team justifies choices during share-out",
            ]
            materials = "Markers, sticky notes or Miro; slides/handout template (optional)."
            grouping = "Pairs or groups of 3."

            act_text = (
                f"Activity {i} — {duration} mins\n"
                f"Grouping: {grouping}\n"
                f"Materials: {materials}\n"
                f"Context:\n{context_text.strip() or '[Add notes or use selected Lesson/Week extract]'}\n\n"
                f"Steps:\n1) {step1}\n2) {step2}\n3) {step3}\n\n"
                f"Output: Diagram or 3-slide mini-deck (export to LMS).\n"
                f"Evidence: Photo or upload to LMS.\n"
                f"Success criteria:\n- " + "\n- ".join(checks)
            )
            activities.append(act_text)

            st.markdown(f"""
            <div class='card'>
              <h4>⭐ Activity {i} — {duration} mins</h4>
              <div class='meta'>Grouping: {grouping}</div>
              <div><span class='label'>🧩 Context:</span> {('Provided' if context_text else 'Add notes or use Lesson/Week extract')}</div>
              <div style='margin-top:8px;'><span class='label'>🛠️ Materials:</span> {materials}</div>
              <div style='margin-top:8px;'><span class='label'>📋 Steps:</span>
                <ol><li>{step1}</li><li>{step2}</li><li>{step3}</li></ol>
              </div>
              <div><span class='label'>📊 Output:</span> Diagram or 3-slide mini-deck.</div>
              <div><span class='label'>📤 Evidence:</span> Photo or upload to LMS.</div>
              <div style='margin-top:8px;'><span class='label'>✅ Success criteria:</span>
                <ul>{''.join([f'<li>{c}</li>' for c in checks])}</ul>
              </div>
            </div>
            """, unsafe_allow_html=True)

        text_output = "\n\n".join(activities)
        edited_output = st.text_area("✏️ Review & edit before export:", text_output, key="act_edit", height=220)

        st.session_state["activities_list"] = activities

        # Exports
        st.download_button("🗎 Word (.rtf)", to_rtf("ADI Builder — Skills Activities", edited_output), file_name="activities.rtf")
        if DOCX_AVAILABLE:
            doc = Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Skills Activities', level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for block in activities:
                lines=[l.rstrip() for l in block.split('\n')]
                title = next((l for l in lines if l.startswith("Activity ")), "Activity")
                doc.add_heading(title, level=2)
                doc.add_paragraph("\n".join(lines))
                doc.add_paragraph("")
            bio = BytesIO(); doc.save(bio); bio.seek(0)
            st.download_button("📝 Word (.docx)", bio.getvalue(), file_name="activities.docx")

# ---------- Full Pack (DOCX) ----------
if DOCX_AVAILABLE and (st.session_state.get("mcq_blocks") or st.session_state.get("activities_list")):
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Export — Full Pack (.docx)")
    st.caption("One Word doc with MCQs and Activities, ready for Moodle/print.")

    def build_full_pack_docx(mcq_blocks, activities_list):
        doc = Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
        doc.add_heading('ADI Builder — Lesson Pack', 0)
        doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))

        if mcq_blocks:
            doc.add_heading('Section A — Knowledge MCQs (Policy Blocks)', level=1)
            for idx, blk in enumerate(mcq_blocks, 1):
                tier = "Low" if idx%3==1 else "Medium" if idx%3==2 else "High"
                lines=[l.rstrip() for l in blk.splitlines() if l.strip()]
                if not lines: continue
                stem=lines[0]; options=[l for l in lines[1:] if re.match(r"^[A-D]\)", l)]
                ans_line = next((l for l in lines if l.lower().startswith('answer:')), '')
                doc.add_heading(f"Question {idx} — {tier}", level=2)
                pkey=f"mcq_passage_{idx}"
                ptxt = st.session_state.get(pkey, "").strip()
                if ptxt: doc.add_heading("Passage", level=3); doc.add_paragraph(ptxt)
                doc.add_paragraph(stem)
                ikey=f"mcq_img_{idx}"
                img = st.session_state.get(ikey)
                if img is not None:
                    try: img.seek(0); doc.add_picture(img, width=Inches(4.5))
                    except Exception: doc.add_paragraph("[Image could not be embedded]")
                for opt in options: doc.add_paragraph(opt, style="List Bullet")
                if ans_line:
                    p = doc.add_paragraph(ans_line); 
                    if p.runs: p.runs[0].italic = True
                doc.add_paragraph("")

        if activities_list:
            doc.add_page_break()
            doc.add_heading('Section B — Skills Activities', level=1)
            for block in activities_list:
                lines=[l.rstrip() for l in block.split('\n')]
                title = next((l for l in lines if l.startswith("Activity ")), "Activity")
                doc.add_heading(title, level=2)
                doc.add_paragraph("\n".join(lines))
                doc.add_paragraph("")

        out = BytesIO(); doc.save(out); out.seek(0); return out.getvalue()

    full_docx = build_full_pack_docx(st.session_state.get("mcq_blocks", []),
                                     st.session_state.get("activities_list", []))
    st.download_button("🧾 Full Pack (.docx)", full_docx, file_name="adi_lesson_pack.docx")
