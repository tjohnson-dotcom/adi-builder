# ADI Builder — working MCQ generator (no external APIs)
# Run:  pip install streamlit
#       streamlit run app.py

import re
import csv
import base64
import os
import io
import random
import streamlit as st

# ---------- Page ----------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ---------- Theme (short & safe) ----------
st.markdown("""
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-green-50:#eef5f0;
  --adi-gold:#c8a85a; --border:#d9dfda; --card:#fff;
}
html,body{background:#FAFAF7}
main .block-container{padding-top:0.8rem; max-width:1220px}
.adi-hero{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));
  color:#fff; border-radius:20px; padding:16px 18px; margin-bottom:12px}
.adi-title{font-weight:800; font-size:20px}
.adi-sub{opacity:.92; font-size:12px}
section.card{background:var(--card); border:1px solid var(--border); border-radius:14px; padding:14px; margin-bottom:14px}
div.stButton>button{background:var(--adi-green); color:#fff; border:none; border-radius:999px;
  padding:.6rem 1rem; font-weight:600}
div.stButton>button:hover{filter:brightness(.97); box-shadow:0 0 0 3px rgba(200,168,90,.35)}
input[type="radio"], input[type="checkbox"]{accent-color: var(--adi-green)}
/* uploader – keep it stable */
[data-testid="stFileUploadDropzone"]{
  border:2px dashed var(--adi-green)!important; background:var(--adi-green-50)!important;
  border-radius:14px!important; pointer-events:auto!important
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
with st.container():
    st.markdown(f"""
    <div class="adi-hero">
      <div class="adi-title">ADI Builder - Lesson Activities & Questions</div>
      <div class="adi-sub">Professional, branded, editable and export-ready.</div>
    </div>
    """, unsafe_allow_html=True)

# ---------- Tabs ----------
tab = st.radio("choose", ["Knowledge MCQs (ADI Policy)", "Skills Activities"], horizontal=True, label_visibility="collapsed")
left, right = st.columns([0.95, 2.05], gap="large")

# ---------- LEFT SIDE ----------
with left:
    # Upload
    with st.container():
        st.markdown('<section class="card">', unsafe_allow_html=True)
        st.markdown("### Upload eBook / Lesson Plan / PPT")
        st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
        file = st.file_uploader("Drag and drop your file, or Browse", type=["pdf","docx","pptx"], accept_multiple_files=False)
        if file:
            st.success(f"Uploaded: **{file.name}**  ·  {file.size/1_000_000:.1f} MB")
            # quick progress animation (purely UI)
            prog = st.progress(0)
            for i in range(0,101,10):
                prog.progress(i)
            prog.empty()
        st.caption("We recommend eBooks (PDF) as source for best results.")
        st.markdown('</section>', unsafe_allow_html=True)

    # Pick from plan
    with st.container():
        st.markdown('<section class="card">', unsafe_allow_html=True)
        st.markdown("### Pick from eBook / Plan / PPT")

        # Lesson 1–5 (simple)
        st.write("**Lesson**")
        lesson = st.radio("", [1,2,3,4,5], index=0, horizontal=True, label_visibility="collapsed")

        # Week 1–14 (ADI policy driver)
        st.write("**Week**")
        week = st.radio("", list(range(1,15)), index=0, horizontal=True, label_visibility="collapsed")

        st.caption("**ADI policy:** Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. The appropriate Bloom tier will be auto-highlighted.")
        b1, b2 = st.columns(2)
        with b1:
            st.button("Pull → MCQs")
        with b2:
            st.button("Pull → Activities")
        st.markdown('</section>', unsafe_allow_html=True)

    # Activity parameters (kept simple)
    with st.container():
        st.markdown('<section class="card">', unsafe_allow_html=True)
        st.markdown("### Activity Parameters")
        a1, a2 = st.columns(2)
        with a1:
            st.number_input("Activities", min_value=1, value=3, step=1)
        with a2:
            st.number_input("Duration (mins)", min_value=5, value=45, step=5)
        st.caption("ADI Bloom tiers used for MCQs: **Low** (define, identify, list, recall, describe, label) · "
                   "**Medium** (apply, demonstrate, solve, illustrate) · **High** (evaluate, synthesize, design, justify)")
        st.markdown('</section>', unsafe_allow_html=True)

# ---------- RIGHT SIDE ----------
def infer_keywords(text: str, k: int = 8):
    if not text:
        return []
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    freq = {}
    for w in words:
        if w in {"this","that","with","from","have","which","their","there","about","into","your","were","will"}:
            continue
        freq[w] = freq.get(w,0) + 1
    out = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w,_ in out[:k]]

LOW_VERBS    = ["define","identify","list","recall","describe","label"]
MED_VERBS    = ["apply","demonstrate","solve","illustrate"]
HIGH_VERBS   = ["evaluate","synthesize","design","justify"]

def week_tier(w:int):
    if w <= 4:  return "Low", LOW_VERBS
    if w <= 9:  return "Medium", MED_VERBS
    return "High", HIGH_VERBS

def make_distr(total:int, w:int):
    # ADI policy weighted distribution
    if w <= 4:       # Low focus
        low = max(1, int(total*0.7)); med = max(0, int(total*0.25)); high = total - low - med
    elif w <= 9:     # Medium focus
        med = max(1, int(total*0.6)); low = max(0, int(total*0.25)); high = total - low - med
    else:            # High focus
        high = max(1, int(total*0.6)); med = max(0, int(total*0.25)); low = total - med - high
    return max(low,0), max(med,0), max(high,0)

def build_mcq(stem, correct, distractors):
    # ensure 4 options
    opts = [correct] + distractors[:3]
    # pad simple distractors if needed
    fill = ["Not applicable","None of the above","All of the above","Insufficient data","Irrelevant"]
    i = 0
    while len(opts) < 4 and i < len(fill):
        if fill[i] not in opts:
            opts.append(fill[i])
        i+=1
    random.shuffle(opts)
    correct_letter = "ABCD"[opts.index(correct)]
    return opts, correct_letter

def generate_mcqs(src_text: str, topic: str, total: int, w: int):
    random.seed(42)  # stable for testing
    tier, verbs = week_tier(w)
    low_n, med_n, high_n = make_distr(total, w)
    kws = infer_keywords((src_text or "") + " " + (topic or ""), k=10)
    if not kws:
        kws = ["policy","procedure","safety","protocol","system","input","output","quality","risk","standard"]
    bank = []
    def mk(level, verb):
        term = random.choice(kws)
        # simple stem patterns per level
        if level=="Low":
            stem = f"{verb.capitalize()} the term '{term}'."
            correct = f"{term} definition"
            distract = [f"{k} definition" for k in random.sample(kws,3)]
        elif level=="Medium":
            stem = f"{verb.capitalize()} how '{term}' would be used in context."
            correct = f"Use '{term}' in a correct example"
            distract = [f"Misuse '{x}' in an example" for x in random.sample(kws,3)]
        else:
            stem = f"{verb.capitalize()} the impact of '{term}' on the module's outcome."
            correct = f"Reasoned judgement about '{term}'"
            distract = [f"Unjustified claim about '{x}'" for x in random.sample(kws,3)]
        opts, ans = build_mcq(stem, correct, distract)
        return {"Tier":level, "Verb":verb, "Question":stem,
                "A":opts[0], "B":opts[1], "C":opts[2], "D":opts[3], "Answer":ans}

    for _ in range(low_n):
        bank.append(mk("Low", random.choice(LOW_VERBS)))
    for _ in range(med_n):
        bank.append(mk("Medium", random.choice(MED_VERBS)))
    for _ in range(high_n):
        bank.append(mk("High", random.choice(HIGH_VERBS)))
    # in case rounding missed length
    if len(bank) < total:
        for _ in range(total - len(bank)):
            bank.append(mk(tier, random.choice(verbs)))
    return bank[:total]

with right:
    st.markdown('<section class="card">', unsafe_allow_html=True)
    if tab.startswith("Knowledge"):
        st.markdown("### Generate MCQs — Policy Blocks (Low → Medium → High)")
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        src   = st.text_area("Source text (optional, editable)", height=130, placeholder="Paste or edit source text here...")

        st.caption("How many MCQs?")
        quick = st.radio("Quick pick", [5,10,15,20,25,30], horizontal=True, index=1, label_visibility="collapsed")
        total = st.number_input("Or type any number", min_value=5, max_value=50, value=int(quick), step=1, key="mcq_total")

        low_n, med_n, high_n = make_distr(total, week)
        st.caption(f"Week **{week}** → distribution: **Low {low_n} · Medium {med_n} · High {high_n}**")

        gen = st.button("Generate MCQs")
        if gen:
            data = generate_mcqs(src, topic, total, week)
            st.success(f"Generated **{len(data)}** MCQs.")
            # show table
            st.dataframe(data, use_container_width=True)

            # download CSV
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=["Tier","Verb","Question","A","B","C","D","Answer"])
            writer.writeheader()
            for r in data: writer.writerow(r)
            st.download_button("Download MCQs (CSV)", buf.getvalue().encode("utf-8"),
                               file_name=f"adi_mcqs_w{week}_{total}.csv", mime="text/csv")

    else:
        st.markdown("### Build Skills Activities")
        st.selectbox("Activity type", ["Case Study","Role Play","Scenario MCQ","Group Discussion","Practical Demo"])
        st.text_input("Learning goal", placeholder="What should learners be able to do?")
        st.text_area("Materials / Inputs", height=110, placeholder="Links, readings, slides, equipment...")
        st.number_input("Groups", min_value=1, value=4)
        st.number_input("Duration (mins)", min_value=5, value=30, step=5, key="skill_dur")
        st.button("Generate Activity Plan")
    st.markdown('</section>', unsafe_allow_html=True)
