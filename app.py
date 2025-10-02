# streamlit_app.py — ADI Builder (Pedagogical + Regenerate + Copy)
import os, io, re, random, json
from collections import Counter
from typing import List, Tuple

import streamlit as st
from docx import Document
from docx.shared import Pt

# Optional parsers (guarded imports)
try:
    from pptx import Presentation
except Exception:
    Presentation = None
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None
try:
    from docx import Document as DocxReader
except Exception:
    DocxReader = None

# ---------- App chrome ----------
st.set_page_config(page_title="ADI Builder", page_icon="📚", layout="wide")
ADI_GREEN = "#245a34"; ADI_GOLD = "#C8A85A"; STONE_BG = "#f5f5f4"; INK = "#1f2937"
st.markdown(f"""
<style>
:root {{ --adi-font-base: 18px; --adi-font-ui: 17px; }}
html, body, [data-testid="stAppViewContainer"] {{
  background:{STONE_BG}; color:{INK};
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, 'Helvetica Neue', Arial;
  font-size: var(--adi-font-base);
}}
.main .block-container {{ max-width: 1360px; margin:0 auto; padding-top:.6rem; padding-bottom:2rem; }}
.stButton>button {{
  background:{ADI_GREEN} !important; color:white !important; border:0; border-radius:14px;
  padding:.55rem .9rem; font-weight:600; font-size:var(--adi-font-ui);
}}
.stButton>button:hover {{ filter:brightness(1.05); }}
.adi-card {{ background:white; border-radius:16px; padding:1.1rem; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
.bloom-chip {{ display:inline-flex; align-items:center; gap:.5rem; padding:.35rem .7rem; border-radius:999px;
  background:linear-gradient(90deg,{ADI_GOLD},{ADI_GREEN}); color:white; font-weight:700; font-size:.92rem; }}
.copybox textarea {{ font-size: 15px !important; }}
hr {{ border:none; border-top:1px solid rgba(0,0,0,.06); margin:.6rem 0; }}
</style>
""", unsafe_allow_html=True)

# ---------- Session state ----------
if "messages" not in st.session_state: st.session_state["messages"] = []
if "uploads" not in st.session_state: st.session_state["uploads"] = {}
if "draft" not in st.session_state: st.session_state["draft"] = None  # stores last generated items

# ---------- Sidebar ----------
with st.sidebar:
    if os.path.isfile("adi_logo.png"):
        st.image("adi_logo.png", use_container_width=True)
    else:
        st.markdown("### **ADI Builder**")

    modes = ["Knowledge", "Activities", "Revision"]  # three modes only
    icons = {"Knowledge":"📘","Activities":"🎯","Revision":"📝"}
    labels = [f"{icons[m]} {m}" for m in modes]
    picked = st.radio("Mode", labels, index=0, label_visibility="collapsed")
    mode = modes[labels.index(picked)]

    week   = st.selectbox("Week", list(range(1,15)), index=0)
    lesson = st.selectbox("Lesson", list(range(1,6)), index=0)
    count  = st.selectbox("Number of items", [1,2,3,4,5,6,8,10,12,15,20], index=4)
    time_per = st.selectbox("Time per item (minutes)", [5,10,15,20,25,30,40,45,50,60], index=2)

    st.markdown("### 📎 Resources")
    with st.expander("📥 Drag & drop files or click to browse"):
        ebook_file = st.file_uploader("📖 eBook / Reader (PDF)", type=["pdf"], key="ebook")
        plan_file  = st.file_uploader("📄 Lesson Plan (DOCX/PDF)", type=["docx","pdf"], key="plan")
        ppt_file   = st.file_uploader("📊 Slides (PPTX)", type=["pptx"], key="ppt")

    # Visible upload status
    def _remember(tag,f):
        if f: st.session_state["uploads"][tag] = {"name":f.name, "size":round(getattr(f,"size",0)/1024/1024,2)}
    _remember("ebook", ebook_file); _remember("plan", plan_file); _remember("ppt", ppt_file)

    if st.session_state["uploads"]:
        st.markdown("#### ✅ Uploaded")
        for tag,meta in st.session_state["uploads"].items():
            icon={"ebook":"📖","plan":"📄","ppt":"📊"}[tag]
            st.markdown(f"- {icon} **{meta['name']}** · {meta['size']} MB")

    run = st.button("✨ Generate for staff")

