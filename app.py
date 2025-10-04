# app.py — ADI Builder (Streamlit)
# Stable, ADI-branded app with MCQs (answer key), Activities, Revision, Bloom visuals,
# cached uploads, course-aware filenames, and safe download keys.

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

# ---------- ADI Theme ----------
ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
ADI_STONE = "#f5f5f3"
TEXT_MUTED = "#6b7280"

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ---------- CSS / Branding ----------
def inject_css():
    st.markdown(
        f"""
        <style>
          /* Primary buttons in ADI green, hover to gold */
          .stButton > button {{
              background: {ADI_GREEN}; color: #fff; border-radius: 12px; border: 0;
          }}
          .stButton > button:hover {{ background: {ADI_GOLD}; }}

          /* Checkboxes & radios use ADI green */
          input[type="checkbox"]:checked {{ accent-color: {ADI_GREEN}; }}
          input[type="radio"]:checked {{ accent-color: {ADI_GREEN}; }}

          /* Active tab underline in ADI green */
          div[data-baseweb="tab"] button[aria-selected="true"] {{
              border-bottom: 2px solid {ADI_GREEN} !important;
          }}

          /* Subtle card utility (if needed later) */
          .adi-card {{ background:#fafafa; border:1px solid #ececec; border-radius:14px; padding:12px 14px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

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
                    if hasattr(shp, "text"): out.append(shp.text)
            return "\n".join(out)
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

# ---------- UI helpers ----------
def verbs_pills(label:str,verbs:List[str],key_prefix:str)->List[str]:
    if label: st.markdown(f"**{label}**")
    cols=st.columns(len(verbs)); picks=[]
    for c,v in zip(cols,verbs):
        with c:
            if st.checkbox(v,key=f"{key_prefix}_{v}"): picks.append(v)
    return picks

# ---------- MAIN ----------
def main():
    inject_css()
    header()

    # Sidebar
    with st.sidebar:
        st.caption("Upload (optional)")
        up=st.file_uploader("Drag & drop file",type=["txt","docx","pptx"],
                            help="We parse .txt, .docx or .pptx",label_visibility="collapsed")
        st.caption("Course details")
        course=st.text_input("Course name","")
        cohort=st.text_input("Class / Cohort","")
        instr=st.text_input("Instructor name (optional)","")
        lesson_date=st.date_input("Date",value=date.today())
        st.caption("Context")
        c1,c2=st.columns(2)
        with c1: lesson=st.selectbox("Lesson",[1,2,3,4,5],0)
        with c2: week=st.selectbox("Week",list(range(1,15)),6)
        topic=st.text_input("Topic / outcome","",placeholder="Module description or knowledge outcome")
        cq,ca=st.columns(2)
        with cq: mcq_n=st.selectbox("MCQs",[5,10,15,20],1)
        with ca: act_n=st.selectbox("Activities",[4,6,8,10],1)
        st.divider()
        st.markdown(
            f"<span style='color:{TEXT_MUTED};font-size:12px'>Week policy: "
            f"<b>{policy_band(int(week))}</b> — (1–4 Low / 5–9 Medium / 10–14 High)</span>",
            unsafe_allow_html=True)

    # Main input
    st.checkbox("Use sample text (quick test)",key="sample_toggle")
    uploaded=read_text_from_upload(up)
    if st.session_state.get("sample_toggle") and not uploaded:
        uploaded=("CNC milling safety requires correct PPE, machine guarding, "
                  "understanding feeds and speeds, and proper clamping of workpieces. "
                  "Operators must verify tool paths and perform dry runs before cutting.")
    src=st.text_area("",value=uploaded or "",height=180,
                     placeholder="Paste or jot key notes, vocab, facts here…")

    # Bloom level display
    band=policy_band(int(week))
    if band=="LOW":
        st.markdown(f"### 🟢 LOW Bloom’s Level — *Remember / Understand*  \n"
                    f"Weeks **1–4** focus on recall and comprehension.  \n"
                    f"**Typical verbs:** {', '.join(LOW_VERBS)}")
    elif band=="MEDIUM":
        st.markdown(f"### 🟡 MEDIUM Bloom’s Level — *Apply / Analyse*  \n"
                    f"Weeks **5–9** focus on applying and analysing concepts.  \n"
                    f"**Typical verbs:** {', '.join(MED_VERBS)}")
    else:
        st.markdown(f"### 🔵 HIGH Bloom’s Level — *Evaluate / Create*  \n"
                    f"Weeks **10–14** focus on higher-order thinking.  \n"
                    f"**Typical verbs:** {', '.join(HIGH_VERBS)}")

    picks=verbs_pills("",BAND_TO_VERBS[band],key_prefix=f"verbs_{band.lower()}")
    if not picks: st.info("Pick at least one Bloom verb (you can select multiple).")

    tabs=st.tabs(["Knowledge MCQs (ADI Policy)","Skills Activities","Revision"])

    # --- MCQs ---
    with tabs[0]:
        if st.button("Generate MCQs",type="primary",key="btn_mcq"):
            qs=build_mcqs(src,mcq_n,picks or BAND_TO_VERBS[band])
            st.success(f"Generated {len(qs)} MCQs.")
            for q in qs:
                st.markdown(f"**{q.stem}**")
                for j,c in enumerate(q.choices): st.markdown(f"- {'ABCD'[j]}. {c}")
                st.markdown("<hr/>",unsafe_allow_html=True)
            show_key=st.checkbox("Include answer key in export",True,key="ck_mcq")
            title=build_title("ADI MCQs",course,lesson,week,topic,instr,cohort,lesson_date)
            doc=mcqs_to_docx(qs,title,show_key)
            course_stub = sanitize_filename(course)
            fname = f"adi_mcqs{'_' + course_stub if course_stub else ''}.docx"
            safe_download("⬇️ Download MCQs (.docx)",doc,fname,
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="mcqs_tab")

    # --- Activities ---
    with tabs[1]:
        if st.button("Generate Activities",key="btn_act"):
            acts=build_activities(src,picks or BAND_TO_VERBS[band],act_n)
            for a in acts: st.markdown(a)
            title=build_title("ADI Activities",course,lesson,week,topic,instr,cohort,lesson_date)
            doc=activities_to_docx(acts,title)
            course_stub = sanitize_filename(course)
            fname = f"adi_activities{'_' + course_stub if course_stub else ''}.docx"
            safe_download("⬇️ Download Activities (.docx)",doc,fname,
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="activities_tab")

    # --- Revision ---
    with tabs[2]:
        rev_n=st.selectbox("How many revision items?",[6,8,10,12],1,key="rev_n")
        if st.button("Generate Revision Items",key="btn_rev"):
            rev=build_revision(src,rev_n)
            for r in rev: st.markdown(r)
            title=build_title("ADI Revision",course,lesson,week,topic,instr,cohort,lesson_date)
            doc=revision_to_docx(rev,title)
            course_stub = sanitize_filename(course)
            fname = f"adi_revision{'_' + course_stub if course_stub else ''}.docx"
            safe_download("⬇️ Download Revision (.docx)",doc,fname,
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          scope="revision_tab")

    st.markdown(f"<div style='color:{TEXT_MUTED};font-size:12px;margin-top:18px'>"
                f"ADI style — green {ADI_GREEN}, gold {ADI_GOLD}, stone bg. Keep it simple for daily use."
                f"</div>",unsafe_allow_html=True)

if __name__=="__main__":
    main()
