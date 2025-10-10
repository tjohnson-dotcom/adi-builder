# app.py — ADI Builder (clean UI + pills + green dashed uploaders + logo uploader)

import base64
import csv
import json
from io import StringIO, BytesIO
from pathlib import Path

import streamlit as st

# ---------------- Page / Theme ----------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

ADI_GREEN = "#245a34"
STONE     = "#F5F4F2"
INK       = "#1f2937"
MUTED     = "#6b7280"

st.markdown(f"""
<style>
  .block-container {{ max-width: 980px; margin: 0 auto; padding-top: .7rem; }}
  .adi-topbar {{
    background:{ADI_GREEN}; color:white; padding:.6rem .9rem;
    border-radius:0 0 12px 12px; display:flex; gap:10px; align-items:center;
    margin-bottom:.8rem; min-height:48px;
  }}
  .adi-topbar img {{ height:34px; }}
  .adi-topbar h1 {{ font-size:1.08rem; margin:0; line-height:1.2; }}

  .adi-card {{ background:{STONE}; border:1px solid #e7e5e4; border-radius:12px; padding:12px; }}
  .muted {{ color:{MUTED}; }}

  .tight > div {{ margin-bottom:.35rem; }}
  .stButton > button {{ border-radius:10px; }}
  [data-baseweb="segmented-control"] [aria-selected="true"] {{
    background:{ADI_GREEN} !important; color:white !important;
  }}

  /* Stronger labels */
  label:has(+ div [role="listbox"]),
  label:has(+ div input[type="number"]),
  label:has(+ div input[type="text"]) {{
    font-weight: 600 !important; color: #374151 !important;
  }}

  /* Pills */
  .pill {{ display:inline-block; padding:2px 10px; border-radius:999px; font-size:.85rem;
          line-height:1.6; white-space:nowrap; margin-left:6px; }}
  .pill-green {{ background:{ADI_GREEN}; color:#fff; }}
  .pill-slate {{ background:#e5e7eb; color:#111827; }}

  /* GREEN DASHED DROPZONES (both uploaders) */
  div[data-testid="stFileUploaderDropzone"] {{
    border:2px dashed {ADI_GREEN} !important;
    background:#f6faf7 !important;
    border-radius:12px !important;
  }}
  div[data-testid="stFileUploaderDropzone"] p {{
    color:#0f3d22 !important;
  }}
</style>
""", unsafe_allow_html=True)

