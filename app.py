# app.py — ADI Builder (polished UI with pills + chips + DOCX export)

import io
import streamlit as st

# Optional export (python-docx)
try:
    from docx import Document
    from docx.shared import Pt
    DOCX_OK = True
except Exception:
    DOCX_OK = False

# ------------------------ Page Setup ------------------------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

ADI_CSS = """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-green-50:#EEF5F0;
  --adi-gold:#C8A85A; --border:#d9dfda; --ink:#1f2937; --muted:#6b7280;
  --card:#ffffff; --bg:#FAFAF7; --shadow:0 10px 24px rgba(0,0,0,.06);
}
html,body{background:var(--bg)}
main .block-container{max-width:1220px;padding-top:1rem;padding-bottom:1.5rem}

/* header hero */
.adi-hero{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));
  color:#fff;border-radius:20px;padding:18px 20px;box-shadow:var(--shadow)}
.adi-hero .title{font-weight:800;font-size:22px}
.adi-hero .sub{opacity:.92;font-size:12px;margin-top:2px}

/* cards */
.adi-card{background:var(--card);border:1px solid var(--border);
  border-radius:16px;padding:14px;box-shadow:var(--shadow);margin-bottom:16px}
.section{font-size:.9rem;letter-spacing:.03em;text-transform:uppercase;color:var(--adi-green);margin:0 0 .5rem}

/* inputs */
textarea, input[type="text"]{border:2px solid var(--adi-green) !important;border-radius:12px !important}
textarea:focus,input[type="text"]:focus{outline:none !important;border-color:var(--adi-green-600) !important;
  box-shadow:0 0 0 3px rgba(36,90,52,.2) !important}

/* upload */
.adi-upload{border:2px dashed var(--adi-green);background:var(--adi-green-50);
  border-radius:14px;padding:12px;display:flex;gap:10px;align-items:center}
.adi-upload .icon{width:30px;height:30px;border-radius:8px;background:var(--adi-green);
  color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700}

/* buttons */
div.stButton>button{background:var(--adi-green);color:#fff;border:none;border-radius:999px;
  padding:.7rem 1.1rem;font-weight:700;box-shadow:0 4px 12px rgba(31,76,44,.22);transition:all .2s}
div.stButton>button:hover{filter:brightness(.97);box-shadow:0 0 0 3px rgba(200,168,90,.35)}

/* radio-as-pills */
.adi-radio .stRadio [role="radiogroup"]{gap:10px}
.adi-radio .stRadio label{border:1.5px solid var(--border);background:#f7faf7;border-radius:999px;
  padding:8px 14px;font-weight:600;color:#243b2a;transition:all .15s}
.adi-radio .stRadio label:hover{border-color:var(--adi-green);background:#eff6f1}
.adi-radio input[type="radio"]{accent-color:var(--adi-green)}   /* green dots */
.adi-radio .stRadio label[data-checked="true"]{
  background:var(--adi-green);color:#fff;border-color:var(--adi-green);
  box-shadow:0 6px 14px rgba(36,90,52,.25)
}

/* quick chips (5/10/20/30) */
.chips{display:flex;gap:10px;flex-wrap:wrap}
.chip{padding:10px 16px;border-radius:999px;border:1.5px solid var(--border);
  background:#fff;cursor:pointer;font-weight:700;color:var(--ink);transition:all .15s; text-align:center}
.chip:hover{border-color:var(--adi-green)}
.chip.active{background:var(--adi-green);color:#fff;border-color:var(--adi-green)}

/* tiny captions */
.small{color:var(--muted);font-size:.85rem}
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# ------------------------ Helpers ------------------------
def radio_pills(title: str, options, value, key: str):
    st.markdown(f"<h3 class='section'>{title}</h3>", unsafe_allow_html=True)
    st.markdown("<div class='adi-radio'>", unsafe_allow_html=True)
    choice = st.radio(
        label="",
        options=list(options),
        index=(list(options).index(value) if value in options else 0),
        horizontal=True,
        key=key,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return choice

def quick_chips(title: str, choices, current: int, session_key: str) -> int:
    st.markdown(f"<h3 class='section'>{title}</h3>", unsafe_allow_html=True)
    cols = st.columns(len(choices))
    picked = current
    for i, c in enumerate(choices):
        with cols[i]:
            active = "active" if c == current else ""
            # Render a chip; use a small invisible button to capture click
            click = st.button(" ", key=f"{session_key}_{c}", help=str(c))
            st.markdown(
                f"<div class='chip {active}'>{c}</div>",
                unsafe_allow_html=True,
            )
            if click:
                picked = c
    return picked

def bloom_for_week(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    if 5 <= week <= 9:
        return "Medium"
    return "High"

def generate_mcq_blocks(topic: str, source: str, blocks: int, bloom: str):
    """Simple placeholder generator — 3 items per block."""
    items = []
    topic_safe = topic.strip() or "Module"
    snippet = (source.strip() or "Reference content").split()
    seed = " ".join(snippet[:18]) if snippet else "Reference content"
    qtypes = {
        "Low":    ["define", "identify", "recall"],
        "Medium": ["apply", "demonstrate", "solve"],
        "High":   ["evaluate", "synthesize", "justify"],
    }[bloom]
    n = 0
    for b in range(blocks):
        for k in range(3):
            verb = qtypes[k % len(qtypes)]
            n += 1
            q = f"{n}. ({bloom}/{verb}) {topic_safe}: Based on '{seed}', write one {verb}-level MCQ."
            items.append(q)
    return items

def export_docx(questions, title="ADI MCQs", bloom=""):
    if not DOCX_OK:
        return None, "python-docx not installed"
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.add_heading(title, level=1)
    if bloom:
        p = doc.add_paragraph()
        p.add_run(f"Bloom focus: {bloom}").bold = True
    doc.add_paragraph()  # spacer
    for q in questions:
        doc.add_paragraph(q, style="List Number")
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio, None

# ------------------------ Header ------------------------
st.markdown(
    """
    <div class="adi-hero">
      <div class="title">ADI Builder – Lesson Activities & Questions</div>
      <div class="sub">Professional, branded, editable and export-ready.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Init state
