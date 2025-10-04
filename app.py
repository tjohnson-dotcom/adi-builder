
# app.py — ADI Builder (Free Override Edition)
# Adds free-text override when KLO/SLO lists are empty.

import io, base64, random, re, json, hashlib
from collections import Counter
from datetime import date
import streamlit as st

try:
    from docx import Document
except Exception:
    Document = None

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")
st.markdown("""
<style>
.block-container { padding-top: 1rem; }
.adi-hero {background: linear-gradient(180deg,#245a34 0%, #214d2f 100%);
  color:#fff;border-radius:14px;padding:14px 16px;box-shadow:0 6px 18px rgba(0,0,0,.06);margin-bottom:10px;}
.adi-hero * {color:#fff !important;}
.adi-hero h1 {font-size:1.0rem;margin:0 0 4px 0;font-weight:700;}
.adi-hero p  {font-size:.85rem;margin:0;opacity:.96;}
.adi-logo { width: 180px; max-width: 100%; height:auto; display:block; }
.hr-soft { height:1px; border:0; background:#e5e7eb; margin:.6rem 0 1rem 0; }
.bloom-group {border:1px solid #e5e7eb;border-radius:12px;padding:12px 12px 8px 12px;margin:10px 0;background:#fff;}
.bloom-low  { background: linear-gradient(180deg,#f1f8f1, #ffffff); }
.bloom-med  { background: linear-gradient(180deg,#fff7e8, #ffffff); }
.bloom-high { background: linear-gradient(180deg,#eef2ff, #ffffff); }
.bloom-focus { border: 2px solid #245a34 !important; box-shadow: 0 0 0 3px rgba(36,90,52,.12) inset !important; background: linear-gradient(180deg, #eaf4ec, #ffffff) !important; }
.bloom-caption {font-size:.80rem;color:#6b7280;margin-left:6px;}
.bloom-pill {display:inline-block;background:#edf2ee;color:#245a34;border-radius:999px;padding:4px 10px;font-weight:600;font-size:.75rem;}
</style>
""", unsafe_allow_html=True)

def _b64(path: str) -> str:
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")
    except Exception: return ""

def week_band(w: int) -> str:
    try: w=int(w)
    except: w=1
    return "Low" if 1<=w<=4 else ("Medium" if 5<=w<=9 else "High")

def docx_download(lines):
    if not Document:
        buf = io.BytesIO(); buf.write("\n".join(lines).encode("utf-8")); buf.seek(0); return buf
    doc = Document(); [doc.add_paragraph(l) for l in lines]; buf = io.BytesIO(); doc.save(buf); buf.seek(0); return buf

def load_modules(path="adi_modules.json"):
    try:
        with open(path,"r",encoding="utf-8") as f: return json.load(f).get("modules",[])
    except Exception: return []

MODULES = load_modules()
COURSE_INDEX = {(m.get("course_title") or m.get("course_code") or f"Course {i}"): m for i,m in enumerate(MODULES)}

def course_display_list():
    return sorted(set([(m.get("course_title") or m.get("course_code") or "Course") for m in MODULES])) or []

def find_module(sel: str):
    if sel in COURSE_INDEX: return COURSE_INDEX[sel]
    for m in MODULES:
        if sel.lower() in ((m.get("course_title","") or "").lower(), (m.get("course_code","") or "").lower()):
            return m
    return None

def auto_klo_for_week(klos, week):
    if not klos: return None
    codes=[k.get("code") for k in klos if k.get("code")]
    if not codes: return None
    i=max(1,int(week or 1))-1
    return codes[i%len(codes)]

def auto_slos_for_week(slos, week, n=2):
    if not slos: return []
    codes=[s.get("code") for s in slos if s.get("code")]
    if not codes: return []
    i=max(1,int(week or 1))-1
    out=[]
    for k in range(min(n,len(codes))): out.append(codes[(i+k)%len(codes)])
    return out

def get_klo_text(module, code):
    if not module or not module.get("klos"): return ""
    for k in module["klos"]:
        if k.get("code")==code: return k.get("text","")
    return ""

def slos_text_list(module, codes):
    if not module or not module.get("slos"): return []
    by={s.get("code"): s.get("text","") for s in module["slos"]}
    return [by[c] for c in (codes or []) if c in by]

