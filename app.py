# app.py — ADI Builder (Single-file, polished ADI look)
# Clean ADI branding (green #245a34, gold #C8A85A), header logo, step tabs,
# Bloom controls, duplicate guard, AI toggle via env/secrets (optional),
# offline fallback, and exports (CSV, GIFT, DOCX). PDF/PPTX/DOCX text extraction is best-effort.
#
# Run:
#   pip install -r requirements.txt
#   streamlit run app.py

import os, io, json, hashlib, random, re
from typing import List, Dict
import pandas as pd
import streamlit as st

# Optional parsers
try:
    from pptx import Presentation  # python-pptx
except Exception:
    Presentation = None

try:
    from docx import Document  # python-docx
except Exception:
    Document = None

try:
    import PyPDF2  # for PDFs
except Exception:
    PyPDF2 = None

# -----------------------------
# ADI Branding
# -----------------------------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#f4f4f2"

def _inject_css():
    st.markdown(f"""
    <style>
      body {{ background:{ADI_STONE}; }}
      .adi-header {{ display:flex; align-items:center; gap:14px; margin:6px 0 12px; }}
      .adi-logo {{ height:56px; width:auto; border-radius:10px; border:2px solid {ADI_GOLD}; background:white; }}
      .adi-title {{ font-size:1.35rem; font-weight:800; color:{ADI_GREEN}; letter-spacing:.2px; }}
      .adi-sub   {{ color:#4b5563; }}
      .adi-card {{ background:#fff; border:1px solid rgba(0,0,0,.06); border-radius:18px; padding:18px;
                   box-shadow:0 2px 14px rgba(0,0,0,.06); }}
      .adi-bigbtn button {{ border-radius:16px !important; padding:12px 18px !important; font-weight:700 !important;
                   background: linear-gradient(135deg, {ADI_GREEN}, #1a4426) !important; color:white !important; border:none !important;
                   box-shadow: 0 3px 14px rgba(0,0,0,.12); }}
      .stTabs [data-baseweb="tab"] {{
        background: white; color:#1f2937; padding:10px 14px; border-radius:14px;
        border:1px solid rgba(0,0,0,.08);
      }}
      .stTabs [aria-selected="true"] {{
        background:{ADI_STONE}; border-color:{ADI_GREEN}; font-weight:700; color:#0f172a;
      }}
      .pill {{
        display:inline-block; padding:6px 10px; border-radius:999px; border:1px solid #d0d0cc; margin-right:6px;
      }}
      .pill.on {{ background:#f7f7f7; border-color:{ADI_GREEN}; }}
      .ok {{ color:#065f46; font-weight:700; }}
      .warn {{ color:#991b1b; font-weight:700; }}
    </style>
    """, unsafe_allow_html=True)

def header_with_logo():
    col1, col2 = st.columns([1,6], vertical_alignment="center")
    with col1:
        # Prefer a local Logo.png if present in repo root; else use any uploaded/URL from state
        logo_path = "Logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=72)
        elif st.session_state.get("adi_logo_data"):
            st.image(st.session_state["adi_logo_data"], width=72)
        elif st.session_state.get("adi_logo_url"):
            st.image(st.session_state["adi_logo_url"], width=72)
        else:
            st.markdown(f"<div class='pill on' style='border-color:{ADI_GOLD};'>ADI</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='adi-title'>ADI Builder</div>", unsafe_allow_html=True)
        st.markdown("<div class='adi-sub'>Clean, polished ADI look · Strict colors · Logo required</div>", unsafe_allow_html=True)

# -----------------------------
# Security / LLM (optional)
# -----------------------------
def have_api()->bool:
    try:
        from streamlit.runtime.secrets import secrets
        if secrets.get("OPENAI_API_KEY"):
            return True
    except Exception:
        pass
    return bool(os.getenv("OPENAI_API_KEY",""))

def _get_api_key()->str:
    try:
        from streamlit.runtime.secrets import secrets
        if secrets.get("OPENAI_API_KEY"):
            return secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY","")

def call_llm(messages: List[Dict], model="gpt-4o-mini", temperature=0.6, base_url=None) -> str:
    """Minimal OpenAI-compatible client. Never shows key in UI/logs."""
    import requests
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("No API key found in env or secrets")
    url = base_url or "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": float(temperature)}
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

