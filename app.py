# app.py (ADI Builder — green-locked + auto-parse + MCQs/Activities)
# Requires (pin in requirements.txt):
#   streamlit==1.37.1
#   python-docx==1.1.2
#   pypdf==4.2.0
#   python-pptx==0.6.23
#   pdfminer.six==20240706

from io import BytesIO
import base64, random, re
from datetime import datetime
from pathlib import Path

import streamlit as st
from docx import Document as DocxDocument
from docx.shared import Pt, Inches
from pypdf import PdfReader
from pptx import Presentation

# Optional PDF fallback (pdfminer.six)
try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except Exception:
    pdfminer_extract_text = None

# ---------------- Page ----------------
LOGO_PATH = Path("assets/adi_logo.png")
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    layout="wide",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else None,
)

# Hard-set theme at runtime (extra insurance against red accents)
st.set_option("theme.primaryColor", "#245a34")
st.set_option("theme.backgroundColor", "#f9f9f7")
st.set_option("theme.secondaryBackgroundColor", "#e5e1da")
st.set_option("theme.textColor", "#1c1c1c")

ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
BG_STONE  = "#f9f9f7"

def _logo_b64():
    try:
        return base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    except Exception:
        return None

logo_b64 = _logo_b64()

# ---------------- CSS ----------------
st.markdown(
    f"""
<style>
  .stApp {{ background: {BG_STONE}; }}
  html, body {{ -webkit-font-smoothing: antialiased; }}

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

  /* Week badge */
  .week-badge {{
    display:inline-block; padding: 8px 12px; border-radius: 999px;
    font-weight: 700; border: 1px solid #d3cec3; margin-top: 6px;
    box-shadow: 0 1px 0 rgba(0,0,0,.04);
  }}
  .week-low    {{ background:#dff0e6; color:#193626; border-color:#c6e0ce; }}
  .week-medium {{ background:#f8e9c6; color:#3a321b; border-color:#ead39d; }}
  .week-high   {{ background:#e8e7ff; color:#27245a; border-color:#d0cef7; }}

  /* Pills */
  .pill {{
    background:#efede8; border:1px solid #d5d1c7; padding:8px 16px;
    border-radius:999px; font-size:14px; font-weight:700;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
  }}
  .pill.active {{
    background:{ADI_GREEN} !important; color:white !important; border-color:{ADI_GREEN} !important;
    box-shadow: 0 0 0 2px rgba(36,90,52,.15);
  }}

  /* Buttons */
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
  section[data-testid="stSidebar"] {{ background: white; border-right: 1px solid #ece9e1; }}
  .muted {{ color: #666; font-size: 12px; }}

  /* Header logo */
  .adi-logo {{ height: 30px; width: auto; display:inline-block; }}
  .adi-logo--mono {{ filter: brightness(0) invert(1) contrast(1.1); }}
  @media (min-width: 1200px) {{ .adi-logo {{ height: 34px; }} }}

  /* **Global green lock** (overrides any cached red) */
  :root, .stApp {{
    --theme-primaryColor:{ADI_GREEN} !important;
    --primary-color:{ADI_GREEN} !important;
  }}
  input:focus, textarea:focus, select:focus {{
    outline:none!important;
    box-shadow:0 0 0 1px {ADI_GREEN} inset, 0 0 0 3px rgba(36,90,52,.2)!important;
    border-color:{ADI_GREEN}!important;
  }}
  [data-baseweb="input"] > div:has(input:focus) {{
    box-shadow:0 0 0 1px {ADI_GREEN} inset, 0 0 0 3px rgba(36,90,52,.2)!important;
    border-color:{ADI_GREEN}!important;
  }}
  [data-testid="stFileUploaderDropzone"]{{border-color:rgba(36,90,52,.35)!important;}}
  [data-testid="stFileUploaderDropzone"]:hover{{border-color:{ADI_GREEN}!important;}}
  [data-testid="stStatusWidget"] svg [fill="#F63366"] {{ fill:{ADI_GREEN}!important; }}
  [data-testid="stStatusWidget"] svg [stroke="#F63366"] {{ stroke:{ADI_GREEN}!important; }}
  [data-testid="stSkeleton"] div[role="progressbar"],
  [data-testid="stProgressBar"] div[role="progressbar"] {{ background:{ADI_GREEN}!important; }}
  header[tabindex="-1"] {{ border-top-color:{ADI_GREEN}!important; }}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Text & generators ----------------
STOP = set("the a an and or for with from by to of on in at is are were was be as it its this that these those which who whom whose what when where why how".split())

def _clean(t: str) -> str:
    t = re.sub(r"\r\n?", "\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def _sentences(t: str):
    t = _clean(t)
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p.strip() for p in parts if len(p.strip()) > 25][:400]

def _keywords(t: str, k: int = 24):
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", t)
    score = {}
    for w in words:
        wl = w.lower()
        if wl in STOP:
            continue
        score[wl] = score.get(wl, 0) + (2 if w[0].isupper() else 0) + min(len(w), 12) / 3
    return [w for w, _ in sorted(score.items(), key=lambda kv: kv[1], reverse=True)[:k]]

LOW = ["define", "identify", "list", "recall", "describe", "label"]
MED = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

def focus_for_week(w: int) -> str:
    if 1 <= w <= 4:
        return "Low"
    if 5 <= w <= 9:
        return "Medium"
    return "High"

def _one_mcq(s: str, terms: list[str]):
    hits = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", s, re.I)]
    focus = max(hits, key=len) if hits else (re.findall(r"[A-Za-z][A-Za-z\-]{4,}", s) or ["concept"])[0]
    stem = re.sub(rf"\b{re.escape(focus)}\b", "_____", s, flags=re.I, count=1)

    pool = [t for t in terms if t.lower() != focus.lower() and len(t) > 2]
    random.shuffle(pool)
    distractors = []
    for c in pool:
        cl = c.lower()
        if cl != focus.lower() and cl not in [d.lower() for d in distractors]:
            distractors.append(c)
        if len(distractors) == 3:
            break
    while len(distractors) < 3:
        filler = (focus[::-1] if len(focus) > 3 else f"{focus}_x")
        if filler.lower() not in [focus.lower()] + [d.lower() for d in distractors]:
            distractors.append(filler)
    options = distractors + [focus]
    random.shuffle(options)
    return stem, options, options.index(focus)

def gen_mcqs(text: str, n: int, verbs: list[str], seed: int = 42):
    random.seed(seed)
    text = (text or "").strip()
    if not text:
        return []
    sents = _sentences(text)
    if not sents:
        terms = _keywords(text, 12) or ["concept", "process", "system", "device"]
        sents = [f"{t.title()} is a key concept in this module." for t in terms[:max(3, n)]]
    terms = _keywords(text, 24) or ["concept", "process", "system", "device"]
    items, seen = [], set()
    for s in sents:
        stem, opts, ans = _one_mcq(s, terms)
        if stem in seen:
            continue
        seen.add(stem)
        items.append({"stem": stem, "options": opts, "answer": ans})
        if len(items) >= max(3, n * 3):
            break
    verbs = verbs or ["define", "identify", "apply", "evaluate"]
    out = []
    for i, it in enumerate(items[:n], 1):
        it["index"] = i
        it["bloom"] = random.choice(verbs)
        out.append(it)
    return out

def mcqs_docx(mcqs: list[dict], topic: str, lesson: int, week: int) -> bytes:
    doc = DocxDocument()
    styles = doc.styles["Normal"]; styles.font.name = "Calibri"; styles.font.size = Pt(11)
    try:
        if LOGO_PATH.exists():
            doc.add_picture(str(LOGO_PATH), width=Inches(1.1))
    except Exception:
        pass
    run = doc.add_paragraph().add_run("ADI Builder — Knowledge MCQs"); run.bold = True; run.font.size = Pt(16)
    doc.add_paragraph(
        f"Topic/Outcome: {topic or '—'}\n"
        f"Lesson {lesson} • Week {week} • Exported {datetime.now():%Y-%m-%d %H:%M}"
    )
    for q in mcqs:
        doc.add_paragraph(f"Q{q['index']}. {q['stem']}")
        letters = ["A", "B", "C", "D"]
        for i, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{letters[i]}. {opt}")
        doc.add_paragraph(f"Answer: {letters[q['answer']]}  (Bloom: {q['bloom']})")
        doc.add_paragraph("")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# ---------------- Activities ----------------
ACT_SHELLS = [
    ("Think–Pair–Share", "pairs", "discussion"),
    ("Case Mini-Analysis", "small groups", "analysis"),
    ("Demonstrate & Critique", "whole class", "critique"),
    ("Gallery Walk", "groups", "review"),
    ("Jigsaw Teaching", "expert groups", "synthesis"),
]

def activity_from(verb: str, focus: str, topic: str) -> dict:
    name, grouping, assess = random.choice(ACT_SHELLS)
    title = f"{name} — {verb.title()}"
    objective = f"Students will {verb} key ideas in {topic or 'the topic'} ({focus} focus)."
    steps = [
        f"Introduce a short stimulus related to {topic or 'the lesson'} (2–3 mins).",
        f"Learners work in {grouping} to {verb} the prompt.",
        "Share-out and consolidate key points.",
    ]
    if focus == "High":
        steps.append("Extend: justify choices using agreed criteria; connect to prior learning.")
    materials = ["Slide or short text prompt", "Timer"]
    diff = "Provide scaffolds (sentence starters/examples) and add challenge questions."
    assessment = f"Observe {assess} with a short checklist aligned to {verb}."
    return {
        "title": title, "objective": objective, "steps": steps,
        "materials": materials, "differentiation": diff, "assessment": assessment
    }

def gen_activities(topic: str, focus: str, verbs: list[str], n: int = 3):
    verbs = verbs or ["define", "apply", "evaluate"]
    return [activity_from(verbs[i % len(verbs)], focus, topic) for i in range(n)]

def acts_docx(acts: list[dict], topic: str, lesson: int, week: int) -> bytes:
    doc = DocxDocument()
    styles = doc.styles["Normal"]; styles.font.name = "Calibri"; styles.font.size = Pt(11)
    try:
        if LOGO_PATH.exists():
            doc.add_picture(str(LOGO_PATH), width=Inches(1.1))
    except Exception:
        pass
    run = doc.add_paragraph().add_run("ADI Builder — Skills Activities"); run.bold = True; run.font.size = Pt(16)
    doc.add_paragraph(
        f"Topic/Outcome: {topic or '—'}\n"
        f"Lesson {lesson} • Week {week} • Exported {datetime.now():%Y-%m-%d %H:%M}"
    )
    for i, a in enumerate(acts, 1):
        doc.add_paragraph(f"{i}. {a['title']}")
        doc.add_paragraph(f"Objective: {a['objective']}")
        doc.add_paragraph("Steps:")
        for s in a["steps"]:
            doc.add_paragraph(f"• {s}")
        doc.add_paragraph(f"Materials: {', '.join(a['materials'])}")
        doc.add_paragraph(f"Differentiation: {a['differentiation']}")
        doc.add_paragraph(f"Assessment: {a['assessment']}")
        doc.add_paragraph("")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# ---------------- Extraction ----------------
def _truncate(t: str, n: int = 12000) -> str:
    t = re.sub(r"\s+\n", "\n", t)
    return t[:n]

def extract_pdf(raw: bytes) -> str:
    txt = ""
    try:
        reader = PdfReader(BytesIO(raw))
        chunks = []
        for p in reader.pages[:80]:
            try:
                chunks.append(p.extract_text() or "")
            except Exception:
                pass
        txt = "\n".join(chunks)
    except Exception:
        txt = ""
    if len(txt.strip()) < 50 and pdfminer_extract_text is not None:
        try:
            txt = pdfminer_extract_text(BytesIO(raw))
        except Exception:
            pass
    return _truncate(txt or "")

def extract_docx(raw: bytes) -> str:
    doc = DocxDocument(BytesIO(raw))
    return _truncate("\n".join(p.text for p in doc.paragraphs))

def extract_pptx(raw: bytes) -> str:
    prs = Presentation(BytesIO(raw))
    chunks = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "has_text_frame") and shape.has_text_frame:
                chunks.append(shape.text)
    return _truncate("\n".join(chunks))

def extract_upload(name: str, data: bytes) -> str:
    ext = Path(name).suffix.lower()
    if ext == ".pdf":  return extract_pdf(data)
    if ext == ".docx": return extract_docx(data)
    if ext in (".pptx", ".ppt"): return extract_pptx(data)
    return ""

# ---------------- Sidebar (auto-parse, debounced toast) ----------------
with st.sidebar:
    if "uploaded_file_bytes" not in st.session_state:
        st.session_state.update(dict(
            uploaded_file_bytes=None, uploaded_filename=None, uploaded_size=0,
            extracted_text="", use_extracted_auto=False, last_toast_key=""
        ))

    upl = st.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"],
                           label_visibility="collapsed", accept_multiple_files=False)

    if upl is not None and upl.name != st.session_state.uploaded_filename:
        data = upl.getvalue()
        size_mb = len(data) / (1024*1024)
        HARD = 200.0
        if size_mb > HARD:
            st.error(f"File is {size_mb:.1f} MB. Please upload ≤ {HARD:.0f} MB.")
            st.stop()

        st.session_state.uploaded_file_bytes = data
        st.session_state.uploaded_filename = upl.name
        st.session_state.uploaded_size = len(data)

        extracted = extract_upload(upl.name, data)
        st.session_state.extracted_text = extracted
        st.session_state.use_extracted_auto = bool(extracted.strip())

        # Debounce the toast (reduces flicker)
        key = f"{upl.name}:{bool(extracted.strip())}"
        if st.session_state.last_toast_key != key:
            st.session_state.last_toast_key = key
            st.toast(("Uploaded & parsed " + upl.name) if extracted.strip()
                     else (f"Uploaded {upl.name} (no selectable text found — try DOCX/PPTX or paste text)."),
                    icon="✅" if extracted.strip() else "⚠️")

    if st.session_state.uploaded_file_bytes:
        sz = st.session_state.uploaded_size / (1024*1024)
        st.markdown(
            f'<div class="upload-ok"><div class="upload-dot"></div>'
            f'<div><b>Uploaded & parsed</b>: {st.session_state.uploaded_filename} '
            f'<span class="muted">({sz:.1f} MB)</span></div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("Limit 200MB per file • PDF, DOCX, PPTX")

    st.markdown("---")
    st.markdown("### Course context")
    lesson = st.selectbox("Lesson", options=list(range(1, 6)), index=0)
    week   = st.selectbox("Week",   options=list(range(1, 15)), index=6)

    st.markdown("---")
    st.markdown("### Quick pick blocks")
    cols = st.columns(5)
    picks = [cols[i].checkbox(v, value=(i==0)) for i, v in enumerate(["5","10","15","20","30"])]
    target_n = [5,10,15,20,30][[i for i,b in enumerate(picks) if b][-1] if any(picks) else 0]
    st.caption(f"Items selected: **{target_n}**")

# ---------------- Header ----------------
st.markdown(
    f"""
<div class="adi-hero">
  <div style="display:flex;align-items:center;gap:12px;">
    {("<img class='adi-logo adi-logo--mono' src='data:image/png;base64," + logo_b64 + "'/>") if logo_b64 else "<div style='background:white;color:#1b3b2a;width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;'>ADI</div>"}
    <div>
      <div style="font-size:18px;font-weight:700;">ADI Builder — Lesson Activities & Questions</div>
      <div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

if st.session_state.uploaded_file_bytes:
    chars = len(st.session_state.extracted_text)
    st.info(f"📄 **{st.session_state.uploaded_filename}** uploaded and parsed ({chars} characters extracted).", icon="✅")

# ---------------- Tabs ----------------
tab1, tab2, tab3 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

with tab1:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with c2:
        focus = focus_for_week(week)
        badge = {"Low":"week-low","Medium":"week-medium","High":"week-high"}[focus]
        st.markdown("**Bloom focus (auto)**")
        st.markdown(f'<span class="week-badge {badge}">Week {week}: {focus}</span>', unsafe_allow_html=True)

    use_sample = st.checkbox("Use sample text (for a quick test)")
    use_extracted = st.session_state.get("use_extracted_auto", False)

    sample_text = (
        "Photosynthesis is the process by which green plants convert light energy into chemical energy, "
        "producing glucose and oxygen from carbon dioxide and water. Chlorophyll in chloroplasts absorbs "
        "light, driving the light-dependent reactions that generate ATP and NADPH. The Calvin cycle then "
        "uses these molecules to fix carbon into sugars."
    )

    default_src = sample_text if use_sample else (
        st.session_state.extracted_text if (use_extracted and st.session_state.extracted_text) else ""
    )

    src = st.text_area("Source text (editable)", height=200, value=default_src,
                       placeholder="Paste or jot key notes, vocab, facts here...")

    if st.session_state.uploaded_file_bytes and not src.strip():
        st.caption("We’ve uploaded your file. If this is empty, the PDF may be scanned. Try DOCX/PPTX or paste text.")

    # Verb toggles + reseed on week change
    if "verb_states" not in st.session_state:
        st.session_state.verb_states = {v: False for v in LOW + MED + HIGH}
    if "last_week" not in st.session_state:
        st.session_state.last_week = week
    if st.session_state.last_week != week:
        st.session_state.verb_states = {v: False for v in LOW + MED + HIGH}
        for v in (LOW if focus=="Low" else MED if focus=="Medium" else HIGH):
            st.session_state.verb_states[v] = True
        st.session_state.last_week = week

    def pills(title: str, verbs: list[str]):
        st.write(f"**{title}**")
        cols = st.columns(6)
        for i, v in enumerate(verbs):
            active = st.session_state.verb_states.get(v, False)
            if cols[i % 6].button(v, key=f"pill-{v}", use_container_width=True):
                st.session_state.verb_states[v] = not active
            # Style the button as a pill (JS only changes classes; no rerun)
            st.markdown(
                f"""
                <script>
                  const el = window.parent.document.querySelector('button[k="pill-{v}"]') ||
                             window.parent.document.querySelector('button[data-testid="pill-{v}"]');
                  if (el) {{
                    el.classList.add('pill');
                    {'el.classList.add("active");' if active else 'el.classList.remove("active");'}
                  }}
                </script>
                """,
                unsafe_allow_html=True,
            )

    pills("LOW (Weeks 1–4): Remember / Understand", LOW)
    pills("MEDIUM (Weeks 5–9): Apply / Analyse", MED)
    pills("HIGH (Weeks 10–14): Evaluate / Create", HIGH)

    cL, cM, cH = st.columns(3)
    if cL.button("LOW", use_container_width=True):
        st.session_state.verb_states = {v: (v in LOW) for v in st.session_state.verb_states}
    if cM.button("MEDIUM", use_container_width=True):
        st.session_state.verb_states = {v: (v in MED) for v in st.session_state.verb_states}
    if cH.button("HIGH", use_container_width=True):
        st.session_state.verb_states = {v: (v in HIGH) for v in st.session_state.verb_states}

    gen = st.button("✨ Generate MCQs", type="primary")
    chosen_verbs = [v for v, on in st.session_state.verb_states.items() if on]

    if gen:
        text = (src or "").strip() or st.session_state.extracted_text.strip()
        if not text:
            st.warning("Please add source text (or upload a text-based PDF/DOCX/PPTX).")
        else:
            st.session_state.mcqs = gen_mcqs(text, n=target_n, verbs=chosen_verbs, seed=42)
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
        st.download_button(
            "⬇️ Export to Word (DOCX)",
            data=mcqs_docx(mcqs, topic, lesson, week),
            file_name=f"ADI_MCQs_L{lesson}_W{week}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Skills Activities")
    st.caption("Generated from your Week focus and selected Bloom verbs.")

    topic2   = st.text_input("Topic / Context (optional)", key="topic2")
    howmany  = st.slider("How many activities?", 1, 6, 3)

    if st.button("🧩 Generate Activities", type="secondary"):
        focus = focus_for_week(week)
        chosen = [v for v, on in st.session_state.verb_states.items() if on]
        st.session_state.activities = gen_activities(topic2 or topic, focus, chosen, n=howmany)
        st.toast("Activities generated", icon="🧩")

    acts = st.session_state.get("activities", [])
    if acts:
        for i, a in enumerate(acts, 1):
            st.write(f"**{i}. {a['title']}**")
            st.write(f"*Objective:* {a['objective']}")
            st.write("**Steps:**")
            for s in a["steps"]:
                st.write(f"- {s}")
            st.write(f"*Materials:* {', '.join(a['materials'])}")
            st.write(f"*Differentiation:* {a['differentiation']}")
            st.write(f"*Assessment:* {a['assessment']}")
            st.markdown("---")
        st.download_button(
            "⬇️ Export Activities (DOCX)",
            data=acts_docx(acts, topic2 or topic, lesson, week),
            file_name=f"ADI_Activities_L{lesson}_W{week}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Revision")
    st.write("• Auto-generate quick recall cards from your source text (copy/paste into your LMS).")
    st.write("• Tip: Use **Quick pick blocks** to change how many items you want.")
    st.markdown('</div>', unsafe_allow_html=True)