# ---------- Bloom band ----------
def bloom_level(w:int)->str:
    if 1<=w<=4: return "LOW — Remember/Understand"
    if 5<=w<=9: return "MEDIUM — Apply/Analyse"
    return "HIGH — Evaluate/Create"
def _band(w:int)->str:
    return "LOW" if w<=4 else ("MEDIUM" if w<=9 else "HIGH")

# ---------- Text extraction (guarded & capped) ----------
STOP = set("a an and are as at be by for from has have in is it its of on or that the to was were with your you we they not this those these which into over under among between about more most less least such than then there their whose where when who what while how why".split())
def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()

def text_from_pdf(file) -> str:
    try:
        if not PdfReader: return ""
        r = PdfReader(file); pages=[]; cap = min(len(r.pages), 40)
        for i in range(cap):
            try: pages.append(r.pages[i].extract_text() or "")
            except Exception: continue
        return _clean(" ".join(pages))
    except Exception: return ""

def text_from_pptx(file) -> str:
    try:
        if not Presentation: return ""
        prs = Presentation(file); buf=[]
        for sl in prs.slides[:80]:
            for sh in sl.shapes:
                if hasattr(sh, "text"): buf.append(sh.text)
        return _clean(" ".join(buf))
    except Exception: return ""

def text_from_docx(file) -> str:
    try:
        if not DocxReader: return ""
        d = DocxReader(file)
        return _clean(" ".join(p.text for p in d.paragraphs))
    except Exception: return ""

def build_corpus():
    parts=[]
    if plan_file and getattr(plan_file, "type", "")=="application/pdf": parts.append(text_from_pdf(plan_file))
    if plan_file and plan_file.type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/msword"):
        parts.append(text_from_docx(plan_file))
    if ebook_file: parts.append(text_from_pdf(ebook_file))
    if ppt_file: parts.append(text_from_pptx(ppt_file))
    return _clean(" ".join(p for p in parts if p))[:250000]

def split_sentences(text: str) -> List[str]:
    s = re.split(r"(?<=[.!?])\s+", text)
    return [x.strip() for x in s if 40 <= len(x) <= 180]

def extract_terms(text: str, topk=140) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text)
    words = [w.lower() for w in words if w.lower() not in STOP]
    freq = Counter(words)
    caps = re.findall(r"\b([A-Z][a-zA-Z]{3,})\b", text)
    for c in caps: freq[c.lower()] += 2
    seen=set(); out=[]
    for w,_ in freq.most_common(topk):
        base=w.rstrip("s")
        if base not in seen:
            out.append(w); seen.add(base)
    return out[:topk]

# ---------- MCQ generation with QA ----------
def stem_pool(topic:str, week:int, n:int) -> List[str]:
    t = topic.strip() if topic else "the topic"
    band=_band(week)
    pools={
        "LOW":[
            "Identify the correct term for {T}.",
            "Select the best definition of {T}.",
            "Recognize the main idea of {T}.",
            "Match the concept that describes {T}.",
        ],
        "MEDIUM":[
            "Apply the concept of {T} to a scenario.",
            "Select the step that should occur next in {T}.",
            "Classify the example according to {T}.",
            "Determine which approach best solves a problem in {T}.",
        ],
        "HIGH":[
            "Evaluate which option best justifies {T}.",
            "Decide which solution most improves {T}.",
            "Critique the argument about {T} and pick the most valid claim.",
            "Prioritize the factors for {T} and choose the top priority.",
        ]
    }
    pool=pools[band]
    return [pool[i%len(pool)].replace("{T}", t) for i in range(n)]

def make_cloze_mcqs(text:str, n:int) -> List[dict]:
    sents=split_sentences(text); terms=extract_terms(text, topk=140)
    if not sents or not terms: return []
    out=[]; used=set(); tries=0
    while len(out)<n and tries<n*10:
        tries+=1; s=random.choice(sents)
        cand=[t for t in terms if re.search(rf"\b{re.escape(t)}\b", s, flags=re.I)]
        if not cand: continue
        term=random.choice(cand); key=(s,term.lower())
        if key in used: continue
        used.add(key)
        stem = re.sub(rf"\b{re.escape(term)}\b","____",s,flags=re.I,count=1)
        pool=[t for t in terms if t!=term and abs(len(t)-len(term))<=4]
        random.shuffle(pool); ds=pool[:3]
        while len(ds)<3: ds.append(random.choice(terms))
        raw=[(term,True),(ds[0],False),(ds[1],False),(ds[2],False)]
        random.shuffle(raw); letters=["A","B","C","D"]
        options=[(letters[i],txt,is_ok) for i,(txt,is_ok) in enumerate(raw)]
        out.append({"stem":stem,"options":options})
    return out