st.session_state.setdefault("lesson", 1)
st.session_state.setdefault("week", 1)
st.session_state.setdefault("mcq_blocks", 10)
st.session_state.setdefault("mcqs", [])

# ------------------------ Tabs ------------------------
tab_mcq, tab_act = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

with tab_mcq:
    left, right = st.columns([1.05, 1.95], gap="large")

    # ---------- Left column: Upload + Pick ----------
    with left:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section'>Upload eBook / Lesson Plan / PPT</h3>", unsafe_allow_html=True)
        st.markdown(
            "<div class='adi-upload'><div class='icon'>UP</div>"
            "<div><b>Drag and drop</b> your file here, or use the button below.<br>"
            "<span class='small'>We recommend eBooks (PDF) as source for best results. (≤200MB)</span></div></div>",
            unsafe_allow_html=True,
        )
        st.file_uploader(" ", type=["pdf", "docx", "pptx"], label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section'>Pick from eBook / Plan / PPT</h3>", unsafe_allow_html=True)
        st.session_state.lesson = radio_pills("Lesson", range(1, 7), st.session_state.lesson, "lesson_pills")
        st.session_state.week   = radio_pills("Week", range(1, 15), st.session_state.week, "week_pills")
        st.caption("ADI policy: Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. Bloom auto-highlights in generator.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Right column: Generate ----------
    with right:
        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section'>Generate MCQs — Policy Blocks (Low → Medium → High)</h3>", unsafe_allow_html=True)
        topic  = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source = st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here...")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
        bloom = bloom_for_week(st.session_state.week)
        st.markdown(f"**Bloom focus for Week {st.session_state.week}: {bloom}**")
        current_blocks = st.session_state.mcq_blocks
        current_blocks = quick_chips("Quick pick", [5, 10, 20, 30], current_blocks, "mcqchips")
        manual = st.number_input("Or enter a custom number", min_value=1, max_value=50, value=current_blocks, step=1)
        st.session_state.mcq_blocks = manual

        if st.button("Generate MCQ Blocks", key="gen_mcq"):
            st.session_state.mcqs = generate_mcq_blocks(topic, source, st.session_state.mcq_blocks, bloom)

        st.markdown("</div>", unsafe_allow_html=True)

        # ---------- Preview & Edit + Export ----------
        if st.session_state.mcqs:
            st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
            st.markdown("<h3 class='section'>Preview & Edit</h3>", unsafe_allow_html=True)

            # Editable questions
            edited = []
            for i, q in enumerate(st.session_state.mcqs, start=1):
                edited_q = st.text_area(f"Question {i}", q, key=f"q_{i}", height=70)
                edited.append(edited_q)
            st.session_state.mcqs = edited

            # Export
            st.markdown("---")
            if DOCX_OK:
                bio, err = export_docx(st.session_state.mcqs, title="ADI MCQs", bloom=bloom)
                if bio:
                    st.download_button("Download Word (.docx)", data=bio, file_name="adi_mcqs.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                elif err:
                    st.info(err)
            else:
                st.info("Install `python-docx` to enable Word export.")
            st.markdown("</div>", unsafe_allow_html=True)

with tab_act:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.markdown("<h3 class='section'>Skills Activities</h3>", unsafe_allow_html=True)
    st.write("This tab will mirror the MCQ styling (cards, pills, chips). We can wire your activity generator here next.")
    st.markdown("</div>", unsafe_allow_html=True)
