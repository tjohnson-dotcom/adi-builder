# app.py — ADI Builder (ultra-tidy UI, chips-only course select, compact verbs)

import base64, csv, json
from io import StringIO, BytesIO
from pathlib import Path
import streamlit as st

# ---------------- Page & brand ----------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
STONE     = "#F5F4F2"
DARK_TEXT = "#1f2937"

st.markdown(f"""
<style>
  /* Center the content and tighten spacing */
  .block-container {{
    max-width: 1100px;
    padding-top: .5rem;
    margin: 0 auto;
  }}

  /* Top header bar */
  .adi-topbar {{
    background:{ADI_GREEN}; color:white; padding:.6rem .9rem;
    border-radius:0 0 12px 12px; display:flex; gap:12px; align-items:center;
    margin-bottom:.75rem;
  }}
  .adi-topbar img {{ height:32px; }}
  .adi-topbar h1 {{ font-size:1.1rem; margin:0; line-height:1.2; }}

  /* Chips */
  .adi-chip, .adi-chip-selected {{
    border-radius:999px; padding:.45rem .9rem; text-align:center;
    border:1px solid #e7e5e4; display:inline-block; white-space:nowrap;
  }}
  .adi-chip button {{
    background:white; color:{DARK_TEXT}; border:1px solid #e7e5e4;
    border-radius:999px; padding:.45rem .9rem;
  }}
  .adi-chip button:hover {{ border-color:{ADI_GREEN}; }}
  .adi-chip-selected {{ background:{ADI_GREEN}; color:white; border:1px solid {ADI_GREEN}; }}

  /* Cards */
  .adi-card {{ background:{STONE}; border:1px solid #e7e5e4; border-radius:12px; padding:12px; }}

  /* Segmented controls (mode & class) */
  [data-baseweb="segmented-control"] div[role="tablist"] > div {{
    border-radius:999px !important; border:1px solid #e7e5e4 !important; background:white !important;
  }}
  [data-baseweb="segmented-control"] [aria-selected="true"] {{ background:{ADI_GREEN} !important; color:white !important; }}

  /* Buttons */
  .stButton > button {{ border-radius:10px; }}

  /* Small caption */
  .muted {{ color:#6b7280; font-size:.85rem; }}
</style>
""", unsafe_allow_html=True)

def _b64_image(path: Path) -> str | None:
    try: return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception: return None

def adi_header(title="ADI Builder — Lesson Activities & Questions", logo_path="assets/adi-logo.png"):
    p = Path(logo_path); img_html = ""
    if p.exists():
        b64 = _b64_image(p)
        if b64: img_html = f"<img src='data:image/png;base64,{b64}' alt='ADI'/>"
    st.markdown(f"<div class='adi-topbar'>{img_html}<h1>{title}</h1></div>", unsafe_allow_html=True)

adi_header()

# ---------------- Session ----------------
def init_state():
    ss = st.session_state
    ss.setdefault("selected_course", None)  # no duplicate widget: chips are the only selector
    ss.setdefault("class_cohort", "D1-C01")
    ss.setdefault("instructor", "Daniel")
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("topic_outcome", "")
    ss.setdefault("mode", "Knowledge")
    ss.setdefault("topics_text", "")
    ss.setdefault("generated_items", [])
    ss.setdefault("show_course_row", True)  # toggle to hide chip row after selection
init_state()

# ---------------- Courses (file-driven) ----------------
def load_courses_from_assets() -> list[tuple[str,str]]:
    csv_path, json_path = Path("assets/courses.csv"), Path("assets/courses.json")
    items: list[tuple[str,str]] = []
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                code, label = (r.get("code") or "").strip(), (r.get("label") or "").strip()
                if code and label: items.append((code,label))
    elif json_path.exists():
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        for r in raw:
            code, label = (r.get("code") or "").strip(), (r.get("label") or "").strip()
            if code and label: items.append((code,label))
    if items: return items
    # fallback (keeps app running)
    return [
        ("GE4-EPM","Defense Technology Practices"),
        ("GE4-IPM","Integrated Project & Materials Mgmt"),
        ("GE4-MRO","Military Vehicle & Aircraft MRO"),
        ("CT4-COM","Computation for Chemical Technologists"),
        ("CT4-EMG","Explosives Manufacturing"),
        ("CT4-TFL","Thermofluids"),
    ]

if "COURSES" not in st.session_state:
    st.session_state.COURSES = load_courses_from_assets()
COURSES: list[tuple[str,str]] = st.session_state.COURSES
code_to_label = dict(COURSES)

# ---------------- Bloom verbs ----------------
LOW_VERBS    = ["define","identify","list","recall","describe","classify","match"]
MEDIUM_VERBS = ["apply","solve","calculate","compare","analyze","demonstrate","explain"]
HIGH_VERBS   = ["evaluate","synthesize","design","justify","critique","optimize","create"]

