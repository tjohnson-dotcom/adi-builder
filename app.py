# app.py — ADI Builder (Clean ADI • Single Bloom Selector • Focused Sequence)
# - ADI green/gold theme
# - One Bloom selector (radio styled as chips) — no duplicate rows
# - "Auto by Focus" biases sequence toward selected Bloom level
# - Activities primary (left), MCQs primary (right)
# - Offline by default; optional AI via env/secrets

import os, io, json, hashlib, random, re
from typing import List, Dict
import pandas as pd
import streamlit as st

# Optional parsers
try:
    from pptx import Presentation
except Exception:
    Presentation = None
try:
    from docx import Document
except Exception:
    Document = None
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

# ---------------- Branding tokens ----------------
ADI_GREEN = "#245a34"
ADI_GREEN_DARK = "#1a4426"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#f4f4f2"
INK       = "#0f172a"

CSS = f"""
<style>
  :root {{
    --adi-green: {ADI_GREEN};
    --adi-green-dark: {ADI_GREEN_DARK};
    --adi-gold:  {ADI_GOLD};
    --adi-stone: {ADI_STONE};
    --ink: {INK};
  }}
  html, body {{ background: var(--adi-stone) !important; }}

  .adi-ribbon {{
    height: 6px;
    background: linear-gradient(90deg, var(--adi-green) 0%, var(--adi-green-dark) 60%, var(--adi-gold) 100%);
    border-radius: 0 0 12px 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,.08);
    margin-bottom: 8px;
  }}

  .adi-title {{ font-size:1.6rem; font-weight:900; color:var(--adi-green); letter-spacing:.2px; }}
  .adi-sub {{ color:#3f4a54; font-weight:600; }}

  .adi-card {{
    background:#fff; border:1px solid rgba(0,0,0,.06); border-radius:20px; padding:20px;
    box-shadow:0 8px 24px rgba(10, 24, 18, .08);
  }}
  .adi-section {{ border-top: 3px solid var(--adi-gold); margin: 8px 0 16px; }}

  .stTabs [data-baseweb="tab"] {{
    background:#fff; color:#1f2937; padding:10px 14px; border-radius:16px;
    border:1px solid rgba(0,0,0,.08); position: relative;
  }}
  .stTabs [data-baseweb="tab"]::before {{
    content:'•'; position:absolute; left:10px; top:8px; color:var(--adi-gold);
  }}
  .stTabs [aria-selected="true"] {{
    background:linear-gradient(0deg, #ffffff 0%, #f7faf8 100%);
    border-color:var(--adi-green); font-weight:800; color:#0f172a;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
  }}

  /* Buttons — force ADI green */
  .stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, var(--adi-green), var(--adi-green-dark)) !important;
    color: #ffffff !important; border: none !important; border-radius: 16px !important;
    font-weight: 800 !important; box-shadow: 0 6px 16px rgba(10,24,18,.20);
  }}
  .stButton > button[kind="primary"]:hover {{ filter: brightness(0.95); }}
  .stButton > button:not([kind="primary"]) {{
    background: #ffffff !important; color: var(--adi-green) !important;
    border: 2px solid var(--adi-green) !important; border-radius: 14px !important; font-weight: 700 !important;
  }}

  /* Bloom radio as chips (green/gold only) */
  .stRadio > div {{ gap: 12px; flex-wrap: wrap; }}
  .stRadio label {{ margin-bottom: 0 !important; }}
  .stRadio [role="radiogroup"] > div label {{
    border:2px solid var(--adi-green); border-radius: 999px; padding:10px 16px; background:#ffffff;
    color:#1f2937; font-weight:700; cursor:pointer; box-shadow:0 1px 2px rgba(0,0,0,.04);
  }}
  .stRadio [role="radiogroup"] > div [aria-checked="true"] label {{
    background:#f7faf8; box-shadow: inset 0 0 0 3px var(--adi-gold);
  }}

  .stDataFrame thead {{ background: #f3faf5 !important; }}

  .ok {{ color:#065f46; font-weight:800; }}
  .warn {{ color:#991b1b; font-weight:800; }}
</style>
"""

