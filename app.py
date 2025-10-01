# ADI Builder — Stable Single-File App
# Includes: upload confirmation, mixture-mode MCQs, variant codes, activities, DOCX & GIFT exports.

import io, re, random, hashlib, secrets, datetime as dt
import streamlit as st

# ------------- Page config & style -------------
st.set_page_config(page_title="ADI Builder", page_icon="✅", layout="wide")
ADI_GREEN = "#245a34"; ADI_GOLD = "#C8A85A"; BG_STONE="#f7f6f3"
st.markdown(f"""
<style>
  .main {{ background: {BG_STONE}; }}
  .adi-topbar {{ height: 6px; background: linear-gradient(90deg,{ADI_GREEN},{ADI_GOLD}); margin: -1rem -1rem 1rem -1rem; }}
  .box {{ background:white; border-radius:16px; padding:1rem; box-shadow:0 2px 10px #00000014; }}
  .stMultiSelect [data-baseweb="tag"] span {{ font-weight: 600; }}
</style>
<div class="adi-topbar"></div>
""", unsafe_allow_html=True)

# ------------- Helpers & defaults -------------
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

def policy_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

def safe_sentences(text:str, default:str):
    # Split text into simple sentence-ish chunks; fall back to default when empty
    items=[s.strip() for s in re.split(r"[.\n]+", text or "") if s.strip()]
    return items or [default]

# ---------- Activities (offline, deterministic) ----------
def offline_activities(verbs, level, count, duration_min, difficulty, week):
    H = {
        "Remember":"recall key facts",
        "Understand":"explain ideas in your own words",
        "Apply":"use the concept in a new example",
        "Analyze":"compare parts and relationships",
        "Evaluate":"justify a position with criteria",
        "Create":"design or propose a new solution",
    }
    tier=BLOOM_TIER.get(level,"Low"); hint=H.get(level,"apply the concept")
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