def extract_keywords(topic, module, klo_code, slo_codes, k=12):
    base=(topic or "").strip()
    if module: base+=" "+get_klo_text(module,klo_code or "")
    if module and slo_codes:
        for t in slos_text_list(module,slo_codes): base+=" "+t
    words=re.findall(r"[A-Za-zأ-ي]+", base)
    stop=set("a an the and or of for with to in on at by from this that these those is are was were be been being into about as it its they them then than can could should would may might will shall اذا هذا هذه تلك الذي التي الذين اللواتي وال او ثم لما لأن إن كان كانت يكون".split())
    toks=[w.lower() for w in words if len(w)>2 and w.lower() not in stop]
    common=[w for w,_ in Counter(toks).most_common(k)]
    return common or ["project","materials","quality","inspection","logistics","supply","risk","schedule"]

TEMPLATES={
 "remember":[
  "Which statement best defines **{kw}** as used in {course_code}?",
  "Identify the correct description of **{kw}** within {course_code}.",
  "Select the accurate meaning of **{kw}** in {course_code}."
 ],
 "apply":[
  "Apply **{kw}** during a practical {course_code} scenario.",
  "Demonstrate how **{kw}** should be used in a {course_code} task.",
  "Solve a problem that requires proper use of **{kw}** in {course_code}."
 ],
 "analyse":[
  "Analyse how **{kw}** influences outcomes in {course_code}.",
  "Classify the result of changes to **{kw}** in a {course_code} workflow."
 ],
 "evaluate":[
  "Evaluate the effectiveness of **{kw}** in a {course_code} operation.",
  "Justify the choice of method for **{kw}** in {course_code}."
 ],
 "create":[
  "Design an approach that uses **{kw}** to improve {course_code} performance.",
  "Create a simple plan incorporating **{kw}** for {course_code}."
 ]
}

def pick_bucket(v):
    v=(v or "").lower()
    if v in ("define","identify","list","recall","describe","label","classify"): return "remember"
    if v in ("apply","demonstrate","solve","illustrate"): return "apply"
    if v in ("analyse","analyze","compare"): return "analyse"
    if v in ("evaluate","critique","justify"): return "evaluate"
    if v in ("design","create","synthesize","synthesise"): return "create"
    return "remember"

def make_distractors(kw, klo, slos):
    anchor=(" and ".join(slos)) if slos else (klo or "the outcome")
    base=kw.lower()
    return [
        f"A partial statement about {base} with missing constraints.",
        f"A common misconception regarding {base} not aligned to {anchor}.",
        f"An unrelated claim that mentions {base} but ignores the scenario."
    ]

def build_mcqs(topic, verbs, n, module, klo_code, slo_codes):
    verbs=list(verbs) or ["identify","define","list","describe","apply","compare"]
    keys=extract_keywords(topic,module,klo_code,slo_codes,12)
    course_code = module.get("course_code","the course") if module else "the course"
    out=[]
    for i in range(n):
        v=verbs[i%len(verbs)]; bucket=pick_bucket(v); kw=keys[i%len(keys)]
        stem=random.choice(TEMPLATES[bucket]).format(kw=kw, course_code=course_code)
        if bucket=="remember":
            correct=f"{kw.title()}: the most accurate, curriculum-aligned definition for {klo_code or 'the outcome'}."
        elif bucket=="apply":
            correct=f"Proper use of {kw} in a realistic {course_code} task, aligned to {klo_code or 'the outcome'}."
        elif bucket=="analyse":
            correct=f"Breaks {kw} into parts and shows their effect on outcomes (per {klo_code or 'the outcome'})."
        elif bucket=="evaluate":
            correct=f"Judges effectiveness of {kw} using explicit criteria linked to {klo_code or 'the outcome'}."
        else:
            correct=f"Produces a viable design/plan that integrates {kw} for {course_code} (per {klo_code or 'the outcome'})."
        options=[correct]+make_distractors(kw,klo_code,slo_codes); random.shuffle(options)
        out.append({"stem":stem,"options":options[:4],"answer":correct,"klo":klo_code or "—","slos":list(slo_codes or [])})
    return out

def build_activities(topic, n, minutes, verbs, module, klo_code, slo_codes):
    verbs=list(verbs) or ["apply","demonstrate","solve"]
    title = module.get("course_code","Module") if module else "Module"
    slo_str=", ".join(slo_codes or []); tag=f"**{title} {klo_code or ''}**"+(f" / SLO: {slo_str}" if slo_str else "")
    return [f"Activity {i} ({minutes} min): {verbs[(i-1)%len(verbs)].title()} — Use {tag} to work with '{topic or 'today’s concept'}' in a short case or mini-lab." for i in range(1,n+1)]