st.set_page_config(page_title="ADI Builder — Clean ADI", page_icon="✅", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<div class='adi-ribbon'></div>", unsafe_allow_html=True)

# Header
c1, c2 = st.columns([1,6], vertical_alignment="center")
with c1:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=78)
    else:
        st.markdown("**ADI**")
with c2:
    st.markdown("<div class='adi-title'>ADI Builder</div>", unsafe_allow_html=True)
    st.markdown("<div class='adi-sub'>Clean, polished ADI look · Strict colors · Logo required</div>", unsafe_allow_html=True)

# ---------------- Security / LLM (optional) ----------------
def have_api()->bool:
    try:
        from streamlit.runtime.secrets import secrets
        if secrets.get("OPENAI_API_KEY"): return True
    except Exception:
        pass
    return bool(os.getenv("OPENAI_API_KEY",""))

def _get_api_key()->str:
    try:
        from streamlit.runtime.secrets import secrets
        if secrets.get("OPENAI_API_KEY"): return secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY","")

def call_llm(messages: List[Dict], model="gpt-4o-mini", temperature=0.6, base_url=None) -> str:
    import requests
    key = _get_api_key()
    if not key: raise RuntimeError("No API key found in env or secrets")
    url = base_url or "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type":"application/json"}
    payload = {"model": model, "messages": messages, "temperature": float(temperature)}
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ---------------- Bloom helpers ----------------
BLOOM_LEVELS = ["Remember","Understand","Apply","Analyze","Evaluate","Create"]
BLOOM_TIER   = {"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}
BLOOM_STEMS  = {
    "Remember":["Define","List","Identify","Match","Name"],
    "Understand":["Explain","Summarize","Classify","Describe"],
    "Apply":["Apply","Use","Compute","Demonstrate"],
    "Analyze":["Differentiate","Organize","Compare","Critique"],
    "Evaluate":["Justify","Assess","Prioritize","Choose"],
    "Create":["Design","Compose","Develop","Propose"],
}
MCQ_COLS = ["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]

def policy_tier(week:int)->str:
    if week <= 4: return "Low"
    if week <= 9: return "Medium"
    return "High"

def weighted_bloom_sequence(selected: str, n: int, rng: random.Random) -> list:
    # Heavily weight the selected level, then neighbors, then others
    idx = BLOOM_LEVELS.index(selected)
    weights = []
    for i, lv in enumerate(BLOOM_LEVELS):
        dist = abs(i - idx)
        w = {0: 5, 1: 3, 2: 2, 3: 1}[min(dist, 3)]
        weights.append(w)
    # Sample with weights
    seq = []
    for _ in range(n):
        x = rng.uniform(0, sum(weights))
        acc = 0
        for lv, w in zip(BLOOM_LEVELS, weights):
            acc += w
            if x <= acc:
                seq.append(lv); break
    return seq

def stable_seed(teacher_id: str, klass: str, lesson: int, week: int, src_text: str) -> int:
    h = hashlib.md5((teacher_id + "|" + klass + "|" + str(lesson) + "|" + str(week) + "|" + (src_text or "")[:5000]).encode()).hexdigest()
    return int(h[:8], 16)

def deduplicate_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df[df["Question"].astype(str).str.len() > 0]
    df = df.loc[~df["Question"].str.lower().duplicated()].copy()
    df["Answer"] = df["Answer"].map(lambda s: s if s in list("ABCD") else "A")
    for col in ["Option A","Option B","Option C","Option D"]:
        df[col] = df[col].fillna("").replace("", "—")
    df["Q#"] = range(1, len(df)+1)
    return df

# ---------------- Generators ----------------
def offline_generate_mcqs(src_text: str, lesson:int, week:int, bloom_levels: list, teacher_seed:str, n:int=10) -> pd.DataFrame:
    rng = random.Random(stable_seed(teacher_seed, "default", lesson, week, src_text or ""))
    rows = []
    base = [s.strip() for s in re.split(r'[.\n]', src_text or "") if s.strip()] or ["This unit covers core concepts and applied practice."]
    for i in range(1, n+1):
        bloom = bloom_levels[(i-1) % len(bloom_levels)]
        tier = BLOOM_TIER.get(bloom, "Medium")
        stem = BLOOM_STEMS[bloom][i % len(BLOOM_STEMS[bloom]) - 1]
        fact = base[i % len(base) - 1]
        key_index = rng.randrange(4)
        opts = [f"Distractor {j+1}: {base[(i+j) % len(base)][:60]}" for j in range(4)]
        opts[key_index] = f"Correct: {fact[:60]}"
        rows.append({"Bloom": bloom,"Tier": tier,"Q#": i,"Question": f"{stem}: {fact}",
                     "Option A": opts[0], "Option B": opts[1], "Option C": opts[2], "Option D": opts[3],
                     "Answer": "ABCD"[key_index], "Explanation": f"The correct answer reflects: {fact[:80]}"})
    df = pd.DataFrame(rows, columns=MCQ_COLS)
    return deduplicate_and_validate(df)

def ai_generate_mcqs(src_text: str, lesson:int, week:int, bloom_levels: list, teacher_id:str, n:int=10) -> pd.DataFrame:
    seed_hex = hashlib.md5((teacher_id + str(lesson) + str(week) + (src_text or "")[:5000]).encode()).hexdigest()[:8]
    system = ("You generate MCQs aligned to Bloom’s taxonomy. Return STRICT JSON list with objects: "
              "{bloom, tier, question, options:[A,B,C,D], answer_letter, explanation}. No extra text.")
    user = f"""
Source text (trimmed):
\"\"\"{(src_text or '')[:6000]}\"\"\"

Lesson: {lesson}, Week: {week}, Seed: {seed_hex}
Bloom sequence: {', '.join(bloom_levels)}
Rules:
- Vary stems appropriate to Bloom level.
- Options must be unique, plausible, concise.
- Exactly 4 options.
- Use tier: Low/Medium/High appropriate to Bloom.
- Avoid repeating stems like “Which of the following…” too often.
Generate {n} MCQs as JSON.
"""
    import requests
    key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
    if not key:
        return offline_generate_mcqs(src_text, lesson, week, bloom_levels, teacher_id, n=n)
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type":"application/json"}
    payload = {"model": "gpt-4o-mini", "messages": [{"role":"system","content":system},{"role":"user","content":user}], "temperature": 0.6}
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"]
    try:
        data = json.loads(raw)
    except Exception:
        start, end = raw.find("["), raw.rfind("]"); data = json.loads(raw[start:end+1])
    rows = []
    for i, q in enumerate(data, start=1):
        opts = q.get("options", [])
        if len(opts) != 4: continue
        rows.append({
            "Bloom": q.get("bloom","Understand"),
            "Tier": q.get("tier","Medium"),
            "Q#": i,
            "Question": (q.get("question","") or "").strip(),
            "Option A": (opts[0] or "").strip(),
            "Option B": (opts[1] or "").strip(),
            "Option C": (opts[2] or "").strip(),
            "Option D": (opts[3] or "").strip(),
            "Answer": q.get("answer_letter","A").upper(),
            "Explanation": (q.get("explanation","") or "").strip()
        })
    df = pd.DataFrame(rows, columns=MCQ_COLS)
    return deduplicate_and_validate(df)

# ---------------- Extraction ----------------
def extract_text_from_pptx(file_bytes: bytes) -> str:
    if not Presentation: return ""
    prs = Presentation(io.BytesIO(file_bytes))
    texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"): texts.append(shape.text)
    return "\n".join(texts)
def extract_text_from_docx(file_bytes: bytes) -> str:
    if not Document: return ""
    doc = Document(io.BytesIO(file_bytes))
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paras)
def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not PyPDF2: return ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join([p.extract_text() or "" for p in reader.pages])
    except Exception:
        return ""

# ---------------- State ----------------
if "mcq_df" not in st.session_state:
    st.session_state.mcq_df = pd.DataFrame(columns=MCQ_COLS)
if "activities" not in st.session_state:
    st.session_state.activities = []

tabs = st.tabs(["① Upload", "② Setup", "③ Generate", "④ Export"])

# ① Upload
with tabs[0]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("Upload source")
    st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    up = st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)", type=["pdf","pptx","docx"])
    pasted = st.text_area("Or paste source text manually", height=180, placeholder="Paste any relevant lesson/topic text here…")
    src_text = ""
    if up is not None:
        data = up.read(); name = up.name.lower()
        if name.endswith(".pptx"): src_text = extract_text_from_pptx(data)
        elif name.endswith(".docx"): src_text = extract_text_from_docx(data)
        elif name.endswith(".pdf"): src_text = extract_text_from_pdf(data)
    if not src_text and pasted.strip(): src_text = pasted.strip()
    st.session_state["src_text"] = src_text
    st.caption(f"Characters loaded: {len(src_text)}")
    st.markdown("</div>", unsafe_allow_html=True)

