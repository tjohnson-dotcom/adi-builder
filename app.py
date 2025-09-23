# app.py — ADI Builder (polished UI • slim pills • editable MCQs & Activities)
# Run:  streamlit run app.py

from __future__ import annotations
import io
from dataclasses import dataclass, asdict
from typing import List, Dict
import streamlit as st

try:
    from docx import Document
    from docx.shared import Pt
except Exception:
    Document = None  # we’ll gate download buttons if docx is missing

# -------------------------------------------------------
# Page setup
# -------------------------------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ADI palette / light polish
CSS = """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c;
  --adi-stone:#f6f6f3; --adi-border:#dfe5df;
  --pill-bg:#eef4ef; --pill-bg-active:#245a34; --pill-text:#23322a;
}
main .block-container{max-width:1200px;}
.adi-hero{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));
  color:#fff;border-radius:18px;padding:14px 18px;margin:8px 0 18px 0;}
.adi-hero h1{margin:0;font-size:20px;font-weight:800}
.adi-hero small{opacity:.95}

.adi-card{background:#fff;border:1px solid var(--adi-border);border-radius:14px;
  padding:14px;box-shadow:0 6px 16px rgba(0,0,0,.04);}
.adi-subtle{color:#5b665f}

.upload-box{border:2px dashed var(--adi-green); background:var(--pill-bg);
  border-radius:12px; padding:10px 12px}

.pill-row{display:flex;flex-wrap:wrap;gap:8px}
.pill{padding:7px 12px;border-radius:999px;border:1px solid var(--adi-border);
  background:#fff;color:var(--pill-text);cursor:pointer;font-weight:600}
.pill:hover{background:var(--pill-bg)}
.pill.active{background:var(--pill-bg-active); border-color:var(--pill-bg-active); color:#fff}

div.stButton>button{background:var(--adi-green); color:#fff; border:none;
  border-radius:999px; padding:.6rem 1rem; font-weight:700}
div.stButton>button:hover{filter:brightness(.97)}

textarea, input, .stTextInput input, .stTextArea textarea{
  border:2px solid var(--adi-green) !important; border-radius:10px !important;
}
textarea:focus, .stTextInput input:focus{box-shadow:0 0 0 3px rgba(36,90,52,.2) !important}
hr{border:none;border-top:1px solid var(--adi-border);margin:12px 0}
.small{font-size:12px}
.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:var(--pill-bg);border:1px solid var(--adi-border);font-weight:600}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

with st.container():
    st.markdown(
        """
        <div class="adi-hero">
          <h1>ADI Builder – Lesson Activities & Questions</h1>
          <small>Professional, branded, editable, and export-ready.</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------------
# Helpers (state, pills, exports, generation)
# -------------------------------------------------------

def init_state():
    ss = st.session_state
    ss.setdefault("tab", "MCQs")
    ss.setdefault("lesson", 1)
    ss.setdefault("week", 1)
    ss.setdefault("mcq_blocks", 3)     # blocks ×3 questions
    ss.setdefault("mcq_data", [])      # list[str] (each block text)
    ss.setdefault("act_count", 3)
    ss.setdefault("act_duration", 45)
    ss.setdefault("acts", [])          # list[Activity]
init_state()

def pill_row(label: str, choices: List[int|str], key: str, value) -> int|str:
    st.caption(label)
    current = st.session_state.get(key, value)
    cols = st.columns(len(choices))
    for i, c in enumerate(choices):
        text = str(c)
        active = (current == c)
        with cols[i]:
            if st.button(text, key=f"{key}_{i}", help=text,
                         type="secondary",
                         use_container_width=True):
                current = c
        # enable CSS “active” look
        st.markdown(
            f"""
            <script>
            const btns = window.parent.document.querySelectorAll('button[k="{key}_{i}"]');
            if (btns.length) {{
               btns[0].classList.add('pill');
               {'btns[0].classList.add("active");' if active else ''}
            }}
            </script>
            """,
            unsafe_allow_html=True,
        )
    st.session_state[key] = current
    return current

def bloom_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    return "High"

