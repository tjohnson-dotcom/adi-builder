# ADI Builder — single-file Streamlit app (Render-ready)
# Features: Policy pills, varied-answer MCQs, Activities generator, DOCX & GIFT export

import io, re, random, datetime as dt
from typing import List
import pandas as pd
import streamlit as st

# ------------------- Page config & simple ADI look -------------------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
BG_STONE  = "#f7f6f3"

st.set_page_config(page_title="ADI Builder", page_icon="✅", layout="wide")
st.markdown(f"""
<style>
  .main {{ background: {BG_STONE}; }}
  .adi-topbar {{ height: 6px; background: linear-gradient(90deg,{ADI_GREEN},{ADI_GOLD}); margin: -1rem -1rem 1rem -1rem; }}
  .box {{ background:white; border-radius:16px; padding:1rem; box-shadow:0 2px 10px #00000014; }}
  .muted {{ color:#666; }}
</style>
<div class="adi-topbar"></div>
""", unsafe_allow_html=True)

# ------------------- Helpers -------------------
BLOOM_LEVELS = ["Remember","Understand","Apply","Analyze","Evaluate","Create"]
BLOOM_TIER   = {"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}
DEFAULT_VERBS = {
    "Remember":  ["list","define","recall","identify"],
    "Understand":["explain","classify","summarize","illustrate"],
    "Apply":     ["use","implement","solve","demonstrate"],
    "Analyze":   ["compare","differentiate","categorize","analyze"],
    "Evaluate":  ["justify","critique","prioritize","defend"],
    "Create":    ["design","compose","propose","develop"],
}

def policy_for_week(week:int)->str:
    if 1 <= week <= 4:  return "Low"
    if 5 <= week <= 9:  return "Medium"
    return "High"

def safe_sentences(text:str, default:str)->List[str]:
    # Robust against copy/paste quote/ellipsis issues
    items = [s.strip() for s in re.split(r"[.\n]+", text or "") if s.strip()]
    return items or [default]

# ------------------- Activities (offline) -------------------
def offline_activities(verbs:List[str], level:str, count:int, duration_min:int, difficulty:str, week:int)->List[str]:
    BLOOM_HINTS = {
        "Remember":"recall key facts",
        "Understand":"explain ideas in your own words",
        "Apply":"use the concept in a new example",
        "Analyze":"compare parts and relationships",
        "Evaluate":"justify a position with criteria",
        "Create":"design or propose a new solution",
    }
    tier = BLOOM_TIER.get(level,"Low")
    hint = BLOOM_HINTS.get(level,"apply the concept")
    verbs = verbs or ["explain","classify","describe","analyze"]
    vseq  = (verbs * ((count // max(1,len(verbs))) + 1))[:count]

    items=[]
    for i, v in enumerate(vseq, start=1):
        v_cap = v.capitalize()
        line  = f"{i}. {v_cap} — In teams, {hint}. Produce a {duration_min}-minute output (difficulty: {difficulty}, ADI: {tier}, week {week})."
        if level in ("Analyze","Evaluate","Create"):
            line += " Include evidence from the text and one counterexample."
        else:
            line += " Include at least 3 key points."
        items.append(line)
    return items

# ------------------- MCQs (varied correct letters) -------------------
def offline_mcqs_varied(src_text:str, blooms:List[str], verbs:List[str], n:int, lesson:int, week:int)->pd.DataFrame:
    topics = safe_sentences(src_text, "This unit covers core concepts and applied practice.")
    verbs  = verbs or ["identify"]
    vseq   = (verbs * ((n // max(1,len(verbs))) + 1))[:n]
    rows=[]
    for i in range(n):
        bloom = blooms[i % len(blooms)] if blooms else "Understand"
        tier  = BLOOM_TIER.get(bloom,"Low")
        fact  = topics[i % len(topics)]
        verb  = vseq[i].capitalize()
        stem  = f"{verb} the MOST appropriate statement about: {fact}"

        option_texts = [
            f"A correct point about {fact}.",               # correct base
            f"An incorrect detail about {fact}.",
            f"Another incorrect detail about {fact}.",
            f"A distractor unrelated to {fact}.",
        ]
        # deterministic placement per lesson/week/question
        rng = random.Random(hash((int(lesson), int(week), i+1)))
        correct_idx = rng.randrange(4)
        if correct_idx != 0:
            correct = option_texts[0]
            others  = option_texts[1:]
            order = [None,None,None,None]
            order[correct_idx] = correct
            k=0
            for j in range(4):
                if order[j] is None:
                    order[j]=others[k]; k+=1
            option_texts = order
        A,B,C,D = option_texts
        answer = "ABCD"[correct_idx]

        rows.append({
            "Bloom": bloom, "Tier": tier, "Q#": i+1, "Question": stem,
            "Option A": A, "Option B": B, "Option C": C, "Option D": D,
            "Answer": answer, "Explanation": f"Verb focus: {verb} · Tier: {tier}"
        })
    cols = ["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]
    return pd.DataFrame(rows, columns=cols)

# ------------------- Exports -------------------
def _docx(paragraphs:List[str], title:str)->bytes|None:
    try:
        from docx import Document
        from docx.shared import Pt
    except Exception:
        return None
    doc = Document()
    style = doc.styles["Normal"]; style.font.name = "Calibri"; style.font.size = Pt(11)
    doc.add_heading(title, level=1)
    for p in paragraphs: doc.add_paragraph(p)
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def mcq_paper_and_key_lines(df:pd.DataFrame):
    paper, key = [], ["Answer Key"]
    if df is None or df.empty: return paper, key
    for _, r in df.iterrows():
        i = int(r["Q#"])
        paper.append(f"{i}. {r['Question']}")
        paper.append(f"   A) {r['Option A']}")
        paper.append(f"   B) {r['Option B']}")
        paper.append(f"   C) {r['Option C']}")
        paper.append(f"   D) {r['Option D']}")
        paper.append("")
        key.append(f"{i}. {r['Answer']}")
    return paper, key

def build_gift(df:pd.DataFrame)->str:
    if df is None or df.empty: return ""
    lines=[]
    for _, r in df.iterrows():
        opts = [("A", r["Option A"]), ("B", r["Option B"]), ("C", r["Option C"]), ("D", r["Option D"])]
        parts=[]
        for letter, text in opts:
            parts.append(("=" if letter==r["Answer"] else "~") + str(text))
        lines.append(f"::{int(r['Q#'])}:: {r['Question']} {{ {' '.join(parts)} }}")
    return "\n\n".join(lines)

# ------------------- State init -------------------
for k,v in {
    "lesson":1, "week":1, "level":"Understand", "verbs":[], "num_mcqs":10,
    "activities_per_class":2, "duration":20, "difficulty":"Medium",
    "src_text":""
}.items():
    st.session_state.setdefault(k, v)

# ------------------- UI -------------------
left, right = st.columns([1.05, 1.4])

with left:
    st.markdown("### ADI Builder")
    st.caption("Clean ADI look · Policy pills · Verb picker · Exports")

    st.write("**Lesson**")
    st.session_state.lesson = st.radio("Lesson", [1,2,3,4,5], index=0, horizontal=True, label_visibility="collapsed")
    st.write("**Week**")
    st.session_state.week = st.radio("Week", list(range(1,15)), index=0, horizontal=True, label_visibility="collapsed")

    policy = policy_for_week(int(st.session_state.week))
    st.markdown(f"**ADI Policy focus:** :green[{policy}]")

    suggested = "Understand" if policy=="Low" else ("Analyze" if policy=="Medium" else "Create")
    st.session_state.level = st.select_slider("Bloom Level", options=BLOOM_LEVELS, value=st.session_state.get("level", suggested))
    st.caption(f"Tip: week → policy **{policy}**; suggested level ~ **{suggested}**")

    verbs_default = DEFAULT_VERBS.get(st.session_state.level, [])
    st.session_state.verbs = st.multiselect("Verb picker", options=sorted(set(sum(DEFAULT_VERBS.values(), []))),
                                            default=verbs_default, key="verbs")

    st.markdown("---")
    st.session_state.num_mcqs = st.number_input("How many MCQs?", 1, 50, value=st.session_state.num_mcqs)
    st.session_state.activities_per_class = st.number_input("Activities per class", 1, 10, value=st.session_state.activities_per_class)
    st.session_state.duration = st.number_input("Activity duration (minutes)", 5, 120, value=st.session_state.duration)
    st.session_state.difficulty = st.selectbox("Difficulty", ["Low","Medium","High"], index=["Low","Medium","High"].index(st.session_state.difficulty))

    st.markdown("**Source text (optional)**")
    st.session_state.src_text = st.text_area("Paste lesson/topic text (improves MCQs/Activities)", height=130, label_visibility="collapsed")

    if st.button("⚡ Auto-fill MCQs", use_container_width=True):
        blooms = [st.session_state.level] * int(st.session_state.num_mcqs)
        st.session_state.mcq_df = offline_mcqs_varied(
            st.session_state.src_text, blooms, st.session_state.verbs,
            int(st.session_state.num_mcqs), int(st.session_state.lesson), int(st.session_state.week)
        )
        st.success(f"Generated {len(st.session_state.mcq_df)} MCQs with varied correct letters.")

    if st.button("🧩 Generate Activities", use_container_width=True):
        acts = offline_activities(
            st.session_state.verbs, st.session_state.level,
            int(st.session_state.activities_per_class), int(st.session_state.duration),
            st.session_state.difficulty, int(st.session_state.week)
        )
        st.session_state.activities = acts
        st.session_state.acts_textarea = "\n".join(acts)
        st.success(f"Generated {len(acts)} activities.")

with right:
    st.markdown("#### MCQs (editable)")
    df = st.session_state.get("mcq_df")
    if df is None or df.empty:
        st.info("Click **Auto-fill MCQs** to generate sample questions.")
    else:
        st.session_state.mcq_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="mcq_editor")

    st.markdown("---")
    st.markdown("#### Activities (editable)")
    st.session_state.acts_textarea = st.text_area("One per line", value=st.session_state.get("acts_textarea",""), height=160)

# ------------------- Export -------------------
st.markdown("---")
st.markdown("### Export")

def _text_bytes(lines:List[str])->bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")

df = st.session_state.get("mcq_df")
acts = st.session_state.get("activities") or [l for l in st.session_state.get("acts_textarea","").splitlines() if l.strip()]
lesson, week = int(st.session_state.lesson), int(st.session_state.week)
date_str = dt.date.today().strftime("%Y-%m-%d")
base = f"ADI_Lesson{lesson}_Week{week}_{date_str}"

c1, c2, c3, c4 = st.columns(4)

with c1:
    if acts:
        data = _docx(acts, "Activity Sheet") or _text_bytes(acts)
        st.download_button("⬇️ Activity Sheet (.docx)", data=data,
                           file_name=f"{base}_ActivitySheet.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.button("⬇️ Activity Sheet (.docx)", disabled=True)

with c2:
    if df is not None and not df.empty:
        paper, _ = mcq_paper_and_key_lines(df)
        data = _docx(paper, "MCQ Paper") or _text_bytes(paper)
        st.download_button("⬇️ MCQ Paper (.docx)", data=data,
                           file_name=f"{base}_MCQPaper.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.button("⬇️ MCQ Paper (.docx)", disabled=True)

with c3:
    if df is not None and not df.empty:
        _, key = mcq_paper_and_key_lines(df)
        data = _docx(key, "Answer Key") or _text_bytes(key)
        st.download_button("⬇️ Answer Key (.docx)", data=data,
                           file_name=f"{base}_AnswerKey.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.button("⬇️ Answer Key (.docx)", disabled=True)

with c4:
    if df is not None and not df.empty:
        gift = build_gift(df).encode("utf-8")
        st.download_button("⬇️ Moodle GIFT (.gift)", data=gift,
                           file_name=f"{base}.gift", mime="text/plain")
    else:
        st.button("⬇️ Moodle GIFT (.gift)", disabled=True)
