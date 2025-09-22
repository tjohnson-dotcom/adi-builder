# app.py — ADI Builder (Streamlit)
# Branded UI • Upload PDF/DOCX/PPTX • Lesson/Week extractor • Bloom + verbs • Difficulty scaler
# MCQs with per-question Passage/Image • Activities with steps • Exports: DOCX + RTF • Full Pack DOCX

from __future__ import annotations
import os, re
from io import BytesIO
from datetime import datetime
import streamlit as st

# ---------- Optional libs (graceful fallbacks) ----------
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="banner">
  <h1>🎓 ADI Builder — Lesson Activities & Questions <span class="badge">Branded</span></h1>
</div>
""", unsafe_allow_html=True)
st.caption("Professional, branded, editable and export-ready.")

# ---------- Logo (no '0' glitch) ----------
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

# ---------- RTF helper (opens instantly in Word) ----------
def to_rtf(title: str, body: str) -> bytes:
    def esc(s: str) -> str:
        s = s.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
        return s.replace("\r\n","\n").replace("\r","\n").replace("\n", r"\line ")
    parts = [
        r"{\rtf1\ansi\deff0", r"{\fonttbl{\f0 Calibri;}}", r"\fs22", r"\pard\f0 "
    ]
    if title: parts.append(r"\b "+esc(title)+r"\b0\line\line ")
    parts.append(esc(body)); parts.append("}")
    return "\n".join(parts).encode("utf-8")

# ---------- Bloom + verbs ----------
VERBS_CATALOG = {
    "Remember": ["define","duplicate","label","list","match","memorize","name","recall","recognize","record","repeat","reproduce","state"],
    "Understand": ["classify","convert","defend","describe","discuss","distinguish","estimate","explain","express","identify","indicate","locate","report","restate","review","select","translate","summarize"],
    "Apply": ["apply","change","choose","compute","demonstrate","discover","employ","illustrate","interpret","manipulate","modify","operate","practice","schedule","sketch","solve","use"],
    "Analyze": ["analyze","appraise","calculate","categorize","compare","contrast","criticize","debate","deduce","diagram","differentiate","discriminate","examine","infer","inspect","question","test"],
    "Evaluate": ["appraise","argue","assess","choose","compare","conclude","criticize","decide","defend","estimate","evaluate","explain","grade","judge","justify","measure","predict","rate","revise","score","select","support","value"],
    "Create": ["arrange","assemble","combine","compose","construct","create","design","develop","formulate","generate","organize","plan","prepare","propose","reconstruct","rewrite","set up","write"],
}
LEVEL_TIPS = {
    "Remember":"Recall/recognize facts & terms.",
    "Understand":"Explain & summarize concepts.",
    "Apply":"Use knowledge in new situations.",
    "Analyze":"Compare/contrast; examine relationships.",
    "Evaluate":"Judge/justify using criteria.",
    "Create":"Produce original work; design & develop."
}
VERBS_DEFAULT = {
    "Remember":["define","list","recall"],
    "Understand":["classify","explain","summarize"],
    "Apply":["demonstrate","solve","use"],
    "Analyze":["compare","differentiate","organize"],
    "Evaluate":["justify","critique","defend"],
    "Create":["design","compose","develop"],
}

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
        prs = Presentation(file); parts = []
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
    sel_lesson = st.sidebar.selectbox("📖 Lesson", options=["—"]+[str(k) for k in lkeys], index=0)
    sel_week   = st.sidebar.selectbox("🗓️ Week",   options=["—"]+[str(k) for k in wkeys], index=0)
    c1,c2 = st.sidebar.columns(2)
    pull_mcq  = c1.button("Pull → MCQs")
    pull_acts = c2.button("Pull → Activities")

    def selected_text():
        parts=[]
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
        st.sidebar.caption("No headings found — generic selectors shown.")

    if pull_mcq:  st.session_state.mcq_seed = preview
    if pull_acts: st.session_state.act_seed = preview

# ---------- Activity parameters ----------
st.sidebar.subheader("Activity Parameters")
col1,col2 = st.sidebar.columns(2)
num_activities = col1.number_input("Activities", 1, 10, 3)
duration       = col2.number_input("Duration (mins)", 5, 180, 45)
level = st.sidebar.selectbox("Bloom's Level", list(VERBS_CATALOG.keys()), index=2, key="level")
st.sidebar.info(f"**{level}**: {LEVEL_TIPS[level]}")

difficulty = st.sidebar.select_slider("Difficulty", options=["Easy","Medium","Hard"], value="Medium",
                                      help="Scales MCQ rigor and activity complexity.")

if "verbs_by_level" not in st.session_state:
    st.session_state.verbs_by_level = {k: VERBS_DEFAULT[k][:] for k in VERBS_DEFAULT}

level_options = VERBS_CATALOG[level]
current_selected = st.session_state.verbs_by_level.get(level, VERBS_DEFAULT[level])

st.sidebar.markdown("<div class='btnrow'>", unsafe_allow_html=True)
if st.sidebar.button("Select all verbs"):
    st.session_state.verbs_by_level[level] = level_options[:]; st.rerun()
if st.sidebar.button("Auto-select best") or st.sidebar.button("Reset to defaults"):
    st.session_state.verbs_by_level[level] = VERBS_DEFAULT[level][:]; st.rerun()
st.sidebar.markdown("</div>", unsafe_allow_html=True)

verbs = st.sidebar.multiselect("Preferred verbs (per level)", options=level_options,
                               default=[v for v in current_selected if v in level_options],
                               key=f"verbs_{level}")
st.session_state.verbs_by_level[level] = verbs or VERBS_DEFAULT[level]

st.sidebar.markdown(
    "<div class='chips'>" +
    "".join([f"<span class='chip'>{v}</span>" for v in st.session_state.verbs_by_level[level][:6]]) +
    (f"<span class='chip more'>+{max(0,len(st.session_state.verbs_by_level[level])-6)}</span>" if len(st.session_state.verbs_by_level[level])>6 else "") +
    "</div>", unsafe_allow_html=True
)

# ---------- Tabs ----------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs", "Skills Activities"])

# ---------- MCQs ----------
with mcq_tab:
    st.subheader("Generate MCQs (from source or manual)")
    if st.session_state.get("mcq_seed"): st.success("Lesson/Week text inserted into MCQ editor.")
    n_mcq = st.number_input("How many MCQs?", 1, 50, 5)
    topic = st.text_input("Topic (optional)", "Module description, knowledge & skills outcomes")
    base_text = st.text_area("Source text (editable)", value=st.session_state.get("mcq_seed",""), key="mcq_source_box", height=180)

    if st.button("Generate MCQs"):
        import random
        BASE_TEMPLATES = [
            lambda t: (f"Which option is the most accurate **definition** of {t}?",
                       ["A) A broad opinion","B) A precise explanation capturing essential characteristics","C) A historical anecdote","D) A list of unrelated facts"], "B"),
            lambda t: (f"Which example **best illustrates** {t} in practice?",
                       ["A) A step that contradicts the concept","B) A realistic case that aligns with the concept","C) A number with no context","D) A generic statement"], "B"),
            lambda t: (f"You are applying {t} to a new scenario. **What is the most appropriate next step?**",
                       ["A) Identify variables and constraints in the scenario","B) Repeat the definition","C) Collect unrelated data points","D) Jump to conclusions"], "A"),
            lambda t: (f"Which statement about {t} is **contextually correct**?",
                       ["A) It always produces identical results","B) It depends on stated assumptions and conditions","C) It is never applicable","D) It is only theoretical"], "B"),
            lambda t: (f"Choose the best **sequence of steps** for {t}.",
                       ["A) Define → Apply → Evaluate","B) Apply → Define → Evaluate","C) Evaluate → Define → Apply","D) Define → Evaluate → Apply"], "A"),
        ]
        HARD_TEMPLATES = [
            lambda t: (f"Given a brief scenario involving {t}, which option best justifies the recommended approach?",
                       ["A) Cites unrelated evidence","B) References assumptions and constraints explicitly","C) Focuses on formatting over reasoning","D) Mentions outcomes without criteria"], "B"),
            lambda t: (f"Which choice best **prioritizes** actions when applying {t} with limited resources?",
                       ["A) Start with tasks requiring the least thought","B) Identify constraints, then map actions to impact","C) Copy a previous solution without adaptation","D) Choose actions randomly"], "B"),
        ]
        pool = BASE_TEMPLATES if difficulty=="Medium" else [BASE_TEMPLATES[0],BASE_TEMPLATES[1]] if difficulty=="Easy" else HARD_TEMPLATES+BASE_TEMPLATES

        mcqs=[]
        for _ in range(n_mcq):
            stem, opts, ans = random.choice(pool)(topic)
            mcqs.append((stem, opts, ans))

        edited_blocks=[]
        for i,(stem,opts,ans) in enumerate(mcqs, start=1):
            st.markdown(f"""
            <div class='card'>
              <h4>📝 Question {i}</h4>
              <div class='meta'>Single best answer</div>
              <div>{stem}</div>
              <div style='margin-top:6px;'>{'<br/>'.join(opts)}</div>
              <div style='margin-top:8px;'>Answer: <span class='answer-badge'>{ans}</span></div>
            </div>
            """, unsafe_allow_html=True)

            q_text = stem + "\n" + "\n".join(opts) + f"\nAnswer: {ans}"
            box = st.text_area(f"✏️ Edit Q{i}", q_text, key=f"mcq_edit_{i}", height=118)

            # Per-question optional attachments (session only)
            st.session_state.setdefault(f"mcq_passage_{i}", "")
            st.session_state.setdefault(f"mcq_img_{i}", None)
            st.text_area(f"📄 Passage (optional) for Q{i}", st.session_state[f"mcq_passage_{i}"], key=f"mcq_passage_{i}", height=80)
            st.file_uploader(f"🖼️ Image (optional) for Q{i}", type=["png","jpg","jpeg"], key=f"mcq_img_{i}")

            edited_blocks.append(box)

        # ---- MCQ exports (RTF + DOCX) ----
        def mcq_blocks_to_docx(blocks):
            if not DOCX_AVAILABLE: return None
            doc = Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
            doc.add_heading('ADI Builder — Knowledge MCQs', level=1)
            doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))
            for idx, blk in enumerate(blocks,1):
                lines=[l.rstrip() for l in blk.splitlines() if l.strip()]
                if not lines: continue
                stem=lines[0]; options=[l for l in lines[1:] if re.match(r"^[A-D]\)", l)]
                ans_line = next((l for l in lines if l.lower().startswith("answer:")), "")
                doc.add_heading(f"Question {idx}", level=2)

                # passage
                pkey=f"mcq_passage_{idx}"
                if pkey in st.session_state and (st.session_state[pkey] or "").strip():
                    doc.add_heading("Passage", level=3); doc.add_paragraph(st.session_state[pkey].strip())

                doc.add_paragraph(stem)

                # image
                ikey=f"mcq_img_{idx}"
                if ikey in st.session_state and st.session_state[ikey] is not None:
                    try:
                        st.session_state[ikey].seek(0)
                        doc.add_picture(st.session_state[ikey], width=Inches(4.5))
                    except Exception:
                        doc.add_paragraph("[Image could not be embedded]")

                for opt in options: doc.add_paragraph(opt, style="List Bullet")
                if ans_line:
                    p = doc.add_paragraph(ans_line); 
                    if p.runs: p.runs[0].italic = True
                doc.add_paragraph("")
            bio = BytesIO(); doc.save(bio); bio.seek(0); return bio.getvalue()

        # RTF mirrors TXT content with a Word-friendly wrapper
        txt_payload = "\n\n".join(edited_blocks)
        mcq_rtf = to_rtf("ADI Builder — Knowledge MCQs", txt_payload)
        st.download_button("🗎 Word (.rtf)", mcq_rtf, file_name="mcqs.rtf")

        docx_payload = mcq_blocks_to_docx(edited_blocks)
        if docx_payload:
            st.download_button("📝 Word (.docx)", docx_payload, file_name="mcqs.docx")

        # keep for Full Pack
        st.session_state["mcq_blocks"] = edited_blocks

# ---------- Activities ----------
with act_tab:
    st.subheader("Generate Skills Activities (from source or manual)")
    st.markdown("**Verbs in use:**", help="Preview of selected verbs for the chosen Bloom level.")
    st.markdown(
        "<div class='chips'>" +
        "".join([f"<span class='chip'>{v}</span>" for v in st.session_state.verbs_by_level[level][:6]]) +
        (f"<span class='chip more'>+{max(0,len(st.session_state.verbs_by_level[level])-6)}</span>" if len(st.session_state.verbs_by_level[level])>6 else "") +
        "</div>", unsafe_allow_html=True
    )

    context_text = st.text_area(
        "Context from eBook / notes (editable)",
        value=st.session_state.get("act_seed",""), key="act_context_box", height=180
    )

    if st.button("Generate Activities", type="primary"):
        chosen_verbs = st.session_state.verbs_by_level[level]
        activities=[]
        for i in range(1, num_activities+1):
            verb = chosen_verbs[(i-1) % max(1,len(chosen_verbs))]
            t_intro = max(3, round(0.15*duration))
            t_work  = max(10, duration - t_intro - 5)
            t_share = max(2, duration - t_intro - t_work)

            step1 = f"Read/skim the provided context and highlight key terms related to the learning outcome. ({t_intro} min)"
            step2 = f"In pairs/small groups, {verb} the concept to the scenario: identify variables, assumptions, constraints. ({t_work} min)"
            step3 = f"Create a concise output (diagram or 3–slide mini-deck). Prepare a 1-minute share-out. ({t_share} min)"
            if difficulty=="Easy":
                step2 = f"In pairs, {verb} a simple example in the scenario; list variables and obvious constraints. ({t_work} min)"
                checks = ["Example matches concept","Key terms identified","Basic visual produced"]
            elif difficulty=="Hard":
                step2 = f"In small teams, {verb} the concept under competing constraints; decide trade-offs and justify. ({t_work} min)"
                checks = ["Trade-offs justified with criteria","Constraints explicit and prioritized","Visual shows reasoning steps"]
            else:
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
                f"Bloom's Level: {level} (verb: {verb})\n"
                f"Grouping: {grouping}\n"
                f"Materials: {materials}\n"
                f"Context:\n{context_text.strip() or '[Add notes or use selected Lesson/Week extract]'}\n\n"
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
              <div class='meta'>Bloom: {level} • Verb: <b>{verb}</b> • Grouping: {grouping}</div>
              <div><span class='label'>🧩 Context:</span> {('Provided' if context_text else 'Add notes or use Lesson/Week extract')}</div>
              <div style='margin-top:8px;'><span class='label'>🛠️ Materials:</span> {materials}</div>
              <div style='margin-top:8px;'><span class='label'>📋 Steps:</span>
                <ol>
                  <li>{step1}</li><li>{step2}</li><li>{step3}</li>
                </ol>
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

        # Exports (RTF + DOCX)
        act_rtf = to_rtf("ADI Builder — Skills Activities", edited_output)
        st.download_button("🗎 Word (.rtf)", act_rtf, file_name="activities.rtf")

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
    st.caption("One Word doc with MCQs and Activities, ready to print or upload to Moodle.")

    def build_full_pack_docx(mcq_blocks, activities_list):
        doc = Document(); s=doc.styles['Normal']; s.font.name='Calibri'; s.font.size=Pt(11)
        doc.add_heading('ADI Builder — Lesson Pack', 0)
        doc.add_paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'))

        if mcq_blocks:
            doc.add_heading('Section A — Knowledge MCQs', level=1)
            for idx, blk in enumerate(mcq_blocks, 1):
                lines=[l.rstrip() for l in blk.splitlines() if l.strip()]
                if not lines: continue
                stem=lines[0]; options=[l for l in lines[1:] if re.match(r"^[A-D]\)", l)]
                ans_line = next((l for l in lines if l.lower().startswith('answer:')), '')
                doc.add_heading(f"Question {idx}", level=2)
                pkey=f"mcq_passage_{idx}"
                if pkey in st.session_state and (st.session_state[pkey] or "").strip():
                    doc.add_heading("Passage", level=3); doc.add_paragraph(st.session_state[pkey].strip())
                doc.add_paragraph(stem)
                ikey=f"mcq_img_{idx}"
                if ikey in st.session_state and st.session_state[ikey] is not None:
                    try:
                        st.session_state[ikey].seek(0); doc.add_picture(st.session_state[ikey], width=Inches(4.5))
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

