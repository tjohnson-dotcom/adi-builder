# app.py — ADI Builder (polished UI + quick-pick MCQs + pill radios + progress)
# Run:
#   pip install streamlit
#   streamlit run app.py

import os
import time
import base64
import streamlit as st

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ---------- logo (optional) ----------
LOGO_PATH = os.path.join("assets", "adi-logo.png")
logo_data_uri = None
try:
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_data_uri = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
except Exception:
    logo_data_uri = None

# ---------- theme css ----------
ADI_CSS = """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-green-50:#EEF5F0;
  --adi-gold:#C8A85A; --adi-sand:#f8f3e8;
  --adi-ink:#1f2937; --muted:#6b7280; --border:#d9dfda;
  --bg:#FAFAF7; --card:#ffffff; --shadow:0 10px 24px rgba(0,0,0,.06);
  --r:18px; --pill:999px;
}
html,body{background:var(--bg)}
main .block-container{padding-top:1rem; padding-bottom:2rem; max-width:1220px;}

/* header */
.adi-hero{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600)); color:#fff; border-radius:20px; padding:18px 20px; box-shadow:var(--shadow);}
.adi-hero-row{display:flex; align-items:center; gap:16px;}
.logo-box{width:48px; height:48px; border-radius:12px; background:rgba(0,0,0,.08); overflow:hidden; display:flex; align-items:center; justify-content:center;}
.logo-box img{width:100%; height:100%; object-fit:contain;}
.logo-fallback{font-weight:800; font-size:20px;}
.adi-title{font-weight:800; font-size:22px; margin:0;}
.adi-sub{opacity:.92; font-size:12px; margin-top:2px;}

/* tabs */
.adi-tabs [role="radiogroup"]{gap:10px; display:flex; flex-wrap:wrap;}
.adi-tabs [role="radio"]{background:#f3f7f3; border:2px solid var(--adi-green-50); color:var(--adi-green-600);
  border-radius:14px; padding:10px 18px; cursor:pointer; font-weight:600; transition:.2s;}
.adi-tabs [role="radio"]:hover{background:#eaf5ec;}
.adi-tabs [role="radio"][aria-checked="true"]{background:var(--adi-green); color:#fff; border-color:var(--adi-green-600);
  box-shadow:0 6px 14px rgba(36,90,52,.25);}

/* pills radios for Lesson/Week (hide dot) */
.stRadio [role="radiogroup"]{display:flex; gap:8px; flex-wrap:wrap}
.stRadio [role="radio"]{border:1px solid var(--border); border-radius:999px; padding:6px 12px; background:#fff; color:var(--adi-ink); font-weight:700}
.stRadio [role="radio"][aria-checked="true"]{background:var(--adi-green); color:#fff; border-color:var(--adi-green)}
.stRadio [role="radio"] > div:first-child{display:none}  /* hide the small dot */

/* make any remaining dots green (e.g., top mode) */
input[type=radio]{accent-color:var(--adi-green) !important}

/* inputs */
input, textarea, select{border:1px solid var(--border) !important; border-radius:var(--pill) !important;
  background:#f3f1ee !important; padding:.5rem .9rem !important;}
textarea{border-radius:28px !important;}
input:focus, textarea:focus, select:focus{outline:none !important; border-color:var(--adi-green) !important;
  box-shadow:0 0 0 3px rgba(36,90,52,.25) !important; background:#fff !important;}
input::placeholder, textarea::placeholder{color:var(--muted); opacity:.95; font-style:italic; font-weight:500}

/* buttons */
div.stButton>button{background:var(--adi-green); color:#fff; border:none; border-radius:var(--pill);
  padding:.70rem 1.1rem; font-weight:600; box-shadow:0 4px 12px rgba(31,76,44,.22); transition:.25s;}
div.stButton>button:hover{filter:brightness(.97); box-shadow:0 0 0 3px rgba(200,168,90,.45);}
.btn-gold button{background:var(--adi-gold) !important; color:#1f2a1f !important;}
.btn-sand button{background:var(--adi-sand) !important; color:#5a4028 !important;}

/* cards */
.adi-card{background:var(--card); border:1px solid var(--border); border-radius:20px; padding:16px; box-shadow:var(--shadow);}

/* uploader */
.adi-up{border:2px dashed var(--adi-green); background:var(--adi-green-50); border-radius:14px; padding:14px; display:flex; align-items:center; gap:12px}
.adi-up-badge{width:36px; height:36px; border-radius:8px; background:var(--adi-green); color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center}

/* bloom chips */
.pills{display:flex; flex-wrap:wrap; gap:8px}
.pill{padding:6px 12px; border-radius:999px; border:1px solid #e3e7e3; background:#f3f7f3; font-size:13px; color:#25402b}
.pill.low{background:#eaf5ec; color:#1f4c2c} .pill.med{background:#f8f3e8; color:#6a4b2d} .pill.hi{background:#f3f1ee; color:#4a4a45}
.pill.active{box-shadow:0 0 0 3px rgba(36,90,52,.25); border-color:var(--adi-green-600)}

/* mcq quick-pick */
.mcq-picks{display:flex; gap:8px; flex-wrap:wrap}
.mcq-picks button{background:#fff !important; color:var(--adi-ink) !important; border:1px solid var(--border) !important;
  border-radius:999px !important; padding:.35rem .75rem !important; box-shadow:none !important;}
.mcq-picks button:hover{box-shadow:0 0 0 3px rgba(36,90,52,.15) !important}
.mcq-picks .active{background:var(--adi-green) !important; color:#fff !important; border-color:var(--adi-green) !important}

/* slider thumb/track if used later */
.stSlider [data-baseweb="slider"] > div:nth-child(2){background:#e6ebe8}
.stSlider [data-baseweb="slider"] > div:nth-child(2) > div{background:var(--adi-green)}
.stSlider [role="slider"]{background:#fff; border:2px solid var(--adi-green); box-shadow:0 2px 6px rgba(36,90,52,.25)}
</style>
"""
st.markdown(ADI_CSS, unsafe_allow_html=True)