# ---------------- Helpers ----------------
def _b64_bytes(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")

def _b64_file(path: Path) -> str | None:
    try:
        return _b64_bytes(path.read_bytes())
    except Exception:
        return None

# ---------------- Session ----------------
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
    ss.setdefault("bloom_level", "Low")         # Low / Medium / High
    ss.setdefault("verbs_selected", [])
    ss.setdefault("generated_items", [])
    # Courses + logo
    ss.setdefault("COURSES", None)              # list[(code,label)]
    ss.setdefault("logo_b64", None)             # user-uploaded or from assets
init_state()

# ---------------- Data: load courses ----------------
def load_courses_from_assets() -> list[tuple[str,str]]:
    items: list[tuple[str,str]] = []
    csvp, jsp = Path("assets/courses.csv"), Path("assets/courses.json")
    if csvp.exists():
        with csvp.open("r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                code = (r.get("code") or "").strip()
                label = (r.get("label") or "").strip()
                if code and label:
                    items.append((code, label))
    elif jsp.exists():
        raw = json.loads(jsp.read_text(encoding="utf-8"))
        for r in raw:
            code = (r.get("code") or "").strip()
            label = (r.get("label") or "").strip()
            if code and label:
                items.append((code, label))
    if items:
        return items
    # fallback
    return [
        ("GE4-EPM","Defense Technology Practices"),
        ("GE4-IPM","Integrated Project & Materials Mgmt"),
        ("GE4-MRO","Military Vehicle & Aircraft MRO"),
        ("CT4-COM","Computation for Chemical Technologists"),
        ("CT4-EMG","Explosives Manufacturing"),
        ("CT4-TFL","Thermofluids"),
    ]

if st.session_state.COURSES is None:
    st.session_state.COURSES = load_courses_from_assets()

def set_courses(new_list: list[tuple[str,str]]):
    st.session_state.COURSES = new_list

def course_codes() -> list[str]:
    return [c for c,_ in st.session_state.COURSES]

def code_to_label() -> dict:
    return dict(st.session_state.COURSES)

# ---------------- Logo handling ----------------
def resolve_logo_b64() -> str | None:
    """Prefer uploaded logo, otherwise assets/adi-logo.png if present."""
    if st.session_state.logo_b64:
        return st.session_state.logo_b64
    p = Path("assets/adi-logo.png")
    return _b64_file(p)

# ---------------- Header (with live logo) ----------------
def header():
    b64 = resolve_logo_b64()
    img_html = f"<img src=\"data:image/png;base64,{b64}\"/>" if b64 else ""
    st.markdown("<div class='adi-topbar'>" + img_html + "<h1>ADI Builder — Lesson Activities & Questions</h1></div>", unsafe_allow_html=True)

header()

# ---------------- Optional upload controls (green dashed) ----------------
with st.expander("Brand & lists (optional)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.caption("**Upload logo** (PNG/JPG/SVG). Once uploaded, the banner updates immediately.")
        logo_up = st.file_uploader("Drag & drop logo here", type=["png","jpg","jpeg","svg"])
        if logo_up is not None:
            try:
                st.session_state.logo_b64 = _b64_bytes(logo_up.getvalue())
                st.success("Logo updated.")
            except Exception as e:
                st.error(f"Logo not loaded: {e}")
    with c2:
        st.caption("Upload **courses.csv** with headers `code,label` to refresh the course list.")
        csv_up = st.file_uploader("Drag & drop courses.csv here", type=["csv"], key="courses_csv")
        if csv_up is not None:
            try:
                reader = csv.DictReader(StringIO(csv_up.getvalue().decode("utf-8")))
                new_courses = []
                for r in reader:
                    code = (r.get("code") or "").strip()
                    label = (r.get("label") or "").strip()
                    if code and label:
                        new_courses.append((code, label))
                if new_courses:
                    set_courses(new_courses)
                    st.success(f"Loaded {len(new_courses)} courses.")
                else:
                    st.warning("No valid rows found. Expecting headers `code,label`.")
            except Exception as e:
                st.error(f"Could not parse CSV: {e}")

# ---------------- Static lists ----------------
COHORTS = [
    "D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05",
    "D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"
]

INSTRUCTORS = [
    "Ben","Abdulmalik","Gerhard","Faiz Lazam","Mohammed Alfarhan","Nerdeen","Dari","Ghamza",
    "Michail","Meshari","Mohammed Alwuthaylah","Myra","Meshal","Ibrahim","Khalil","Salem",
    "Rana","Daniel","Ahmed Albader"
]

VERBS = {
    "Low":    ["define","identify","list","recall","describe","classify","match"],
    "Medium": ["apply","solve","calculate","compare","analyze","demonstrate","explain"],
    "High":   ["evaluate","synthesize","design","justify","critique","optimize","create"]
}

def bloom_from_week(week: int) -> str:
    return "Low" if week <= 4 else ("Medium" if week <= 9 else "High")

# --- Safe callbacks ---
def sync_bloom_from_week():
    st.session_state.bloom_level = bloom_from_week(int(st.session_state.week))
    st.session_state.verbs_selected = VERBS[st.session_state.bloom_level][:]

def update_verbs_on_bloom_change():
    allowed = set(VERBS[st.session_state.bloom_level])
    st.session_state.verbs_selected = [v for v in st.session_state.verbs_selected if v in allowed]

def select_all_verbs():
    st.session_state.verbs_selected = VERBS[st.session_state.bloom_level][:]

def clear_verbs():
    st.session_state.verbs_selected = []

# ---------------- Setup Row ----------------
codes = course_codes()
labels = code_to_label()
if not st.session_state.course_code and codes:
    st.session_state.course_code = codes[0]

st.markdown("<div class='adi-card'>", unsafe_allow_html=True)

r1c = st.columns([2, 1.8, .8, .8, 1.6])
with r1c[0]:
    st.selectbox("Course (code)", options=codes,
                 index=codes.index(st.session_state.course_code) if st.session_state.course_code in codes else 0,
                 key="course_code")
    long_name = labels.get(st.session_state.course_code, "")
    st.markdown(
        f"<span class='muted'>{long_name}</span>"
        f"<span class='pill pill-green'>{st.session_state.course_code}</span>",
        unsafe_allow_html=True
    )

with r1c[1]:
    st.selectbox("Class / Cohort", COHORTS,
                 index=COHORTS.index(st.session_state.class_cohort)
                       if st.session_state.class_cohort in COHORTS else 0,
                 key="class_cohort",
                 help="Type to search (e.g., D2-M03) or pick from the list.")
    st.markdown(f"<span class='pill pill-green'>{st.session_state.class_cohort}</span>",
                unsafe_allow_html=True)

with r1c[2]:
    st.number_input("Lesson", min_value=1, max_value=20, step=1, key="lesson")

with r1c[3]:
    st.number_input("Week", min_value=1, max_value=14, step=1,
                    key="week", on_change=sync_bloom_from_week)

with r1c[4]:
    st.selectbox("Instructor", INSTRUCTORS, key="instructor")
    st.markdown(f"<span class='pill pill-slate'>{st.session_state.instructor}</span>",
                unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Authoring ----------------
st.markdown("### Authoring")
st.markdown("<div class='adi-card tight'>", unsafe_allow_html=True)

st.text_input("Topic / Outcome (optional)", key="topic_outcome",
              placeholder="e.g., Integrated Project and …")
st.caption(
    f"ADI policy: Weeks 1–4 Low • 5–9 Medium • 10–14 High  |  "
    f"Recommended Bloom: **{bloom_from_week(int(st.session_state.week))}**"
)

st.segmented_control("Mode", ["Knowledge","Skills","Revision","Print Summary"], key="mode")

if st.session_state.mode != "Print Summary":
    # ---- Verbs ----
    a1, a2, a3, a4 = st.columns([.9, .9, .9, 1.6])
    with a1:
        st.selectbox("Bloom level", ["Low","Medium","High"],
                     key="bloom_level", on_change=update_verbs_on_bloom_change)
    with a2:
        st.button("Select all", on_click=select_all_verbs)
    with a3:
        st.button("Clear", on_click=clear_verbs)
    with a4:
        st.button("Use recommended for this week", on_click=sync_bloom_from_week)

    verbs_for_level = VERBS[st.session_state.bloom_level]
    st.multiselect(f"Learning verbs (selected {len(st.session_state.verbs_selected)})",
                   options=verbs_for_level, key="verbs_selected")

    # ---- Topics ----
    st.text_area(
        "Topics (one per line)",
        key="topics_text",
        height=110,
        placeholder="e.g.\n- Welding safety checks\n- NDT techniques (PT, MT, UT)\n- Inspection documentation flow"
    )

    # ---- MCQ controls ----
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        include_key = st.checkbox("Answer key", value=True)
    with c2:
        mcq_count = st.selectbox("MCQs", [5,10,15,20], index=1)
    with c3:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("Generate MCQs", type="primary"):
            topics = [t.strip() for t in st.session_state.topics_text.splitlines() if t.strip()]
            topic0 = topics[0] if topics else "topic"
            st.session_state.generated_items = [{
                "stem": f"Sample question {i+1} on {topic0}?",
                "options": ["A) …", "B) …", "C) …", "D) …"],
                "answer": "A"
            } for i in range(int(mcq_count))]

    # ---- Preview & export ----
    if st.session_state.generated_items:
        st.markdown("#### Preview")
        for idx, q in enumerate(st.session_state.generated_items):
            with st.expander(f"Q{idx+1}: {q['stem'][:90]}"):
                q["stem"] = st.text_input("Stem", value=q["stem"], key=f"stem-{idx}")
                a,b = st.columns(2)
                q["options"][0] = a.text_input("Option A", value=q["options"][0], key=f"oa-{idx}")
                q["options"][1] = b.text_input("Option B", value=q["options"][1], key=f"ob-{idx}")
                c,d = st.columns(2)
                q["options"][2] = c.text_input("Option C", value=q["options"][2], key=f"oc-{idx}")
                q["options"][3] = d.text_input("Option D", value=q["options"][3], key=f"od-{idx}")
                q["answer"] = st.selectbox("Correct", ["A","B","C","D"],
                                           index=["A","B","C","D"].index(q["answer"]), key=f"ans-{idx}")

        # TXT export
        txt = "\n\n".join(
            [f"Q{n+1}. {q['stem']}\n" + "\n".join(q["options"]) +
             (f"\nAnswer: {q['answer']}" if include_key else "")
             for n,q in enumerate(st.session_state.generated_items)]
        )
        st.download_button(
            "Export (TXT)", data=txt,
            file_name=f"{st.session_state.course_code}_L{st.session_state.lesson}_W{st.session_state.week}_mcqs.txt"
        )

        # DOCX export (optional)
        def as_docx(items) -> bytes | None:
            try:
                from docx import Document
                from docx.shared import Pt
                doc = Document()
                doc.add_heading(
                    f"{st.session_state.course_code} — Lesson {st.session_state.lesson} (Week {st.session_state.week})",
                    level=1
                )
                doc.add_paragraph()
                for i, q in enumerate(items, start=1):
                    doc.add_paragraph(f"Q{i}. {q['stem']}")
                    for opt in q["options"]:
                        doc.add_paragraph(opt)
                    if include_key:
                        p = doc.add_paragraph(f"Answer: {q['answer']}")
                        p.runs[0].font.bold = True
                    doc.add_paragraph()
                doc.styles["Normal"].font.name = "Calibri"
                doc.styles["Normal"].font.size = Pt(11)
                buf = BytesIO(); doc.save(buf); return buf.getvalue()
            except Exception:
                return None

        docx_bytes = as_docx(st.session_state.generated_items)
        if docx_bytes:
            st.download_button(
                "Export (Word .docx)", data=docx_bytes,
                file_name=f"{st.session_state.course_code}_L{st.session_state.lesson}_W{st.session_state.week}_mcqs.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.caption("Install `python-docx` for Word export (TXT is always available).")

else:
    # Print Summary
    ss = st.session_state
    topics_list = [t for t in ss.topics_text.splitlines() if t.strip()] or ["(add topics in other modes)"]
    st.markdown(
        f"""
        <div class="adi-card" style="max-width:860px;">
          <h2 style="margin:0 0 .3rem 0; color:{ADI_GREEN}">{ss.course_code} — Lesson {ss.lesson} (Week {ss.week})</h2>
          <div class="muted">{code_to_label().get(ss.course_code,'')}</div>
          <div class="muted"><strong>Instructor:</strong> {ss.instructor} &nbsp;|&nbsp;
               <strong>Class:</strong> {ss.class_cohort} &nbsp;|&nbsp;
               <strong>Bloom:</strong> {bloom_from_week(int(ss.week))}</div>
          <h3 style="margin:.8rem 0 .4rem 0;">Topics</h3>
          <ol style="margin-top:0;">{"".join(f"<li>{t}</li>" for t in topics_list)}</ol>
          <h3 style="margin:.8rem 0 .4rem 0;">MCQs (summary)</h3>
          <ol>{"".join(f"<li>{q['stem']}</li>" for q in (ss.generated_items or []))}</ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)