def build_revision(topic, verbs, qty, module, klo_code, slo_codes):
    verbs=list(verbs) or ["recall","classify","compare","justify","design"]
    title = module.get("course_code","Module") if module else "Module"
    slo_str=", ".join(slo_codes or []); tag=f"{title} {klo_code or ''}"+(f" / {slo_str}" if slo_str else "")
    return [f"Rev {i}: {verbs[(i-1)%len(verbs)].title()} — Summarize how **{tag}** connects to this week’s topic ('{topic or 'module focus'}') in 3–4 sentences." for i in range(1,qty+1)]

s=st.session_state
if "_ok" not in s:
    s._ok=True
    courses=course_display_list(); s.course_sel=(courses[0] if courses else "Select a course")
    s.cohorts=["D1-C01","D1-E01","D1-E02","D1-M01","D1-M02","D1-M03","D1-M04","D1-M05","D2-C01","D2-M01","D2-M02","D2-M03","D2-M04","D2-M05","D2-M06"]
    s.instructors=["GHAMZA LABEEB KHADER","DANIEL JOSEPH LAMB","NARDEEN TARIQ","FAIZ LAZAM ALSHAMMARI","DR. MASHAEL ALSHAMMARI","AHMED ALBADER","Noura Aldossari","Ahmed Gasem Alharbi","Mohammed Saeed Alfarhan","Abdulmalik Halawani","Dari AlMutairi","Meshari AlMutrafi","Myra Crawford","Meshal Alghurabi","Ibrahim Alrawili","Michail Mavroftas","Gerhard Van der Poel","Khalil Razak","Mohammed Alwuthylah","Rana Ramadan","Salem Saleh Subaih","Barend Daniel Esterhuizen"]
    s.lesson=1; s.week=1; s.date_str=date.today().isoformat(); s.source_text=""; s.deep_scan=False; s.bloom_picks=set(); s.last_generated={}; s.klo_sel=""; s.slo_sel_list=[]

