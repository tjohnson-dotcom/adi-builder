# app.py
# ADI Builder — Lesson Activities & Questions (Streamlit)
# Requirements: streamlit, python-docx
#   pip install streamlit==1.37.1 python-docx==1.1.2

from io import BytesIO
import random
import re
from datetime import datetime

import streamlit as st
from docx import Document
from docx.shared import Pt

# ----------------------------------------------------
# Page setup
# ----------------------------------------------------
st.set_page_config(
    page_title="ADI Builder — Lesson Activities & Questions",
    layout="wide",
)

# ----------------------------------------------------
# Theme & CSS (ADI palette + shaded pills + week badge)
# ----------------------------------------------------
ADI_GREEN = "#245a34"
ADI_GOLD  = "#C8A85A"
ADI_STONE = "#e5e1da"
BG_STONE  = "#f9f9f7"

st.markdown(
    f"""
<style>
  .stApp {{ background: {BG_STONE}; }}
  html, body, [class*="css"] {{ -webkit-font-smoothing: antialiased; }}

  .adi-hero {{
    background: {ADI_GREEN}; color: white; border-radius: 18px;
    padding: 18px 22px; box-shadow: 0 6px 18px rgba(0,0,0,.10);
  }}
  .adi-subtle {{ opacity: .9; font-size: 13px; }}

  .adi-card {{
    background: white; border-radius: 16px; border: 1px solid rgba(0,0,0,.06);
    box-shadow: 0 4px 14px rgba(0,0,0,.05); padding: 16px; margin-bottom: 14px;
  }}

  /* Tabs underline */
  .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
    border-bottom: 3px solid {ADI_GOLD} !important; color: {ADI_GREEN} !important;
  }}

  /* Week badge */
  .week-badge {{
    display:inline-block; padding: 8px 12px; border-radius: 999px;
    font-weight: 600; border: 1px solid #d9d5cd; margin-top: 6px;
  }}
  .week-low    {{ background:#e9f4ec; color:#1c3b2a; border-color:#cfe3d4; }}
  .week-medium {{ background:#fbf3df; color:#3a321b; border-color:#eadbb4; }}
  .week-high   {{ background:#efeefe; color:#2f2b5f; border-color:#d8d6f3; }}

  /* Pills */
  .pill {{
    background:#f3f2ef; border:1px solid #d9d5cd; padding:8px 14px;
    border-radius:999px; font-size:14px; font-weight:600;
  }}
  .pill.low    {{ background:#e9f4ec; border-color:#cfe3d4; }}
  .pill.medium {{ background:#fbf3df; border-color:#eadbb4; }}
  .pill.high   {{ background:#efeefe; border-color:#d8d6f3; }}
  .pill.active {{
    background:{ADI_GREEN} !important; color:white !important; border-color:{ADI_GREEN} !important;
    box-shadow: 0 0 0 2px rgba(36,90,52,.12);
  }}

  /* Buttons default (for LOW/MEDIUM/HIGH row, etc.) */
  .stButton>button {{
    border-radius:999px; border:1px solid #d9d5cd; background:#f3f2ef; color:#1c1c1c;
    padding:8px 14px; font-weight:600;
  }}

  /* Sidebar */
  section[data-testid="stSidebar"] {{
    background: white; border-right: 1px solid #ece9e1;
  }}
  .muted {{ color: #666; font-size: 12px; }}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------
# Helpers
# ----------------------------------------------------
LOW_VERBS = ["define", "identify", "list", "recall", "describe", "label"]
MED_VERBS = ["apply", "demonstrate", "solve", "illustrate", "classify", "compare"]
HIGH_VERBS = ["evaluate", "synthesize", "design", "justify", "critique", "create"]

POLICY_MAP = {"Low": LOW_VERBS, "Medium": MED_VERBS, "High": HIGH_VERBS}

def bloom_focus_for_week(week: int) -> str:
    if 1 <= week <= 4:
        return "Low"
    if 5 <= week <= 9:
        return "Medium"
    return "High"

def extract_key_terms(text: str, max_terms: int = 12):
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text)
    scored = {}
    for w in words:
        wl = w.lower()
        score = (2 if w[0].isupper() else 0) + min(len(w), 12) / 3
        scored[wl] = scored.get(wl, 0) + score
    stop = set("the a an and or for with from by to of on in at is are were was be as it its this that these those which".split())
    scored = {k: v for k, v in scored.items() if k not in stop}
    candidates = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
    return [w for w, _ in candidates[:max_terms]]

def sentence_split(text: str):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 25]

def make_mcq_from_sentence(sent: str, terms: list[str]) -> dict:
    t_hits = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", sent, flags=re.I)]
    if not t_hits:
        words = re.findall(r"[A-Za-z][A-Za-z\-]{4,}", sent)
        focus = random.choice(words) if words else "concept"
    else:
        focus = max(t_hits, key=len)

    stem = re.sub(rf"\b{re.escape(focus)}\b", "_____", sent, flags=re.I, count=1)
    pool = [t for t in terms if t.lower() != focus.lower()]
    random.shuffle(pool)
    distractors = pool[:3]
    while len(distractors) < 3:
        distractors.append(focus[::-1])

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
    for s in sentences[: max(3, n * 2)]:
        q = make_mcq_from_sentence(s, terms)
        items.append(q)

    out = []
    if not verbs_selected:
        verbs_selected = LOW_VERBS
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

    meta = doc.add_paragraph(
        f"Topic/Outcome: {topic or '—'}\n"
        f"Lesson {lesson} • Week {week} • Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    for q in mcqs:
        p = doc.add_paragraph(f"Q{q['index']}. {q['stem']}")
        letters = ["A", "B", "C", "D"]
        for i, opt in enumerate(q["options"]):
            doc.add_paragraph(f"{letters[i]}. {opt}")
        doc.add_paragraph(f"Answer: {letters[q['answer']]}  (Bloom: {q['bloom']})")
        doc.add_paragraph("")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ----------------------------------------------------
# Sidebar (flicker-free uploader + context + picks)
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### Upload (optional)")

    if "uploaded_file_bytes" not in st.session_state:
        st.session_state.uploaded_file_bytes = None
        st.session_state.uploaded_filename = None

    # Put the uploader in a form to prevent auto re-runs while uploading
    with st.form("upload_form"):
        upl = st.file_uploader(
            "Drag and drop file here",
            type=["pdf", "docx", "pptx"],
            label_visibility="collapsed",
            accept_multiple_files=False,
        )
        submitted = st.form_submit_button("Add file")

    if submitted and upl is not None:
        st.session_state.uploaded_file_bytes = upl.getvalue()
        st.session_state.uploaded_filename = upl.name
        st.success(f"Added: {upl.name}")

    if st.session_state.uploaded_file_bytes:
        st.caption(f"Loaded: **{st.session_state.uploaded_filename}**")
    else:
        st.caption("Limit 200MB per file • PDF, DOCX, PPTX")

    st.markdown("---")
    st.markdown("### Course context")
    lesson = st.selectbox("Lesson", options=list(range(1, 6)), index=0)
    week = st.selectbox("Week", options=list(range(1, 15)), index=6)

    st.markdown("---")
    st.markdown("### Quick pick blocks")
    cols = st.columns(5)
    with cols[0]: pick5 = st.checkbox("5", value=True)
    with cols[1]: pick10 = st.checkbox("10", value=False)
    with cols[2]: pick15 = st.checkbox("15", value=False)
    with cols[3]: pick20 = st.checkbox("20", value=False)
    with cols[4]: pick30 = st.checkbox("30", value=False)

    target_n = 5
    if pick30: target_n = 30
    elif pick20: target_n = 20
    elif pick15: target_n = 15
    elif pick10: target_n = 10
    st.caption(f"Items selected: **{target_n}**")

# ----------------------------------------------------
# Header
# ----------------------------------------------------
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

# ----------------------------------------------------
# Tabs
# ----------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

with tab1:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)

    # Row: Topic + Bloom focus badge
    c1, c2 = st.columns([2, 1])
    with c1:
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
    with c2:
        auto_focus = bloom_focus_for_week(week)
        badge_cls = {"Low": "week-low", "Medium": "week-medium", "High": "week-high"}[auto_focus]
        st.markdown("**Bloom focus (auto)**")
        st.markdown(
            f'<span class="week-badge {badge_cls}">Week {week}: {auto_focus}</span>',
            unsafe_allow_html=True,
        )

    # Source text
    src = st.text_area("Source text (editable)", height=180, placeholder="Paste or jot key notes, vocab, facts here...")

    # Seed text area once after upload (no heavy parsing to keep it snappy)
    if st.session_state.uploaded_file_bytes and not src.strip():
        st.info(f"Upload detected — **{st.session_state.uploaded_filename}**. Add your key points below.")

    st.markdown("#### Bloom’s verbs (ADI Policy)")
    st.caption("Grouped by policy tiers and week ranges")

    # Verb selection state
    if "verb_states" not in st.session_state:
        st.session_state.verb_states = {v: False for v in LOW_VERBS + MED_VERBS + HIGH_VERBS}
        st.session_state.auto_seeded = False

    # Auto-seed once per session based on current week
    if not st.session_state.auto_seeded:
        for v in POLICY_MAP[auto_focus]:
            st.session_state.verb_states[v] = True
        st.session_state.auto_seeded = True

    def render_pills(tier_label: str, verbs: list[str], css_class: str):
        st.write(f"**{tier_label}**")
        cols = st.columns(6)
        for i, v in enumerate(verbs):
            col = cols[i % 6]
            with col:
                active = st.session_state.verb_states.get(v, False)
                key = f"pill-{v}"
                clicked = st.button(v, key=key, use_container_width=True)
                if clicked:
                    st.session_state.verb_states[v] = not active
                # Class toggle (lightweight, once per render)
                st.markdown(
                    f"""
                    <script>
                      const btn = window.parent.document.querySelector('button[k="{key}"]')
                               || window.parent.document.querySelector('button[data-testid="{key}"]');
                      if (btn) {{
                        btn.classList.add('pill','{css_class}');
                        {"btn.classList.add('active');" if active else "btn.classList.remove('active');"}
                      }}
                    </script>
                    """,
                    unsafe_allow_html=True,
                )

    render_pills("LOW (Weeks 1–4): Remember / Understand", LOW_VERBS, "low")
    render_pills("MEDIUM (Weeks 5–9): Apply / Analyse", MED_VERBS, "medium")
    render_pills("HIGH (Weeks 10–14): Evaluate / Create", HIGH_VERBS, "high")

    st.write("")
    c_low, c_med, c_high = st.columns(3)
    with c_low:
        if st.button("LOW", use_container_width=True):
            for v in LOW_VERBS: st.session_state.verb_states[v] = True
    with c_med:
        if st.button("MEDIUM", use_container_width=True):
            for v in MED_VERBS: st.session_state.verb_states[v] = True
    with c_high:
        if st.button("HIGH", use_container_width=True):
            for v in HIGH_VERBS: st.session_state.verb_states[v] = True

    st.write("")
    gen = st.button("✨ Generate MCQs", type="primary")

    chosen_verbs = [v for v, on in st.session_state.verb_states.items() if on]

    if gen:
        if not src.strip():
            st.warning("Please paste some source text (key notes, facts, definitions) to generate MCQs.")
        else:
            st.session_state["mcqs"] = generate_mcqs(src, n=target_n, verbs_selected=chosen_verbs)

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