def validate_mcq(stem:str, options:List[Tuple[str,str,bool]]) -> Tuple[bool,List[str]]:
    issues=[]
    if len(stem.split())>28: issues.append("Stem too long")
    if not any(ok for _,_,ok in options): issues.append("No correct option")
    if sum(1 for _,_,ok in options if ok)!=1: issues.append("Multiple correct options")
    opt_lens=[len(t.split()) for _,t,_ in options]
    if max(opt_lens)-min(opt_lens)>15: issues.append("Options length varies too much")
    for _,t,_ in options:
        if any(w in t.lower() for w in ["always","never","all of the above","none of the above"]):
            issues.append("Absolute/banned phrasing")
    return (len(issues)==0, issues)

def generate_mcqs(topic:str, week:int, count:int, corpus:str) -> Tuple[List[dict],List[dict]]:
    items=[]; checks=[]
    cloze = make_cloze_mcqs(corpus, count) if corpus else []
    if len(cloze)<count:
        fillers=stem_pool(topic,week,count-len(cloze))
        for fs in fillers:
            raw=[("Best answer aligned to the topic",True),
                 ("Partly correct but incomplete",False),
                 ("Confuses two concepts",False),
                 ("Irrelevant detail",False)]
            random.shuffle(raw); letters=["A","B","C","D"]
            options=[(letters[i],txt,ok) for i,(txt,ok) in enumerate(raw)]
            cloze.append({"stem":fs,"options":options})
    for q in cloze[:count]:
        ok, issues = validate_mcq(q["stem"], q["options"])
        if not ok:
            q["stem"]=" ".join(q["stem"].split()[:26])
            new_opts=[]
            for letter,text,is_ok in q["options"]:
                words=text.split()[:18]; new_opts.append((letter," ".join(words),is_ok))
            q["options"]=new_opts
            ok, issues = validate_mcq(q["stem"], q["options"])
        items.append(q); checks.append({"ok":ok,"issues":issues})
    return items, checks

# ---------- Activity/Revision generation ----------
def activity_blocks(mode:str, topic:str, n:int, mins:int):
    t = topic or "the topic"
    base_titles = (["Think–Pair–Share","Jigsaw teach-back","Gallery walk","Case vignette","Concept map"]
                   if mode=="Activities" else
                   ["Cheat sheet","5 Q short answer","Flashcards","Past-paper drill","Exit ticket"])
    blocks=[]
    for i in range(n):
        title = base_titles[i%len(base_titles)]
        # tie objective to topic for alignment
        obj = f"To deepen understanding of {t} and demonstrate applied knowledge."
        grouping = "Pairs" if mode=="Activities" else "Individual"
        materials = "Board, sticky notes" if mode=="Activities" else "Paper, pens"
        if title=="Think–Pair–Share":
            steps = ["Think (2m): list 3 facts, 2 links, 1 question.",
                     "Pair (5m): compare, refine, decide top 3 points.",
                     "Share (rest): selected pairs share; teacher synthesises."]
        elif title=="Jigsaw teach-back":
            steps = ["Split subtopics among groups.", "Create a 3‑bullet explainer.",
                     "Teach-back: rotate speakers; peers ask one question."]
        elif title=="Gallery walk":
            steps = ["Groups draft posters on misconceptions.", "Walk: add sticky-note corrections.",
                     "Debrief: highlight two strong corrections."]
        else:
            steps = ["Brief: clarify focus and success criteria.",
                     "Do: produce the artefact/output.",
                     "Debrief: share, compare, refine using criteria."]
        success = ["Accurate key points","Clear explanation","Evidence/example used"]
        quick = "Exit ticket: 1 insight + 1 question."
        blocks.append({
            "title": title, "objective": obj, "time": mins, "grouping": grouping,
            "materials": materials, "steps": steps, "success": success, "check": quick
        })
    return blocks

def validate_activity(b):
    issues=[]
    if not b["objective"]: issues.append("Missing objective")
    if not b["steps"] or len(b["steps"])<3: issues.append("Too few steps")
    if b["time"]<5: issues.append("Time too short")
    return (len(issues)==0, issues)