def bloom_level(week:int) -> str: return "Low" if week<=4 else ("Medium" if week<=9 else "High")

def add_verb(v:str):
    ss = st.session_state
    lines = [t.strip() for t in ss.topics_text.splitlines() if t.strip()]
    if v not in lines:
        ss.topics_text = (ss.topics_text.rstrip() + ("\n" if ss.topics_text.strip() else "") + v)

def remove_verbs(vs:list[str]):
    lines = [t.strip() for t in st.session_state.topics_text.splitlines()]
    st.session_state.topics_text = "\n".join([ln for ln in lines if ln not in vs])

# ---------------- Course chips row (single control) ----------------
st.toggle("Change course", key="show_course_row")

if st.session_state.show_course_row:
    # CSV uploader inline (tiny)
    up_col, _ = st.columns([1,5])
    with up_col:
        upl = st.file_uploader("Update list (CSV: code,label)", type=["csv"], label_visibility="collapsed", key="courses_uploader")
        if upl:
            reader = csv.DictReader(StringIO(upl.getvalue().decode("utf-8")))
            new_list = []
            for r in reader:
                code, label = (r.get("code") or "").strip(), (r.get("label") or "").strip()
                if code and label: new_list.append((code,label))
            if new_list:
                st.session_state.COURSES = new_list
                COURSES[:] = new_list
                code_to_label.clear(); code_to_label.update(dict(new_list))
                st.success(f"Loaded {len(new_list)} courses.")

    # chips in one compact row
    row = st.container()
    with row:
        cols = st.columns(len(COURSES) if len(COURSES)<=6 else 6)
        for i, (code, label) in enumerate(COURSES):
            col = cols[i % len(cols)]
            with col:
                selected = (st.session_state.selected_course == code)
                if selected:
                    st.markdown(f"<div class='adi-chip-selected'>{code}</div>", unsafe_allow_html=True)
                else:
                    if st.button(code, key=f"chip-{code}", use_container_width=True):
                        st.session_state.selected_course = code

# If nothing selected yet, default to first to keep flow simple
if not st.session_state.selected_course and COURSES:
    st.session_state.selected_course = COURSES[0][0]

