# app.py — ADI Builder (clean UX: chips-only course select, badge summary, tidy verbs)

import base64, csv, json
from io import StringIO, BytesIO
from pathlib import Path
import streamlit as st

# ---------------- Page ----------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

# ---------------- Brand ----------------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
STONE     = "#F5F4F2"
DARK_TEXT = "#1f2937"

st.markdown(f"""
<style>
  .block-container {{ padding-top: .75rem; }}

  .adi-topbar {{
    background:{ADI_GREEN}; color:white; padding:.75rem 1rem;
    border-radius:0 0 12px 12px; display:flex; gap:14px; align-items:center;
    margin-bottom:1rem;
  }}
  .adi-topbar img {{ height:36px; }}
  .adi-topbar h1 {{ font-size:1.25rem; margin:0; line-height:1.2; }}

  .adi-card {{ background:{STONE}; border:1px solid #e7e5e4; border-radius:14px; padding:14px; }}

  .adi-chip, .adi-chip-selected {{ border-radius:14px; padding:14px 10px; text-align:center; border:1px solid #e7e5e4; }}
  .adi-chip button {{ width:100%; background:white; color:{DARK_TEXT}; border:1px solid #e7e5e4; border-radius:14px; padding:14px 10px; }}
  .adi-chip button:hover {{ border-color:{ADI_GREEN}; box-shadow:0 0 0 2px rgba(36,90,52,.08) inset; }}
  .adi-chip-selected {{ background:{ADI_GREEN}; color:white; border:1px solid {ADI_GREEN}; }}
  .adi-chip-selected small {{ display:block; color:{ADI_GOLD}; opacity:.95; font-style:italic; }}

  /* Mode + class pills */
  [data-baseweb="segmented-control"] div[role="tablist"] > div {{ border-radius:999px !important; border:1px solid #e7e5e4 !important; background:white !important; }}
  [data-baseweb="segmented-control"] div[role="tab"] {{ color:{DARK_TEXT} !important; }}
  [data-baseweb="segmented-control"] [aria-selected="true"] {{ background:{ADI_GREEN} !important; color:white !important; }}

  .stButton > button {{ border-radius:10px; }}

  /* Verb bands (inside expanders) */
  .verb-actions {{ display:flex; gap:.5rem; margin:.25rem 0 .5rem 0; }}
  .verb-actions .stButton>button {{ border-radius:999px; padding:6px 12px; }}
  .verb-pill .stButton>button {{ border-radius:999px; padding:6px 12px; margin:4px 6px 0 0; }}
</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
def _b64_image(path: Path) -> str | None:
    try:
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception:
        return None

def adi_header(title="ADI Builder — Lesson Activities & Questions", logo_path="assets/adi-logo.png"):
    p = Path(logo_path)
    img_html = ""
    if p.exists():
        b64 = _b64_image(p)
        if b64:
            img_html = f"<img src='data:image/png;base64,{b64}' alt='ADI'/>"
    st.markdown(f"<div class='adi-topbar'>{img_html}<h1>{title}</h1></div>", unsafe_allow_html=True)

# ---------------- Session ----------------
def init_state():
    ss = st.session_state
    ss.setdefault("selected_course", "GE4-EPM")  # chips control this
    ss.setdefault("class_cohort", "D1-C01")      # segmented control
    ss.setdefault("instructor", "Daniel")
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("topic_outcome", "")
    ss.setdefault("mode", "Knowledge")
    ss.setdefault("topics_text", "Topic A\nTopic B\nTopic C")
    ss.setdefault("include_key", True)  # don't pass value= to widget → no yellow warning
    ss.setdefault("mcq_count", 10)
    ss.setdefault("topics", [])
    ss.setdefault("generated_items", [])
init_state()

# ---------------- Course catalog (file-driven) ----------------
def load_courses_from_assets() -> list[tuple[str, str]]:
    csv_path  = Path("assets/courses.csv")
    json_path = Path("assets/courses.json")
    data: list[tuple[str, str]] = []

    if csv_path.exists():
        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = (row.get("code") or "").strip()
                    label = (row.get("label") or "").strip()
                    if code and label:
                        data.append((code, label))
        except Exception:
            pass
    elif json_path.exists():
        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
            for item in raw:
                code = (item.get("code") or "").strip()
                label = (item.get("label") or "").strip()
                if code and label:
                    data.append((code, label))
        except Exception:
            pass

    if data:
        return data

    # Fallback so it still runs if no file yet
    return [
        ("GE4-EPM", "Defense Technology Practices"),
        ("GE4-IPM", "Integrated Project & Materials Mgmt"),
        ("GE4-MRO", "Military Vehicle & Aircraft MRO"),
        ("CT4-COM", "Computation for Chemical Technologists"),
        ("CT4-EMG", "Explosives Manufacturing"),
        ("CT4-TFL", "Thermofluids"),
    ]

if "COURSES" not in st.session_state:
    st.session_state.COURSES = load_courses_from_assets()
COURSES: list[tuple[str, str]] = st.session_state.COURSES

# ---------------- Bloom verbs ----------------
LOW_VERBS    = ["define", "identify", "list", "recall", "describe", "classify", "match"]
MEDIUM_VERBS = ["apply", "solve", "calculate", "compare", "analyze", "demonstrate", "explain"]
HIGH_VERBS   = ["evaluate", "synthesize", "design", "justify", "critique", "optimize", "create"]

def bloom_level(week:int) -> str:
    return "Low" if week <= 4 else ("Medium" if week <= 9 else "High")

# ---------------- Components ----------------
def render_course_chip(code: str, label: str, *, col):
    selected = (st.session_state.selected_course == code)
    with col:
        if selected:
            st.markdown(
                f"<div class='adi-chip-selected'><div>{label}</div><small>{code}</small></div>",
                unsafe_allow_html=True,
            )
        else:
            if st.button(f"{label}\n\n*{code}*", key=f"chip-{code}", use_container_width=True):
                st.session_state.selected_course = code
                st.rerun()

def add_verb_to_topics(verb: str):
    ss = st.session_state
    lines = [t.strip() for t in ss.topics_text.splitlines() if t.strip()]
    if verb not in lines:
        ss.topics_text = (ss.topics_text.rstrip() + ("\n" if ss.topics_text.strip() else "") + verb)

def remove_verbs_from_topics(removals: list[str]):
    lines = [t.strip() for t in st.session_state.topics_text.splitlines()]
    keep = [ln for ln in lines if ln not in removals]
    st.session_state.topics_text = "\n".join(keep)

def verb_band(title: str, verbs: list[str], style: str, *, expanded: bool = False):
    with st.expander(title, expanded=expanded):
        # action row
        ca, cc = st.columns([1,1])
        with ca:
            if st.button(f"Add all ({len(verbs)})", key=f"addall-{style}"):
                for v in verbs: add_verb_to_topics(v)
        with cc:
            if st.button("Clear these verbs", key=f"clear-{style}"):
                remove_verbs_from_topics(verbs)
        # pill grid
        cols = st.columns(3)
        for i, v in enumerate(verbs):
            with cols[i % 3]:
                st.button(v, key=f"verb-{style}-{v}", on_click=add_verb_to_topics, args=(v,))

def try_export_docx(course, lesson, week, items, include_key: bool) -> bytes | None:
    try:
        from docx import Document
        from docx.shared import Pt
        doc = Document()
        doc.add_heading(f"{course} — Lesson {lesson} (Week {week})", level=1)
        doc.add_paragraph()
        for i, q in enumerate(items, start=1):
            doc.add_paragraph(f"Q{i}. {q['stem']}")
            for opt in q["options"]:
                doc.add_paragraph(opt)
            if include_key:
                p = doc.add_paragraph(f"Answer: {q['answer']}")
                p.runs[0].font.bold = True
            doc.add_paragraph()
        style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(11)
        buf = BytesIO(); doc.save(buf); return buf.getvalue()
    except Exception:
        return None

# ---------------- Page ----------------
adi_header()

# Two columns layout
colL, colR = st.columns([1.15, 1])

# RIGHT: course quick-pick + optional CSV upload
with colR:
    st.markdown("### Course quick-pick")

    uploaded = st.file_uploader(
        "Update course list (CSV with columns: code,label)",
        type=["csv"], accept_multiple_files=False, key="courses_uploader"
    )
    if uploaded is not None:
        try:
            reader = csv.DictReader(StringIO(uploaded.getvalue().decode("utf-8")))
            new_list: list[tuple[str, str]] = []
            for row in reader:
                code = (row.get("code") or "").strip()
                label = (row.get("label") or "").strip()
                if code and label: new_list.append((code, label))
            if new_list:
                st.session_state.COURSES = new_list
                COURSES = new_list
                st.success(f"Loaded {len(new_list)} courses from upload.")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

    # chips grid
    if len(COURSES) == 0:
        st.info("No courses configured yet. Add items via assets/courses.csv.", icon="⚙️")
    else:
        for i in range(0, len(COURSES), 3):
            row = COURSES[i:i+3]
            cols = st.columns(3)
            for (code, label), c in zip(row, cols):
                render_course_chip(code, label, col=c)

# LEFT: details & authoring
with colL:
    st.markdown("### Course details")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)

    # badge summary (no duplicate dropdown)
    code_to_label = dict(COURSES)
    sel_code = st.session_state.selected_course
    sel_label = code_to_label.get(sel_code, sel_code)
    st.markdown(
        f"""
        <div style="display:inline-block; margin-bottom:.5rem;">
          <strong>Selected course:</strong>
          <span style="background:{ADI_GREEN}; color:white; padding:2px 8px; border-radius:999px; margin-left:6px;">{sel_code}</span>
          <span style="margin-left:8px; color:{DARK_TEXT}; opacity:.9;">— {sel_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # class cohort as pills
    st.segmented_control("Class / Cohort", ["D1-C01","D1-C02","D2-C01"], key="class_cohort")
    st.text_input("Instructor name", key="instructor")
    c1, c2 = st.columns(2)
    with c1: st.number_input("Lesson", min_value=1, max_value=20, step=1, key="lesson")
    with c2: st.number_input("Week", min_value=1, max_value=14, step=1, key="week")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Authoring")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)

    st.text_input("Topic / Outcome (optional)", key="topic_outcome", placeholder="e.g., Integrated Project and …")
    st.caption(f"ADI policy: Weeks 1–4 Low • 5–9 Medium • 10–14 High  |  Recommended Bloom: **{bloom_level(st.session_state.week)}**")

    st.segmented_control("Mode", ["Knowledge","Skills","Revision","Print Summary"], key="mode")

    if st.session_state.mode != "Print Summary":
        wk = st.session_state.week
        verb_band("Low (Weeks 1–4) — Remember / Understand", LOW_VERBS, "low",   expanded=(wk <= 4))
        verb_band("Medium (Weeks 5–9) — Apply / Analyze",    MEDIUM_VERBS, "med", expanded=(5 <= wk <= 9))
        verb_band("High (Weeks 10–14) — Evaluate / Create",  HIGH_VERBS, "high",  expanded=(wk >= 10))

        st.text_area("Enter topics (one per line)", key="topics_text", height=120)
        st.checkbox("Include answer key", key="include_key")  # no value= → no yellow warning
        st.selectbox("How many MCQs?", [5,10,15,20], key="mcq_count",
                     index=[5,10,15,20].index(int(st.session_state.mcq_count)) if st.session_state.mcq_count in [5,10,15,20] else 1)

        if st.button("Generate MCQs", type="primary"):
            ss = st.session_state
            ss.topics = [t.strip() for t in ss.topics_text.splitlines() if t.strip()]
            first_topic = ss.topics[0] if ss.topics else "topic"
            ss.generated_items = [{
                "stem": f"Sample question {i+1} on {first_topic}?",
                "options": ["A) …", "B) …", "C) …", "D) …"],
                "answer": "A"
            } for i in range(int(ss.mcq_count))]
            st.success(f"Generated {len(ss.generated_items)} items.")

        if st.session_state.generated_items:
            st.markdown("#### Preview & quick edit")
            for idx, q in enumerate(st.session_state.generated_items):
                with st.expander(f"Q{idx+1}: {q['stem'][:80]}"):
                    q["stem"] = st.text_input("Stem", value=q["stem"], key=f"stem-{idx}")
                    a,b = st.columns(2); q["options"][0] = a.text_input("Option A", value=q["options"][0], key=f"oa-{idx}"); q["options"][1] = b.text_input("Option B", value=q["options"][1], key=f"ob-{idx}")
                    c,d = st.columns(2); q["options"][2] = c.text_input("Option C", value=q["options"][2], key=f"oc-{idx}"); q["options"][3] = d.text_input("Option D", value=q["options"][3], key=f"od-{idx}")
                    q["answer"] = st.selectbox("Correct answer", ["A","B","C","D"], index=["A","B","C","D"].index(q["answer"]), key=f"ans-{idx}")

            # Exports
            ss = st.session_state
            txt = "\n\n".join([
                f"Q{n+1}. {q['stem']}\n" + "\n".join(q["options"]) + (f"\nAnswer: {q['answer']}" if ss.include_key else "")
                for n, q in enumerate(ss.generated_items)
            ])
            st.download_button("Export (TXT)", data=txt, file_name=f"{ss.selected_course}_L{ss.lesson}_W{ss.week}_mcqs.txt")

            docx_bytes = try_export_docx(ss.selected_course, ss.lesson, ss.week, ss.generated_items, ss.include_key)
            if docx_bytes:
                st.download_button(
                    "Export (Word .docx)", data=docx_bytes,
                    file_name=f"{ss.selected_course}_L{ss.lesson}_W{ss.week}_mcqs.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                st.info("Install `python-docx` to enable Word export (TXT export is always available).", icon="ℹ️")

    else:
        st.markdown("#### Print Summary")
        ss = st.session_state
        st.markdown(f"""
        <div style="max-width:900px;">
          <div class="adi-card">
            <h2 style="margin:0 0 .25rem 0; color:{ADI_GREEN}">{ss.selected_course} — Lesson {ss.lesson} (Week {ss.week})</h2>
            <div style="margin-bottom:.5rem;"><strong>Instructor:</strong> {ss.instructor}</div>
            <div style="margin-bottom:.75rem;"><strong>Bloom focus:</strong> {bloom_level(ss.week)}</div>
            <h3 style="margin: 1rem 0 .5rem 0;">Topics</h3>
            <ol style="margin-top:0;">{"".join(f"<li>{t}</li>" for t in (ss.topics or ["(add topics in other modes)"]))}</ol>
            <h3 style="margin: 1rem 0 .5rem 0;">MCQs (summary)</h3>
            <ol>{"".join(f"<li>{q['stem']}</li>" for q in (ss.generated_items or []))}</ol>
          </div>
          <div style="margin-top:.5rem;"><em>Tip: use your browser’s “Print to PDF”.</em></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close Authoring card

