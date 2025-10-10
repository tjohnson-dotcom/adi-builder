# app.py — ADI Builder (clean & minimal: single selector, compact verbs)

import base64, csv, json
from io import StringIO, BytesIO
from pathlib import Path
import streamlit as st

# ---------- Page & brand ----------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
STONE     = "#F5F4F2"
INK       = "#1f2937"
MUTED     = "#6b7280"

st.markdown(f"""
<style>
  .block-container {{ max-width: 980px; margin: 0 auto; padding-top: .7rem; }}
  .adi-topbar {{
    background:{ADI_GREEN}; color:white; padding:.6rem .9rem;
    border-radius:0 0 12px 12px; display:flex; gap:10px; align-items:center;
    margin-bottom:.8rem;
  }}
  .adi-topbar img {{ height:30px; }}
  .adi-topbar h1 {{ font-size:1.05rem; margin:0; line-height:1.2; }}
  .adi-card {{ background:{STONE}; border:1px solid #e7e5e4; border-radius:12px; padding:12px; }}
  .muted {{ color:{MUTED}; }}
  .tight > div {{ margin-bottom:.35rem; }}     /* condense default widget spacing */
  .stButton > button {{ border-radius:10px; }}
  [data-baseweb="segmented-control"] [aria-selected="true"] {{ background:{ADI_GREEN} !important; color:white !important; }}
</style>
""", unsafe_allow_html=True)

def _b64(path: Path) -> str | None:
    try: return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception: return None

def header(title="ADI Builder — Lesson Activities & Questions", logo="assets/adi-logo.png"):
    p = Path(logo); img = _b64(p) if p.exists() else None
    st.markdown(
        f"<div class='adi-topbar'>{f'<img src=\"data:image/png;base64,{img}\"/>' if img else ''}<h1>{title}</h1></div>",
        unsafe_allow_html=True,
    )

header()

# ---------- Session ----------
def init_state():
    ss = st.session_state
    ss.setdefault("course_code", "")
    ss.setdefault("class_cohort", "D1-C01")
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("instructor", "Daniel")
    ss.setdefault("topic_outcome", "")
    ss.setdefault("mode", "Knowledge")
    ss.setdefault("topics_text", "Topic A\nTopic B\nTopic C")
    ss.setdefault("generated_items", [])
    ss.setdefault("verb_selection", [])
init_state()