def generate_mcq_block(topic: str, source: str, tier: str, index: int) -> str:
    # Simple templates teachers can edit immediately
    low = [
        f"Define the key term related to **{topic}**.",
        f"Identify one core principle of **{topic}** and give a brief example.",
        f"List three facts drawn from the source."
    ]
    med = [
        f"Apply the principle of **{topic}** to a short scenario of your choosing.",
        "Demonstrate understanding by paraphrasing the main idea in two sentences.",
        "Solve a simple case: what would be your first step and why?"
    ]
    high = [
        "Evaluate two approaches and justify the stronger one.",
        f"Synthesize: combine two ideas from the source to propose a new guideline for **{topic}**.",
        "Design: outline a 3-step plan that meets the stated constraints."
    ]
    bank = {"Low": low, "Medium": med, "High": high}[tier]
    # Return block text (three questions separated by blank lines)
    return "\n\n".join(bank)

@dataclass
class Activity:
    tier: str
    title: str
    objective: str
    steps: str
    materials: str
    assessment: str

def generate_activity(tier: str, idx: int, topic: str, duration: int) -> Activity:
    return Activity(
        tier=tier,
        title=f"Module: Activity {idx}",
        objective=f"Students will {('recall/apply' if tier!='High' else 'analyze/design')} key skills of {topic}.",
        steps=f"1) Briefing (5m)\n2) Main task ({duration-10}m)\n3) Share-out (5m)",
        materials="Projector, handout, whiteboard",
        assessment="Participation rubric; short reflective note"
    )

def word_doc_from_text_blocks(title: str, blocks: List[str]) -> io.BytesIO:
    if Document is None:
        return io.BytesIO()
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(11)
    doc.add_heading(title, level=1)
    for i, b in enumerate(blocks, start=1):
        doc.add_heading(f"Block {i}", level=2)
        for q in b.split("\n"):
            doc.add_paragraph(q)
    buf = io.BytesIO(); doc.save(buf); buf.seek(0); return buf

def word_doc_from_activities(acts: List[Activity]) -> io.BytesIO:
    if Document is None:
        return io.BytesIO()
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(11)
    doc.add_heading("Activity Plan", level=1)
    for i, a in enumerate(acts, start=1):
        doc.add_heading(f"Activity {i} — {a.title}", level=2)
        doc.add_paragraph(f"Tier: {a.tier}")
        doc.add_paragraph(f"Objective: {a.objective}")
        doc.add_paragraph("Steps:"); doc.add_paragraph(a.steps)
        doc.add_paragraph(f"Materials: {a.materials}")
        doc.add_paragraph(f"Assessment: {a.assessment}")
    buf = io.BytesIO(); doc.save(buf); buf.seek(0); return buf

def gift_from_mcqs(blocks: List[str]) -> io.BytesIO:
    # Very basic “short answer” GIFT-like export (teachers can refine)
    lines = []
    idx = 1
    for block in blocks:
        for q in block.split("\n"):
            q_clean = q.strip()
            if not q_clean: continue
            lines.append(f"::Q{idx}:: {q_clean} {{}}")
            idx += 1
    data = "\n".join(lines).encode("utf-8")
    return io.BytesIO(data)

def csv_from_activities(acts: List[Activity]) -> io.BytesIO:
    import csv
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(asdict(acts[0]).keys()))
    writer.writeheader()
    for a in acts:
        writer.writerow(asdict(a))
    return io.BytesIO(buf.getvalue().encode("utf-8"))

# -------------------------------------------------------
# Tabs
# -------------------------------------------------------
tab_mcq, tab_act = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

