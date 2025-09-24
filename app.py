import base64
import io
import os
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

# Optional parsers (install in your env):
#   pip install python-docx python-pptx PyPDF2
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    from docx import Document
    from pptx import Presentation
except Exception:
    Document = None
    Presentation = None

# ----------------------------- Page setup -----------------------------
st.set_page_config(
    page_title="ADI Builder",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGO_PATH = "logo.png"

def _read_logo_data_uri(path: str) -> str | None:
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass
    return None

logo_uri = _read_logo_data_uri(LOGO_PATH)

# ----------------------------- ONE CSS block (polished UI + gold underline) -----------------------------
ADI_CSS = """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-gold:#C8A85A;
  --ink:#1f2937; --muted:#6b7280; --bg:#F7F7F4; --card:#ffffff; --border:#E3E8E3;
  --shadow:0 12px 28px rgba(0,0,0,.07);
}
html,body{background:var(--bg);} main .block-container{max-width:1180px; padding-top:0.6rem}

/* HERO */
.adi-hero{display:flex; align-items:center; gap:14px; padding:18px 20px; border-radius:22px; color:#fff;
  background:linear-gradient(95deg,var(--adi-green),var(--adi-green-600)); box-shadow:var(--shadow); margin-bottom:14px}
.logo{width:48px;height:48px;border-radius:12px;background:rgba(0,0,0,.12);display:flex;align-items:center;justify-content:center;overflow:hidden}
.logo img{width:100%;height:100%;object-fit:contain}
.h-title{font-size:22px;font-weight:800;margin:0}
.h-sub{font-size:12px;opacity:.95;margin:2px 0 0 0}

/* SIDEBAR (elegant) */
section[data-testid='stSidebar']>div{background:#F3F2ED; height:100%}
.side-card{background:#fff; border:1px solid var(--border); border-radius:16px; padding:12px 12px 14px; margin:12px 6px; box-shadow:var(--shadow)}
.side-cap{display:flex; align-items:center; gap:8px; font-size:12px; color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; margin:0 0 8px}
.side-cap .dot{width:8px;height:8px;border-radius:999px;background:var(--adi-gold); box-shadow:0 0 0 3px rgba(200,168,90,.15)}
.rule{height:2px; background:linear-gradient(90deg,var(--adi-gold),transparent); border:0; margin:6px 0 12px}

/* prettier uploader */
div[data-testid="stFileUploaderDropzone"]{border-radius:14px; border:1px dashed #cfd6cf; background:#ffffff}
div[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--adi-green); box-shadow:0 0 0 3px rgba(36,90,52,.12)}

/* CARDS (main area) */
.card{background:var(--card); border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow); padding:16px; margin:10px 0}
.cap{color:var(--adi-green); text-transform:uppercase; letter-spacing:.06em; font-size:12px; margin:0 0 10px}

/* INPUTS */
.stTextArea textarea, .stTextInput input{border:2px solid var(--adi-green)!important; border-radius:12px!important}
.stTextArea textarea:focus, .stTextInput input:focus{box-shadow:0 0 0 3px rgba(36,90,52,.18)!important}

/* BUTTONS */
div.stButton>button{background:var(--adi-green); color:#fff; border:none; border-radius:999px; padding:.6rem 1.1rem; font-weight:700; box-shadow:0 8px 18px rgba(31,76,44,.25)}
div.stButton>button:hover{filter:brightness(.98); box-shadow:0 0 0 3px rgba(200,168,90,.35)}

/* TABS */
[data-testid='stTabs'] button{font-weight:700; color:#445; border-bottom:3px solid transparent}
[data-testid='stTabs'] button[aria-selected='true']{color:var(--adi-green)!important; border-bottom:3px solid var(--adi-gold)!important}

/* BLOOM badges */
.badge{display:inline-flex; align-items:center; justify-content:center; padding:6px 10px; border-radius:999px; border:1px solid var(--border); margin:2px 6px 2px 0; font-weight:600}
.low{background:#eaf5ec; color:#245a34}
.med{background:#f8f3e8; color:#6a4b2d}
.high{background:#f3f1ee; color:#4a4a45}
.active-glow{box-shadow:0 0 0 3px rgba(36,90,52,.25)}
.active-amber{box-shadow:0 0 0 3px rgba(200,168,90,.35)}
.active-gray{box-shadow:0 0 0 3px rgba(120,120,120,.25)}

/* DOWNLOAD STRIP */
.dl-row{display:flex; gap:10px; flex-wrap:wrap}

/* Badge to confirm CSS loaded */
.adi-badge{position:fixed;top:10px;right:12px;z-index:9999;background:var(--adi-green);color:#fff;padding:6px 10px;border-radius:999px;font-size:12px;box-shadow:0 2px 10px rgba(0,0,0,.15)}
</style>
<div class='adi-badge'>ADI style v14</div>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# ----------------------------- State/consts -----------------------------
def ensure_state():
    ss = st.session_state
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("mcq_blocks", 10)
    ss.setdefault("mcq_df", None)
    ss.setdefault("act_df", None)
    ss.setdefault("upload_text", "")

ensure_state()

LOW_VERBS = ["define","identify","list","recall","describe","label"]
MED_VERBS = ["apply","demonstrate","solve","illustrate"]
HIGH_VERBS = ["evaluate","synthesize","design","justify"]

# ----------------------------- Utilities -----------------------------
def _fallback(text:str|None, default:str)->str:
    return text.strip() if text and str(text).strip() else default

def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# ----------------------------- Smarter parsing -----------------------------

def extract_text_from_upload(up_file) -> str:
    """Extracts compact, clean text from PDF/DOCX/PPTX for seeding the source box."""
    if up_file is None:
        return ""
    name = up_file.name.lower()
    text = ""
    try:
        if name.endswith(".pdf") and PdfReader:
            reader = PdfReader(up_file)
            for page in reader.pages[:10]:
                txt = page.extract_text() or ""
                text += txt + "\n"
        elif name.endswith(".docx") and Document:
            doc = Document(up_file)
            for p in doc.paragraphs[:150]:
                text += (p.text or "") + "\n"
        elif name.endswith(".pptx") and Presentation:
            prs = Presentation(up_file)
            for slide in prs.slides[:30]:
                for shp in slide.shapes:
                    if hasattr(shp, "text") and shp.text:
                        text += shp.text + "\n"
        # tidy
        text = text.replace("\r", "\n")
        lines = [ln.strip() for ln in text.split("\n")]
        lines = [ln for ln in lines if ln]
        return "\n".join(lines)[:2000]
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ----------------------------- Tiny NLP helpers (no external libs) -----------------------------
_STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","as","is","are","be","was","were",
    "this","that","these","those","it","its","at","from","into","over","under","about","between","within",
    "use","used","using","also","than","which","such","may","can","could","should","would","will","not",
    "if","when","while","after","before","each","per","via","more","most","less","least","other","another"
}

def _sentences(text: str) -> list[str]:
    rough = []
    for chunk in text.split("\n"):
        parts = [p.strip() for p in chunk.replace("•", ". ").replace("–", "-").split(".")]
        for p in parts:
            if p:
                rough.append(p)
    out = []
    seen = set()
    for s in rough:
        k = s.lower()
        if len(s) >= 30 and k not in seen:
            out.append(s)
            seen.add(k)
    return out[:80]

def _keywords(text: str, top_n: int = 20) -> list[str]:
    from collections import Counter
    tokens = []
    for w in text.replace("/", " ").replace("-", " ").replace(",", " ").replace(".", " ").split():
        w = "".join(ch for ch in w if ch.isalnum()).lower()
        if len(w) >= 4 and w not in _STOP:
            tokens.append(w)
    common = Counter(tokens).most_common(top_n * 2)
    roots = []
    for w, _ in common:
        if all(not w.startswith(r[:5]) and not r.startswith(w[:5]) for r in roots):
            roots.append(w)
        if len(roots) >= top_n:
            break
    return roots

def _find_sentence_with(term: str, sentences: list[str]) -> str | None:
    term_l = term.lower()
    for s in sentences:
        if term_l in s.lower():
            return s.strip()
    return None

def _distractors(correct: str, pool: list[str], n: int) -> list[str]:
    import random
    rand = random.Random(42)
    ckey = correct.lower()[:60]
    cands = [p for p in pool if p and p.lower()[:60] != ckey and p.lower() != correct.lower()]
    rand.shuffle(cands)
    out = []
    for s in cands:
        short = s.strip()
        if 25 <= len(short) <= 130 and short not in out:
            out.append(short)
        if len(out) == n:
            break
    filler = [
        "None of the above statements is accurate in this context.",
        "The statement is incomplete and misses a key constraint.",
        "This describes a different concept and does not apply here."
    ]
    i = 0
    while len(out) < n:
        out.append(filler[i % len(filler)])
        i += 1
    return out

# ----------------------------- SMART Generators (topic-aware) -----------------------------

def generate_mcq_blocks(topic: str, source: str, num_blocks: int, week: int) -> pd.DataFrame:
    """Build MCQs that reference your text (Low/Medium/High per block)."""
    topic = _fallback(topic, "Module")
    src = _fallback(source, "")
    sents = _sentences(src) or [f"{topic} covers core concepts, key steps, and typical pitfalls."]
    keys  = _keywords(src or topic, top_n=max(12, num_blocks)) or ["principles","process","safety","quality"]

    rows: list[dict[str, Any]] = []

    def add_mcq(block: int, tier: str, question: str, options: list[str], correct_index: int):
        rows.append({
            "Block": block,
            "Tier": tier,
            "Question": question.strip(),
            "Option A": options[0], "Option B": options[1], "Option C": options[2], "Option D": options[3],
            "Answer": ["A","B","C","D"][correct_index],
            "Explanation": "Chosen option aligns best with the definition/context in the source.",
        })

    import random
    rnd = random.Random(123)
    pool = sents[:]

    for b in range(1, num_blocks + 1):
        # LOW
        term = keys[(b - 1) % len(keys)]
        sent = _find_sentence_with(term, sents) or f"{term.capitalize()} is a key element related to {topic}."
        correct = sent if len(sent) <= 140 else sent[:137] + "…"
        distracts = _distractors(correct, pool, 3)
        q_low = f"Which statement best describes **{term}** in the context of *{topic}*?"
        opts = distracts + [correct]
        rnd.shuffle(opts)
        add_mcq(b, "Low", q_low, opts, opts.index(correct))

        # MEDIUM
        term2 = keys[(b + 3) % len(keys)]
        base = _find_sentence_with(term2, sents) or f"When applying {term2} in {topic}, which action is most appropriate?"
        scenario = f"A learner is working on **{topic}**. Which action best applies **{term2}**?"
        correct2 = base if len(base) <= 130 else base[:127] + "…"
        distracts2 = _distractors(correct2, pool, 3)
        opts2 = distracts2 + [correct2]; rnd.shuffle(opts2)
        add_mcq(b, "Medium", scenario, opts2, opts2.index(correct2))

        # HIGH
        term3 = keys[(b + 6) % len(keys)]
        base3 = _find_sentence_with(term3, sents) or f"An effective approach to {term3} in {topic} prioritizes evidence and constraints."
        prompt = f"Which option provides the **best justification/implication** regarding **{term3}** for *{topic}*?"
        correct3 = base3 if len(base3) <= 130 else base3[:127] + "…"
        distracts3 = _distractors(correct3, pool, 3)
        opts3 = distracts3 + [correct3]; rnd.shuffle(opts3)
        add_mcq(b, "High", prompt, opts3, opts3.index(correct3))

    return pd.DataFrame(rows)


def generate_activities(count: int, duration: int, tier: str, topic: str) -> pd.DataFrame:
    """Structured activities with Objective, timed Steps, Materials, Assessment."""
    topic = _fallback(topic, "the module")
    verbs = {
        "Low":    ["identify", "list", "describe", "recall"],
        "Medium": ["apply", "demonstrate", "analyze", "solve"],
        "High":   ["evaluate", "synthesize", "design", "justify"],
    }[tier]

    rows = []
    for i in range(1, count + 1):
        v = verbs[(i - 1) % len(verbs)]
        t1 = max(5, int(duration * 0.2))
        t2 = max(10, int(duration * 0.5))
        t3 = max(5, duration - (t1 + t2))
        steps = [
            f"Starter ({t1}m): {v.capitalize()} prior knowledge of {topic} using a quick think-pair-share.",
            f"Main ({t2}m): In small groups, {v} a case/task related to {topic}; capture outcomes on a mini-whiteboard.",
            f"Plenary ({t3}m): Share, compare and refine answers; agree success criteria.",
        ]
        rows.append({
            "Tier": tier,
            "Title": f"{tier} Activity {i}",
            "Objective": f"Students will {v} key ideas from {topic}.",
            "Steps": " ".join(steps),
            "Materials": "Slides/board, markers, handouts (optional), timer",
            "Assessment": "Observe group work, check exemplars; quick exit ticket (1–2 prompts).",
            "Duration (mins)": duration,
        })
    return pd.DataFrame(rows)

# ----------------------------- Exporters (DOCX, CSV, GIFT) -----------------------------

def df_to_docx_mcqs(df: pd.DataFrame, topic: str) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument(); doc.add_heading(f"ADI MCQs — {topic}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    p = doc.add_paragraph("Each block: Low → Medium → High"); p.runs[0].italic = True
    for b in sorted(df["Block"].unique()):
        doc.add_heading(f"Block {b}", 2)
        for _, r in df[df["Block"] == b].iterrows():
            pr = doc.add_paragraph().add_run(f"[{r['Tier']}] {r['Question']}"); pr.bold = True
            doc.add_paragraph(f"A. {r['Option A']}")
            doc.add_paragraph(f"B. {r['Option B']}")
            doc.add_paragraph(f"C. {r['Option C']}")
            doc.add_paragraph(f"D. {r['Option D']}")
            doc.add_paragraph(f"Answer: {r['Answer']}")
            doc.add_paragraph(f"Explanation: {r['Explanation']}")
            doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()


def mcq_to_gift(df: pd.DataFrame, topic: str) -> bytes:
    lines = [f"// ADI MCQs — {topic}", f"// Exported {datetime.now():%Y-%m-%d %H:%M}", ""]
    for i, row in df.reset_index(drop=True).iterrows():
        qname = f"Block{row['Block']}-{row['Tier']}-{i+1}"
        stem = row['Question'].replace("\n", " ").strip()
        opts = [row['Option A'], row['Option B'], row['Option C'], row['Option D']]
        ans_idx = {"A":0, "B":1, "C":2, "D":3}.get(row['Answer'].strip().upper(), 0)
        def esc(s): return s.replace('{','\\{').replace('}','\\}')
        lines.append(f"::{qname}:: {esc(stem)} {{")
        for j, o in enumerate(opts):
            lines.append(f"={esc(o)}" if j == ans_idx else f"~{esc(o)}")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO(); df.to_csv(bio, index=False); return bio.getvalue()


def df_to_docx_activities(df: pd.DataFrame, topic: str) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument(); doc.add_heading(f"ADI Activities — {topic}", 1)
    doc.add_paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    for _, r in df.iterrows():
        doc.add_heading(r['Title'], 2)
        doc.add_paragraph(f"Tier: {r['Tier']}")
        doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph(f"Steps: {r['Steps']}")
        doc.add_paragraph(f"Materials: {r['Materials']}")
        doc.add_paragraph(f"Assessment: {r['Assessment']}")
        doc.add_paragraph(f"Duration: {r['Duration (mins)']} mins")
        doc.add_paragraph("")
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

# ----------------------------- Header -----------------------------
with st.container():
    st.markdown(
        f"""
        <div class='adi-hero'>
          <div class='logo'>{('<img src="'+logo_uri+'" alt="ADI"/>') if logo_uri else 'ADI'}</div>
          <div>
            <div class='h-title'>ADI Builder — Lesson Activities & Questions</div>
            <div class='h-sub'>Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    # Upload
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>UPLOAD (OPTIONAL)</div><hr class='rule'/>", unsafe_allow_html=True)
        up_file = st.file_uploader(
            "Choose a file",
            type=["pdf","docx","pptx"],
            label_visibility="collapsed",
            help="Drop an eBook, lesson plan, or PPT to prefill Source text."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Course context
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>COURSE CONTEXT</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.lesson = st.selectbox("Lesson", list(range(1,7)), index=st.session_state.lesson-1)
        st.session_state.week = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1)
        bloom = bloom_focus_for_week(st.session_state.week)
        st.markdown(
            f"<span class='policy-chip'><span class='pill'></span> Week {st.session_state.week} • <strong>{bloom}</strong> focus</span>"
            "<div style='font-size:11px;color:#6b7280;margin-top:6px'>ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High.</div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # MCQ blocks
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>KNOWLEDGE MCQs (ADI POLICY)</div><hr class='rule'/>", unsafe_allow_html=True)
        pick = st.radio(
            "Quick pick blocks", [5,10,20,30],
            horizontal=True,
            index=[5,10,20,30].index(st.session_state.mcq_blocks) if st.session_state.mcq_blocks in [5,10,20,30] else 1,
        )
        st.session_state.mcq_blocks = pick
        st.markdown("</div>", unsafe_allow_html=True)

    # Activities refs
    with st.container():
        st.markdown("<div class='side-card'><div class='side-cap'><span class='dot'></span>SKILLS ACTIVITIES</div><hr class='rule'/>", unsafe_allow_html=True)
        st.session_state.setdefault("ref_act_n",3)
        st.session_state.setdefault("ref_act_d",45)
        st.session_state.ref_act_n = st.number_input("Activities count", min_value=1, value=st.session_state.ref_act_n, step=1)
        st.session_state.ref_act_d = st.number_input("Duration (mins)", min_value=5, value=st.session_state.ref_act_d, step=5)
        st.markdown("</div>", unsafe_allow_html=True)

    # Parse upload after UI so spinner doesn't block
    if up_file:
        st.session_state.upload_text = extract_text_from_upload(up_file)

# ----------------------------- Tabs -----------------------------
mcq_tab, act_tab = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

with mcq_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>MCQ Generator</p>", unsafe_allow_html=True)
    col1, col2 = st.columns([1,1])
    with col1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with col2:
        st.text_input("Bloom focus (auto)", value=f"Week {st.session_state.week}: {bloom}", disabled=True)

    source = st.text_area("Source text (editable)", value=st.session_state.upload_text, height=160)

    # Bloom legend with policy highlight
    st.markdown("**Bloom’s verbs (ADI Policy)**")
    low_class = "badge low " + ("active-glow" if bloom=="Low" else "")
    med_class = "badge med " + ("active-amber" if bloom=="Medium" else "")
    high_class = "badge high " + ("active-gray" if bloom=="High" else "")
    st.markdown(" ".join([f"<span class='{low_class}'>{w}</span>" for w in LOW_VERBS]), unsafe_allow_html=True)
    st.markdown(" ".join([f"<span class='{med_class}'>{w}</span>" for w in MED_VERBS]), unsafe_allow_html=True)
    st.markdown(" ".join([f"<span class='{high_class}'>{w}</span>" for w in HIGH_VERBS]), unsafe_allow_html=True)

    if st.button("Generate MCQ Blocks"):
        with st.spinner("Building MCQ blocks…"):
            st.session_state.mcq_df = generate_mcq_blocks(topic, source, int(st.session_state.mcq_blocks), int(st.session_state.week))

    if st.session_state.mcq_df is None:
        st.info("No MCQs yet. Use the button above to generate.")
    else:
        edited = st.data_editor(st.session_state.mcq_df, num_rows="dynamic", use_container_width=True, key="mcq_editor")
        st.session_state.mcq_df = edited
        st.markdown("<div class='dl-row'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", df_to_docx_mcqs(edited, _fallback(topic,"Module")),
                           file_name="adi_mcqs.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download Moodle (GIFT)", mcq_to_gift(edited, _fallback(topic,"Module")),
                           file_name="adi_mcqs_gift.txt", mime="text/plain")
        st.download_button("Download CSV", df_to_csv_bytes(edited),
                           file_name="adi_mcqs.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with act_tab:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='cap'>Activities Planner</p>", unsafe_allow_html=True)
    default_idx = ["Low","Medium","High"].index(bloom if bloom in ["Low","Medium","High"] else "Medium")
    tier = st.radio("Emphasis", ["Low","Medium","High"], horizontal=True, index=default_idx)
    topic2 = st.text_input("Topic (optional)", value="", placeholder="Module or unit focus")

    if st.button("Generate Activities"):
        with st.spinner("Assembling activities…"):
            st.session_state.act_df = generate_activities(int(st.session_state.ref_act_n), int(st.session_state.ref_act_d), tier, topic2)

    if st.session_state.act_df is None:
        st.info("No activities yet. Use the button above to generate.")
    else:
        act_edit = st.data_editor(st.session_state.act_df, num_rows="dynamic", use_container_width=True, key="act_editor")
        st.session_state.act_df = act_edit
        st.markdown("<div class='dl-row'>", unsafe_allow_html=True)
        st.download_button("Download Word (.docx)", df_to_docx_activities(act_edit, _fallback(topic2,"Module")),
                           file_name="adi_activities.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download CSV", df_to_csv_bytes(act_edit),
                           file_name="adi_activities.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- Tips -----------------------------
st.divider()
st.markdown(
    """
    **Tips**  
    • If styles ever look default, use **Rerun and Clear Cache** and hard-refresh (Ctrl/Cmd+Shift+R).  
    • Look for the green **ADI style v14** badge (top-right) to confirm CSS loaded.  
    • Gold underline on the active tab indicates the correct theme.  
    """
)