# ---------------- Course details (compact) ----------------
with st.container():
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    sel_code = st.session_state.selected_course or ""
    sel_label = code_to_label.get(sel_code, "")
    st.markdown(
        f"<strong>Selected course:</strong> "
        f"<span style='background:{ADI_GREEN};color:#fff;border-radius:999px;padding:2px 8px;'>{sel_code}</span>"
        f"<span class='muted'> — {sel_label}</span>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        st.segmented_control("Class / Cohort", ["D1-C01","D1-C02","D2-C01"], key="class_cohort")
    with c2:
        st.number_input("Lesson", min_value=1, max_value=20, step=1, key="lesson")
    with c3:
        st.number_input("Week", min_value=1, max_value=14, step=1, key="week")
    st.text_input("Instructor", key="instructor")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Authoring (clean) ----------------
st.markdown("### Authoring")
st.markdown("<div class='adi-card'>", unsafe_allow_html=True)

st.text_input("Topic / Outcome (optional)", key="topic_outcome", placeholder="e.g., Integrated Project and …")
st.caption(f"ADI policy: Weeks 1–4 Low • 5–9 Medium • 10–14 High  |  Recommended Bloom: **{bloom_level(st.session_state.week)}**")

st.segmented_control("Mode", ["Knowledge","Skills","Revision","Print Summary"], key="mode")

if st.session_state.mode != "Print Summary":
    # Show only recommended verbs inline
    wk = st.session_state.week
    rec_title, rec_verbs = (
        ("Low — Remember / Understand", LOW_VERBS) if wk<=4 else
        ("Medium — Apply / Analyze", MEDIUM_VERBS) if wk<=9 else
        ("High — Evaluate / Create", HIGH_VERBS)
    )
    st.markdown(f"**Recommended verbs** ({rec_title})")
    rec_cols = st.columns(min(6, max(3, len(rec_verbs)//2)))
    for i,v in enumerate(rec_verbs):
        with rec_cols[i % len(rec_cols)]:
            st.button(v, key=f"rec-{v}", on_click=add_verb, args=(v,))

    # “More verbs” holds the other two bands and has Add all / Clear
    with st.expander("More verbs"):
        def band(title, verbs, keyprefix):
            a,b = st.columns([1,1])
            with a:
                if st.button(f"Add all ({len(verbs)})", key=f"addall-{keyprefix}"):
                    for v in verbs: add_verb(v)
            with b:
                if st.button("Clear these", key=f"clear-{keyprefix}"):
                    remove_verbs(verbs)
            cols = st.columns(6)
            for i,v in enumerate(verbs):
                with cols[i % 6]:
                    st.button(v, key=f"{keyprefix}-{v}", on_click=add_verb, args=(v,))
        if rec_verbs is LOW_VERBS:
            band("Medium — Apply / Analyze", MEDIUM_VERBS, "med")
            band("High — Evaluate / Create", HIGH_VERBS, "high")
        elif rec_verbs is MEDIUM_VERBS:
            band("Low — Remember / Understand", LOW_VERBS, "low")
            band("High — Evaluate / Create", HIGH_VERBS, "high")
        else:
            band("Low — Remember / Understand", LOW_VERBS, "low")
            band("Medium — Apply / Analyze", MEDIUM_VERBS, "med")

    st.text_area("Topics (one per line)", key="topics_text", height=90, placeholder="Topic A\nTopic B\nTopic C")
    include_key = st.checkbox("Include answer key", value=True)  # widget owns default (no warning)
    mcq_count = st.selectbox("How many MCQs?", [5,10,15,20], index=1)  # widget owns default (no warning)

    if st.button("Generate MCQs", type="primary"):
        lines = [t.strip() for t in st.session_state.topics_text.splitlines() if t.strip()]
        first_topic = lines[0] if lines else "topic"
        st.session_state.generated_items = [{
            "stem": f"Sample question {i+1} on {first_topic}?",
            "options": ["A) …", "B) …", "C) …", "D) …"],
            "answer": "A"
        } for i in range(int(mcq_count))]
        st.success(f"Generated {len(st.session_state.generated_items)} items.")

    if st.session_state.generated_items:
        st.markdown("#### Preview")
        for idx, q in enumerate(st.session_state.generated_items):
            with st.expander(f"Q{idx+1}: {q['stem'][:80]}"):
                q["stem"] = st.text_input("Stem", value=q["stem"], key=f"stem-{idx}")
                a,b = st.columns(2); q["options"][0] = a.text_input("Option A", value=q["options"][0], key=f"oa-{idx}"); q["options"][1] = b.text_input("Option B", value=q["options"][1], key=f"ob-{idx}")
                c,d = st.columns(2); q["options"][2] = c.text_input("Option C", value=q["options"][2], key=f"oc-{idx}"); q["options"][3] = d.text_input("Option D", value=q["options"][3], key=f"od-{idx}")
                q["answer"] = st.selectbox("Correct", ["A","B","C","D"], index=["A","B","C","D"].index(q["answer"]), key=f"ans-{idx}")

        # Exports
        txt = "\n\n".join([
            f"Q{n+1}. {q['stem']}\n" + "\n".join(q["options"]) + (f"\nAnswer: {q['answer']}" if include_key else "")
            for n,q in enumerate(st.session_state.generated_items)
        ])
        st.download_button("Export (TXT)", data=txt, file_name=f"{st.session_state.selected_course}_L{st.session_state.lesson}_W{st.session_state.week}_mcqs.txt")

        def try_export_docx(items) -> bytes | None:
            try:
                from docx import Document
                from docx.shared import Pt
                doc = Document()
                doc.add_heading(f"{st.session_state.selected_course} — Lesson {st.session_state.lesson} (Week {st.session_state.week})", level=1)
                doc.add_paragraph()
                for i, q in enumerate(items, start=1):
                    doc.add_paragraph(f"Q{i}. {q['stem']}")
                    for opt in q["options"]: doc.add_paragraph(opt)
                    if include_key:
                        p = doc.add_paragraph(f"Answer: {q['answer']}")
                        p.runs[0].font.bold = True
                    doc.add_paragraph()
                style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(11)
                buf = BytesIO(); doc.save(buf); return buf.getvalue()
            except Exception: return None

        docx_bytes = try_export_docx(st.session_state.generated_items)
        if docx_bytes:
            st.download_button("Export (Word .docx)", data=docx_bytes,
                file_name=f"{st.session_state.selected_course}_L{st.session_state.lesson}_W{st.session_state.week}_mcqs.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.caption("Install `python-docx` for Word export. TXT export always available.")

else:
    # Print Summary
    ss = st.session_state
    st.markdown(f"""
    <div class="adi-card" style="max-width:900px;">
      <h2 style="margin:0 0 .25rem 0; color:{ADI_GREEN}">{ss.selected_course} — Lesson {ss.lesson} (Week {ss.week})</h2>
      <div class="muted"><strong>Instructor:</strong> {ss.instructor}</div>
      <div class="muted"><strong>Bloom:</strong> {bloom_level(ss.week)}</div>
      <h3 style="margin: .8rem 0 .4rem 0;">Topics</h3>
      <ol style="margin-top:0;">{"".join(f"<li>{t}</li>" for t in (ss.topics_text.splitlines() if ss.topics_text.strip() else ["(add topics in other modes)"]))}</ol>
      <h3 style="margin: .8rem 0 .4rem 0;">MCQs (summary)</h3>
      <ol>{"".join(f"<li>{q['stem']}</li>" for q in (ss.generated_items or []))}</ol>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # close Authoring card