# ======================== MCQs TAB ======================
with tab_mcq:
    left, right = st.columns([0.95, 2.05], gap="large")

    with left:
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.subheader("Upload eBook / Lesson Plan / PPT", divider=False)
        st.caption("Accepted: PDF · DOCX · PPTX (≤200 MB)")
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        file = st.file_uploader("Drag & drop or Browse", type=["pdf","docx","pptx"], label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        if file is not None:
            # Faux progress so users feel it’s “processing”
            prog = st.progress(0)
            for i in range(1, 101, 20):
                prog.progress(min(i, 100))
            prog.empty()
            st.success(f"Loaded: {file.name}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.subheader("Pick from eBook / Plan / PPT", divider=False)
        lesson = pill_row("Lesson", [1,2,3,4,5,6], "lesson", st.session_state.lesson)
        week   = pill_row("Week",   [1,2,3,4,5,6,7,8,9,10,11,12,13,14], "week", st.session_state.week)
        focus = bloom_for_week(int(week))
        st.caption(f"ADI policy → Bloom focus for Week {week}:  **{focus}**")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.subheader("Activity Parameters", divider=False)
        st.number_input("Number of activities", min_value=1, max_value=10, step=1, key="act_count")
        st.number_input("Duration (mins, per activity)", min_value=10, max_value=120, step=5, key="act_duration")
        st.caption("Bloom tiers used for MCQs:  Low → Medium → High (policy-driven).")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="adi-card">', unsafe_allow_html=True)
        st.subheader("Generate MCQs — Policy Blocks (Low → Medium → High)", divider=False)

        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source = st.text_area("Source text (optional, editable)", height=120, placeholder="Paste or edit source text here...")

        st.caption("How many MCQ blocks? (×3 questions per block)")
        # quick picks + numeric
        quick = pill_row("Quick pick", [1,2,3,5,10], "mcq_blocks", st.session_state.mcq_blocks)
        mcq_blocks = st.number_input("Or enter blocks manually", min_value=1, max_value=20, step=1, value=int(quick))

        if st.button("Generate MCQ Blocks", type="primary"):
            st.session_state.mcq_blocks = int(mcq_blocks)
            focus = bloom_for_week(int(st.session_state.week))
            blocks = []
            # 1/3 low, 1/3 med, 1/3 high (or focus if you prefer force)
            tiers = ["Low","Medium","High"]
            for i in range(st.session_state.mcq_blocks):
                tier = tiers[i % 3] if focus not in tiers else focus  # keep it simple: all focus
                blocks.append(generate_mcq_block(topic or "your topic", source or "", tier, i+1))
            st.session_state.mcq_data = blocks

        # Editable blocks
        if st.session_state.mcq_data:
            st.divider()
            st.subheader("Preview & Edit")
            new_blocks = []
            for i, blk in enumerate(st.session_state.mcq_data, start=1):
                txt = st.text_area(f"Block {i}", blk, height=150, key=f"mcq_block_{i}")
                new_blocks.append(txt)
            st.session_state.mcq_data = new_blocks

            colD1, colD2 = st.columns(2)
            with colD1:
                if Document is None:
                    st.info("Install `python-docx` to enable Word export.")
                else:
                    buf = word_doc_from_text_blocks("MCQs", st.session_state.mcq_data)
                    st.download_button("Download Word (.docx)", buf, file_name=f"adi_mcqs_w{st.session_state.week}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            with colD2:
                gift = gift_from_mcqs(st.session_state.mcq_data)
                st.download_button("Download Moodle GIFT", gift, file_name=f"adi_mcqs_w{st.session_state.week}.gift", mime="text/plain", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ===================== ACTIVITIES TAB ====================
with tab_act:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.subheader("Generate Activities", divider=False)
    st.caption("Pick parameters on the left; Bloom focus follows ADI policy.")
    if st.button("Generate Activity Plan"):
        tier = bloom_for_week(int(st.session_state.week))
        topic_guess = st.session_state.get("last_topic", "") or "Module"
        acts = []
        for i in range(1, st.session_state.act_count + 1):
            acts.append(generate_activity(tier, i, topic_guess, int(st.session_state.act_duration)))
        st.session_state.acts = acts

    # Editable table-like blocks
    if st.session_state.acts:
        st.divider()
        st.subheader("Preview & Edit")
        edited: List[Activity] = []
        for i, a in enumerate(st.session_state.acts, start=1):
            with st.expander(f"Activity {i}: {a.title}", expanded=(i==1)):
                tier_v = st.selectbox("Tier", ["Low","Medium","High"], index=["Low","Medium","High"].index(a.tier), key=f"act_tier_{i}")
                title_v = st.text_input("Title", a.title, key=f"act_title_{i}")
                obj_v = st.text_area("Objective", a.objective, key=f"act_obj_{i}")
                steps_v = st.text_area("Steps", a.steps, key=f"act_steps_{i}")
                mat_v = st.text_input("Materials", a.materials, key=f"act_mat_{i}")
                assess_v = st.text_input("Assessment", a.assessment, key=f"act_assess_{i}")
                edited.append(Activity(tier_v, title_v, obj_v, steps_v, mat_v, assess_v))
        st.session_state.acts = edited

        c1, c2 = st.columns(2)
        with c1:
            if Document is None:
                st.info("Install `python-docx` to enable Word export.")
            else:
                bufA = word_doc_from_activities(st.session_state.acts)
                st.download_button("Download Word (.docx)", bufA, file_name=f"adi_activities_w{st.session_state.week}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with c2:
            csvb = csv_from_activities(st.session_state.acts)
            st.download_button("Download CSV", csvb, file_name=f"adi_activities_w{st.session_state.week}.csv", mime="text/csv", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
