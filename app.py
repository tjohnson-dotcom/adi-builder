# app.py — ADI Builder (Streamlit)
# Stable, ADI-branded app with MCQs (answer key), Activities, Revision.
# Final right-side look (pills + band cards + Bloom chip), PDF parsing, cached uploads,
# course-aware titles, and unique download keys to avoid StreamlitDuplicateElementId.

from __future__ import annotations
import io, re, random
from datetime import date
from dataclasses import dataclass
from typing import List
from pathlib import Path

import streamlit as st

# ---------- Optional deps (graceful fallback if missing) ----------
try:
    from docx import Document as Docx
    from docx.shared import Pt
except Exception:
    Docx = None

try:
    from pptx import Presentation
except Exception:
    Presentation = None

# PDF support (enable via requirements.txt: pymupdf==1.24.9)
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# ---------- ADI Theme ----------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#f5f5f3"
TEXT_MUTED = "#6b7280"

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ---------- CSS / Branding ----------
def inject_css():
    st.markdown(f"""
    <style>
      /* ---------- Global / Theme touches ---------- */
      .stButton > button {{
          background:{ADI_GREEN}; color:#fff; border-radius:12px; border:0; padding:0.55rem 0.95rem;
      }}
      .stButton > button:hover {{ background:{ADI_GOLD}; }}
      .stTextInput>div>div>input,
      .stTextArea textarea,
      .stSelectbox > div > div {{ border-radius:10px !important; border-color:#cbd5e1 !important; }}
      div[data-baseweb="tab"] button[aria-selected="true"] {{
        border-bottom: 3px solid {ADI_GREEN} !important;
      }}

      /* ---------- Header bar (dark green rounded strip) ---------- */
      div[style*="ADI Builder — Lesson Activities"] {{
        box-shadow: 0 3px 18px rgba(0,0,0,0.06);
        border-radius: 18px !important;
      }}

      /* ---------- Section separators / micro UI ---------- */
      .adi-title {{ height:8px; border-radius:999px; background:#eaeaea; margin:6px 0 14px 0; }}
      .adi-chip {{
        border:1px solid #d1d5db; border-radius:10px; padding:6px 10px; font-size:13px; color:#374151;
        background:#f9fafb; display:inline-block;
      }}

      /* ---------- Band cards (Low/Medium/High) ---------- */
      .adi-band {{ border-radius:18px; padding:14px 16px; margin-top:10px; border:1px solid #eaeaea; }}
      .adi-low  {{ background:linear-gradient(0deg,#f4fbf6,#ffffff); }}
      .adi-med  {{ background:linear-gradient(0deg,#fff9f0,#ffffff); }}
      .adi-high {{ background:linear-gradient(0deg,#f4f7ff,#ffffff); }}
      .adi-band-cap {{ float:right; color:#6b7280; font-size:13px; }}

      /* ---------- Pills (verb checkboxes) ---------- */
      .adi-pills .stCheckbox label {{
        background:#f3f4f6; border:1px solid #e5e7eb; border-radius:9999px;
        padding:6px 12px; display:inline-flex; align-items:center; gap:8px;
      }}
      .adi-pills .stCheckbox div[role="checkbox"] {{ transform: scale(0.9); }}
      .adi-low  .stCheckbox label {{ background:#edf7ef; }}
      .adi-med  .stCheckbox label {{ background:#fff2e0; }}
      .adi-high .stCheckbox label {{ background:#e9f0ff; }}

      /* ---------- Light shadow on main content area ---------- */
      section.main > div:has(.adi-title) {{ box-shadow: 0 2px 10px rgba(0,0,0,.04); border-radius:16px; }}
    </style>
    """, unsafe_allow_html=True)