# ---------- Courses (file-driven) ----------
def load_courses() -> list[tuple[str,str]]:
    items: list[tuple[str,str]] = []
    csvp, jsp = Path("assets/courses.csv"), Path("assets/courses.json")
    if csvp.exists():
        with csvp.open("r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                code, label = (r.get("code") or "").strip(), (r.get("label") or "").strip()
                if code and label: items.append((code, label))
    elif jsp.exists():
        raw = json.loads(jsp.read_text(encoding="utf-8"))
        for r in raw:
            code, label = (r.get("code") or "").strip(), (r.get("label") or "").strip()
            if code and label: items.append((code, label))
    if items: return items
    return [
        ("GE4-EPM", "Defense Technology Practices"),
        ("GE4-IPM", "Integrated Project & Materials Mgmt"),
        ("GE4-MRO", "Military Vehicle & Aircraft MRO"),
        ("CT4-COM", "Computation for Chemical Technologists"),
        ("CT4-EMG", "Explosives Manufacturing"),
        ("CT4-TFL", "Thermofluids"),
    ]

COURSES = load_courses()
code_to_label = dict(COURSES)
codes = [c for c,_ in COURSES]

# Default course (first) if none chosen yet
if not st.session_state.course_code and codes:
    st.session_state.course_code = codes[0]

# ---------- Bloom verbs (single multiselect) ----------
LOW    = ["define","identify","list","recall","describe","classify","match"]
MEDIUM = ["apply","solve","calculate","compare","analyze","demonstrate","explain"]
HIGH   = ["evaluate","synthesize","design","justify","critique","optimize","create"]

def bloom_focus(week:int) -> str:
    return "Low" if week<=4 else ("Medium" if week<=9 else "High")

def recommended_verbs(week:int):
    return LOW if week<=4 else (MEDIUM if week<=9 else HIGH)

# ---------- Course setup (single row, no duplication) ----------
st.markdown("<div class='adi-card'>", unsafe_allow_html=True)

setup = st.container()
with setup:
    top = st.columns([2, 1.2, 1, 1, 1.6])
    with top[0]:
        st.selectbox("Course (code)", options=codes, key="course_code", index=codes.index(st.session_state.course_code))
        st.caption(f"<span class='muted'>{code_to_label.get(st.session_state.course_code, '')}</span>", unsafe_allow_html=True)
    with top[1]:
        st.segmented_control("Class", ["D1-C01","D1-C02","D2-C01"], key="class_cohort")
    with top[2]:
        st.number_input("Lesson", min_value=1, max_value=20, step=1, key="lesson")
    with top[3]:
        st.number_input("Week", min_value=1, max_value=14, step=1, key="week")
    with top[4]:
        st.text_input("Instructor", key="instructor")

st.markdown("</div>", unsafe_allow_html=True)

# ---------- Authoring ----------
st.markdown("### Authoring")
st.markdown("<div class='adi-card tight'>", unsafe_allow_html=True)

st.text_input("Topic / Outcome (optional)", key="topic_outcome", placeholder="e.g., Integrated Project and …")
st.caption(f"ADI policy: Weeks 1–4 Low • 5–9 Medium • 10–14 High | Recommended Bloom: **{bloom_focus(st.session_state.week)}**")

st.segmented_control("Mode", ["Knowledge","Skills","Revision","Print Summary"], key="mode")

if st.session_state.mode != "Print Summary":
    # VERBS — single multiselect with helpers
    all_verbs = [f"[Low] {v}" for v in LOW] + [f"[Medium] {v}" for v in MEDIUM] + [f"[High] {v}" for v in HIGH]
    # Preselect based on week (only if empty)
    if not st.session_state.verb_selection:
        rec = [f"[{bloom_focus(st.session_state.week)}] {v}" for v in recommended_verbs(st.session_state.week)]
        st.session_state.verb_selection = rec

    cverb1, cverb2, cverb3 = st.columns([2.4, .8, .8])
    with cverb1:
        st.multiselect("Learning verbs (Bloom)", options=all_verbs, key="verb_selection")
    with cverb2:
        if st.button("Select recommended"):
            st.session_state.verb_selection = [f"[{bloom_focus(st.session_state.week)}] {v}" for v in recommended_verbs(st.session_state.week)]
    with cverb3:
        if st.button("Clear"):
            st.session_state.verb_selection = []

    # topics textarea
    st.text_area("Topics (one per line)", key="topics_text", height=100, placeholder="Topic A\nTopic B\nTopic C")

    # controls
    cc1, cc2, cc3 = st.columns([1,1,2])
    with cc1:
        include_key = st.checkbox("Answer key", value=True)
    with cc2:
        count = st.selectbox("MCQs", [5,10,15,20], index=1)
    with cc3:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("Generate MCQs", type="primary"):
            lines = [t.strip() for t in st.session_state.topics_text.splitlines() if t.strip()]
            first = lines[0] if lines else "topic"
            st.session_state.generated_items = [{
                "stem": f"Sample question {i+1} on {first}?",
                "options": ["A) …", "B) …", "C) …", "D) …"],
                "answer": "A"
            } for i in range(int(count))]

    # preview + export
    if st.session_state.generated_items:
        st.markdown("#### Preview")
        for i, q in enumerate(st.session_state.generated_items):
            with st.expander(f"Q{i+1}: {q['stem'][:90]}"):
                q["stem"] = st.text_input("Stem", value=q["stem"], key=f"stem-{i}")
                a,b = st.columns(2); q["options"][0] = a.text_input("Option A", value=q["options"][0], key=f"oa-{i}"); q["options"][1] = b.text_input("Option B", value=q["options"][1], key=f"ob-{i}")
                c,d = st.columns(2); q["options"][2] = c.text_input("Option C", value=q["options"][2], key=f"oc-{i}"); q["options"][3] = d.text_input("Option D", value=q["options"][3], key=f"od-{i}")
                q["answer"] = st.selectbox("Correct", ["A","B","C","D"], index=["A","B","C","D"].index(q["answer"]), key=f"ans-{i}")

        # build TXT
        txt = "\n\n".join(
            [f"Q{n+1}. {q['stem']}\n" + "\n".join(q["options"]) + (f"\nAnswer: {q['answer']}" if include_key else "")
             for n, q in enumerate(st.session_state.generated_items)]
        )
        st.download_button("Export (TXT)", data=txt,
                           file_name=f"{st.session_state.course_code}_L{st.session_state.lesson}_W{st.session_state.week}_mcqs.txt")

        # optional DOCX
        def to_docx(items) -> bytes | None:
            try:
                from docx import Document
                from docx.shared import Pt
                doc = Document()
                doc.add_heading(f"{st.session_state.course_code} — Lesson {st.session_state.lesson} (Week {st.session_state.week})", level=1)
                doc.add_paragraph()
                for i, q in enumerate(items, start=1):
                    doc.add_paragraph(f"Q{i}. {q['stem']}")
                    for opt in q["options"]:
                        doc.add_paragraph(opt)
                    if include_key:
                        p = doc.add_paragraph(f"Answer: {q['answer']}")
                        p.runs[0].font.bold = True
                    doc.add_paragraph()
                doc.styles['Normal'].font.name = 'Calibri'
                doc.styles['Normal'].font.size = Pt(11)
                buf = BytesIO(); doc.save(buf); return buf.getvalue()
            except Exception:
                return None

        docx_bytes = to_docx(st.session_state.generated_items)
        if docx_bytes:
            st.download_button("Export (Word .docx)", data=docx_bytes,
                               file_name=f"{st.session_state.course_code}_L{st.session_state.lesson}_W{st.session_state.week}_mcqs.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.caption("Install `python-docx` for Word export (TXT export is always available).")
else:
    # Print Summary (simple and print-friendly)
    ss = st.session_state
    st.markdown(f"""
    <div class="adi-card" style="max-width:860px;">
      <h2 style="margin:0 0 .3rem 0; color:{ADI_GREEN}">{ss.course_code} — Lesson {ss.lesson} (Week {ss.week})</h2>
      <div class="muted">{code_to_label.get(ss.course_code,'')}</div>
      <div class="muted"><strong>Instructor:</strong> {ss.instructor} &nbsp;|&nbsp; <strong>Bloom:</strong> {bloom_focus(ss.week)}</div>
      <h3 style="margin:.8rem 0 .4rem 0;">Topics</h3>
      <ol style="margin-top:0;">{"".join(f"<li>{t}</li>" for t in (ss.topics_text.splitlines() if ss.topics_text.strip() else ["(add topics in other modes)"]))}</ol>
      <h3 style="margin:.8rem 0 .4rem 0;">MCQs (summary)</h3>
      <ol>{"".join(f"<li>{q['stem']}</li>" for q in (ss.generated_items or []))}</ol>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # close authoring card