# -----------------------------
# Bloom helpers
# -----------------------------
BLOOM_LEVELS = ["Remember","Understand","Apply","Analyze","Evaluate","Create"]
BLOOM_TIER   = {"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}
BLOOM_STEMS = {
    "Remember":  ["Define","List","Identify","Match","Name"],
    "Understand":["Explain","Summarize","Classify","Describe"],
    "Apply":     ["Apply","Use","Compute","Demonstrate"],
    "Analyze":   ["Differentiate","Organize","Compare","Critique"],
    "Evaluate":  ["Justify","Assess","Prioritize","Choose"],
    "Create":    ["Design","Compose","Develop","Propose"],
}
MCQ_COLS = ["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]

def pick_bloom_sequence(rng: random.Random, n: int) -> List[str]:
    order = BLOOM_LEVELS.copy(); rng.shuffle(order)
    seq = []
    while len(seq) < n: seq.extend(order)
    return seq[:n]

def stable_seed(teacher_id: str, klass: str, lesson: int, week: int, src_text: str) -> int:
    h = hashlib.md5((teacher_id + "|" + klass + "|" + str(lesson) + "|" + str(week) + "|" + (src_text or "")[:5000]).encode()).hexdigest()
    return int(h[:8], 16)

def deduplicate_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["Question"].str.len() > 0]
    df = df.loc[~df["Question"].str.lower().duplicated()].copy()
    df["Answer"] = df["Answer"].map(lambda s: s if s in list("ABCD") else "A")
    for col in ["Option A","Option B","Option C","Option D"]:
        df[col] = df[col].fillna("").replace("", "—")
    df["Q#"] = range(1, len(df)+1)
    return df

# -----------------------------
# Generators
# -----------------------------
def offline_generate_mcqs(src_text: str, lesson:int, week:int, bloom_levels: List[str], teacher_seed:str, n:int=10) -> pd.DataFrame:
    rng = random.Random(stable_seed(teacher_seed, "default", lesson, week, src_text or ""))
    rows = []
    base = [s.strip() for s in re.split(r'[.\n]', src_text or "") if s.strip()] or ["This unit covers core concepts and applied practice."]
    for i in range(1, n+1):
        bloom = bloom_levels[(i-1) % len(bloom_levels)]
        tier = BLOOM_TIER.get(bloom, "Medium")
        stem = rng.choice(BLOOM_STEMS[bloom])
        fact = rng.choice(base)
        key_index = rng.randrange(4)
        opts = [f"Distractor {j+1}: {rng.choice(base)[:60]}" for j in range(4)]
        opts[key_index] = f"Correct: {fact[:60]}"
        rows.append({"Bloom": bloom,"Tier": tier,"Q#": i,"Question": f"{stem}: {fact}",
                     "Option A": opts[0], "Option B": opts[1], "Option C": opts[2], "Option D": opts[3],
                     "Answer": "ABCD"[key_index], "Explanation": f"The correct answer reflects: {fact[:80]}"})
    df = pd.DataFrame(rows, columns=MCQ_COLS)
    return deduplicate_and_validate(df)

def ai_generate_mcqs(src_text: str, lesson:int, week:int, bloom_levels: List[str], teacher_id:str, n:int=10) -> pd.DataFrame:
    seed_hex = hashlib.md5((teacher_id + str(lesson) + str(week) + (src_text or "")[:5000]).encode()).hexdigest()[:8]
    system = (
        "You generate MCQs aligned to Bloom’s taxonomy. "
        "Return STRICT JSON list with objects: "
        "{bloom, tier, question, options:[A,B,C,D], answer_letter, explanation}. "
        "No extra text."
    )
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
    raw = call_llm(
        [{"role":"system","content":system},{"role":"user","content":user}],
        model="gpt-4o-mini", temperature=0.6
    )
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

# -----------------------------
# Extraction
# -----------------------------
def extract_text_from_pptx(file_bytes: bytes) -> str:
    if not Presentation:
        return ""
    prs = Presentation(io.BytesIO(file_bytes))
    texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                texts.append(shape.text)
    return "\n".join(texts)

def extract_text_from_docx(file_bytes: bytes) -> str:
    if not Document:
        return ""
    doc = Document(io.BytesIO(file_bytes))
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paras)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not PyPDF2:
        return ""
    text = []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            text.append(page.extract_text() or "")
    except Exception:
        return ""
    return "\n".join(text)

# -----------------------------
# App UI
# -----------------------------
st.set_page_config(page_title="ADI Builder — Polished", page_icon="✅", layout="wide")
_inject_css()
header_with_logo()

if "mcq_df" not in st.session_state:
    st.session_state.mcq_df = pd.DataFrame(columns=MCQ_COLS)
if "activities" not in st.session_state:
    st.session_state.activities = []
if "adi_logo_data" not in st.session_state:
    st.session_state.adi_logo_data = None
if "adi_logo_url" not in st.session_state:
    st.session_state.adi_logo_url = ""

tabs = st.tabs(["① Upload", "② Setup", "③ Generate", "④ Export"])