def header():
    logo_html = ""
    logo_path = Path("adi_logo.png")
    if logo_path.exists():
        logo_html = '<img src="adi_logo.png" style="height:34px; float:right; margin-top:-6px;" />'
    st.markdown(
        f"""
        <div style="background:{ADI_STONE};border-radius:14px;padding:14px 18px;margin:8px 0 16px 0;border:1px solid #e5e7eb">
          {logo_html}
          <div style="font-weight:800;color:{ADI_GREEN};letter-spacing:.2px;">ADI Builder — Lesson Activities & Questions</div>
          <div style="color:{TEXT_MUTED};font-size:14px">Sleek, professional and engaging. Print-ready handouts for instructors.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Utilities ----------
def policy_band(week:int)->str:
    if 1 <= week <= 4: return "LOW"
    if 5 <= week <= 9: return "MEDIUM"
    return "HIGH"

LOW_VERBS = ["define","identify","list","recall","describe","label"]
MED_VERBS = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","critique","create"]
BAND_TO_VERBS = {"LOW": LOW_VERBS,"MEDIUM": MED_VERBS,"HIGH": HIGH_VERBS}

def chunk_text(s:str)->List[str]:
    if not s: return []
    parts = re.split(r"(?<=[.!?])\s+", s.strip())
    return [p.strip() for p in parts if len(p.strip())>=25][:60]

@st.cache_data(show_spinner=False)
def _read_upload_cached(name: str, raw: bytes) -> str:
    try:
        if name.endswith(".txt"):
            return raw.decode("utf-8", errors="ignore")
        if name.endswith(".docx") and Docx:
            d = Docx(io.BytesIO(raw))
            return "\n".join(p.text for p in d.paragraphs)
        if name.endswith(".pptx") and Presentation:
            prs = Presentation(io.BytesIO(raw))
            out = []
            for sld in prs.slides:
                for shp in sld.shapes:
                    if hasattr(shp, "text"):
                        out.append(shp.text)
            return "\n".join(out)
        if name.endswith(".pdf") and fitz:
            doc = fitz.open(stream=raw, filetype="pdf")
            return "\n".join(page.get_text("text") for page in doc)
    except Exception:
        pass
    return ""

def read_text_from_upload(upload)->str:
    if upload is None: return ""
    return _read_upload_cached(upload.name.lower(), upload.read())

def safe_download(label:str,data:bytes,filename:str,mime:str,scope:str):
    st.download_button(label,data=data,file_name=filename,mime=mime,key=f"dl_{scope}")

def build_title(prefix,course,lesson,week,topic,instr,cohort,lesson_date):
    return " — ".join([s for s in [
        prefix, course or None, f"Lesson {lesson} Week {week}",
        topic or None, instr or None, cohort or None,
        lesson_date.strftime("%Y-%m-%d") if lesson_date else None] if s])

def sanitize_filename(course: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", course.strip()) if course else ""

# ---------- MCQs ----------
@dataclass
class MCQ:
    stem:str; choices:List[str]; answer_idx:int

def make_mcq(seed_text:str,verb:str,i:int)->MCQ:
    base=re.sub(r"\s+"," ",seed_text.strip())
    stem=f"{i+1}. {verb.capitalize()} the best answer based on the notes: {base[:160]}…"
    correct=f"{verb.capitalize()} the main concept accurately."
    distractors=[
        f"{verb.capitalize()} a partially correct idea.",
        f"{verb.capitalize()} an unrelated detail.",
        f"{verb.capitalize()} the concept but misapply it."
    ]
    choices=[correct]+distractors
    random.shuffle(choices)
    answer_idx=choices.index(correct)
    return MCQ(stem,choices,answer_idx)

def build_mcqs(source:str,count:int,verbs:List[str])->List[MCQ]:
    sents=chunk_text(source) or [source or "Instructor-provided notes."]
    out=[]
    for i in range(count):
        v=verbs[i%max(1,len(verbs))]
        out.append(make_mcq(sents[i%len(sents)],v,i))
    return out

def mcqs_to_docx(mcqs:List[MCQ],title:str,show_key:bool)->bytes:
    if not Docx:
        buf=io.StringIO(); buf.write(title+"\n\n")
        for q in mcqs:
            buf.write(q.stem+"\n")
            for j,c in enumerate(q.choices): buf.write(f"  {'ABCD'[j]}. {c}\n")
            buf.write("\n")
        if show_key:
            buf.write("Answer Key:\n")
            for i,q in enumerate(mcqs,1): buf.write(f"{i}. {'ABCD'[q.answer_idx]}\n")
        return buf.getvalue().encode("utf-8")
    doc=Docx(); style=doc.styles["Normal"]; style.font.name="Calibri"; style.font.size=Pt(11)
    doc.add_heading(title,level=1)
    for q in mcqs:
        doc.add_paragraph(q.stem)
        for j,c in enumerate(q.choices): doc.add_paragraph(f"{'ABCD'[j]}. {c}")
        doc.add_paragraph("")
    if show_key:
        doc.add_heading("Answer Key",level=2)
        for i,q in enumerate(mcqs,1): doc.add_paragraph(f"{i}. {'ABCD'[q.answer_idx]}")
    b=io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- Activities ----------
def build_activities(src:str,verbs:List[str],count:int=6)->List[str]:
    base=chunk_text(src) or [src or "Topic notes"]
    out=[]
    for i in range(count):
        v=verbs[i%len(verbs or ['apply'])]
        snippet=re.sub(r"\s+"," ",base[i%len(base)])[:120]
        out.append(f"{i+1}. Using **{v}**: Create a short activity engaging students with “{snippet}…”.")
    return out

def activities_to_docx(items:List[str],title:str)->bytes:
    if not Docx: return ("\n".join([title,""]+items)).encode("utf-8")
    doc=Docx(); s=doc.styles["Normal"]; s.font.name="Calibri"; s.font.size=Pt(11)
    doc.add_heading(title,level=1)
    for it in items: doc.add_paragraph(it)
    b=io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- Revision ----------
def build_revision(src:str,count:int=8)->List[str]:
    bits=chunk_text(src) or [src or "Topic notes"]; out=[]
    for i in range(count):
        sn=re.sub(r"\s+"," ",bits[i%len(bits)])[:110]
        out.append(f"{i+1}. Recall: Summarize the key point from — “{sn}…”")
    return out

def revision_to_docx(items:List[str],title:str)->bytes:
    if not Docx: return ("\n".join([title,""]+items)).encode("utf-8")
    doc=Docx(); s=doc.styles["Normal"]; s.font.name="Calibri"; s.font.size=Pt(11)
    doc.add_heading(title,level=1)
    for it in items: doc.add_paragraph(it)
    b=io.BytesIO(); doc.save(b); return b.getvalue()

# ---------- MAIN ----------
def main():
    inject_css()
    header()

    # Sidebar (left)
    with st.sidebar:
        st.caption("Upload (optional)")
        up = st.file_uploader(
            "Drag & drop file",
            type=["txt","docx","pptx","pdf"],
            help="We parse .txt, .docx, .pptx, and .pdf",
            label_visibility="collapsed",
        )

        st.caption("Course details")
        course = st.text_input("Course name","")
        cohort = st.text_input("Class / Cohort","")
        instr  = st.text_input("Instructor name (optional)","")
        lesson_date = st.date_input("Date", value=date.today())

        st.caption("Context")
        c1,c2 = st.columns(2)
        with c1: lesson = st.selectbox("Lesson",[1,2,3,4,5],0)
        with c2: week   = st.selectbox("Week", list(range(1,15)), 0)

        st.markdown(
            f"<div style='font-size:12px;color:{TEXT_MUTED};margin-top:2px'>"
            f"ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.</div>",
            unsafe_allow_html=True,
        )

        st.markdown("### ")
        st.caption("Quick pick blocks")
        st.radio("MCQs", [5,10,20,30], index=1, key="qp_mcqs", horizontal=True)
        st.caption("")  # spacer

    # ---------- RIGHT PANE LOOK ----------
    # Title bar strip
    st.markdown('<div class="adi-title"></div>', unsafe_allow_html=True)

    # Topic / Bloom focus row
    gc1, gc2 = st.columns([1,1])
    with gc1:
        st.caption("Topic / Outcome (optional)")
        topic = st.text_input("", value="", placeholder="Module description, knowledge & skills outcomes")
    with gc2:
        st.caption("Bloom focus (auto)")
        st.markdown(
            f'<span class="adi-chip">Week {week}: '
            f'{"Low" if policy_band(week)=="LOW" else "Medium" if policy_band(week)=="MEDIUM" else "High"}</span>',
            unsafe_allow_html=True,
        )

    # Source (from upload) — optional
    uploaded_text = read_text_from_upload(up)
    with st.expander("Source (from upload) — optional", expanded=False):
        src = st.text_area("", value=uploaded_text or "", height=140,
                           placeholder="Any key notes extracted from your upload will appear here…")
    if up and up.name.lower().endswith(".pdf") and fitz is None:
        st.warning("PDF uploaded, but PDF parsing is not enabled on this build. Add `pymupdf==1.24.9` to requirements.txt.")

    # Bloom’s verbs — band cards with pills
    band = policy_band(int(week))

    # LOW band
    st.markdown(
        f'<div class="adi-band adi-low"><span class="adi-band-cap">Remember / Understand</span>'
        f'<b>Low (Weeks 1–4)</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="adi-pills">', unsafe_allow_html=True)
    low_cols = st.columns(len(LOW_VERBS)); low_sel=[]
    for c, v in zip(low_cols, LOW_VERBS):
        with c:
            if st.checkbox(v, key=f"low_{v}", value=(band=="LOW")): low_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    # MEDIUM band
    st.markdown(
        f'<div class="adi-band adi-med"><span class="adi-band-cap">Apply / Analyse</span>'
        f'<b>Medium (Weeks 5–9)</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="adi-pills">', unsafe_allow_html=True)
    med_cols = st.columns(len(MED_VERBS)); med_sel=[]
    for c, v in zip(med_cols, MED_VERBS):
        with c:
            if st.checkbox(v, key=f"med_{v}", value=(band=="MEDIUM")): med_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    # HIGH band
    st.markdown(
        f'<div class="adi-band adi-high"><span class="adi-band-cap">Evaluate / Create</span>'
        f'<b>High (Weeks 10–14)</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="adi-pills">', unsafe_allow_html=True)
    high_cols = st.columns(len(HIGH_VERBS)); high_sel=[]
    for c, v in zip(high_cols, HIGH_VERBS):
        with c:
            if st.checkbox(v, key=f"high_{v}", value=(band=="HIGH")): high_sel.append(v)
    st.markdown('</div>', unsafe_allow_html=True)

    # Merge selections, preserve order & uniqueness
    picks = list(dict.fromkeys(low_sel + med_sel + high_sel))
    if not picks:
        st.info("Pick at least one Bloom verb block above (you can select multiple).")

    st.markdown("### ")

    # ------------------ TABS ------------------
    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

    # === Tab 1: MCQs ===
    with tabs[0]:
        colL, colR = st.columns([1,1])
        with colL:
            mcq_n = st.selectbox("How many MCQs?", [5,10,15,20], index=1, key="mcq_n_sel")
        with colR:
            show_key = st.checkbox("Include answer key in export", True, key="ck_mcq_key")

        if st.button("Generate MCQs", type="primary", key="btn_mcq"):
            source_text = src or "Instructor-provided notes about this week’s topic."
            qs = build_mcqs(source_text, mcq_n, picks or BAND_TO_VERBS[policy_band(int(week))])
            st.success(f"Generated {len(qs)} MCQs.")
            for q in qs:
                st.markdown(f"**{q.stem}**")
                for j, c in enumerate(q.choices):
                    st.markdown(f"- {'ABCD'[j]}. {c}")
                st.markdown("<hr/>", unsafe_allow_html=True)

            title = build_title("ADI MCQs", course="", lesson=lesson, week=week,
                                topic=topic, instr="", cohort="", lesson_date=lesson_date)
            doc = mcqs_to_docx(qs, title, show_key)
            safe_download("⬇️ Download MCQs (.docx)", doc, "adi_mcqs.docx",
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="mcqs_tab")

    # === Tab 2: Activities ===
    with tabs[1]:
        act_n = st.selectbox("How many activity prompts?", [4,6,8,10], index=1, key="act_n_sel")
        if st.button("Generate Activities", key="btn_act"):
            source_text = src or "Topic notes"
            acts = build_activities(source_text, picks or BAND_TO_VERBS[policy_band(int(week))], act_n)
            for a in acts:
                st.markdown(a)

            title = build_title("ADI Activities", course="", lesson=lesson, week=week,
                                topic=topic, instr="", cohort="", lesson_date=lesson_date)
            doc = activities_to_docx(acts, title)
            safe_download("⬇️ Download Activities (.docx)", doc, "adi_activities.docx",
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="activities_tab")

    # === Tab 3: Revision ===
    with tabs[2]:
        rev_n = st.selectbox("How many revision items?", [6,8,10,12], index=1, key="rev_n")
        if st.button("Generate Revision Items", key="btn_rev"):
            source_text = src or "Topic notes"
            rev = build_revision(source_text, rev_n)
            for r in rev:
                st.markdown(r)

            title = build_title("ADI Revision", course="", lesson=lesson, week=week,
                                topic=topic, instr="", cohort="", lesson_date=lesson_date)
            doc = revision_to_docx(rev, title)
            safe_download("⬇️ Download Revision (.docx)", doc, "adi_revision.docx",
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="revision_tab")

    st.markdown(
        f"<div style='color:{TEXT_MUTED};font-size:12px;margin-top:18px'>"
        f"ADI style — green {ADI_GREEN}, gold {ADI_GOLD}, stone bg. Keep it simple for daily use."
        f"</div>", unsafe_allow_html=True
    )

if __name__=="__main__":
    main()

