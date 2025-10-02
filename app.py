# app.py
# Streamlit ADI Builder — Lesson Activities & Questions
# Requirements: streamlit, python-docx
#    pip install streamlit python-docx

from io import BytesIO
import random
import re
from datetime import datetime
from textwrap import dedent

import streamlit as st
from docx import Document
from docx.shared import Pt, Inches

# ------------------------------
# ADI THEME + CSS (no red accents)
# ------------------------------
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", layout="wide")

ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"
ADI_STONE = "#e5e1da"
BG_STONE = "#f9f9f7"

st.markdown(
    f"""
    <style>
      /* Page background + font smoothing */
      .stApp {{ background: {BG_STONE}; }}
      html, body, [class*="css"] {{ -webkit-font-smoothing: antialiased; }}

      /* Header card */
      .adi-hero {{
        background: {ADI_GREEN};
        color: white;
        border-radius: 18px;
        padding: 18px 22px;
        box-shadow: 0 6px 18px rgba(0,0,0,.10);
      }}
      .adi-subtle {{ opacity: .9; font-size: 13px; }}

      /* Cards */
      .adi-card {{
        background: white;
        border-radius: 16px;
        border: 1px solid rgba(0,0,0,.06);
        box-shadow: 0 4px 14px rgba(0,0,0,.05);
        padding: 16px;
        margin-bottom: 14px;
      }}

      /* Tabs (underline in ADI gold) */
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-bottom: 3px solid {ADI_GOLD} !important;
        color: {ADI_GREEN} !important;
      }}
      .stTabs [data-baseweb="tab-list"] button {{ gap: 6px; }}

      /* Pills: we use buttons styled as pills */
      .pill-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
      .pill {{
        background: #f3f2ef;
        border: 1px solid #d9d5cd;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 14px;
        cursor: pointer;
        user-select: none;
      }}
      .pill.low    {{ background: #eef6f0; border-color: #d7e6db; }}
      .pill.medium {{ background: #fbf7ec; border-color: #ecdfc3; }}
      .pill.high   {{ background: #f2f1fd; border-color: #dcdaf4; }}

      .pill.active {{
        background: {ADI_GREEN} !important;
        color: white !important;
        border-color: {ADI_GREEN} !important;
      }}

      /* MultiSelect “tags” (in case you use it anywhere) */
      .stMultiSelect div[data-baseweb="tag"] {{
        background-color: {ADI_GREEN} !important;
        color: white !important;
        border-radius: 20px !important;
        padding: 2px 8px !important;
      }}

      /* Buttons */
      .stButton>button {{
        border-radius: 12px;
        padding: 8px 14px;
      }}

      /* Sidebar tweaks */
      section[data-testid="stSidebar"] {{
        background: white;
        border-right: 1px solid #ece9e1;
      }}

      /* Small help text */
      .muted {{ color: #666; font-size: 12px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# Helpers
# ------------------------------
LOW_VERBS = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

POLICY_MAP = {
    "Low": LOW_VERBS,
    "Medium": MED_VERBS,
    "High": HIGH_VERBS,
}

def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    if 5 <= week <= 9:
        return "Medium"
    return "High"

def extract_key_terms(text: str, max_terms: int = 12):
    # naive keyword-ish extractor: pick capitalized words and frequent nouns
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text)
    # prefer capitalized and longer words
    scored = {}
    for w in words:
        wl = w.lower()
        score = (2 if w[0].isupper() else 0) + min(len(w), 12) / 3
        scored[wl] = scored.get(wl, 0) + score
    # filter common words
    stop = set("the a an and or for with from by to of on in at is are were was be as it its this that these those which".split())
    scored = {k: v for k, v in scored.items() if k not in stop}
    candidates = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
    return [w for w, _ in candidates[:max_terms]]

def sentence_split(text: str):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 25]

def make_mcq_from_sentence(sent: str, terms: list[str]) -> dict:
    """Create a simple MCQ by blanking a key term or phrase and offering distractors."""
    t_hits = [t for t in terms if re.search(rf"\\b{re.escape(t)}\\b", sent, flags=re.I)]
    if not t_hits:
        # fallback: pick a long-ish word
        words = re.findall(r"[A-Za-z][A-Za-z\-]{4,}", sent)
        focus = random.choice(words) if words else "concept"
    else:
        focus = max(t_hits, key=len)

    stem = re.sub(rf"\\b{re.escape(focus)}\\b", "_____", sent, flags=re.I, count=1)

    # Build distractors
    pool = [t for t in terms if t.lower() != focus.lower()]
    random.shuffle(pool)
    distractors = pool[:3]
    while len(distractors) < 3:
        distractors.append(focus[::-1])  # trivial filler if needed

    options = distractors + [focus]
    random.shuffle(options)
    correct_index = options.index(focus)

    return {"stem": stem, "options": options, "answer": correct_index, "answer_text": focus}

def generate_mcqs(source_text: str, n: int, verbs_selected: list[str]):
    sentences = sentence_split(source_text)
    if not sentences:
        sentences = [source_text.strip()]
    terms = extract_key_terms(source_text, max_terms=20)
    random.shuffle(sentences)

    items = []
    for s in sentences[: max(3, n * 2)]:  # skim more sentences than needed
        q = make_mcq_from_sentence(s, terms)
        items.append(q)

    # keep N and attach a Bloom verb randomly (from selected)
    out = []
    if not verbs_selected:
        verbs_selected = LOW_VERBS  # safe default
    for i, q in enumerate(items[:n], start=1):
        verb = random.choice(verbs_selected)
        out.append({**q, "bloom": verb, "index": i})
    return out

def mcqs_to_docx(mcqs: list[dict], topic: str, lesson: int, week: int) -> bytes:
    doc = Document()
    styles = doc.styles["Normal"]
    styles.font.name = "Calibri"
    styles.font.size = Pt(11)

    title = doc.add_paragraph()
    run = title.add_run("ADI Builder — Knowledge MCQs")
    run.bold = True
    run.font.size = Pt(16)

    meta = doc.add_paragraph(f"Topic/Outcome: {topic or '—'}\nLesson {lesson} • Week {week} • Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    meta.paragraph_format.space_after = Pt(8)

    for q in mcqs:
        p = doc.add_paragraph(f"Q{q['index']}. {q['stem']}")
        p.paragraph_format.space_after = Pt(2)
        letters = ["A", "B", "C", "D"]
        for i, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{letters[i]}. {opt}", style=None)
        doc.add_paragraph(f"Answer: {letters[q['answer']]}  (Bloom: {q['bloom']})")
        doc.add_paragraph("")  # spacer

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ------------------------------
# Sidebar (Upload, context, quick picks)
# ------------------------------
with st.sidebar:
    st.markdown("### Upload (optional)")
    upl = st.file_uploader("Drag and drop file here", type=["pdf", "docx", "pptx"], label_visibility="collapsed")
    st.caption("Limit 200MB per file • PDF, DOCX, PPTX")

    st.markdown("---")
    st.markdown("### Course context")

    lesson = st.selectbox("Lesson", options=list(range(1, 6)), index=0)
    week = st.selectbox("Week", options=list(range(1, 15)), index=6)  # default Week 7

    # Quick pick blocks
    st.markdown("---")
    st.markdown("### Quick pick blocks")
    cols = st.columns(5)
    with cols[0]: pick5 = st.checkbox("5", value=True)
    with cols[1]: pick10 = st.checkbox("10", value=False)
    with cols[2]: pick15 = st.checkbox("15", value=False)
    with cols[3]: pick20 = st.checkbox("20", value=False)
    with cols[4]: pick30 = st.checkbox("30", value=False)

    # determine target count
    target_n = 5
    if pick30: target_n = 30
    elif pick20: target_n = 20
    elif pick15: target_n = 15
    elif pick10: target_n = 10
    st.caption(f"Items selected: **{target_n}**")

# ------------------------------
# Header
# ------------------------------
st.markdown(
    """
    <div class="adi-hero">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="background:white;color:#1b3b2a;width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;">ADI</div>
        <div>
          <div style="font-size:18px;font-weight:700;">ADI Builder — Lesson Activities & Questions</div>
          <div class="adi-subtle">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# Tabs
# ------------------------------
tab1, tab2, tab3 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

with tab1:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)

    # Row: Topic & Bloom focus (auto)
    c1, c2 = st.columns([2, 1])
    with c1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with c2:
        auto_focus = bloom_focus_for_week(week)
        st.text_input("Bloom focus (auto)", value=f"Week {week}: {auto_focus}", disabled=True)

    # Source text
    src = st.text_area("Source text (editable)", height=180, placeholder="Paste or jot key notes, vocab, facts here...")

    # (Optional) very simple file text stub
    if upl and not src:
        # Keep this deliberately minimal – we don't parse; just note the filename
        src = f"Notes from uploaded file: {upl.name}. Add your key points here."
        st.info("Upload detected — you can paste or type key points in the box above.")

    st.markdown("#### Bloom’s verbs (ADI Policy)")
    st.caption("Grouped by policy tiers and week ranges")

    # Grouped verb selectors as pill buttons
    # We keep selection state in session_state for toggling
    if "verb_states" not in st.session_state:
        st.session_state.verb_states = {v: False for v in LOW_VERBS + MED_VERBS + HIGH_VERBS}

    # Auto-select tier based on week (but don't override manual toggles after first run)
    if "auto_seeded" not in st.session_state:
        default_tier = auto_focus
        for v in POLICY_MAP[default_tier]:
            st.session_state.verb_states[v] = True
        st.session_state.auto_seeded = True

    def render_pills(tier_label: str, verbs: list[str], css_class: str):
        st.write(f"**{tier_label}**")
        cols = st.columns(6)
        # render in rows using columns
        i = 0
        for v in verbs:
            col = cols[i % 6]
            with col:
                active = st.session_state.verb_states.get(v, False)
                key = f"pill-{v}"
                # Use a button to toggle
                clicked = st.button(
                    v,
                    key=key,
                    use_container_width=True,
                )
                # Apply custom CSS class by writing a marker div we can target – Streamlit doesn't allow class injection on button.
                st.markdown(
                    f"""
                    <script>
                      const root = window.parent.document.querySelector('button[k="{key}"]') || window.parent.document.querySelector('button[data-testid="{key}"]');
                      if (root) {{
                        root.classList.add('pill','{css_class}');
                        {"root.classList.add('active');" if active else "root.classList.remove('active');"}
                      }}
                    </script>
                    """,
                    unsafe_allow_html=True,
                )
                if clicked:
                    st.session_state.verb_states[v] = not active
            i += 1

    render_pills("LOW (Weeks 1–4): Remember / Understand", LOW_VERBS, "low")
    render_pills("MEDIUM (Weeks 5–9): Apply / Analyse", MED_VERBS, "medium")
    render_pills("HIGH (Weeks 10–14): Evaluate / Create", HIGH_VERBS, "high")

    # Tier toggles
    st.write("")
    c_low, c_med, c_high = st.columns(3)
    with c_low:
        if st.button("LOW", use_container_width=True):
            for v in LOW_VERBS:
                st.session_state.verb_states[v] = True
    with c_med:
        if st.button("MEDIUM", use_container_width=True):
            for v in MED_VERBS:
                st.session_state.verb_states[v] = True
    with c_high:
        if st.button("HIGH", use_container_width=True):
            for v in HIGH_VERBS:
                st.session_state.verb_states[v] = True

    st.write("")
    gen = st.button("✨ Generate MCQs", type="primary")

    chosen_verbs = [v for v, on in st.session_state.verb_states.items() if on]

    if gen:
        if not src.strip():
            st.warning("Please paste some source text (key notes, facts, definitions) to generate MCQs.")
        else:
            mcqs = generate_mcqs(src, n=target_n, verbs_selected=chosen_verbs)
            st.session_state["mcqs"] = mcqs

    # Render MCQs if present
    mcqs = st.session_state.get("mcqs", [])
    if mcqs:
        st.markdown("---")
        st.markdown("### Generated MCQs")
        for q in mcqs:
            st.write(f"**Q{q['index']}.** {q['stem']}")
            letters = ["A", "B", "C", "D"]
            for i, opt in enumerate(q["options"]):
                st.write(f"- {letters[i]}. {opt}")
            st.caption(f"Answer: **{letters[q['answer']]}**  •  Bloom: **{q['bloom']}**")

        # Export to Word (first)
        docx_bytes = mcqs_to_docx(mcqs, topic, lesson, week)
        st.download_button(
            "⬇️ Export to Word (DOCX)",
            data=docx_bytes,
            file_name=f"ADI_MCQs_L{lesson}_W{week}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Skills Activities")
    st.caption("Simple templates aligned with ADI policy. (Lightweight placeholders you can edit or export.)")
    activities = [
        ("Think–Pair–Share", "Pose a scenario using your Week focus; learners think alone, discuss in pairs, then share."),
        ("Case Mini-Analysis", "Provide a short case; groups identify problem, propose two actions, justify pick."),
        ("Demonstration & Critique", "Demonstrate a process; learners critique steps using criteria you set.")
    ]
    for i, (name, desc) in enumerate(activities, 1):
        st.write(f"**{i}. {name}** — {desc}")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Revision")
    st.write("• Auto-generate quick recall cards from your source text (copy/paste into your LMS).")
    st.write("• Tip: Use **Quick pick blocks** to change how many items you want.")
    st.markdown('</div>', unsafe_allow_html=True)
