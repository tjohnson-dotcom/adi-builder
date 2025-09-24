import io
from typing import Any

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

# ----------------------------- Page & ONE CSS block -----------------------------
st.set_page_config(
    page_title="ADI Builder v3",
    page_icon="📚",
    layout="wide",
)

ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
ADI_STONE = "#F5F3EF"  # subtle background

st.markdown(
    f"""
    <style>
    /* ====== ADI style v14 ====== */
    :root {{
        --adi-green: {ADI_GREEN};
        --adi-gold: {ADI_GOLD};
        --adi-stone: {ADI_STONE};
        --adi-charcoal: #2a2a2a;
        --adi-brown: #6B5845;
    }}

    /* Page background and base text */
    .stApp {{ background: var(--adi-stone); color: var(--adi-charcoal); }}

    /* Sidebar section headers */
    section[data-testid="stSidebar"] h2 {{
        font-size: 0.9rem !important; text-transform: uppercase; letter-spacing: .08em;
        margin-top: 1.2rem; margin-bottom: .4rem; padding: .2rem .4rem;
        background: rgba(36,90,52,.08); border-left: 4px solid var(--adi-green); border-radius: .25rem;
    }}

    /* Inputs: bold numbers, pale background, green borders */
    .stNumberInput input, .stTextInput input, .stTextArea textarea {{
        background: white; border: 1.5px solid rgba(36,90,52,.35); border-radius: .6rem; font-weight: 600;
    }}
    .stNumberInput input:focus, .stTextInput input:focus, .stTextArea textarea:focus {{
        outline: none; box-shadow: 0 0 0 3px rgba(36,90,52,.25);
        border-color: var(--adi-green);
    }}

    /* Quick pick block: gold outline */
    .adi-quickpick {{ border: 2px solid var(--adi-gold); border-radius: 1rem; padding: .75rem; background: rgba(200,168,90,.07); }}

    /* Tabs: use pills with ADI gold underline for active */
    .stTabs [data-baseweb="tab-list"] {{ gap: .25rem; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 999px; padding: .35rem .9rem; font-weight: 600; background: white; border: 1px solid rgba(0,0,0,.06);
    }}
    .stTabs [aria-selected="true"] {{
        border-color: var(--adi-gold); box-shadow: 0 2px 0 0 var(--adi-gold) inset;
    }}

    /* Radio/checkbox sizing */
    label[data-testid="stMarkdownContainer"] p {{ margin-bottom: .35rem; }}

    /* Bloom tier headings */
    .bloom-low h4 {{ color: var(--adi-green); }}
    .bloom-med h4 {{ color: var(--adi-brown); }}
    .bloom-high h4 {{ color: #111; }}

    /* Tiny badge to confirm CSS loaded */
    .adi-badge {{
        position: fixed; top: 10px; right: 12px; z-index: 9999; background: var(--adi-green); color: white;
        padding: 6px 10px; border-radius: 999px; font-size: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.15);
    }}
    </style>
    <div class="adi-badge">ADI style v14</div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Helpers -----------------------------
def _fallback(val: str | None, default: str) -> str:
    return (val or "").strip() or default

# ----------------------------- Smarter parsing -----------------------------
def extract_text_from_upload(up_file) -> str:
    """
    Extracts a compact, clean snippet from PDF/DOCX/PPTX to seed the source box.
    - Normalizes whitespace
    - Keeps headings / bullet-like lines
    - Truncates to ~2k chars for editing
    """
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
        # collapse multiple newlines, trim long runs of spaces
        lines = [ln.strip() for ln in text.split("\n")]
        lines = [ln for ln in lines if ln]
        text = "\n".join(lines)
        return text[:2000]
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ----------------------------- Tiny NLP (no external libs) -----------------------------
_STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","as","is","are","be","was","were",
    "this","that","these","those","it","its","at","from","into","over","under","about","between","within",
    "use","used","using","also","than","which","such","may","can","could","should","would","will","not",
    "if","when","while","after","before","each","per","via","more","most","less","least","other","another"
}

def _sentences(text: str) -> list[str]:
    # Split on full stops / line breaks; keep short slides as individual “sentences”.
    rough = []
    for chunk in text.split("\n"):
        parts = [p.strip() for p in chunk.replace("•", ". ").replace("–", "-").split(".")]
        for p in parts:
            if p:
                rough.append(p)
    # de-dup tiny fragments
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
    rand = random.Random(42)  # deterministic so export stable
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

# ----------------------------- Generators -----------------------------
def generate_mcq_blocks(topic: str, source: str, num_blocks: int, week: int) -> pd.DataFrame:
    """
    Builds MCQs that actually reference your text:
    - Pulls key terms and sentences from the source
    - Low: recall/identify
    - Medium: apply/analyze
    - High: evaluate/create
    Keeps the same schema your export expects.
    """
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
    """Structured, printable activities with Objectives, Steps (timed), Materials, Assessment."""
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

# ----------------------------- Exporters -----------------------------
def df_to_docx_mcqs(df: pd.DataFrame) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument()
    doc.add_heading("ADI MCQs", level=1)
    block_no = None
    for _, r in df.iterrows():
        if block_no != r["Block"]:
            block_no = r["Block"]
            doc.add_heading(f"Block {int(block_no)}", level=2)
        doc.add_paragraph(f"Tier: {r['Tier']}")
        doc.add_paragraph(r["Question"]).bold = True
        for label in ["A","B","C","D"]:
            doc.add_paragraph(f"{label}. {r[f'Option {label}']}")
        doc.add_paragraph(f"Answer: {r['Answer']}")
        doc.add_paragraph(f"Explanation: {r['Explanation']}")
        doc.add_paragraph("")
    f = io.BytesIO()
    doc.save(f)
    return f.getvalue()


def df_to_docx_activities(df: pd.DataFrame) -> bytes:
    if DocxDocument is None:
        raise RuntimeError("python-docx not installed")
    doc = DocxDocument()
    doc.add_heading("ADI Activities", level=1)
    for _, r in df.iterrows():
        doc.add_heading(r["Title"], level=2)
        doc.add_paragraph(f"Tier: {r['Tier']}")
        doc.add_paragraph(f"Objective: {r['Objective']}")
        doc.add_paragraph(f"Steps: {r['Steps']}")
        doc.add_paragraph(f"Materials: {r['Materials']}")
        doc.add_paragraph(f"Assessment: {r['Assessment']}")
        doc.add_paragraph(f"Duration: {r['Duration (mins)']} minutes")
        doc.add_paragraph("")
    f = io.BytesIO()
    doc.save(f)
    return f.getvalue()

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.header("Upload")
    up = st.file_uploader("Upload PPTX / PDF / DOCX", type=["pptx","pdf","docx"])

    st.header("Course Context")
    course = st.text_input("Course / Program", "Applied Digital Intelligence")
    module = st.text_input("Module / Topic", "Introduction to AI Ethics")

    colA, colB = st.columns(2)
    with colA:
        lesson = st.number_input("Lesson", 1, 5, 1)
    with colB:
        week = st.number_input("Week", 1, 14, 1)

    st.header("Quick Picks")
    with st.container():
        st.markdown('<div class="adi-quickpick">', unsafe_allow_html=True)
        st.write("Pick emphasis & counts")
        col1, col2, col3 = st.columns(3)
        with col1:
            num_blocks = st.number_input("MCQ Blocks", 1, 10, 3)
        with col2:
            act_count = st.number_input("Activities", 1, 8, 3)
        with col3:
            duration = st.number_input("Duration (mins)", 15, 120, 45, step=5)
        st.markdown('</div>', unsafe_allow_html=True)

    # Bloom policy mapping (Weeks 1–4 Low, 5–9 Medium, 10–14 High)
    if week <= 4:
        default_tier = "Low"
    elif week <= 9:
        default_tier = "Medium"
    else:
        default_tier = "High"

    st.header("Bloom Emphasis")
    tier = st.radio("Select tier (auto-suggested by week)", ["Low","Medium","High"], index=["Low","Medium","High"].index(default_tier), horizontal=True)

    st.caption("Policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High (auto-suggest applied)")

# ----------------------------- Main layout -----------------------------
left, right = st.columns([0.48, 0.52])

with left:
    st.subheader("Source Preview")
    extracted = extract_text_from_upload(up)
    src_text = st.text_area("Editable source (mined from upload)", value=extracted, height=220)

    st.subheader("Generate")
    gen_mcq = st.button("Generate MCQs", type="primary")
    gen_act = st.button("Generate Activities", type="secondary")

with right:
    tabs = st.tabs(["Knowledge MCQs (ADI Policy)", "Activities"])

    with tabs[0]:
        st.markdown("<div class='bloom-low'><h4>MCQs</h4></div>", unsafe_allow_html=True)
        if 'mcq_df' not in st.session_state:
            st.session_state.mcq_df = None
        if gen_mcq:
            st.session_state.mcq_df = generate_mcq_blocks(module, src_text, int(num_blocks), int(week))
        if st.session_state.mcq_df is not None:
            st.dataframe(st.session_state.mcq_df, use_container_width=True)
            csv = st.session_state.mcq_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download MCQs (CSV)", csv, file_name="adi_mcqs.csv", mime="text/csv")
            try:
                docx_bytes = df_to_docx_mcqs(st.session_state.mcq_df)
                st.download_button("Download MCQs (DOCX)", docx_bytes, file_name="adi_mcqs.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            except Exception as e:
                st.info(f"DOCX export unavailable: {e}")
        else:
            st.write("⬅️ Upload a file and click **Generate MCQs**.")

    with tabs[1]:
        st.markdown("<div class='bloom-med'><h4>Activities</h4></div>", unsafe_allow_html=True)
        if 'act_df' not in st.session_state:
            st.session_state.act_df = None
        if gen_act:
            st.session_state.act_df = generate_activities(int(act_count), int(duration), tier, module)
        if st.session_state.act_df is not None:
            st.dataframe(st.session_state.act_df, use_container_width=True)
            csv2 = st.session_state.act_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Activities (CSV)", csv2, file_name="adi_activities.csv", mime="text/csv")
            try:
                docx_bytes2 = df_to_docx_activities(st.session_state.act_df)
                st.download_button("Download Activities (DOCX)", docx_bytes2, file_name="adi_activities.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            except Exception as e:
                st.info(f"DOCX export unavailable: {e}")
        else:
            st.write("⬅️ Set counts and click **Generate Activities**.")

# ----------------------------- Hints -----------------------------
st.divider()
st.markdown(
    f"""
    **Tips**  
    • If styles look default (small grey text, default radios), use **Rerun and Clear Cache** in the menu and hard-refresh (Ctrl/Cmd+Shift+R).  
    • Look for the green **ADI style v14** badge (top-right) to confirm the CSS loaded.  
    • Gold underline on the active tab indicates the correct theme.  
    • Bloom auto-suggestion by week can be overridden any time.
    """
)