LOGO64=_b64("adi_logo.png")
st.markdown("""<div class="adi-hero"><h1>ADI Builder — Lesson Activities &amp; Questions</h1><p>Sleek, professional and engaging. Print-ready handouts for your instructors.</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    if LOGO64: st.markdown(f'<img class="adi-logo" src="data:image/png;base64,{LOGO64}" />', unsafe_allow_html=True)
    st.caption("ADI")
    st.write("### Upload (optional)")
    st.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"], key="uploader")
    f=s.get("uploader")
    if f is not None:
        size_kb=(getattr(f,"size",0) or 0)/1024; st.success(f"✅ File selected: **{f.name}** ({size_kb:.1f} KB)")
    if st.button("Process source", disabled=(f is None)):
        try:
            data=f.getvalue() if hasattr(f,"getvalue") else f.read()
            text=data.decode("utf-8",errors="ignore") if data else ""
            if text.strip(): s["source_text"]=text; st.toast("Upload processed.",icon="✅")
            s["uploader"]=None
        except Exception as e: st.error(f"Could not process file: {e}")

    course_choices=course_display_list() or ["(no modules found)"]
    s.course_sel=st.selectbox("Course name", course_choices, index=0)
    st.selectbox("Class / Cohort", s.cohorts, index=0, key="coh_sel")
    st.selectbox("Instructor name", s.instructors, index=0, key="ins_sel")
    st.text_input("Date", key="date_str")

    c1,c2=st.columns(2)
    with c1: st.number_input("Lesson", min_value=1, key="lesson")
    with c2: st.number_input("Week", min_value=1, key="week")
    st.caption("ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.")

    mod=find_module(s.get("course_sel","")); klos=(mod.get("klos",[]) if mod else []); slos=(mod.get("slos",[]) if mod else [])
    klo_codes=[k.get("code") for k in klos if k.get("code")] if klos else []
    slo_codes=[sl.get("code") for sl in slos if sl.get("code")] if slos else []
    auto_klo=auto_klo_for_week(klos,s.get("week",1)); auto_slo_list=auto_slos_for_week(slos,s.get("week",1),2)

    with st.expander("Outcome alignment", expanded=True):
        st.caption(f"Auto-linked **KLO** for Week {int(s.get('week',1))}: **{auto_klo or '(none)'}**")
        if auto_slo_list: st.caption("Auto-linked **SLO(s)**: "+", ".join(auto_slo_list))

        # Always allow overrides. If no codes, show free-text fields.
        st.checkbox("Override KLO for this lesson", key="klo_override")
        if s.get("klo_override"):
            if klo_codes:
                default_idx=klo_codes.index(auto_klo) if (auto_klo in klo_codes) else 0
                s.klo_sel_manual=st.selectbox("Choose KLO", klo_codes, index=default_idx)
            else:
                s.klo_sel_manual=st.text_input("Enter KLO code (e.g., KLO3)", value=s.get("klo_sel") or "")
            klo_code=s.get("klo_sel_manual") or auto_klo
            st.caption("KLO override active.")
        else:
            klo_code=auto_klo

        st.checkbox("Override SLOs for this lesson", key="slo_override")
        if s.get("slo_override"):
            if slo_codes:
                default=auto_slo_list if auto_slo_list else []
                s.slo_sel_manual=st.multiselect("Choose SLO(s)", slo_codes, default=default)
                slo_list=s.slo_sel_manual
            else:
                s.slo_text_free=st.text_input("Enter SLO codes (comma-separated)", value=", ".join(auto_slo_list or []))
                slo_list=[c.strip() for c in s.slo_text_free.split(",") if c.strip()]
            st.caption("SLO override active.")
        else:
            slo_list=auto_slo_list

        # Show KLO text if present
        if klo_code:
            t=None
            if mod and mod.get("klos"):
                for k in mod["klos"]:
                    if k.get("code")==klo_code: t=k.get("text",""); break
            if t: st.caption(f"**{klo_code}** — {t}")

    s["klo_sel"]=klo_code or ""
    s["slo_sel_list"]=slo_list or []

st.write("**Topic / Outcome (optional)**")
st.text_area("Module description, knowledge & skills outcomes", value=s.get("source_text",""), height=110, label_visibility="collapsed", key="source_text")
st.toggle("Deep scan source (slower, better coverage)", value=s.get("deep_scan", False), key="deep_scan")

LOW=["define","identify","list","recall","describe","label"]
MED=["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH=["evaluate","synthesize","design","justify","critique","create"]
band=week_band(s.get("week",1))
st.markdown(f"<div style='text-align:right'><span class='bloom-pill'>Week {int(s.get('week',1))}: {band}</span></div>", unsafe_allow_html=True)

def bloom_group(title, subtitle, verbs, css, band_name):
    classes=f"bloom-group {css}"+(" bloom-focus" if band_name==band else "")
    st.markdown(f'<div class="{classes}">', unsafe_allow_html=True)
    st.markdown(f"**{title}**  <span class='bloom-caption'>{subtitle}</span>", unsafe_allow_html=True)
    cols=st.columns(len(verbs)); picks=s.setdefault("bloom_picks", set())
    for i,v in enumerate(verbs):
        with cols[i]:
            k=f"verb-{v}"; val=st.checkbox(v, value=s.get(k, False), key=k)
            if val: picks.add(v)
            else: picks.discard(v)
    st.markdown("</div>", unsafe_allow_html=True)

bloom_group("Low (Weeks 1–4)","Remember / Understand", LOW,"bloom-low","Low")
bloom_group("Medium (Weeks 5–9)","Apply / Analyse", MED,"bloom-med","Medium")
bloom_group("High (Weeks 10–14)","Evaluate / Create", HIGH,"bloom-high","High")

st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

page=st.radio("Mode", ["Activities","MCQs","Revision","Print Summary"], horizontal=True, key="mode_radio")
picked=sorted(list(s.get("bloom_picks", set())))
topic=s.get("source_text","").strip(); mod=find_module(s.get("course_sel",""))
klo=s.get("klo_sel","") or ""
slo_l=s.get("slo_sel_list", [])

def header_lines():
    slo_head=", ".join(slo_l or []) or "—"
    return [f"Course: {s.get('course_sel','')}", f"Week: {int(s.get('week',1))} • Lesson: {int(s.get('lesson',1))}", f"Instructor: {s.get('ins_sel','')}", f"Linked KLO: {klo or '—'}", f"SLO(s): {slo_head}", ""]

def seed_now():
    random.seed(int(hashlib.sha256(f"{s.get('ins_sel','')}|{s.get('course_sel','')}|{s.get('week',1)}|{s.get('lesson',1)}".encode('utf-8')).hexdigest()[:8], 16))

if page=="Activities":
    slo_cap=", ".join(slo_l or []) or "—"
    st.subheader("Activities")
    st.caption(f"Linked KLO: {klo or '—'} • SLO(s): {slo_cap} • Instructor: {s.get('ins_sel','')} • Week {int(s.get('week',1))} • Lesson {int(s.get('lesson',1))}")
    st.selectbox("Number of activities", [1,2,3,4], index=1, key="acts_count_sel")
    st.number_input("Minutes per activity", min_value=5, max_value=60, step=5, value=20, key="acts_minutes_input")
    if st.button("Generate Activities", type="primary"):
        seed_now(); s.last_generated["activities"]=build_activities(topic, s.get("acts_count_sel",2), s.get("acts_minutes_input",20), picked, mod or {}, klo, slo_l); st.success(f"Generated {len(s.last_generated['activities'])} activities.")
    acts=s.last_generated.get("activities") or build_activities(topic,2,15,picked,mod or {},klo,slo_l)
    for a in acts: st.write("• "+a)
    st.download_button("Download Activities (DOCX)", data=docx_download(header_lines()+[f\"{i+1}. {a}\" for i,a in enumerate(acts)]), file_name="ADI_Activities.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif page=="MCQs":
    slo_cap=", ".join(slo_l or []) or "—"
    st.subheader("Knowledge MCQs")
    st.caption(f"Linked KLO: {klo or '—'} • SLO(s): {slo_cap} • Instructor: {s.get('ins_sel','')} • Week {int(s.get('week',1))} • Lesson {int(s.get('lesson',1))}")
    st.selectbox("How many MCQs?", [5,10,15,20,25,30], index=1, key="mcq_count_sel")
    st.checkbox("Include answer key in export", value=True, key="include_answer_chk")
    if st.button("Generate MCQs", type="primary"):
        seed_now(); s.last_generated["mcqs"]=build_mcqs(topic,picked,s.get("mcq_count_sel",10),mod or {},klo,slo_l); st.success(f"Generated {len(s.last_generated['mcqs'])} MCQs.")
    mcqs=s.last_generated.get("mcqs") or build_mcqs(topic,picked,5,mod or {},klo,slo_l)
    letters=["A","B","C","D"]
    for i,q in enumerate(mcqs,1):
        st.markdown(f"**Q{i}. {q['stem']}**")
        for L,opt in zip(letters,q["options"]): st.write(f"- **{L}.** {opt}")
        if s.get("include_answer_chk", True): st.caption(f"Answer: {q['answer']}")
        slo_tag=", ".join(q.get("slos", [])) or "—"
        st.caption(f"Linked KLO: {q.get('klo',klo or '—')} • SLO(s): {slo_tag} • Instructor: {s.get('ins_sel','')}")
        st.divider()
    lines=header_lines()
    for i,q in enumerate(mcqs,1):
        lines.append(f"Q{i}. {q['stem']}"); 
        for L,opt in zip(letters,q["options"]): lines.append(f\"{L}. {opt}\")
        if s.get("include_answer_chk", True): lines.append(f\"Answer: {q['answer']}\"); lines.append("")
    st.download_button("Download MCQs (DOCX)", data=docx_download(lines), file_name="ADI_MCQs.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif page=="Revision":
    slo_cap=", ".join(slo_l or []) or "—"
    st.subheader("Revision")
    st.caption(f"Linked KLO: {klo or '—'} • SLO(s): {slo_cap} • Instructor: {s.get('ins_sel','')} • Week {int(s.get('week',1))} • Lesson {int(s.get('lesson',1))}")
    st.selectbox("How many revision prompts?", list(range(3,13)), index=2, key="rev_qty_sel")
    if st.button("Generate Revision", type="primary"):
        seed_now(); s.last_generated["revision"]=build_revision(topic,picked,s.get("rev_qty_sel",5),mod or {},klo,slo_l); st.success(f"Generated {len(s.last_generated['revision'])} revision prompts.")
    rev=s.last_generated.get("revision") or build_revision(topic,picked,5,mod or {},klo,slo_l)
    for r in rev: st.write("• "+r)
    st.download_button("Download Revision (DOCX)", data=docx_download(header_lines()+[f\"{i+1}. {r}\" for i,r in enumerate(rev)]), file_name="ADI_Revision.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

else:
    st.subheader("Print Summary")
    slo_head=", ".join(slo_l or []) or "—"
    st.write(f"**Course**: {s.get('course_sel','')}  \n**Cohort**: {s.get('coh_sel','')}  \n**Instructor**: {s.get('ins_sel','')}  \n**Week**: {s.get('week',1)}  \n**Lesson**: {s.get('lesson',1)}  \n**Date**: {s.get('date_str','')}  \n**Linked KLO**: {klo or '—'}  \n**SLO(s)**: {slo_head}")
    if topic: st.subheader("Module notes / outcomes"); st.write(topic)
    g=s.last_generated
    if g.get("mcqs"): st.subheader("Latest MCQs"); [st.write(f\"{i}. {q['stem']}\") for i,q in enumerate(g['mcqs'][:5],1)]
    if g.get("activities"): st.subheader("Latest Activities"); [st.write("• "+a) for a in g["activities"]]
    if g.get("revision"): st.subheader("Latest Revision"); [st.write("• "+r) for r in g["revision"]]
