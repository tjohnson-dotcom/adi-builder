
# ADI Builder — Lesson Activities & Questions (Render-safe, single file)
# UI: Sidebar upload + Week/Lesson → Tabs: Knowledge MCQs / Skills Activities / Revision
# Notes:
# - No layout changes beyond the screenshot flow
# - Upload toast + "File ready" banner
# - Deterministic MCQs with varied answer letters
# - Optional per-teacher variant and mixed stems via environment variables (no UI)
#     ADI_VARIANT=TEACHER_A     → different-but-reproducible sets per teacher
#     ADI_ENABLE_MIX=1          → balanced stem styles (keeps OFF by default)
#
# Start on Render:
#   Build Command: pip install -r requirements.txt
#   Start Command: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0

import io, os, re, random, hashlib, datetime as dt
import streamlit as st

# ---------- Page ----------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="✅", layout="wide")

# ---------- Backend feature switches (no new UI) ----------
ADI_ENABLE_MIX = os.environ.get("ADI_ENABLE_MIX", "0") == "1"   # default OFF
ADI_VARIANT    = os.environ.get("ADI_VARIANT", "").strip()      # optional per-teacher code

# ---------- Helpers ----------
BLOOM_LEVELS = ["Remember","Understand","Apply","Analyze","Evaluate","Create"]
BLOOM_TIER   = {"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}
DEFAULT_VERBS = {
    "Remember":["list","define","recall","identify"],
    "Understand":["explain","classify","summarize","illustrate"],
    "Apply":["use","implement","solve","demonstrate"],
    "Analyze":["compare","differentiate","categorize","analyze"],
    "Evaluate":["justify","critique","prioritize","defend"],
    "Create":["design","compose","propose","develop"],
}

def policy_caption(week:int)->str:
    if 1 <= week <= 3: return "Policy: Low · Weeks 1–3"
    if 4 <= week <= 8: return "Policy: Medium · Weeks 4–8"
    return "Policy: High · Weeks 9–14"

def safe_sentences(text:str, default:str):
    items=[s.strip() for s in re.split(r"[.\n]+", text or "") if s.strip()]
    return items or [default]

def _rng_for(lesson:int, week:int, q_index:int, regen_token:int, variant:str)->random.Random:
    """Deterministic RNG per (lesson, week, question, regen_token, variant)."""
    base = f"{lesson}|{week}|{q_index}|{regen_token}|{(variant or '').upper()}"
    seed = int(hashlib.sha256(base.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)

# Optional balanced stems (enabled only by ADI_ENABLE_MIX)
_MIX_TEMPLATES = [
    lambda t: f"Which statement best defines **{t}**?",
    lambda t: f"Which option correctly identifies **{t}**?",
    lambda t: f"Which option best applies **{t}** to a real case?",
    lambda t: f"Which option best analyzes **{t}** (evidence vs. trade-offs)?",
    lambda t: f"Which option best evaluates **{t}** using clear criteria?",
    lambda t: f"Which option proposes a sound design using **{t}**?",
]
def _mixed_stem_for(topic:str, rng:random.Random)->str:
    return _MIX_TEMPLATES[rng.randrange(len(_MIX_TEMPLATES))](topic)

# ---------- Activities ----------
def build_activities(verbs, level, count, duration_min, difficulty, week):
    hints = {
        "Remember":"recall key facts",
        "Understand":"explain ideas in your own words",
        "Apply":"use the concept in a new example",
        "Analyze":"compare parts and relationships",
        "Evaluate":"justify a position with criteria",
        "Create":"design or propose a new solution",
    }
    tier=BLOOM_TIER.get(level,"Low")
    hint=hints.get(level,"apply the concept")
    verbs = verbs or ["explain","classify","describe","analyze"]
    vseq  = (verbs * ((count // max(1,len(verbs))) + 1))[:count]
    out=[]
    for i,v in enumerate(vseq, start=1):
        line=f"{i}. {v.capitalize()} — In teams, {hint}. Produce a {duration_min}-minute output (difficulty: {difficulty}, ADI: {tier}, week {week})."
        if level in ("Analyze","Evaluate","Create"):
            line += " Include evidence from the text and one counterexample."
        else:
            line += " Include at least 3 key points."
        out.append(line)
    return out

# ---------- MCQs ----------
def build_mcqs(src_text, bloom, verbs, n, lesson, week, regen_token:int):
    topics=safe_sentences(src_text, "this topic")
    verbs = verbs or ["identify"]
    vseq  = (verbs * ((n // max(1,len(verbs))) + 1))[:n]
    rows=[]
    for i in range(n):
        fact  = topics[i%len(topics)]
        tier  = BLOOM_TIER.get(bloom,"Low")

        rng = _rng_for(int(lesson), int(week), i+1, int(regen_token), ADI_VARIANT)
        stem = _mixed_stem_for(fact, rng) if ADI_ENABLE_MIX else f"Which option best demonstrates **{fact}**?"

        correct = f"A correct point about {fact}."
        distractors = [
            f"A misconception about {fact}.",
            f"An incomplete or vague description of {fact}.",
            f"A distractor unrelated to {fact}.",
        ]

        correct_idx = rng.randrange(4)
        opts=[None]*4; opts[correct_idx]=correct; k=0
        for j in range(4):
            if opts[j] is None:
                opts[j]=distractors[k]; k+=1
        A,B,C,D=opts
        rows.append({
            "Q#":i+1, "Bloom":bloom, "Tier":tier, "Question":stem,
            "Option A":A, "Option B":B, "Option C":C, "Option D":D,
            "Answer":"ABCD"[correct_idx], "Explanation":f"Verb focus: {vseq[i].capitalize()} · Tier: {tier}"
        })
    return rows

# ---------- Exports ----------
def _docx(paragraphs, title):
    try:
        from docx import Document
        from docx.shared import Pt
    except Exception:
        return None
    doc=Document(); style=doc.styles["Normal"]; style.font.name="Calibri"; style.font.size=Pt(11)
    doc.add_heading(title, level=1)
    for p in paragraphs: doc.add_paragraph(p)
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def mcq_paper_and_key_lines(mcqs):
    paper=[]; key=["Answer Key"]
    for r in mcqs:
        i=r["Q#"]
        paper += [f"{i}. {r['Question']}",
                  f"   A) {r['Option A']}",
                  f"   B) {r['Option B']}",
                  f"   C) {r['Option C']}",
                  f"   D) {r['Option D']}", ""]
        key.append(f"{i}. {r['Answer']}")
    return paper, key

def build_gift(mcqs)->str:
    lines=[]
    for r in mcqs:
        parts=[("=" if L==r["Answer"] else "~")+r[f"Option {L}"] for L in "ABCD"]
        lines.append(f"::{int(r['Q#'])}:: {r['Question']} {{ {' '.join(parts)} }}")
    return "\n\n".join(lines)

# ---------- State ----------
defaults = dict(
    lesson=1, week=1, level="Understand",
    verbs=[], num_mcqs=10, activities_per_class=1, duration=45,
    difficulty="Medium", src_text="", mcqs=[], acts_textarea="",
    activities=[], __regen_token_mcq=0
)
for k,v in defaults.items(): st.session_state.setdefault(k,v)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Upload PDF / DOCX / PPTX")
    uploaded = st.file_uploader("Drag and drop file here", type=["pdf","docx","pptx"], key="uploader")
    if uploaded:
        if st.session_state.get("_last_upload") != uploaded.name:
            st.session_state["_last_upload"] = uploaded.name
            st.toast(f"Uploaded **{uploaded.name}** ({uploaded.size/1024:.1f} KB)", icon="✅")
        st.success(f"File ready: **{uploaded.name}**")

    st.write("Week")
    st.session_state["week"] = st.selectbox("Week", list(range(1,15)), index=st.session_state["week"]-1)
    st.write("Lesson")
    st.session_state["lesson"] = st.selectbox("Lesson", list(range(1,21)), index=st.session_state["lesson"]-1)
    st.caption(policy_caption(int(st.session_state["week"])))

# ---------- Header ----------
st.markdown("### ADI Builder — Lesson Activities & Questions")
st.caption("Professional, branded, editable and export-ready.")
st.markdown("Weeks **1–3** · Weeks **4–8** · Weeks **9–14**")

# ---------- Tabs ----------
tab_mcq, tab_act, tab_rev = st.tabs(["🧠 Knowledge MCQs", "🛠️ Skills Activities", "🔁 Revision"])

# === MCQ TAB ===
with tab_mcq:
    left, right = st.columns([1.05,1.4])
    with left:
        st.session_state["level"] = st.select_slider("Bloom Level", options=BLOOM_LEVELS, value=st.session_state["level"])
        verbs_default = DEFAULT_VERBS.get(st.session_state["level"], [])
        st.session_state["verbs"] = st.multiselect("Verb picker",
            options=sorted(set(sum(DEFAULT_VERBS.values(), []))),
            default=verbs_default, key="verbs_mcq")

        st.session_state["num_mcqs"] = st.number_input("How many MCQs?", 1, 50, int(st.session_state["num_mcqs"]))

        st.markdown("**Source text (optional)**")
        st.session_state["src_text"] = st.text_area("Paste lesson/topic text (improves MCQs)",
            value=st.session_state.get("src_text",""), height=130, label_visibility="collapsed")

        colg, colr = st.columns(2)
        if colg.button("⚡ Auto-fill MCQs", use_container_width=True):
            st.session_state["__regen_token_mcq"] += 1
            st.session_state["mcqs"] = build_mcqs(
                st.session_state["src_text"], st.session_state["level"],
                st.session_state["verbs"], int(st.session_state["num_mcqs"]),
                int(st.session_state["lesson"]), int(st.session_state["week"]),
                st.session_state["__regen_token_mcq"]
            )
            st.success(f"Generated {len(st.session_state['mcqs'])} MCQs.")
        if colr.button("🔁 Regenerate", use_container_width=True):
            st.session_state["__regen_token_mcq"] += 1
            st.session_state["mcqs"] = build_mcqs(
                st.session_state["src_text"], st.session_state["level"],
                st.session_state["verbs"], int(st.session_state["num_mcqs"]),
                int(st.session_state["lesson"]), int(st.session_state["week"]),
                st.session_state["__regen_token_mcq"]
            )
            st.info("MCQs regenerated.")

    with right:
        st.markdown("#### MCQs (editable)")
        if st.session_state["mcqs"]:
            edited = st.data_editor(st.session_state["mcqs"], num_rows="dynamic", use_container_width=True, key="mcq_editor")
            st.session_state["mcqs"] = edited
        else:
            st.info("Click **Auto-fill MCQs** to generate sample questions.")

    st.markdown("---")
    c1,c2,c3 = st.columns(3)
    df = st.session_state.get("mcqs", [])
    base = f"ADI_Lesson{int(st.session_state['lesson'])}_Week{int(st.session_state['week'])}_{dt.date.today().strftime('%Y-%m-%d')}"
    with c1:
        if df:
            paper,_ = mcq_paper_and_key_lines(df)
            data = _docx(paper, "MCQ Paper") or ("\n".join(paper)+"\n").encode("utf-8")
            st.download_button("⬇️ MCQ Paper (.docx)", data=data, file_name=f"{base}_MCQPaper.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.button("⬇️ MCQ Paper (.docx)", disabled=True)
    with c2:
        if df:
            _,key = mcq_paper_and_key_lines(df)
            data = _docx(key, "Answer Key") or ("\n".join(key)+"\n").encode("utf-8")
            st.download_button("⬇️ Answer Key (.docx)", data=data, file_name=f"{base}_AnswerKey.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.button("⬇️ Answer Key (.docx)", disabled=True)
    with c3:
        if df:
            gift = build_gift(df).encode("utf-8")
            st.download_button("⬇️ Moodle GIFT (.gift)", data=gift, file_name=f"{base}.gift", mime="text/plain")
        else:
            st.button("⬇️ Moodle GIFT (.gift)", disabled=True)

# === ACTIVITIES TAB ===
with tab_act:
    left, right = st.columns([1.05,1.4])
    with left:
        st.write("Activities")
        st.session_state["activities_per_class"] = st.number_input("", 1, 10, int(st.session_state["activities_per_class"]), key="acts_count")
        st.write("Duration per activity (mins)")
        st.session_state["duration"] = st.number_input(" ", 5, 120, int(st.session_state["duration"]), step=5, key="acts_duration")
        st.write("Preferred action verbs")
        st.session_state["verbs"] = st.multiselect("Pick verbs",
            options=sorted(set(sum(DEFAULT_VERBS.values(), []))),
            default=["apply","demonstrate","evaluate","design"], key="verbs_acts")
        cA,cB = st.columns(2)
        if cA.button("✅ Generate Activities", use_container_width=True):
            acts = build_activities(
                st.session_state["verbs"], st.session_state["level"],
                int(st.session_state["activities_per_class"]), int(st.session_state["duration"]),
                "Medium", int(st.session_state["week"])
            )
            st.session_state["activities"] = acts
            st.session_state["acts_textarea"] = "\n".join(acts)
            st.success(f"Generated {len(acts)} activities.")
        if cB.button("🔁 Regenerate Activities", use_container_width=True):
            acts = build_activities(
                st.session_state["verbs"], st.session_state["level"],
                int(st.session_state["activities_per_class"]), int(st.session_state["duration"]),
                "Medium", int(st.session_state["week"])
            )
            st.session_state["activities"] = acts
            st.session_state["acts_textarea"] = "\n".join(acts)
            st.info("Activities regenerated.")
    with right:
        st.markdown("#### Activities (editable)")
        st.session_state["acts_textarea"] = st.text_area("",
            value=st.session_state.get("acts_textarea",""), height=140, key="acts_editor")

    st.markdown("---")
    acts = st.session_state.get("activities") or [l for l in st.session_state.get("acts_textarea","").splitlines() if l.strip()]
    baseA = f"ADI_Lesson{int(st.session_state['lesson'])}_Week{int(st.session_state['week'])}_{dt.date.today().strftime('%Y-%m-%d')}"
    if acts:
        data = _docx(acts, "Activity Sheet") or ("\n".join(acts)+"\n").encode("utf-8")
        st.download_button("⬇️ Download Activities (.docx)", data=data, file_name=f"{baseA}_Activities.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.button("⬇️ Download Activities (.docx)", disabled=True)

# === REVISION TAB ===
with tab_rev:
    st.info("Use Knowledge MCQs for questions or Skills Activities to generate activities. This tab is reserved for future revision templates.")