# ② Setup
with tabs[1]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("Setup")
    st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    cA, cB, cC, cD = st.columns(4)
    lesson = cA.number_input("Lesson", min_value=1, max_value=20, value=1, step=1)
    week   = cB.number_input("Week",   min_value=1, max_value=20, value=1, step=1)
    teacher_id = cC.text_input("Teacher ID", value="teacher_001")
    klass      = cD.text_input("Class/Section", value="class_A")

    st.write("")
    st.markdown("**Bloom’s taxonomy**")
    bloom_level = st.radio("Pick focus level", BLOOM_LEVELS, index=1, horizontal=True, label_visibility="collapsed")

    mode = st.radio("Sequence mode", ["Auto by Focus", "Target level(s)"], horizontal=True)
    if mode == "Auto by Focus":
        count = st.slider("How many MCQs?", 4, 30, 10, 1)
        rng = random.Random(week*100 + lesson)
        blooms = weighted_bloom_sequence(bloom_level, count, rng)
    else:
        sel = st.multiselect("Pick Bloom levels (will cycle)", BLOOM_LEVELS, default=["Understand","Apply","Analyze"])
        count = st.slider("How many MCQs?", 4, 30, 10, 1)
        if not sel: sel = ["Understand"]
        blooms = (sel * ((count // len(sel)) + 1))[:count]
    st.write("Sequence preview:", ", ".join(blooms))

    current_policy = policy_tier(int(week))
    selected_tier = BLOOM_TIER[bloom_level]
    if selected_tier == current_policy:
        st.markdown(f"Policy: **{current_policy}** · Selected: **<span class='ok'>{selected_tier}</span>** ✓", unsafe_allow_html=True)
    else:
        st.markdown(f"Policy: **{current_policy}** · Selected: **<span class='warn'>{selected_tier}</span>** (mismatch)", unsafe_allow_html=True)

    st.write("---")
    ai_possible = have_api()
    use_ai = st.checkbox("Use AI generator (if key available)", value=ai_possible)
    if use_ai and not ai_possible:
        st.info("No API key found in env or secrets; will fall back to offline generator.")
    st.markdown("</div>", unsafe_allow_html=True)

# ③ Generate
with tabs[2]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    
st.subheader("Generate MCQs & Activities")
st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
src_text = st.session_state.get("src_text","")

# --- Activities selectors (visible and simple) ---
ctl1, ctl2, ctl3, ctl4 = st.columns([1,1,1,1])
with ctl1:
    activity_count = st.slider("Activities", 1, 4, 2, 1)
with ctl2:
    activity_style = st.selectbox("Style", ["Mixed","Quick tasks","Pair/Group","Project","Assessment"], index=0)
with ctl3:
    activity_difficulty = st.radio("Difficulty", ["Low","Medium","High"], index=1, horizontal=True)
with ctl4:
    duration = st.selectbox("Duration (mins)", [15,20,25,30,35,40,45,50,55,60], index=1)
use_bloom_verbs = st.checkbox("Use Bloom verbs", value=True)


    colA, colB = st.columns(2)
    
with colA:
        if st.button("Generate Activities", type="primary", key="btn_acts"):
            rng = random.Random(stable_seed(teacher_id, klass, lesson, week, src_text))
            # Stems bank by style & difficulty
            base_stems = {
                "Quick tasks": ["Do-now:","Exit ticket:","3-minute write:","Sketch-note:","One-sentence summary:"],
                "Pair/Group": ["Think–Pair–Share:","Mini-debate:","Jigsaw teach-back:","Peer review:","Gallery walk:"],
                "Project": ["Prototype:","Mini-project:","Concept map:","Storyboard:","Case design:"],
                "Assessment": ["Quiz item:","Short answer:","Spot the error:","Classify:","Rank & justify:"],
                "Mixed": ["Pair-share on","Mini-poster:","Role-play:","Think–Pair–Share:","Quick debate:","Case critique:"]
            }
            diff_suffix = {"Low":" (recall)","Medium":" (apply/analyze)","High":" (create/evaluate)"}
            chosen = base_stems.get(activity_style, base_stems["Mixed"])

            base = [s.strip() for s in re.split(r'[.
]', src_text) if s.strip()] or ["today's topic"]
            acts = []
            for i in range(activity_count):
                stem = chosen[i % len(chosen)]
                topic = base[i % len(base)]
                if use_bloom_verbs:
                    # Pull a verb from selected Bloom level neighbors
                    lv = blooms[i % len(blooms)]
                    verbs = BLOOM_STEMS.get(lv, ["Explore"])
                    verb = verbs[i % len(verbs)]
                    prompt = f"{stem} {verb} {topic}{diff_suffix.get(activity_difficulty,'')}"
                else:
                    prompt = f"{stem} {topic}{diff_suffix.get(activity_difficulty,'')}"
                acts.append(f"[{duration} min] " + prompt)
            st.session_state.activities = acts
    with colB:
        if st.button("Generate MCQs", type="primary", key="btn_mcq"):
            if use_ai and have_api():
                with st.spinner("Generating with AI…"):
                    df = ai_generate_mcqs(src_text, lesson, week, blooms, teacher_id, n=len(blooms))
            else:
                with st.spinner("Generating (offline)…"):
                    df = offline_generate_mcqs(src_text, lesson, week, blooms, teacher_id, n=len(blooms))
            st.session_state.mcq_df = df

    st.write("")
    st.markdown("**Quick Editor**")
    st.caption("Edit inline. Your exports will use this exact table.")
    st.session_state.mcq_df = st.data_editor(
        st.session_state.mcq_df, num_rows="dynamic", use_container_width=True, key="editor_mcq"
    )

    st.write("")
    st.markdown("**Activities (editable)**")
    acts_text = "\n".join(st.session_state.get("activities", []))
    acts_text = st.text_area("One per line", value=acts_text, height=140, key="acts_text")
    st.session_state.activities = [a.strip() for a in acts_text.split("\n") if a.strip()]

    st.markdown("</div>", unsafe_allow_html=True)

# ④ Export
def to_gift(df: pd.DataFrame) -> str:
    lines = []
    for _, r in df.iterrows():
        q = r["Question"].replace("\n"," ")
        options = [r["Option A"], r["Option B"], r["Option C"], r["Option D"]]
        ans_idx = "ABCD".index(r["Answer"])
        gift_opts = []
        for i, opt in enumerate(options):
            opt = opt.replace("}", "\\}")
            gift_opts.append(("=" if i==ans_idx else "~")+opt)
        lines.append("{"+q+"}{"+" ".join(gift_opts)+"}")
    return "\n\n".join(lines)

def activities_docx(activities: list) -> bytes:
    if not Document: return b""
    doc = Document()
    doc.add_heading("Activities", level=1)
    for i, a in enumerate(activities, start=1):
        doc.add_paragraph(f"{i}. {a}")
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

with tabs[3]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("Export")
    st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    df = st.session_state.mcq_df.copy()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if not df.empty:
            st.download_button("MCQs CSV", data=df.to_csv(index=False).encode("utf-8"),
                               file_name="mcqs.csv", mime="text/csv", use_container_width=True)
    with c2:
        if not df.empty:
            gift_text = to_gift(df)
            st.download_button("MCQs GIFT", data=gift_text.encode("utf-8"),
                               file_name="mcqs.gift.txt", mime="text/plain", use_container_width=True)
    with c3:
        if st.session_state.get("activities"):
            st.download_button("Activities CSV", data=("\n".join(st.session_state["activities"])).encode("utf-8"),
                               file_name="activities.csv", mime="text/csv", use_container_width=True)
    with c4:
        if st.session_state.get("activities") and Document:
            st.download_button("Activities DOCX", data=activities_docx(st.session_state["activities"]),
                               file_name="activities.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True)
        elif st.session_state.get("activities"):
            st.info("Install python-docx to enable DOCX export.")

    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Security: API keys (if used) stay server-side (env or .streamlit/secrets). Never accept keys via UI.")
