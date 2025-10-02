# app.py
# ADI Builder — Lesson Activities & Questions (Streamlit)
# Deps (requirements.txt):
#   streamlit==1.37.1
#   python-docx==1.1.2
#   pypdf==4.2.0
#   python-pptx==0.6.23

from io import BytesIO
import random
import re
from datetime import datetime
import os
import pathlib

import streamlit as st
from docx import Document as DocxDocument
from docx.shared import Pt
from pypdf import PdfReader
from pptx import Presentation

# ----------------------------------------------------
# Page setup
# ----------------------------------------------------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    layout="wide",
)

# ----------------------------------------------------
# Theme & CSS (ADI palette + stronger shading + week badge)
# ----------------------------------------------------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#e5e1da"
BG_STONE  = "#f9f9f7"

st.markdown(
    f"""
<style>
  .stApp {{ background: {BG_STONE}; }}
  html, body, [class*="css"] {{ -webkit-font-smoothing: antialiased; }}

  .adi-hero {{
    background: {ADI_GREEN}; color: white; border-radius: 18px;
    padding: 18px 22px; box-shadow: 0 6px 18px rgba(0,0,0,.10);
  }}
  .adi-subtle {{ opacity: .9; font-size: 13px; }}

  .adi-card {{
    background: white; border-radius: 16px; border: 1px solid rgba(0,0,0,.06);
    box-shadow: 0 4px 14px rgba(0,0,0,.05); padding: 16px; margin-bottom: 14px;
  }}

  /* Tabs underline */
  .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
    border-bottom: 3px solid {ADI_GOLD} !important; color: {ADI_GREEN} !important;
  }}

  /* Week badge (stronger tint + subtle shadow) */
  .week-badge {{
    display:inline-block; padding: 8px 12px; border-radius: 999px;
    font-weight: 700; border: 1px solid #d3cec3; margin-top: 6px;
    box-shadow: 0 1px 0 rgba(0,0,0,.04);
  }}
  .week-low    {{ background:#dff0e6; color:#193626; border-color:#c6e0ce; }}
  .week-medium {{ background:#f8e9c6; color:#3a321b; border-color:#ead39d; }}
  .week-high   {{ background:#e8e7ff; color:#27245a; border-color:#d0cef7; }}

  /* Pills (deeper shading) */
  .pill {{
    background:#efede8; border:1px solid #d5d1c7; padding:8px 16px;
    border-radius:999px; font-size:14px; font-weight:700;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
  }}
  .pill.low    {{ background:#dff0e6; border-color:#c6e0ce; }}
  .pill.medium {{ background:#f8e9c6; border-color:#ead39d; }}
  .pill.high   {{ background:#e8e7ff; border-color:#d0cef7; }}
  .pill.active {{
    background:{ADI_GREEN} !important; color:white !important; border-color:{ADI_GREEN} !important;
    box-shadow: 0 0 0 2px rgba(36,90,52,.15);
  }}

  /* Buttons default (for LOW/MEDIUM/HIGH row, etc.) */
  .stButton>button {{
    border-radius:999px; border:1px solid #d9d5cd; background:#f3f2ef; color:#1c1c1c;
    padding:8px 14px; font-weight:700;
  }}

  /* Upload status card */
  .upload-ok {{
    background:#e8f5ed; border:1px solid #cfe5d6; color:#163a28;
    border-radius:12px; padding:10px 12px; display:flex; gap:10px; align-items:center;
  }}
  .upload-dot {{ width:10px;height:10px;border-radius:999px;background:{ADI_GREEN}; }}

  /* Sidebar */
  section[data-testid="stSidebar"] {{
    background: white; border-right: 1px solid #ece9e1;
  }}
  .muted {{ color: #666; font-size: 12px; }}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------
# Helpers
# ----------------------------------------------------
LOW_VERBS = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

POLICY_MAP = {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}

def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4:  return "Low"
    if 5 <= week <= 9:  return "Medium"
    return "High"

def extract_key_terms(text: str, max_terms: int = 12):
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text)
    scored = {}
    for w in words:
        wl = w.lower()
        score = (2 if w[0].isupper() else 0) + min(len(w), 12) / 3
        scored[wl] = scored.get(wl, 0) + score
    stop = set("the a an and or for with from by to of on in at is are were was be as it its this that these those which".split())
    scored = {k: v for k, v in scored.items() if k not in stop}
    candidates = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
    return [w for w, _ in candidates[:max_terms]]

def sentence_split(text: str):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 25]

def make_mcq_from_sentence(sent: str, terms: list[str]) -> dict:
    t_hits = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", sent, flags=re.I)]
    if not t_hits:
        words = re.findall(r"[A-Za-z][A-Za-z\-]{4,}", sent)
        focus = random.choice(words) if words else "concept"
    else:
        focus = max(t_hits, key=len)
    stem = re.sub(rf"\b{re.escape(focus)}\b", "_____", sent, flags=re.I, count=1)
    pool = [t for t in terms if t.lower() != focus.lower()]
    random.shuffle(pool)
    distractors = pool[:3]
    while len(distractors) < 3:
        distractors.append(focus[::-1])
    options = distractors + [focus]
    random.shuffle(options)
    correct_index = options.index(focus)
    return {"stem": stem, "options": options, "answer": correct_index, "answer_text": focus}

def generate_mcqs(source_text: str, n: int, verbs_selected: list[str]):
    sentences = sentence_split(source_text)
    if not sentences:
        sentences = [source_text.strip()]
    terms = extract_key_terms(source_text, max_terms=20)
    random.shuffle(sentences)
    items = [make_mcq_from_sentence(s, terms) for s in sentences[: max(3, n * 2)]]
    if not verbs_selected:
        verbs_selected = LOW_VERBS
    out = []
    for i, q in enumerate(items[:n], start=1):
        verb = random.choice(verbs_selected)
        out.append({**q, "bloom": verb, "index": i})
    return out

def mcqs_to_docx(mcqs: list[dict], topic: str, lesson: int, week: int) -> bytes:
    doc = DocxDocument()
    styles = doc.styles["Normal"]; styles.font.name = "Calibri"; styles.font.size = Pt(11)
    run = doc.add_paragraph().add_run("ADI Builder — Knowledge MCQs"); run.bold = True; run.font.size = Pt(16)
    doc.add_paragraph(
        f"Topic/Outcome: {topic or '—'}\n"
        f"Lesson {lesson} • Week {week} • Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    for q in mcqs:
        doc.add_paragraph(f"Q{q['index']}. {q['stem']}")
        letters = ["A","B","C","D"]
        for i, opt in enumerate(q["options"]): doc.add_paragraph(f"{letters[i]}. {opt}")
        doc.add_paragraph(f"Answer: {letters[q['answer']]}  (Bloom: {q['bloom']})")
        doc.add_paragraph("")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# ---------- File extraction ----------
def _safe_truncate(text: str, max_chars: int = 12000) -> str:
    text = re.sub(r"\s+\n", "\n", text)
    return text[:max_chars]

def extract_text_from_pdf(raw: bytes) -> str:
    reader = PdfReader(BytesIO(raw))
    chunks = []
    for page in reader.pages[:80]:  # cap for speed
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            pass
    return _safe_truncate("\n".join(chunks))

def extract_text_from_docx(raw: bytes) -> str:
    doc = DocxDocument(BytesIO(raw))
    paras = [p.text for p in doc.paragraphs]
    return _safe_truncate("\n".join(paras))

def extract_text_from_pptx(raw: bytes) -> str:
    prs = Presentation(BytesIO(raw))
    chunks = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "has_text_frame") and shape.has_text_frame:
                chunks.append(shape.text)
    return _safe_truncate("\n".join(chunks))

def extract_text_from_upload(filename: str, data: bytes) -> str:
    ext = pathlib.Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(data)
    if ext == ".docx":
        return extract_text_from_docx(data)
    if ext in (".pptx", ".ppt"):
        return extract_text_from_pptx(data)
    return ""
# ------------------------------------

# ----------------------------------------------------
# Sidebar (flicker-free uploader + context + picks)
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### Upload (optional)")

    if "uploaded_file_bytes" not in st.session_state:
        st.session_state.uploaded_file_bytes = None
        st.session_state.uploaded_filename = None
        st.session_state.uploaded_size = 0
        st.session_state.extracted_text = ""

    with st.form("upload_form"):
        upl = st.file_uploader(
            "Drag and drop file here",
            type=["pdf", "docx", "pptx"],
            label_visibility="collapsed",
            accept_multiple_files=False,
        )
        submitted = st.form_submit_button("Add file")

    if submitted and upl is not None:
        data = upl.getvalue()
        st.session_state.uploaded_file_bytes = data
        st.session_state.uploaded_filename = upl.name
        st.session_state.uploaded_size = len(data)
        # Parse to text (fast, lightweight)
        try:
            st.session_state.extracted_text = extract_text_from_upload(upl.name, data)
            st.toast(f"Uploaded & parsed {upl.name}", icon="✅")
        except Exception:
            st.session_state.extracted_text = ""
            st.toast(f"Uploaded {upl.name} (could not parse text)", icon="⚠️")

    if st.session_state.uploaded_file_bytes:
        size_mb = st.session_state.uploaded_size / (1024*1024)
        st.markdown(
            f'<div class="upload-ok"><div class="upload-dot"></div>'
            f'<div><b>Uploaded & parsed</b>: {st.session_state.uploaded_filename} '
            f' <span class="muted">({size_mb:.1f} MB)</span></div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("Limit 200MB per file • PDF, DOCX, PPTX")

    st.markdown("---")
    st.markdown("### Course context")
    lesson = st.selectbox("Lesson", options=list(range(1, 6)), index=0)
    week = st.selectbox("Week", options=list(range(1, 15)), index=6)

    st.markdown("---")
    st.markdown("### Quick pick blocks")
    cols = st.columns(5)
    with cols[0]: pick5 = st.checkbox("5", value=True)
    with cols[1]: pick10 = st.checkbox("10", value=False)
    with cols[2]: pick15 = st.checkbox("15", value=False)
    with cols[3]: pick20 = st.checkbox("20", value=False)
    with cols[4]: pick30 = st.checkbox("30", value=False)

    target_n = 5
    if pick30: target_n = 30
    elif pick20: target_n = 20
    elif pick15: target_n = 15
    elif pick10: target_n = 10
    st.caption(f"Items selected: **{target_n}**")

# ----------------------------------------------------
# Header
# ----------------------------------------------------
st.markdown(
    """
    <div class="adi-hero">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="background:white;color:#1b3b2a;width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;">ADI</div>
        <div>
          <div style="font-size:18px;font-weight:700;">ADI Builder — Lesson Activities & Questions</div>
          <div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# If uploaded, show a main-area banner too (very obvious)
if st.session_state.uploaded_file_bytes:
    chars = len(st.session_state.extracted_text)
    st.info(f"📄 **{st.session_state.uploaded_filename}** uploaded and parsed "
            f"({chars} characters of text extracted). Use the toggle below to insert it.", icon="✅")

# ----------------------------------------------------
# Tabs
# ----------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

with tab1:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)

    # Row: Topic + Bloom focus badge
    c1, c2 = st.columns([2, 1])
    with c1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with c2:
        auto_focus = bloom_focus_for_week(week)
        badge_cls = {"Low": "week-low", "Medium": "week-medium", "High": "week-high"}[auto_focus]
        st.markdown("**Bloom focus (auto)**")
        st.markdown(
            f'<span class="week-badge {badge_cls}">Week {week}: {auto_focus}</span>',
            unsafe_allow_html=True,
        )

    # Source text (with helpers)
    use_sample = st.checkbox("Use sample text (for a quick test)")
    use_extracted = st.checkbox("Use extracted text (from upload)")

    sample_text = (
        "Photosynthesis is the process by which green plants convert light energy into chemical energy, "
        "producing glucose and oxygen from carbon dioxide and water. Chlorophyll in chloroplasts absorbs "
        "light, driving the light-dependent reactions that generate ATP and NADPH. The Calvin cycle then "
        "uses these molecules to fix carbon into sugars."
    )

    default_value = ""
    if use_sample:
        default_value = sample_text
    elif use_extracted and st.session_state.extracted_text:
        default_value = st.session_state.extracted_text

    src = st.text_area(
        "Source text (editable)",
        height=200,
        value=default_value,
        placeholder="Paste or jot key notes, vocab, facts here...",
    )

    # If uploaded but not used yet, nudge gently
    if st.session_state.uploaded_file_bytes and not use_extracted and not src.strip():
        st.caption("Tip: Toggle **Use extracted text (from upload)** to insert text from your e-book.")

    st.markdown("#### Bloom’s verbs (ADI Policy)")
    st.caption("Grouped by policy tiers and week ranges")

    # Verb selection state + reseed when week changes
    if "verb_states" not in st.session_state:
        st.session_state.verb_states = {v: False for v in LOW_VERBS + MED_VERBS + HIGH_VERBS}
    if "last_week" not in st.session_state:
        st.session_state.last_week = week

    if st.session_state.last_week != week:
        st.session_state.verb_states = {v: False for v in LOW_VERBS + MED_VERBS + HIGH_VERBS}
        for v in POLICY_MAP[bloom_focus_for_week(week)]:
            st.session_state.verb_states[v] = True
        st.session_state.last_week = week

    def render_pills(tier_label: str, verbs: list[str], css_class: str):
        st.write(f"**{tier_label}**")
        cols = st.columns(6)
        for i, v in enumerate(verbs):
            col = cols[i % 6]
            with col:
                active = st.session_state.verb_states.get(v, False)
                key = f"pill-{v}"
                clicked = st.button(v, key=key, use_container_width=True)
                if clicked:
                    st.session_state.verb_states[v] = not active
                st.markdown(
                    f"""
                    <script>
                      const btn = window.parent.document.querySelector('button[k="{key}"]')
                               || window.parent.document.querySelector('button[data-testid="{key}"]');
                      if (btn) {{
                        btn.classList.add('pill','{css_class}');
                        {"btn.classList.add('active');" if active else "btn.classList.remove('active');"}
                      }}
                    </script>
                    """,
                    unsafe_allow_html=True,
                )

    render_pills("LOW (Weeks 1–4): Remember / Understand", LOW_VERBS, "low")
    render_pills("MEDIUM (Weeks 5–9): Apply / Analyse", MED_VERBS, "medium")
    render_pills("HIGH (Weeks 10–14): Evaluate / Create", HIGH_VERBS, "high")

    st.write("")
    c_low, c_med, c_high = st.columns(3)
    with c_low:
        if st.button("LOW", use_container_width=True):
            st.session_state.verb_states = {v: (v in LOW_VERBS) for v in st.session_state.verb_states}
    with c_med:
        if st.button("MEDIUM", use_container_width=True):
            st.session_state.verb_states = {v: (v in MED_VERBS) for v in st.session_state.verb_states}
    with c_high:
        if st.button("HIGH", use_container_width=True):
            st.session_state.verb_states = {v: (v in HIGH_VERBS) for v in st.session_state.verb_states}

    st.write("")
    gen = st.button("✨ Generate MCQs", type="primary")

    chosen_verbs = [v for v, on in st.session_state.verb_states.items() if on]

    if gen:
        # If textarea empty but we have extracted text, use it
        text_to_use = src.strip()
        if not text_to_use and st.session_state.extracted_text:
            text_to_use = st.session_state.extracted_text
        if not text_to_use:
            st.warning("Please add source text (or toggle **Use extracted text** / **Use sample text**) to generate MCQs.")
        else:
            st.session_state["mcqs"] = generate_mcqs(text_to_use, n=target_n, verbs_selected=chosen_verbs)
            st.toast("MCQs generated", icon="✨")

    mcqs = st.session_state.get("mcqs", [])
    if mcqs:
        st.markdown("---")
        st.markdown("### Generated MCQs")
        for q in mcqs:
            st.write(f"**Q{q['index']}.** {q['stem']}")
            letters = ["A", "B", "C", "D"]
            for i, opt in enumerate(q["options"]):
                st.write(f"- {letters[i]}. {opt}")
            st.caption(f"Answer: **{letters[q['answer']]}**  •  Bloom: **{q['bloom']}**")

        docx_bytes = mcqs_to_docx(mcqs, topic, lesson, week)
        st.download_button(
            "⬇️ Export to Word (DOCX)",
            data=docx_bytes,
            file_name=f"ADI_MCQs_L{lesson}_W{week}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Skills Activities")
    st.caption("Simple templates aligned with ADI policy. (Lightweight placeholders you can edit or export.)")
    activities = [
        ("Think–Pair–Share", "Pose a scenario using your Week focus; learners think alone, discuss in pairs, then share."),
        ("Case Mini-Analysis", "Provide a short case; groups identify problem, propose two actions, justify pick."),
        ("Demonstration & Critique", "Demonstrate a process; learners critique steps using criteria you set.")
    ]
    for i, (name, desc) in enumerate(activities, 1):
        st.write(f"**{i}. {name}** — {desc}")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Revision")
    st.write("• Auto-generate quick recall cards from your source text (copy/paste into your LMS).")
    st.write("• Tip: Use **Quick pick blocks** to change how many items you want.")
    st.markdown('</div>', unsafe_allow_html=True)


