# app.py — ADI Builder (Streamlit, Branded + Upload + Lesson/Week Extractor + Bloom Verbs + Full Exports)
# Upload eBook/Plan/PPT → select Lesson/Week → generate MCQs & step-by-step Activities → edit → export (TXT, GIFT, DOC, DOCX, Full Pack).

from __future__ import annotations
import streamlit as st
from io import BytesIO
from datetime import datetime
import re
import os

# ---- Optional libs (graceful fallbacks) ----
try:
    from docx import Document
    from docx.shared import Pt
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

st.set_page_config(page_title="ADI Builder", page_icon="🎓", layout="wide")

# ---- Brand colors ----
ADI_GREEN = "#006C35"
ADI_BEIGE = "#C8B697"
ADI_SAND  = "#D9CFC2"
ADI_BROWN = "#6B4E3D"
ADI_GRAY  = "#F5F5F5"

# ---- CSS ----
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(180deg, #ffffff 0%, {ADI_GRAY} 100%); }}
html, body, [class*="css"] {{ font-family: 'Segoe UI', Roboto, Inter, sans-serif; }}
h1, h2, h3 {{ font-weight: 700; color: {ADI_GREEN}; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  border-bottom: 4px solid {ADI_GREEN};
  font-weight: 600; color: {ADI_GREEN};
}}

/* Banner */
.banner {{ background: {ADI_GREEN}; color: white; padding: 18px 28px; border-radius: 0 0 12px 12px;
          display: flex; align-items: center; gap:12px; margin-bottom: 18px; }}
.banner h1 {{ color: white !important; font-size: 1.6rem; margin: 0; }}

/* Cards */
.card {{ background:#fff; border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,0.08); padding:20px; margin:14px 0; border-left:6px solid {ADI_GREEN}; }}
.card h4 {{ margin:0 0 10px 0; color:{ADI_GREEN}; }}
.card .meta {{ color:#666; font-size:0.9rem; margin-bottom:8px; }}
.card .label {{ font-weight:600; color:{ADI_BROWN}; }}

/* Toolbar */
.toolbar {{ display:flex; justify-content:flex-end; gap:12px; margin:16px 0; flex-wrap: wrap; }}

/* Buttons */
.stButton>button {{ background:{ADI_GREEN}; color:#fff; border:none; border-radius:10px; padding:8px 14px; font-weight:600; font-size:0.9rem; white-space:nowrap; transition:background .2s; }}
.stButton>button:hover {{ background:{ADI_BROWN}; }}

/* Inputs / text areas visibility */
textarea {{ border:1.5px solid #bbb !important; border-radius:10px !important; padding:10px !important; background:#fff !important; }}
textarea:focus {{ outline:none !important; border-color:{ADI_GREEN} !important; box-shadow:0 0 0 2px rgba(0,108,53,0.15); }}

/* Chips + badge */
.badge {{ display:inline-block; padding:4px 8px; background:{ADI_BEIGE}; border-radius:8px; font-size:.8rem; color:#333; }}
.chips {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }}
.chip {{ background:{ADI_SAND}; color:{ADI_BROWN}; border:1px solid #e7ddd2; padding:4px 8px; border-radius:999px; font-size:.8rem; }}
.chip.more {{ background:#f0ebe4; color:#555; }}

/* Multiselect chips */
.stMultiSelect [data-baseweb="tag"] {{ background:{ADI_GREEN}; color:#fff; border-radius:999px; }}
.stMultiSelect [data-baseweb="tag"] svg {{ display:none; }}

/* Inline pill buttons */
.btn-row {{ display:flex; gap:10px; flex-wrap:wrap; }}
.btn-row .stButton>button {{ border-radius:999px; }}

/* Answer badge */
.answer-badge {{ display:inline-block; background:{ADI_GREEN}; color:#fff; padding:2px 8px; border-radius:999px; font-size:0.8rem; }}
</style>
""", unsafe_allow_html=True)

# ---- Banner (text-only) ----
st.markdown("""
<div class='banner'>
  <h1>🎓 ADI Builder — Lesson Activities & Questions <span class='badge'>Branded</span></h1>
</div>
""", unsafe_allow_html=True)
st.caption("Professional, branded, editable and export-ready.")

# ---- Sidebar logo with fallback (prevents the '0' glitch) ----
def show_sidebar_logo():
    local_path = "assets/adi-logo.png"  # put your logo here if you have it
    url_fallback = "https://raw.githubusercontent.com/LCI-ADI/assets/main/adi-logo.png"
    try:
        if os.path.exists(local_path):
            st.sidebar.image(local_path, width=180)
        else:
            st.sidebar.image(url_fallback, width=180)
    except Exception:
        st.sidebar.markdown("**Academy of Defense Industries**")

show_sidebar_logo()

# =========================
#       DATA & HELPERS
# =========================

VERBS_CATALOG = {
    "Remember": ["define","duplicate","label","list","match","memorize","name","omit","recall","recognize","record","repeat","reproduce","state"],
    "Understand": ["classify","convert","defend","describe","discuss","distinguish","estimate","explain","express","identify","indicate","locate","report","restate","review","select","translate","summarize"],
    "Apply": ["apply","change","choose","compute","demonstrate","discover","dramatize","employ","illustrate","interpret","manipulate","modify","operate","practice","schedule","sketch","solve","use"],
    "Analyze": ["analyze","appraise","break down","calculate","categorize","compare","contrast","criticize","debate","deduce","diagram","differentiate","discriminate","examine","experiment","infer","inspect","inventory","question","test"],
    "Evaluate": ["appraise","argue","assess","attach value","choose","compare","conclude","contrast","criticize","decide","defend","estimate","evaluate","explain","grade","judge","justify","measure","predict","rate","revise","score","select","support","value"],
    "Create": ["arrange","assemble","categorize","collect","combine","compose","construct","create","design","develop","explain solution","formulate","generate","manage","organize","plan","prepare","propose","rearrange","reconstruct","relate","rewrite","set up","summarize","write"],
}
LEVEL_TIPS = {
    "Remember":"Recall/recognize facts & terms.",
    "Understand":"Explain & summarize concepts.",
    "Apply":"Use knowledge in new situations.",
    "Analyze":"Compare/contrast; examine relationships.",
    "Evaluate":"Judge/justify using criteria.",
    "Create":"Produce original work; design & develop.",
}
VERBS_DEFAULT = {
    "Remember":["define","list","recall"],
    "Understand":["classify","explain","summarize"],
    "Apply":["demonstrate","solve","use"],
    "Analyze":["compare","differentiate","organize"],
    "Evaluate":["justify","critique","defend"],
    "Create":["design","compose","develop"],
}

# ---- Upload + parsing ----
st.sidebar.header("Upload eBook / Lesson Plan / PPT")
upload = st.sidebar.file_uploader("PDF / DOCX / PPTX (≤200MB)", type=["pdf","docx","pptx"])

@st.cache_resource(show_spinner=False)
def parse_file(file):
    if file is None:
        return ""
    name = file.name.lower()
    if name.endswith(".pdf") and PDF_AVAILABLE:
        reader = PdfReader(file)
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages)
    if name.endswith(".docx") and DOCX_AVAILABLE:
        from docx import Document as _D
        doc = _D(file)
        return "\n".join(p.text for p in doc.paragraphs)
    if name.endswith(".pptx") and PPTX_AVAILABLE:
        prs = Presentation(file)
        parts = []
        for s in prs.slides:
            for shp in s.shapes:
                if hasattr(shp, "text"):
                    parts.append(shp.text)
        return "\n".join(parts)
    return ""

@st.cache_resource(show_spinner=False)
def index_sections(full_text: str):
    if not full_text:
        return {}, {}
    text = re.sub(r"\u00a0", " ", full_text)
    lesson_matches = list(re.finditer(r"(?im)^(lesson\s*(\d{1,2}))\b.*$", text))
    week_matches   = list(re.finditer(r"(?im)^(week\s*(\d{1,2}))\b.*$", text))

    def slice_by(matches):
        sections = {}
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            try:
                idx = int(m.group(2))
            except Exception:
                continue
            sections[idx] = text[start:end].strip()
        return sections

    return slice_by(lesson_matches), slice_by(week_matches)

if upload is not None and "parsed_text_blob" not in st.session_state:
    blob = parse_file(upload)
    st.session_state.parsed_text_blob = blob
    st.session_state.lessons, st.session_state.weeks = index_sections(blob)

# ---- Select lesson/week (if parsed) ----
if st.session_state.get("parsed_text_blob"):
    st.sidebar.subheader("Pick from eBook/Plan/PPT")
    lkeys = sorted(st.session_state.lessons.keys()) or list(range(1,15))
    wkeys = sorted(st.session_state.weeks.keys()) or list(range(1,15))
    sel_lesson = st.sidebar.selectbox("📖 Lesson", options=["—"]+[str(k) for k in lkeys], index=0)
    sel_week   = st.sidebar.selectbox("🗓️ Week",   options=["—"]+[str(k) for k in wkeys], index=0)
    c1, c2 = st.sidebar.columns(2)
    pull_mcq  = c1.button("Pull → MCQs")
    pull_acts = c2.button("Pull → Activities")

    def selected_text():
        parts = []
        if sel_lesson.isdigit() and int(sel_lesson) in st.session_state.lessons:
            parts.append(st.session_state.lessons[int(sel_lesson)])
        if sel_week.isdigit() and int(sel_week) in st.session_state.weeks:
            parts.append(st.session_state.weeks[int(sel_week)])
        return "\n\n".join(parts).strip()

    preview = selected_text()
    if preview:
        st.sidebar.caption("Preview of selection:")
        st.sidebar.text_area("", value=preview[:2000], height=140)
    else:
        st.sidebar.caption("No Lesson/Week headings detected — using generic 1–14 selectors.")

    if pull_mcq:
        st.session_state.mcq_seed = preview
    if pull_acts:
        st.session_state.act_seed = preview

# ---- Activity parameters + Bloom ----
st.sidebar.subheader("Activity Parameters")
col1, col2 = st.sidebar.columns(2)
num_activities = col1.number_input("Activities", 1, 10, 3)
duration       = col2.number_input("Duration (mins)", 5, 180, 45)

level = st.sidebar.selectbox("Bloom's Level", list(VERBS_CATALOG.keys()), index=2, key="level")
st.sidebar.info(f"**{level}**: {LEVEL_TIPS[level]}")

if "verbs_by_level" not in st.session_state:
    st.session_state.verbs_by_level = {k: VERBS_DEFAULT[k][:] for k in VERBS_DEFAULT}

level_options = VERBS_CATALOG[level]
current_selected = st.session_state.verbs_by_level.get(level, VERBS_DEFAULT[level])

st.sidebar.markdown("<div class='btn-row'>", unsafe_allow_html=True)
btn_select_all = st.sidebar.button("Select all verbs")
btn_auto_best  = st.sidebar.button("Auto-select best")
btn_reset      = st.sidebar.button("Reset to defaults")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

if btn_select_all:
    st.session_state.verbs_by_level[level] = level_options[:]
    st.rerun()
if btn_auto_best or btn_reset:
    st.session_state.verbs_by_level[level] = VERBS_DEFAULT[level][:]
    st.rerun()

valid_defaults = [v for v in current_selected if v in level_options]
verbs = st.sidebar.multiselect(
    "Preferred verbs (per level)",
    options=level_options,
    default=valid_defaults if valid_defaults else VERBS_DEFAULT[level],
    key=f"verbs_{level}"
)
st.session_state.verbs_by_level[level] = [v for v in (verbs if verbs else VERBS_DEFAULT[level]) if v in level_options]

st.sidebar.markdown("**Selected verbs preview:**")
sel_preview = st.session_state.verbs_by_level[level]
st.sidebar.markdown(
    "<div class='chips'>"
    + "".join([f"<span class='chip'>{v}</span>" for v in sel_preview[:6]])
    + (f"<span class='chip more'>+{len(sel_preview)-6} more</span>" if len(sel_preview)>6 else "")
    + "</div>",
    unsafe_allow_html=True
)

# =========================
#          TABS
# =========================
kn_tab, skills_tab = st.tabs(["Knowledge MCQs", "Skills Activities"])

# ---- MCQs ----
with kn_tab:
    st.subheader("Generate MCQs (from source or manual)")
    if st.session_state.get("mcq_seed"):
        st.success("Inserted Lesson/Week text into MCQ editor.")
    n_mcq = st.number_input("How many MCQs?", 1, 50, 5)
    topic = st.text_input("Topic (optional)", "Module description, knowledge & skills outcomes")
    base_text = st.text_area("Source text (editable)", value=st.session_state.get("mcq_seed", ""), key="mcq_source_box", height=200)

    if st.button("Generate MCQs"):
        import random
        # Templates intentionally exclude True/False and 'All/None of the above'
        TEMPLATES = [
            lambda t: (f"Which option is the most accurate **definition** of {t}?",
                       ["A) A broad opinion", "B) A precise explanation capturing essential characteristics",
                        "C) A historical anecdote", "D) A list of unrelated facts"], "B"),
            lambda t: (f"Which example **best illustrates** {t} in practice?",
                       ["A) A step that contradicts the concept", "B) A realistic case that aligns with the concept",
                        "C) A number with no context", "D) A generic statement"], "B"),
            lambda t: (f"You are applying {t} to a new scenario. **What is the most appropriate next step?**",
                       ["A) Identify variables and constraints in the scenario", "B) Repeat the definition",
                        "C) Collect unrelated data points", "D) Jump to conclusions"], "A"),
            lambda t: (f"Which statement about {t} is **contextually correct**?",
                       ["A) It always produces identical results", "B) It depends on stated assumptions and conditions",
                        "C) It is never applicable", "D) It is only theoretical"], "B"),
            lambda t: (f"Complete the idea: **{t}** typically involves ____.",
                       ["A) random guessing", "B) structured analysis with criteria",
                        "C) ignoring conflicting evidence", "D) repeating examples from memory"], "B"),
            lambda t: (f"Choose the best **sequence of steps** for {t}.",
                       ["A) Define → Apply → Evaluate", "B) Apply → Define → Evaluate",
                        "C) Evaluate → Define → Apply", "D) Define → Evaluate → Apply"], "A"),
        ]

        mcqs = []
        for _ in range(n_mcq):
            stem, opts, ans = random.choice(TEMPLATES)(topic)
            mcqs.append((stem, opts, ans))

        edited_blocks = []
        for i, (stem, opts, ans) in enumerate(mcqs, 1):
            st.markdown(
                f"""
                <div class='card'>
                  <h4>📝 Question {i}</h4>
                  <div class='meta'>Single best answer</div>
                  <div>{stem}</div>
                  <div style='margin-top:6px;'>{'<br/>'.join(opts)}</div>
                  <div style='margin-top:8px;'>Answer: <span class='answer-badge'>{ans}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            q_text = stem + "\n" + "\n".join(opts) + f"\nAnswer: {ans}"
            box = st.text_area(f"✏️ Edit Q{i}", q_text, key=f"mcq_edit_{i}", height=120)
            edited_blocks.append(box)

        # ---- Exports for MCQs ----
        def mcq_blocks_to_txt(blocks:list[str])->str:
            return "\n\n".join(b.strip() for b in blocks)

        def mcq_blocks_to_gift(blocks:list[str])->str:
            out = []
            for idx, blk in enumerate(blocks, 1):
                lines = [l.strip() for l in blk.strip().splitlines() if l.strip()]
                if not lines: continue
                stem = lines[0]
                options = [l for l in lines[1:] if re.match(r"^[A-D]\)", l)]
                ans_line = next((l for l in lines if l.lower().startswith("answer:")), "Answer: A")
                ans_letter = ans_line.split(":",1)[1].strip()[:1].upper() if ":" in ans_line else "A"
                letters = ["A","B","C","D"]
                correct_idx = letters.index(ans_letter) if ans_letter in letters else 0
                gift_opts = []
                for j,opt in enumerate(options):
                    txt = opt[3:].strip() if len(opt)>3 else opt
                    gift_opts.append(("=" if j==correct_idx else "~") + txt)
                out.append(f"::Q{idx}:: {stem} {{ {' '.join(gift_opts)} }}")
            return "\n\n".join(out)

        def mcq_blocks_to_docx(blocks:list[str])->bytes|None:
            if not DOCX_AVAILABLE:
                return None
            doc = Document()
            s = doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Knowledge MCQs', level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for idx, blk in enumerate(blocks, 1):
                lines = [l.rstrip() for l in blk.splitlines() if l.strip()]
                if not lines: continue
                stem = lines[0]
                options = [l for l in lines[1:] if re.match(r"^[A-D]\)", l)]
                ans_line = next((l for l in lines if l.lower().startswith('answer:')), '')
                doc.add_heading(f"Question {idx}", level=2)
                doc.add_paragraph(stem)
                for opt in options:
                    doc.add_paragraph(opt, style='List Bullet')
                if ans_line:
                    p = doc.add_paragraph(ans_line)
                    if p.runs: p.runs[0].italic = True
                doc.add_paragraph("")
            bio = BytesIO(); doc.save(bio); bio.seek(0)
            return bio.getvalue()

        txt_payload = mcq_blocks_to_txt(edited_blocks)
        gift_payload = mcq_blocks_to_gift(edited_blocks)
        docx_payload = mcq_blocks_to_docx(edited_blocks)

        st.session_state["mcq_blocks"] = edited_blocks  # for Full Pack

        st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
        st.download_button("📄 TXT", txt_payload, file_name="mcqs.txt")
        st.download_button("📥 Moodle GIFT", gift_payload, file_name="mcqs.gift")
        st.download_button("🗎 Word (.doc)", txt_payload, file_name="mcqs.doc")
        if docx_payload:
            st.download_button("📝 Word (.docx)", docx_payload, file_name="mcqs.docx")
        st.markdown("</div>", unsafe_allow_html=True)

# ---- Skills Activities ----
with skills_tab:
    st.subheader("Generate Skills Activities (from source or manual)")
    st.markdown("**Verbs in use:**")
    st.markdown(
        "<div class='chips'>"
        + "".join([f"<span class='chip'>{v}</span>" for v in sel_preview[:6]])
        + (f"<span class='chip more'>+{len(sel_preview)-6} more</span>" if len(sel_preview)>6 else "")
        + "</div>",
        unsafe_allow_html=True
    )

    context_text = st.text_area("Context from eBook / notes (editable)",
                                value=st.session_state.get("act_seed", ""),
                                key="act_context_box", height=200)

    if st.button("Generate Activities", type="primary"):
        chosen_verbs = st.session_state.verbs_by_level[level]
        activities = []
        for i in range(1, num_activities+1):
            verb = chosen_verbs[(i-1) % max(1, len(chosen_verbs))]
            # time split
            t_intro = max(3, round(0.15*duration))
            t_work  = max(10, duration - t_intro - 5)
            t_share = max(2, duration - t_intro - t_work)

            step1 = f"Read/skim the provided context and highlight key terms related to the learning outcome. ({t_intro} min)"
            step2 = f"In pairs/small groups, {verb} the concept to the scenario: identify variables, assumptions, constraints. ({t_work} min)"
            step3 = f"Create a concise output (diagram or 3–slide mini-deck). Prepare a 1-minute share-out. ({t_share} min)"

            materials = "Markers, sticky notes or Miro board; slides/handout template (optional)."
            grouping = "Pairs or groups of 3."
            checks = [
                "Output correctly applies the concept to the given context",
                "Reasoning is explicit: assumptions and constraints are noted",
                "Visual is clear and labeled (diagram or 3 slides)",
                "Team can justify choices during a 1-min share-out",
            ]

            act_text = (
                f"Activity {i} — {duration} mins\n"
                f"Bloom's Level: {level} (verb: {verb})\n"
                f"Grouping: {grouping}\n"
                f"Materials: {materials}\n"
                f"Context:\n{context_text.strip() if context_text else '[Add notes or use selected Lesson/Week extract]'}\n\n"
                f"Steps:\n"
                f"1) {step1}\n"
                f"2) {step2}\n"
                f"3) {step3}\n\n"
                f"Output: Diagram or 3-slide mini-deck (export to LMS).\n"
                f"Evidence: Photo or upload to LMS.\n"
                f"Success criteria:\n- " + "\n- ".join(checks)
            )
            activities.append(act_text)

            st.markdown(f"""
            <div class='card'>
              <h4>⭐ Activity {i} — {duration} mins</h4>
              <div class='meta'>Bloom's Level: {level} • Verb: <b>{verb}</b> • Grouping: {grouping}</div>
              <div><span class='label'>🧩 Context:</span> {('Provided' if context_text else 'Add notes or use Lesson/Week extract')}</div>
              <div style='margin-top:8px;'><span class='label'>🛠️ Materials:</span> {materials}</div>
              <div style='margin-top:8px;'><span class='label'>📋 Steps:</span>
                <ol>
                  <li>{step1}</li>
                  <li>{step2}</li>
                  <li>{step3}</li>
                </ol>
              </div>
              <div><span class='label'>📊 Output:</span> Diagram or 3-slide mini-deck.</div>
              <div><span class='label'>📤 Evidence:</span> Photo or upload to LMS.</div>
              <div style='margin-top:8px;'><span class='label'>✅ Success criteria:</span>
                <ul>
                  {''.join([f'<li>{c}</li>' for c in checks])}
                </ul>
              </div>
            </div>
            """, unsafe_allow_html=True)

        text_output = "\n\n".join(activities)
        edited_output = st.text_area("✏️ Review & edit before export:", text_output, key="act_edit", height=240)

        st.session_state["activities_list"] = activities  # for Full Pack

        st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
        st.download_button("📄 TXT", edited_output, file_name="adi_activities.txt")
        st.download_button("📥 Moodle GIFT", edited_output, file_name="adi_activities.gift")
        st.download_button("🗎 Word (.doc)", edited_output, file_name="adi_activities.doc")
        # Structured DOCX for activities
        if DOCX_AVAILABLE:
            from docx import Document as _D
            doc = _D()
            s = doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Skills Activities', level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for block in activities:
                lines = [l.rstrip() for l in block.split('\n')]
                title = next((l for l in lines if l.startswith('Activity ')), 'Activity')
                doc.add_heading(title, level=2)
                def add_section(label):
                    try:
                        idx = next(i for i,l in enumerate(lines) if l.lower().startswith(label))
                    except StopIteration:
                        return
                    doc.add_heading(label[:-1].title(), level=3)
                    i = idx+1
                    while i < len(lines) and lines[i].strip():
                        txt = lines[i].strip()
                        if re.match(r'^(\d+\)|- )', txt):
                            style = 'List Number' if txt[0].isdigit() else 'List Bullet'
                            doc.add_paragraph(re.sub(r'^(\d+\)|- )\s*','',txt), style=style)
                        else:
                            doc.add_paragraph(txt)
                        i += 1
                for sec in ['context:','steps:','output:','evidence:','success criteria:']:
                    add_section(sec)
                doc.add_paragraph("")
            bio = BytesIO(); doc.save(bio); bio.seek(0)
            st.download_button("📝 Word (.docx)", bio.getvalue(), file_name="adi_activities.docx")
        st.markdown("</div>", unsafe_allow_html=True)

# ---- Global: Full Pack (MCQs + Activities) ----
if DOCX_AVAILABLE and (st.session_state.get("mcq_blocks") or st.session_state.get("activities_list")):
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Export — Full Pack")
    st.caption("One Word document containing MCQs and Activities, ready to use or upload to Moodle.")

    def build_full_pack_docx(mcq_blocks, activities_list):
        doc = Document()
        s = doc.styles['Normal']; s.font.name='Calibri'; s.font.size = Pt(11)
        doc.add_heading('ADI Builder — Lesson Pack', level=1)
        doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))

        if mcq_blocks:
            doc.add_heading('Section A — Knowledge MCQs', level=1)
            for idx, blk in enumerate(mcq_blocks, 1):
                lines = [l.rstrip() for l in blk.splitlines() if l.strip()]
                if not lines: continue
                stem = lines[0]
                options = [l for l in lines[1:] if re.match(r'^[A-D]\)', l)]
                ans_line = next((l for l in lines if l.lower().startswith('answer:')), '')
                doc.add_heading(f'Question {idx}', level=2)
                doc.add_paragraph(stem)
                for opt in options:
                    doc.add_paragraph(opt, style='List Bullet')
                if ans_line:
                    p = doc.add_paragraph(ans_line)
                    if p.runs: p.runs[0].italic = True
                doc.add_paragraph("")

        if activities_list:
            # Page break before activities for neat separation
            doc.add_page_break()
            doc.add_heading('Section B — Skills Activities', level=1)
            for block in activities_list:
                lines = [l.rstrip() for l in block.split('\n')]
                title = next((l for l in lines if l.startswith('Activity ')), 'Activity')
                doc.add_heading(title, level=2)
                def add_sec(label):
                    try:
                        idx = next(i for i,l in enumerate(lines) if l.lower().startswith(label))
                    except StopIteration:
                        return
                    doc.add_heading(label[:-1].title(), level=3)
                    i = idx+1
                    while i < len(lines) and lines[i].strip():
                        txt = lines[i].strip()
                        if re.match(r'^(\d+\)|- )', txt):
                            style = 'List Number' if txt[0].isdigit() else 'List Bullet'
                            doc.add_paragraph(re.sub(r'^(\d+\)|- )\s*','',txt), style=style)
                        else:
                            doc.add_paragraph(txt)
                        i += 1
                for sec in ['context:','steps:','output:','evidence:','success criteria:']:
                    add_sec(sec)
                doc.add_paragraph("")
        bio = BytesIO(); doc.save(bio); bio.seek(0)
        return bio.getvalue()

    full_docx = build_full_pack_docx(st.session_state.get('mcq_blocks', []), st.session_state.get('activities_list', []))
    if full_docx:
        st.download_button("🧾 Full Pack (.docx)", full_docx, file_name="adi_lesson_pack.docx")