# ---------- Utilities for per‑item regenerate ----------
def init_draft(mode, week, lesson, count, time_per, topic, notes, corpus=""):
    st.session_state["draft"] = {
        "mode": mode, "week": week, "lesson": lesson,
        "count": count, "time_per": time_per, "topic": topic, "notes": notes,
        "corpus_ok": bool(corpus), "corpus_len": len(corpus or ""),
        "items": [], "checks": []
    }
    if mode=="Knowledge":
        items, checks = generate_mcqs(topic, week, count, corpus)
    else:
        items = activity_blocks(mode, topic, count, time_per)
        checks = [validate_activity(b) for b in items]
    st.session_state["draft"]["items"] = items
    st.session_state["draft"]["checks"] = checks

def regenerate_one(index, corpus):
    d = st.session_state.get("draft")
    if not d: return
    mode = d["mode"]
    if mode=="Knowledge":
        # generate 1 new MCQ
        new_item, new_check = generate_mcqs(d["topic"], d["week"], 1, corpus)
        d["items"][index] = new_item[0]
        d["checks"][index] = new_check[0]
    else:
        # regenerate 1 activity block
        tmp = activity_blocks(mode, d["topic"], 1, d["time_per"])[0]
        d["items"][index] = tmp
        d["checks"][index] = validate_activity(tmp)

# ---------- Main layout ----------
left, right = st.columns([1,1], gap="large")
with left:
    st.subheader(f"{mode} — Week {week}, Lesson {lesson}")
    st.caption("ADI-aligned prompts and activities. No sliders. Easy picks.")
    st.markdown(f"<span class='bloom-chip'>Bloom: {bloom_level(week)}</span>", unsafe_allow_html=True)
    topic = st.text_input("Topic / Objective (short)")
    notes = st.text_area("Key notes (optional)", height=110)