# ---------- header ----------
st.markdown(
    f"""
    <div class="adi-hero">
      <div class="adi-hero-row">
        <div class="logo-box">{('<img src="'+logo_data_uri+'" alt="ADI"/>') if logo_data_uri else '<div class="logo-fallback">A</div>'}</div>
        <div>
          <div class="adi-title">ADI Builder - Lesson Activities & Questions</div>
          <div class="adi-sub">Professional, branded, editable and export-ready.</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- top tabs ----------
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Knowledge MCQs (ADI Policy)"

st.markdown('<div class="adi-tabs">', unsafe_allow_html=True)
tab = st.radio(
    "choose",
    ["Knowledge MCQs (ADI Policy)", "Skills Activities"],
    index=0 if st.session_state.active_tab.startswith("Knowledge") else 1,
    horizontal=True,
    label_visibility="collapsed",
)
st.markdown("</div>", unsafe_allow_html=True)
st.session_state.active_tab = tab

# ---------- layout ----------
left, right = st.columns([0.95, 2.05], gap="large")

# ========== LEFT ==========
with left:
    # upload
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Upload eBook / Lesson Plan / PPT")
    st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
    st.markdown('<div class="adi-up"><div class="adi-up-badge">UP</div><div>', unsafe_allow_html=True)
    file = st.file_uploader("Drag and drop your file", type=["pdf", "docx", "pptx"], label_visibility="collapsed")
    st.markdown("</div></div>", unsafe_allow_html=True)

    if file:
        st.caption(f"**{file.name}** · {file.size/1_000_000:.1f} MB")
        colp1, colp2 = st.columns([1, 2])
        with colp1:
            if st.button("Process upload"):
                prog = st.progress(0, text="Processing…")
                for i in range(0, 101, 5):
                    time.sleep(0.02)
                    prog.progress(i, text=f"Processing… {i}%")
                prog.empty()
                st.success("Upload processed.")
        with colp2:
            st.caption("We recommend eBooks (PDF) as source for best results.")
    else:
        st.caption("We recommend eBooks (PDF) as source for best results.")
    st.markdown("</div>", unsafe_allow_html=True)

    # pick from plan
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Pick from eBook / Plan / PPT")
    c1, c2 = st.columns(2)
    with c1:
        lesson = st.radio("Lesson", [1, 2, 3, 4, 5], horizontal=True, index=0, key="lesson_radio")
    with c2:
        week = st.radio("Week", list(range(1, 15)), horizontal=True, index=0, key="week_radio")

    st.caption("**ADI policy:** Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. The appropriate Bloom tier will be auto-highlighted below.")

    b1, b2 = st.columns(2)
    with b1:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("Pull → MCQs", use_container_width=True, key="pull_mcqs")
        st.markdown('</div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="btn-sand">', unsafe_allow_html=True)
        st.button("Pull → Activities", use_container_width=True, key="pull_acts")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # activity parameters + bloom chips
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Activity Parameters")
    cc1, cc2 = st.columns(2)
    num_acts = cc1.number_input("Activities", min_value=1, value=3, step=1)
    duration = cc2.number_input("Duration (mins)", min_value=5, value=45, step=5)

    # bloom auto-highlight
    tier = "low" if 1 <= week <= 4 else ("med" if 5 <= week <= 9 else "hi")
    st.caption("ADI Bloom tiers used for MCQs:")
    colL, colM, colH = st.columns(3)
    with colL:
        st.markdown("**Low tier**")
        st.markdown('<div class="pills">' + ''.join(
            [f'<span class="pill low {"active" if tier=="low" else ""}">{w}</span>' for w in
             ["define","identify","list","recall","describe","label"]]
        ) + '</div>', unsafe_allow_html=True)
    with colM:
        st.markdown("**Medium tier**")
        st.markdown('<div class="pills">' + ''.join(
            [f'<span class="pill med {"active" if tier=="med" else ""}">{w}</span>' for w in
             ["apply","demonstrate","solve","illustrate"]]
        ) + '</div>', unsafe_allow_html=True)
    with colH:
        st.markdown("**High tier**")
        st.markdown('<div class="pills">' + ''.join(
            [f'<span class="pill hi {"active" if tier=="hi" else ""}">{w}</span>' for w in
             ["evaluate","synthesize","design","justify"]]
        ) + '</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ========== RIGHT ==========
with right:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)

    if st.session_state.active_tab.startswith("Knowledge"):
        st.markdown("### Generate MCQs — Policy Blocks (Low → Medium → High)")
        st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here…")

        # ----- MCQ total with quick picks -----
        st.markdown("#### MCQ Quantity")
        if "mcq_total" not in st.session_state:
            st.session_state.mcq_total = 9

        quick = [5, 10, 15, 20, 25, 30]
        st.write("")  # breathing space
        pick_cols = st.columns(len(quick))
        for i, q in enumerate(quick):
            pressed = pick_cols[i].button(f"{q}", key=f"mcq_qp_{q}")
            # set active style on the one that's current
            if st.session_state.mcq_total == q:
                pick_cols[i].markdown('<div class="mcq-picks"><button class="active">selected</button></div>', unsafe_allow_html=True)
            if pressed:
                st.session_state.mcq_total = q

        mcq_total = st.slider("Total MCQ questions", 5, 30, st.session_state.mcq_total, 1, key="mcq_total_slider")
        st.session_state.mcq_total = mcq_total

        # convert to blocks of 3 (round up)
        mcq_blocks = (mcq_total + 2) // 3
        st.caption(f"{mcq_total} questions → **{mcq_blocks}** policy blocks (3 per block).")

        if st.button("Generate MCQs", key="gen_mcqs"):
            # Placeholder action (hook up your generator here)
            st.success(f"Preparing {mcq_total} MCQs across {mcq_blocks} blocks (Week {week} → {tier.upper()} tier emphasis).")
            # TODO: call your generation pipeline with: file, topic text, source text, week, lesson, mcq_total/mcq_blocks

    else:
        st.markdown("### Build Skills Activities")
        st.selectbox("Activity type", ["Case Study", "Role Play", "Scenario MCQ", "Group Discussion", "Practical Demo"])
        st.text_input("Learning goal", placeholder="What should learners be able to do?")
        st.text_area("Materials / Inputs", height=120, placeholder="Links, readings, slides, equipment…")
        st.number_input("Groups", min_value=1, value=4)
        st.number_input("Duration (mins)", min_value=5, value=30, step=5, key="skill_dur")
        if st.button("Generate Activity Plan", key="gen_acts"):
            st.success("Activity plan generated (placeholder).")
    st.markdown("</div>", unsafe_allow_html=True)

