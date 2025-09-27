
import io, re, random, hashlib
from typing import List, Tuple
import pandas as pd
import streamlit as st

# =====================
# Page & Theme
# =====================
st.set_page_config(page_title="ADI Learning Tracker", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{
  --brand:#2c6e49; --brand-2:#3e8b63; --ink:#0d1a14; --muted:#63756b;
  --bg:#f7faf8; --card:#ffffff; --ring:#e6efe9;
}
html, body, .stApp { background: var(--bg); }
.block-container{ padding-top: 1.8rem; padding-bottom: 3rem; }
.hero{ padding:.6rem 0 1.0rem; border-bottom:1px solid var(--ring); position:sticky; top:0; background:var(--bg); z-index:5; }
.hero h1{ margin:0; font-size:2.2rem; font-weight:900; color:var(--ink); letter-spacing:-.2px; }
.hero p{ margin:.1rem 0 0; color:var(--muted); }
.card{ background:var(--card); border:1px solid var(--ring); border-radius:18px;
       padding:1.25rem 1.25rem 1rem; box-shadow:0 12px 30px rgba(23,51,38,.06); margin-bottom:1.1rem; }
.kit{ display:flex; gap:.6rem; flex-wrap:wrap; margin:.35rem 0 .9rem; }
.kit .chip{ background:#f1f6f3; border:1px solid var(--ring); padding:.45rem .75rem; border-radius:1000px;
            font-weight:600; color:#274332; font-size:.92rem; }
div.stButton > button{ width:100%; background:linear-gradient(180deg, var(--brand), var(--brand-2)); color:#fff;
  font-weight:700; border:0; border-radius:14px; padding:.85rem 1rem; box-shadow:0 6px 18px rgba(44,110,73,.25); }
div.stButton > button:hover{ filter:brightness(1.03); }
[data-testid="stDataFrame"] { border:1px solid var(--ring); border-radius:14px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>ADI Learning Tracker</h1><p>Transform lessons into measurable learning</p></div>', unsafe_allow_html=True)

# =====================
# Safe session defaults (no callables)
# =====================
_defaults = {
    "seen_q_sigs_global": set(),
    "mcq_df": pd.DataFrame(),
    "act_df": pd.DataFrame(),
    "lesson": 1, "week": 1, "source_type": "E-book", "focus": "Focus Medium",
    "teacher_seed": "", "src_text": "",
    "bloom_mode": "Auto (by Focus)", "bloom_target": "Understand",
}
for k,v in _defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# =====================
# Constants
# =====================
BLOOMS = ["Remember","Understand","Apply","Analyze","Evaluate","Create"]
MCQ_COLS = ["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]
ACT_COLS = ["Title","Objective","Steps","Materials","Assessment","Duration (mins)","Policy focus"]
ANSWER_LETTERS = ["A","B","C","D"]

# =====================
# Helpers
# =====================
def _strip_noise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()

def _keywords(text: str, top_n: int = 24):
    t = re.sub(r"[^A-Za-z0-9\- ]+", " ", (text or "").lower())
    words = [w for w in t.split() if len(w) >= 3]
    if not words: return []
    from collections import Counter
    uni = Counter(words)
    bi = Counter([" ".join(p) for p in zip(words, words[1:]) if all(len(w)>=3 for w in p)])
    merged = uni | bi
    items = list(merged.items()); items.sort(key=lambda kv: (-kv[1], -len(kv[0])))
    stop = {"the","and","with","from","into","that","this","those","these","for","are","was","were","your","their","its","our"}
    return [k for k,_ in items if k not in stop][:top_n]

def _seed_salt() -> int:
    txt = (st.session_state.get("teacher_seed") or "").strip()
    if not txt: return 0
    h = hashlib.md5(txt.encode("utf-8")).hexdigest()[:8]
    return int(h, 16)

def _quality_gate(options):
    options = [str(o).strip() for o in options]
    if any(not o for o in options): return False
    if len(set(options)) < len(options): return False
    if sum(1 for o in options if len(o.split()) <= 1) >= 2: return False
    return True

def _distractors_for_sentence(sent: str):
    corpus = (st.session_state.get("src_text") or "")
    s = _strip_noise(sent or "")
    if not s: return [], ""
    loc_kws = _keywords(s, top_n=10)
    correct = ""
    for kw in loc_kws:
        if " " in kw and len(kw) >= 8: correct = kw; break
    if not correct: correct = (loc_kws[0] if loc_kws else s.split(".")[0])[:160]
    correct = correct.strip().capitalize()
    glob_kws = _keywords(corpus, top_n=60) if corpus else []
    cset = set(correct.lower().split()); d = []
    for kw in glob_kws:
        if kw == correct.lower(): continue
        if set(kw.split()).intersection(cset): continue
        if kw.strip() and kw.lower() not in {"none","all","above","below"}: d.append(kw.capitalize())
        if len(d) >= 6: break
    while len(d) < 3:
        extra = correct.split(); extra = extra[::-1] if len(extra) > 1 else extra
        cand = " ".join(extra).capitalize() or (correct + " policy").capitalize()
        if cand not in d and cand != correct: d.append(cand)
        else: d.append((correct + " guideline").capitalize())
    return d[:3], correct

def _explain_choice(correct: str, options, topic: str = "") -> str:
    return "Correct because it aligns with the source facts." if not topic else f"Correct because it aligns with {topic}."

BLOOM_STEMS = {
    "Remember": ["Which statement accurately recalls {anchor}?","Identify the definition of {anchor}.","Select the correct term related to {anchor}."],
    "Understand": ["Which claim best explains {anchor}?","Which paraphrase captures the meaning of {anchor}?","What is the main idea regarding {anchor}?"],
    "Apply": ["Which action should be taken regarding {anchor}?","Choose the best procedure to handle {anchor}.","What is the appropriate next step for {anchor}?"],
    "Analyze": ["Which option best distinguishes components of {anchor}?","Which factor is most critical in analyzing {anchor}?","Which relationship explains {anchor}?"],
    "Evaluate": ["Which justification is most defensible for {anchor}?","Which option is the best critique of {anchor}?","Which policy should be prioritized about {anchor}?"],
    "Create": ["Which proposal best designs a solution for {anchor}?","Which combination forms a new approach to {anchor}?","Which plan best synthesizes ideas about {anchor}?"],
}

def _pick_bloom_sequence(rnd: random.Random, count: int) -> list:
    mode = st.session_state.get("bloom_mode","Auto (by Focus)")
    target = st.session_state.get("bloom_target","Understand")
    if mode.startswith("Auto"):
        focus = st.session_state.get("focus","Focus Medium")
        if "Low" in focus: pool, w = ["Remember","Understand","Apply"], [3,3,2]
        elif "High" in focus: pool, w = ["Analyze","Evaluate","Create"], [3,3,2]
        else: pool, w = ["Understand","Apply","Analyze"], [2,3,2]
        return rnd.choices(pool, weights=w, k=count)
    return [target] * count

# =====================
# File reading
# =====================
def _read_upload(file) -> str:
    if not file: return ""
    name = file.name.lower(); data = file.read()
    try:
        if name.endswith(".txt"):
            return data.decode("utf-8", errors="ignore")
        if name.endswith(".docx"):
            try:
                import docx
                doc = docx.Document(io.BytesIO(data))
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception:
                return ""
        if name.endswith(".pptx"):
            try:
                from pptx import Presentation
                prs = Presentation(io.BytesIO(data)); txt = []
                for slide in prs.slides:
                    for shp in slide.shapes:
                        if hasattr(shp, "text"): txt.append(shp.text)
                return "\n".join(txt)
            except Exception:
                return ""
        if name.endswith(".pdf"):
            return ""
    except Exception:
        return ""
    return ""

# =====================
# Generators
# =====================
def generate_mcqs(src: str, lesson: int, week: int, focus: str, source_type: str) -> pd.DataFrame:
    if not src or len(_strip_noise(src)) < 40:
        return pd.DataFrame(columns=MCQ_COLS)
    rnd = random.Random(int(week) * 100 + int(lesson) + (_seed_salt() % 100000))
    sents = re.split(r'(?<=[.!?])\s+', _strip_noise(src))
    sents = [s for s in sents if 25 <= len(s) <= 240] or [src]
    rows = []
    sig_seen = st.session_state.setdefault("seen_q_sigs_global", set())
    kws_global = _keywords(src, top_n=60)
    tiers = ["Low","Medium","High"]
    blooms_seq = _pick_bloom_sequence(rnd, min(12, len(sents)))
    qn = 1
    for s, bloom in zip(sents[:12], blooms_seq):
        anchor = (kws_global[(qn + week + _seed_salt()) % len(kws_global)] if kws_global else s.split()[0].lower())
        distractors, correct = _distractors_for_sentence(s)
        opts = [correct] + distractors; rnd.shuffle(opts)
        if not _quality_gate(opts): continue
        stem = rnd.choice(BLOOM_STEMS.get(bloom, BLOOM_STEMS["Understand"])).format(anchor=anchor)
        tier = rnd.choice(tiers if bloom in ["Understand","Apply"] else (["High"] if bloom in ["Evaluate","Create","Analyze"] else ["Low","Medium"]))
        sig = (bloom, stem.split("?")[0][:100].lower())
        if sig in sig_seen: continue
        sig_seen.add(sig)
        answer_letter = ANSWER_LETTERS[opts.index(correct)] if correct in opts else "A"
        rows.append({
            "Bloom": bloom, "Tier": tier, "Q#": qn, "Question": stem,
            "Option A": opts[0], "Option B": opts[1], "Option C": opts[2], "Option D": opts[3] if len(opts)>3 else "None of the above",
            "Answer": answer_letter, "Explanation": _explain_choice(correct, opts, topic=anchor),
        })
        qn += 1
    return pd.DataFrame(rows, columns=MCQ_COLS) if rows else pd.DataFrame(columns=MCQ_COLS)

def generate_activities(lesson:int, week:int, focus:str) -> pd.DataFrame:
    rnd = random.Random(week*1000 + lesson*7 + (_seed_salt() % 9999))
    focus = (focus or "Focus Medium").split()[-1].capitalize()
    templates = [
        ("Think-Pair-Share","Discuss and refine understanding of the core idea.",15),
        ("Case Study","Analyze a scenario and propose recommendations.",30),
        ("Concept Mapping","Map key concepts and relationships.",20),
        ("Gallery Walk","Create posters then circulate and give feedback.",25),
        ("Peer Review","Critique sample answers using a rubric.",20),
        ("Scenario Cards","Respond to short scenarios and justify choices.",25),
        ("Design Sprint","Prototype a quick solution and demo.",35),
    ]
    rnd.shuffle(templates); rows = []
    for title, obj, dur in templates[:3]:
        steps = [
            "Starter (5m). Activate prior knowledge.",
            f"Main ({max(10, dur-10)}m). Team task focused on {focus}.",
            "Plenary (5m). Share one insight and one question."
        ]
        rows.append({
            "Title":title, "Objective":obj + f" (Lesson {lesson}, Week {week}, focus: {focus}).",
            "Steps":" ".join(steps), "Materials":"Timer; A3 paper; markers; student handout",
            "Assessment":f"Rubric aligned to {focus} (clarity, correctness, application).",
            "Duration (mins)":dur, "Policy focus":focus,
        })
    return pd.DataFrame(rows, columns=ACT_COLS)

# =====================
# Exporters
# =====================
def export_mcqs_gift(df: pd.DataFrame) -> bytes:
    lines = []
    for _, r in df.iterrows():
        stem = _strip_noise(str(r.get("Question","")))
        opts = [str(r.get("Option A","")), str(r.get("Option B","")), str(r.get("Option C","")), str(r.get("Option D",""))]
        ans = str(r.get("Answer","A")).strip().upper()
        correct = {"A":0,"B":1,"C":2,"D":3}.get(ans, 0)
        gift = f"::{_strip_noise(stem)[:50]}:: {stem} {{"
        for i, o in enumerate(opts): gift += (" =" if i==correct else " ~") + o
        gift += " }\n"; lines.append(gift)
    return ("\n".join(lines)).encode("utf-8")

def export_acts_docx(df: pd.DataFrame) -> bytes:
    try:
        import docx
        doc = docx.Document(); doc.add_heading("Activities", level=1)
        for _, r in df.iterrows():
            doc.add_heading(str(r.get("Title","Activity")), level=2)
            doc.add_paragraph(f"Objective: {r.get('Objective','')}")
            doc.add_paragraph(f"Steps: {r.get('Steps','')}")
            doc.add_paragraph(f"Materials: {r.get('Materials','')}")
            doc.add_paragraph(f"Assessment: {r.get('Assessment','')}")
            doc.add_paragraph(f"Duration (mins): {r.get('Duration (mins)', '')}")
            doc.add_paragraph(f"Policy focus: {r.get('Policy focus','')}"); doc.add_paragraph("")
        bio = io.BytesIO(); doc.save(bio); return bio.getvalue()
    except Exception:
        return df.to_csv(index=False).encode("utf-8")

# =====================
# UI
# =====================
# --- Upload ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("① Upload")
up = st.file_uploader("Upload .pptx / .docx / .txt (PDF disabled in this build).", type=["pptx","docx","txt","pdf"])
st.session_state.src_text = _read_upload(up)
st.session_state.src_text = st.text_area("Or paste lesson content below", value=st.session_state.get("src_text",""), height=160, placeholder="Paste lesson text here…")
st.markdown('</div>', unsafe_allow_html=True)

# --- Setup ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("② Setup")
c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.session_state.lesson = st.number_input("Lesson", 1, 30, int(st.session_state.get("lesson",1)), 1)
with c2: st.session_state.week   = st.number_input("Week",   1, 52, int(st.session_state.get("week",1)), 1)
with c3: st.session_state.source_type = st.radio("Source", ["PPT","E-book","Lesson plan"], horizontal=True, index=(["PPT","E-book","Lesson plan"].index(st.session_state.get("source_type","E-book"))))
with c4: st.session_state.focus = st.radio("Focus", ["Focus Low","Focus Medium","Focus High"], horizontal=True, index=(["Focus Low","Focus Medium","Focus High"].index(st.session_state.get("focus","Focus Medium"))))
with c5: st.session_state.teacher_seed = st.text_input("Teacher ID (variation seed)", value=st.session_state.get("teacher_seed",""), placeholder="e.g., t.johnson@adi or class code")
st.caption(f"Context: Lesson {st.session_state.lesson} • Week {st.session_state.week} • {st.session_state.source_type}")

st.markdown("**Bloom’s taxonomy**")
b1,b2 = st.columns([2,2])
with b1: st.session_state.bloom_mode = st.radio("Mode", ["Auto (by Focus)","Target level"], horizontal=True, key="bmode")
with b2: st.session_state.bloom_target = st.selectbox("Target level", BLOOMS, index=BLOOMS.index(st.session_state.get("bloom_target","Understand")), disabled=st.session_state.bloom_mode.startswith("Auto"))
st.button("Reset MCQ uniqueness memory", on_click=lambda: st.session_state.setdefault("seen_q_sigs_global", set()).clear(), help="Clears the global duplicate blocklist for this session.")
st.markdown('</div>', unsafe_allow_html=True)

# --- Generate ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("③ Generate")
st.markdown('<div class="kit"><span class="chip">Lesson ' + str(st.session_state.lesson) + '</span><span class="chip">Week ' + str(st.session_state.week) + '</span><span class="chip">' + str(st.session_state.source_type) + '</span><span class="chip">' + str(st.session_state.focus) + '</span><span class="chip">Bloom: ' + (st.session_state.bloom_target if st.session_state.bloom_mode!="Auto (by Focus)" else "Auto") + '</span></div>', unsafe_allow_html=True)

cA, cB = st.columns(2)
with cA:
    if st.button("📝 Generate MCQs"):
        try:
            st.session_state.mcq_df = generate_mcqs(st.session_state.get("src_text",""),
                                                    int(st.session_state.get("lesson",1)),
                                                    int(st.session_state.get("week",1)),
                                                    st.session_state.get("focus","Focus Medium"),
                                                    st.session_state.get("source_type","E-book"))
            if len(st.session_state.mcq_df)==0: st.warning("No MCQs generated — add more text in ① Upload.")
        except Exception as e:
            st.error(f"Couldn't generate MCQs: {e}")
with cB:
    if st.button("🧩 Generate Activities"):
        try:
            st.session_state.act_df = generate_activities(int(st.session_state.get("lesson",1)),
                                                          int(st.session_state.get("week",1)),
                                                          st.session_state.get("focus","Focus Medium"))
        except Exception as e:
            st.error(f"Couldn't generate Activities: {e}")

st.markdown("#### MCQs Preview")
if isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df) > 0:
    st.dataframe(st.session_state.mcq_df, use_container_width=True)
else:
    st.info("No MCQs to show yet — click **Generate MCQs** above.")

st.markdown("#### Activities Preview")
if isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df) > 0:
    st.dataframe(st.session_state.act_df, use_container_width=True)
else:
    st.info("No Activities to show yet — click **Generate Activities** above.")

# --- Quick Editor (inline)
with st.expander("✏️ Quick Editor (MCQs & Activities)", expanded=False):
    mode = st.radio("Edit", ["MCQs","Activities"], horizontal=True, key="inline_mode")
    if mode=="MCQs" and isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df)>0:
        df = st.session_state.mcq_df
        c1,c2 = st.columns([1,3])
        with c1:
            row = st.number_input("Row", 0, len(df)-1, 0, 1)
            if st.button("🧬 Duplicate", key="mcq_dup"):
                st.session_state.mcq_df = pd.concat([df.iloc[:row+1], df.iloc[row:row+1], df.iloc[row+1:]], ignore_index=True); st.toast("Duplicated")
            if st.button("🗑 Delete", key="mcq_del") and len(df)>1:
                st.session_state.mcq_df = df.drop(index=row).reset_index(drop=True); st.toast("Deleted")
        with c2:
            qtxt = st.text_area("Question", str(df.loc[row,"Question"]), height=120)
            colA,colB = st.columns(2)
            with colA:
                oa = st.text_area("Option A", str(df.loc[row,"Option A"]), height=70)
                oc = st.text_area("Option C", str(df.loc[row,"Option C"]), height=70)
            with colB:
                ob = st.text_area("Option B", str(df.loc[row,"Option B"]), height=70)
                od = st.text_area("Option D", str(df.loc[row,"Option D"]), height=70)
            ans = st.selectbox("Answer", ANSWER_LETTERS, index=ANSWER_LETTERS.index(str(df.loc[row,"Answer"])) if str(df.loc[row,"Answer"]) in ANSWER_LETTERS else 0)
            expl = st.text_area("Explanation", str(df.loc[row,"Explanation"]), height=90)
            if st.button("Apply changes", key="mcq_apply"):
                df.loc[row, ["Question","Option A","Option B","Option C","Option D","Answer","Explanation"]] = [qtxt, oa, ob, oc, od, ans, expl]
                st.session_state.mcq_df = df; st.toast("Applied MCQ changes")

    if mode=="Activities" and isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df)>0:
        df = st.session_state.act_df
        c1,c2 = st.columns([1,3])
        with c1:
            row = st.number_input("Row ", 0, len(df)-1, 0, 1)
            if st.button("🧬 Duplicate", key="act_dup"):
                st.session_state.act_df = pd.concat([df.iloc[:row+1], df.iloc[row:row+1], df.iloc[row+1:]], ignore_index=True); st.toast("Duplicated")
            if st.button("🗑 Delete", key="act_del") and len(df)>1:
                st.session_state.act_df = df.drop(index=row).reset_index(drop=True); st.toast("Deleted")
        with c2:
            title = st.text_input("Title", str(df.loc[row,"Title"]))
            objective = st.text_area("Objective", str(df.loc[row,"Objective"]), height=90)
            steps = st.text_area("Steps", str(df.loc[row,"Steps"]), height=140)
            materials = st.text_area("Materials", str(df.loc[row,"Materials"]), height=80)
            assessment = st.text_area("Assessment", str(df.loc[row,"Assessment"]), height=100)
            duration = st.number_input("Duration (mins)", int(df.loc[row,"Duration (mins)"]), step=5)
            focus_txt = st.text_input("Policy focus", str(df.loc[row,"Policy focus"]))
            if st.button("Apply changes", key="act_apply"):
                df.loc[row, ["Title","Objective","Steps","Materials","Assessment","Duration (mins)","Policy focus"]] = [title,objective,steps,materials,assessment,int(duration),focus_txt]
                st.session_state.act_df = df; st.toast("Applied Activity changes")

st.markdown('</div>', unsafe_allow_html=True)

# --- Export ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("④ Export")
c1, c2, c3 = st.columns(3)
if isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df) > 0:
    with c1:
        st.download_button("Download MCQs (CSV)", st.session_state.mcq_df.to_csv(index=False).encode("utf-8"),
                           file_name="mcqs.csv", mime="text/csv", use_container_width=True)
    with c2:
        st.download_button("Download MCQs (GIFT)", export_mcqs_gift(st.session_state.mcq_df),
                           file_name="mcqs_gift.txt", mime="text/plain", use_container_width=True)
else:
    st.info("No MCQs to export yet.")
if isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df) > 0:
    data = export_acts_docx(st.session_state.act_df)
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if data[:2] != b"Ti" else "text/csv"
    st.download_button("Download Activities (DOCX/CSV)", data, file_name="activities.docx",
                       mime=mime, use_container_width=True)
else:
    st.info("No Activities to export yet.")
st.markdown('</div>', unsafe_allow_html=True)