# ① Upload
with tabs[0]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("Upload source")
    up = st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)",
                          type=["pdf","pptx","docx"])
    pasted = st.text_area("Or paste source text manually", height=180, placeholder="Paste any relevant lesson/topic text here…")
    src_text = ""
    if up is not None:
        data = up.read()
        name = up.name.lower()
        if name.endswith(".pptx"):
            src_text = extract_text_from_pptx(data)
        elif name.endswith(".docx"):
            src_text = extract_text_from_docx(data)
        elif name.endswith(".pdf"):
            src_text = extract_text_from_pdf(data)
    if not src_text and pasted.strip():
        src_text = pasted.strip()
    st.session_state["src_text"] = src_text
    st.caption(f"Characters loaded: {len(src_text)}")

    with st.expander("Branding (logo)"):
        st.caption("This build enforces ADI branding. Put an official **Logo.png** in the repo root, or set below.")
        colu, colf = st.columns(2)
        logo_url = colu.text_input("Logo URL (PNG/SVG)", value=st.session_state.get("adi_logo_url",""))
        logo_file = colf.file_uploader("Or upload a logo file", type=["png","jpg","jpeg","svg"], key="logo_up")
        cc1, cc2 = st.columns(2)
        if cc1.button("Apply URL"):
            st.session_state.adi_logo_url = logo_url.strip()
        if logo_file is not None and cc2.button("Use uploaded"):
            st.session_state.adi_logo_data = logo_file.read()

    st.markdown("</div>", unsafe_allow_html=True)

# ② Setup
with tabs[1]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("Setup")

    s1, s2, s3, s4 = st.columns([1,1,1,1])
    lesson = s1.number_input("Lesson", min_value=1, max_value=20, value=1, step=1)
    week   = s2.number_input("Week",   min_value=1, max_value=20, value=1, step=1)
    teacher_id = s3.text_input("Teacher ID", value="teacher_001")
    klass = s4.text_input("Class/Section", value="class_A")

    st.write("---")
    st.markdown("**Bloom’s controls**")
    mode = st.radio("Mode", ["Auto by Focus", "Target level(s)"], horizontal=True)
    if mode == "Auto by Focus":
        count = st.slider("How many MCQs?", 4, 30, 10, 1)
        rng = random.Random(week*100 + lesson)
        blooms = pick_bloom_sequence(rng, count)
    else:
        sel = st.multiselect("Pick Bloom levels (will cycle)", BLOOM_LEVELS, default=["Understand","Apply","Analyze"])
        count = st.slider("How many MCQs?", 4, 30, 10, 1)
        if not sel: sel = ["Understand"]
        blooms = (sel * ((count // len(sel)) + 1))[:count]
    st.write("Sequence preview:", ", ".join(blooms))

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
    src_text = st.session_state.get("src_text","")

    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Generate MCQs", type="primary"):
            if use_ai and have_api():
                with st.spinner("Generating with AI…"):
                    df = ai_generate_mcqs(src_text, lesson, week, blooms, teacher_id, n=len(blooms))
            else:
                with st.spinner("Generating (offline)…"):
                    df = offline_generate_mcqs(src_text, lesson, week, blooms, teacher_id, n=len(blooms))
            st.session_state.mcq_df = df
    with colB:
        if st.button("Generate Activities"):
            rng = random.Random(stable_seed(teacher_id, klass, lesson, week, src_text))
            stems = ["Pair-share on", "Mini-poster:", "Role-play:", "Think–Pair–Share:", "Quick debate:", "Case critique:"]
            base = [s.strip() for s in re.split(r'[.\n]', src_text) if s.strip()] or ["today's topic"]
            acts = [f"{stems[i%len(stems)]} {base[i%len(base)]}" for i in range(10)]
            st.session_state.activities = acts

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
        q = r["Question"].replace("\n", " ")
        options = [r["Option A"], r["Option B"], r["Option C"], r["Option D"]]
        ans_idx = "ABCD".index(r["Answer"])
        gift_opts = []
        for i, opt in enumerate(options):
            opt = opt.replace("}", "\\}")
            gift_opts.append(("=" if i==ans_idx else "~")+opt)
        lines.append("{"+q+"}{"+" ".join(gift_opts)+"}")
    return "\n\n".join(lines)

def activities_docx(activities: List[str]) -> bytes:
    if not Document:
        return b""
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
    df = st.session_state.mcq_df.copy()

    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        if not df.empty:
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button("MCQs CSV", data=csv_bytes, file_name="mcqs.csv", mime="text/csv", use_container_width=True)
    with c2:
        if not df.empty:
            gift_text = to_gift(df)
            st.download_button("MCQs GIFT", data=gift_text.encode("utf-8"),
                               file_name="mcqs.gift.txt", mime="text/plain", use_container_width=True)
    with c3:
        if st.session_state.activities:
            acts_csv = "\n".join(st.session_state.activities).encode("utf-8")
            st.download_button("Activities CSV", data=acts_csv, file_name="activities.csv",
                               mime="text/csv", use_container_width=True)
    with c4:
        if st.session_state.activities:
            if Document:
                doc_bytes = activities_docx(st.session_state.activities)
                st.download_button("Activities DOCX", data=doc_bytes, file_name="activities.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   use_container_width=True)
            else:
                st.info("Install python-docx to enable DOCX export.")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Security: Keep API keys server-side only (env or .streamlit/secrets). Never accept keys via UI.")