# ---------- MCQs (varied answers + mixture-mode stems) ----------
MIX_TEMPLATES = {
    "define":   lambda t: f"Which statement best defines **{t}**?",
    "identify": lambda t: f"Which option correctly identifies **{t}**?",
    "apply":    lambda t: f"Which option best applies **{t}** to a real case?",
    "analyze":  lambda t: f"Which option best analyzes **{t}** (evidence vs. trade-offs)?",
    "evaluate": lambda t: f"Which option best evaluates **{t}** using clear criteria?",
    "create":   lambda t: f"Which option proposes a sound design using **{t}**?",
}
def choose_mix(n: int):
    base = ["define","identify","apply","apply","analyze","evaluate","create"]
    return (base * ((n//len(base))+2))[:n]

def rng_for(lesson:int, week:int, i:int, variant:str):
    base = f"{lesson}|{week}|{variant}|{i}"
    seed = int(hashlib.sha256(base.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)

def offline_mcqs_varied(src_text, blooms, verbs, n, lesson, week, mix_mode:bool, variant:str):
    topics=safe_sentences(src_text, "this topic")
    verbs = verbs or ["identify"]
    vseq  = (verbs * ((n // max(1,len(verbs))) + 1))[:n]
    mix_order = choose_mix(n) if mix_mode else None

    rows=[]
    for i in range(n):
        bloom = blooms[i%len(blooms)] if blooms else "Understand"
        tier  = BLOOM_TIER.get(bloom,"Low")
        fact  = topics[i%len(topics)]
        verb  = vseq[i].capitalize()

        if mix_mode:
            kind = mix_order[i]
            stem = MIX_TEMPLATES[kind](fact)
        else:
            stem = f"Which option best demonstrates **{fact}**?"

        # Option templates: one correct + three distractors
        correct = f"A correct point about {fact}."

        distractors = [
            f"A misconception about {fact}.",
            f"An incomplete or vague description of {fact}.",
            f"A distractor unrelated to {fact}.",
        ]

        # Deterministic varied correct letter
        rng = rng_for(int(lesson), int(week), i+1, variant or "")
        correct_idx = rng.randrange(4)

        # Place correct and fill others in a stable order
        order = [None]*4
        order[correct_idx] = correct
        k = 0
        for j in range(4):
            if order[j] is None:
                order[j] = distractors[k]
                k += 1

        A,B,C,D = order

        rows.append({
            "Q#":i+1, "Bloom":bloom, "Tier":tier, "Question":stem,
            "Option A":A, "Option B":B, "Option C":C, "Option D":D,
            "Answer":"ABCD"[correct_idx], "Explanation":f"Verb focus: {verb} · Tier: {tier}"
        })
    return rows

# ---------- Exports ----------
def _docx(paragraphs, title):
    try:
        from docx import Document
        from docx.shared import Pt
    except Exception:
        return None
    doc=Document()
    style=doc.styles["Normal"]; style.font.name="Calibri"; style.font.size=Pt(11)
    doc.add_heading(title, level=1)
    for p in paragraphs:
        doc.add_paragraph(p)
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
        parts=[]
        for letter in "ABCD":
            text = r[f"Option {letter}"]
            parts.append(("=" if letter==r["Answer"] else "~")+str(text))
        lines.append(f"::{int(r['Q#'])}:: {r['Question']} {{ {' '.join(parts)} }}")
    return "\n\n".join(lines)

# ---------- State init ----------
defaults = {
    "lesson":1, "week":1, "level":"Understand",
    "verbs":[], "num_mcqs":10, "activities_per_class":2, "duration":20,
    "difficulty":"Medium", "src_text":"", "mcqs":[], "acts_textarea":"",
    "activities":[], "variant_code":"", "mix_mode": False
}
for k,v in defaults.items(): st.session_state.setdefault(k,v)

# ---------- Sidebar upload with confirmation ----------
with st.sidebar:
    st.header("Upload PDF / DOCX / PPTX")
    uploaded = st.file_uploader("Drag & drop or choose", type=["pdf","docx","pptx"], key="uploader")
    if uploaded:
        if st.session_state.get("last_upload_name") != uploaded.name:
            st.session_state["last_upload_name"] = uploaded.name
            kb = uploaded.size/1024
            st.toast(f"Uploaded **{uploaded.name}** ({kb:.1f} KB)", icon="✅")
        st.success(f"File ready: **{uploaded.name}**")

    st.write("---")
    st.write("**Week**")
    st.session_state["week"] = st.selectbox("Week", list(range(1,15)),
                                            index=st.session_state["week"]-1, key="week_select")
    st.write("**Lesson**")
    st.session_state["lesson"] = st.selectbox("Lesson", list(range(1,21)),
                                              index=st.session_state["lesson"]-1, key="lesson_select")
    st.caption(f"Policy: **{policy_for_week(int(st.session_state['week']))}**")

# ---------- Main layout ----------
left, right = st.columns([1.05, 1.4])

with left:
    st.markdown("### ADI Builder")
    st.caption("Policy pills · Verb picker · MCQs · Activities · Exports")

    # Level & verbs
    policy = policy_for_week(int(st.session_state["week"]))
    suggested = "Understand" if policy=="Low" else ("Analyze" if policy=="Medium" else "Create")
    st.session_state["level"] = st.select_slider("Bloom Level",
        options=BLOOM_LEVELS, value=st.session_state.get("level", suggested))
    verbs_default = DEFAULT_VERBS.get(st.session_state["level"], [])
    verbs_sel = st.multiselect("Verb picker",
        options=sorted(set(sum(DEFAULT_VERBS.values(), []))),
        default=verbs_default, key="verbs_picker")
    st.session_state["verbs"] = verbs_sel

    # Mixture & variant
    st.session_state["mix_mode"] = st.toggle("Mixture mode (varied question types)",
                                             value=bool(st.session_state.get("mix_mode", False)))
    cV1, cV2 = st.columns([3,1])
    st.session_state["variant_code"] = cV1.text_input(
        "Variant code (optional)",
        st.session_state.get("variant_code",""),
        placeholder="e.g., A1, B, 7F2C",
        help="Use different codes to generate different MCQ sets for the same lesson/week."
    )
    if cV2.button("New variant"):
        st.session_state["variant_code"] = secrets.token_hex(2).upper()

    # Counts & options
    st.session_state["num_mcqs"] = st.number_input("How many MCQs?", 1, 50,
        value=int(st.session_state["num_mcqs"]))
    st.session_state["activities_per_class"] = st.number_input("Activities per class", 1, 10,
        value=int(st.session_state["activities_per_class"]))
    st.session_state["duration"] = st.number_input("Activity duration (minutes)", 5, 120,
        value=int(st.session_state["duration"]))
    st.session_state["difficulty"] = st.selectbox("Difficulty", ["Low","Medium","High"],
        index=["Low","Medium","High"].index(st.session_state["difficulty"]))

    # Source text
    st.markdown("**Source text (optional)**")
    st.session_state["src_text"] = st.text_area(
        "Paste lesson/topic text (improves MCQs/Activities)",
        height=130, label_visibility="collapsed")

    # Action buttons
    if st.button("⚡ Auto-fill MCQs", use_container_width=True):
        blooms = [st.session_state["level"]] * int(st.session_state["num_mcqs"])
        st.session_state["mcqs"] = offline_mcqs_varied(
            st.session_state["src_text"], blooms, st.session_state["verbs"],
            int(st.session_state["num_mcqs"]), int(st.session_state["lesson"]), int(st.session_state["week"]),
            bool(st.session_state["mix_mode"]), st.session_state.get("variant_code","").strip()
        )
        st.success(f"Generated {len(st.session_state['mcqs'])} MCQs.")

    if st.button("🧩 Generate Activities", use_container_width=True):
        acts = offline_activities(
            st.session_state["verbs"], st.session_state["level"],
            int(st.session_state["activities_per_class"]), int(st.session_state["duration"]),
            st.session_state["difficulty"], int(st.session_state["week"])
        )
        st.session_state["activities"] = acts
        st.session_state["acts_textarea"] = "\n".join(acts)
        st.success(f"Generated {len(acts)} activities.")

with right:
    st.markdown("#### MCQs (editable)")
    if st.session_state["mcqs"]:
        edited = st.data_editor(st.session_state["mcqs"], num_rows="dynamic",
                                use_container_width=True, key="mcq_editor")
        st.session_state["mcqs"] = edited
    else:
        st.info("Click **Auto-fill MCQs** to generate sample questions.")

    st.markdown("---")
    st.markdown("#### Activities (editable)")
    st.session_state["acts_textarea"] = st.text_area("One per line",
        value=st.session_state.get("acts_textarea",""), height=160, key="acts_text_area")

# ---------- Export section ----------
st.markdown("---"); st.markdown("### Export")

def _text_bytes(lines): return ("\n".join(lines) + "\n").encode("utf-8")

df = st.session_state["mcqs"]
acts = st.session_state.get("activities") or [l for l in st.session_state.get("acts_textarea","").splitlines() if l.strip()]
lesson, week = int(st.session_state["lesson"]), int(st.session_state["week"])
variant = st.session_state.get("variant_code","").strip()
vtag = f"_v{variant}" if variant else ""
date_str = dt.date.today().strftime("%Y-%m-%d")
base = f"ADI_Lesson{lesson}_Week{week}{vtag}_{date_str}"

c1,c2,c3,c4 = st.columns(4)

with c1:
    if acts:
        data = _docx(acts, "Activity Sheet") or _text_bytes(acts)
        st.download_button("⬇️ Activity Sheet (.docx)", data=data,
                           file_name=f"{base}_ActivitySheet.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.button("⬇️ Activity Sheet (.docx)", disabled=True)

with c2:
    if df:
        paper, _ = mcq_paper_and_key_lines(df)
        data = _docx(paper, "MCQ Paper") or _text_bytes(paper)
        st.download_button("⬇️ MCQ Paper (.docx)", data=data,
                           file_name=f"{base}_MCQPaper.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.button("⬇️ MCQ Paper (.docx)", disabled=True)

with c3:
    if df:
        _, key = mcq_paper_and_key_lines(df)
        data = _docx(key, "Answer Key") or _text_bytes(key)
        st.download_button("⬇️ Answer Key (.docx)", data=data,
                           file_name=f"{base}_AnswerKey.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.button("⬇️ Answer Key (.docx)", disabled=True)

with c4:
    if df:
        gift = build_gift(df).encode("utf-8")
        st.download_button("⬇️ Moodle GIFT (.gift)", data=gift,
                           file_name=f"{base}.gift", mime="text/plain")
    else:
        st.button("⬇️ Moodle GIFT (.gift)", disabled=True)