with right:
    st.markdown("### 📤 Draft outputs")
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)

    # Build or reuse draft
    corpus = build_corpus() if (run and mode=="Knowledge") else (st.session_state.get("last_corpus") or "")
    if run:
        init_draft(mode, week, lesson, count, time_per, topic, notes, corpus)
        st.session_state["last_corpus"] = corpus

    d = st.session_state.get("draft")
    if not d:
        st.info("Upload resources (optional), set Week/Lesson, choose mode, number of items, and time per item. Then click **Generate**.")
    else:
        # Render items with Regenerate + Copy
        if d["mode"]=="Knowledge":
            answer_key=[]
            for i,q in enumerate(d["items"], start=1):
                colA, colB = st.columns([0.8,0.2])
                with colA:
                    st.write(f"**Q{i}.** {q['stem']}")
                    # Copy block
                    text_block = "Q{}: {}\n{}\n{}\n{}\n{}".format(
                        i, q['stem'],
                        f"A. {q['options'][0][1]}",
                        f"B. {q['options'][1][1]}",
                        f"C. {q['options'][2][1]}",
                        f"D. {q['options'][3][1]}",
                    )
                    st.text_area("Copy", value=text_block, height=120, key=f"copy_mcq_{i}", label_visibility="collapsed")
                    for letter,text,is_ok in q["options"]:
                        st.write(f" {letter}. {text}")
                        if is_ok: answer_key.append((i,letter))
                    if not d["checks"][i-1]["ok"]:
                        st.caption("⚠️ Auto-fixed: " + ", ".join(d['checks'][i-1]['issues']))
                with colB:
                    if st.button("🔄 Regenerate", key=f"regen_mcq_{i}"):
                        regenerate_one(i-1, st.session_state.get("last_corpus",""))
                        st.experimental_rerun()
                st.write("")
            st.markdown("**Answer Key**")
            st.write(", ".join([f"Q{q} → {a}" for q,a in answer_key]))

            # Exports
            def export_mcq_docx():
                doc=Document(); doc.add_heading(f"ADI Knowledge — W{d['week']} L{d['lesson']}", 1)
                if d["topic"]: doc.add_paragraph(f"Topic: {d['topic']}")
                if d["notes"]: doc.add_paragraph(f"Notes: {d['notes']}")
                for i,q in enumerate(d["items"],1):
                    doc.add_paragraph(f"Q{i}. {q['stem']}")
                    for letter,text,_ in q["options"]:
                        p=doc.add_paragraph(f"   {letter}. {text}")
                        for run in p.runs: run.font.size=Pt(11)
                doc.add_heading("Answer Key",2)
                ak=", ".join([f"Q{q} → {a}" for q,a in answer_key])
                doc.add_paragraph(ak)
                bio=io.BytesIO(); doc.save(bio); bio.seek(0); return bio

            def export_mcq_gift():
                lines=[]
                for i,q in enumerate(d["items"],1):
                    lines.append(f"::Q{i}:: {q['stem']} {{")
                    for letter,text,is_ok in q["options"]:
                        lines.append(("=" if is_ok else "~") + text)
                    lines.append("}")
                return io.BytesIO("\n".join(lines).encode("utf-8"))

            c1,c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Export MCQs (DOCX)", data=export_mcq_docx(),
                                   file_name=f"ADI_Knowledge_W{d['week']}_L{d['lesson']}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   use_container_width=True)
            with c2:
                st.download_button("⬇️ Export MCQs (Moodle GIFT)", data=export_mcq_gift(),
                                   file_name=f"ADI_Knowledge_W{d['week']}_L{d['lesson']}.gift",
                                   mime="text/plain", use_container_width=True)

        else:
            # Activities / Revision
            for i,b in enumerate(d["items"], start=1):
                colA, colB = st.columns([0.8,0.2])
                singular = "Activity" if d["mode"]=="Activities" else "Task"
                with colA:
                    st.write(f"**{singular} {i} ({b['time']} min) — {b['title']}**")
                    st.caption(b["objective"])
                    st.write(f"**Grouping:** {b['grouping']}  |  **Materials:** {b['materials']}")
                    st.write("**Procedure:**")
                    for step in b["steps"]:
                        st.write(f"- {step}")
                    st.write("**Success criteria:** " + ", ".join(b["success"]))
                    st.write(f"**Quick check:** {b['check']}")
                    # Copy block
                    text_block = f"""{singular} {i} ({b['time']} min) — {b['title']}
Objective: {b['objective']}
Grouping: {b['grouping']}  |  Materials: {b['materials']}
Steps:
- """ + "\n- ".join(b["steps"]) + f"""
Success criteria: {', '.join(b['success'])}
Quick check: {b['check']}
"""
                    st.text_area("Copy", value=text_block, height=160, key=f"copy_act_{i}", label_visibility="collapsed")
                    ok, issues = st.session_state["draft"]["checks"][i-1]
                    if not ok:
                        st.caption("⚠️ " + ", ".join(issues))
                with colB:
                    if st.button("🔄 Regenerate", key=f"regen_act_{i}"):
                        regenerate_one(i-1, st.session_state.get("last_corpus",""))
                        st.experimental_rerun()
                st.write("")

            def export_plan_docx():
                doc=Document(); doc.add_heading(f"ADI {d['mode']} Plan — W{d['week']} L{d['lesson']}", 1)
                if d["topic"]: doc.add_paragraph(f"Topic: {d['topic']}")
                if d["notes"]: doc.add_paragraph(f"Notes: {d['notes']}")
                for i,b in enumerate(d["items"],1):
                    singular = "Activity" if d["mode"]=="Activities" else "Task"
                    doc.add_paragraph(f"{singular} {i} ({b['time']} min) — {b['title']}")
                    doc.add_paragraph(f"Objective: {b['objective']}")
                    doc.add_paragraph(f"Grouping: {b['grouping']}  |  Materials: {b['materials']}")
                    doc.add_paragraph("Procedure:")
                    for step in b["steps"]:
                        doc.add_paragraph(f" - {step}")
                    doc.add_paragraph("Success criteria: " + ", ".join(b["success"]))
                    doc.add_paragraph(f"Quick check: {b['check']}")
                    doc.add_paragraph("")
                bio=io.BytesIO(); doc.save(bio); bio.seek(0); return bio

            st.download_button(f"⬇️ Export {d['mode']} Plan (DOCX)", data=export_plan_docx(),
                               file_name=f"ADI_{d['mode']}_W{d['week']}_L{d['lesson']}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Chat ----------
st.markdown("### 💬 Conversation")
st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
if prompt := st.chat_input("Ask ADI Builder…"):
    st.session_state["messages"].append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(prompt)
    reply = "Understood. Use Generate for drafts. You can Regenerate a single item or Copy any item, then Export at the bottom."
    st.session_state["messages"].append({"role":"assistant","content":reply})
    with st.chat_message("assistant"): st.markdown(reply)

# ---------- Guards ----------
problems=[]
if run:
    try:
        if ebook_file and getattr(ebook_file,"size",0) > 40*1024*1024: problems.append("eBook exceeds 40MB.")
        if ppt_file and not ppt_file.name.lower().endswith(".pptx"): problems.append("Slides must be .pptx.")
    except Exception:
        pass
if problems: st.warning("\\n".join([f"• {p}" for p in problems]))
