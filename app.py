# app.py — ADI Builder (Streamlined Left Sidebar, ADI-branded, working tabs)
# Run:  pip install streamlit
#       streamlit run app.py

import base64
import os
import streamlit as st

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ------------------------ Logo Embed ------------------------
LOGO_PATH = os.path.join("assets", "adi-logo.png")  # place your PNG here
logo_data_uri = None
try:
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_data_uri = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
except Exception:
    logo_data_uri = None

# ------------------------ Theme CSS -------------------------
ADI_CSS = f"""
<style>
:root{{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-green-50:#EEF5F0;
  --adi-gold:#C8A85A; --adi-stone:#f3f1ee; --adi-stone-text:#4a4a45;
  --adi-sand:#f8f3e8; --adi-sand-text:#6a4b2d; --adi-ink:#1f2937; --adi-muted:#6b7280;
  --bg:#FAFAF7; --card:#ffffff; --border:#d9dfda; --shadow:0 10px 24px rgba(0,0,0,.06);
  --radius:18px; --radius-pill:999px;
}}
html,body{{background:var(--bg)}}
main .block-container{{padding-top:1rem; padding-bottom:2rem; max-width:1220px;}}

/* Header */
.adi-hero{{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600)); color:#fff; border-radius:20px; padding:18px 20px; box-shadow:var(--shadow);}}
.adi-hero-row{{display:flex; align-items:center; gap:16px;}}
.logo-box{{width:48px; height:48px; border-radius:12px; background:rgba(0,0,0,.08); overflow:hidden; display:flex; align-items:center; justify-content:center;}}
.logo-box img{{width:100%; height:100%; object-fit:contain;}}
.logo-fallback{{font-weight:800; font-size:20px;}}
.adi-title{{font-weight:800; font-size:22px; margin:0;}}
.adi-sub{{opacity:.92; font-size:12px; margin-top:2px;}}

/* Prominent Tabs */
.adi-tabs [role="radiogroup"]{{ gap:10px; display:flex; flex-wrap:wrap; }}
.adi-tabs label{{ background:#e9efe9; border:1px solid #c9d7cb; color:#204A2C; border-radius:14px; padding:10px 16px; cursor:pointer; box-shadow:0 2px 6px rgba(0,0,0,.04); font-weight:600; }}
.adi-tabs label[aria-checked="true"]{{ background:#ffffff; border-color:#b9ccb9; box-shadow:0 8px 18px rgba(0,0,0,.07); }}

/* Layout */
.grid{{display:grid; grid-template-columns: 340px 1fr; gap:20px; margin-top:12px;}}
.sidebar{{max-width:340px;}}

/* Cards - STRAPLINED (compact) */
.adi-card{{ background:var(--card); border:1px solid var(--border); border-radius:16px; box-shadow:var(--shadow); padding:12px 12px; }}
.adi-card h3{{ margin:0 0 8px 0; color:var(--adi-green); font-size:12px; text-transform:uppercase; letter-spacing:.05em; }}
.adi-card .tight{{ margin-top:8px; }}

/* Upload */
.adi-upload{{ border:2px dashed var(--adi-green); background:var(--adi-green-50); border-radius:14px; padding:12px; display:flex; gap:10px; align-items:center; }}
.adi-upload .icon{{ width:28px; height:28px; border-radius:7px; background:var(--adi-green); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; }}
.adi-upload small{{ color:var(--adi-muted) }}

/* Inputs */
input, textarea{{ border-radius:12px !important; }}
div[data-baseweb="input"] input{{ border-radius:var(--radius-pill); }}

/* Pills */
.pills{{ display:flex; flex-wrap:wrap; gap:8px; }}
.pill{{ padding:6px 10px; border-radius:999px; border:1px solid #e3e7e3; background:#f3f7f3; font-size:12px; color:#25402b; }}
.pill.low{{ background:#eaf5ec; color:#1f4c2c; }}
.pill.med{{ background:var(--adi-sand); color:var(--adi-sand-text); }}
.pill.hi{{ background:var(--adi-stone); color:var(--adi-stone-text); }}

/* Buttons */
div.stButton>button{{ background:var(--adi-green); color:#fff; border:none; border-radius:var(--radius-pill); padding:.55rem .9rem; font-weight:600; box-shadow:0 4px 12px rgba(31,76,44,.22); }}
.btn-gold button{{ background:var(--adi-gold) !important; color:#1f2a1f !important; box-shadow:0 4px 12px rgba(200,168,90,.32) !important; }}

/* Small buttons in a row */
.btn-row{{ display:flex; gap:8px; }}

/* Stepper aesthetics */
.step-row{{ display:flex; align-items:center; gap:10px; }}
.stepper{{ display:inline-flex; align-items:center; border:1px solid #cbd5cb; border-radius:999px; overflow:hidden; background:#fff; }}
.stepper button{{ border:none; background:#fff; padding:6px 10px; cursor:pointer; }}
.stepper input{{ width:54px; border:none; text-align:center; padding:8px 6px; }}

</style>
"""

st.markdown(ADI_CSS, unsafe_allow_html=True)

# ------------------------ Header ------------------------
with st.container():
    st.markdown(
        f"""
        <div class="adi-hero">
          <div class="adi-hero-row">
            <div class="logo-box">{('<img src="' + logo_data_uri + '" alt="ADI"/>') if logo_data_uri else '<div class="logo-fallback">A</div>'}</div>
            <div>
              <div class="adi-title">ADI Builder - Lesson Activities & Questions</div>
              <div class="adi-sub">Professional, branded, editable and export-ready.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------ Tabs (working + prominent) ------------------------
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Knowledge MCQs (ADI Policy)"

with st.container():
    st.markdown('<div class="adi-tabs">', unsafe_allow_html=True)
    tab_choice = st.radio(
        label="choose",
        options=["Knowledge MCQs (ADI Policy)", "Skills Activities"],
        index=0 if st.session_state.active_tab.startswith("Knowledge") else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="adi_tabs_radio",
    )
    st.session_state.active_tab = tab_choice
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------ Grid ------------------------
left, right = st.columns([0.88, 2.12], gap="large")

# ------------------------ LEFT (straplined) ------------------------
with left:
    st.markdown('<div class="sidebar">', unsafe_allow_html=True)

    # Upload
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Upload eBook / Lesson Plan / PPT")
    st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
    st.markdown(
        '<div class="adi-upload"><div class="icon">UP</div>'
        '<div><strong>Drag and drop</strong> your file here, or <u>Browse</u><br>'
        '<small>We recommend eBooks (PDF) as source for best results.</small></div></div>',
        unsafe_allow_html=True,
    )
    st.file_uploader(" ", type=["pdf", "docx", "pptx"], label_visibility="collapsed", key="file")
    st.markdown('</div>', unsafe_allow_html=True)

    # Pick from source
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Pick from eBook / Plan / PPT")
    c1, c2 = st.columns(2)
    c1.selectbox("Lesson", options=["—", "1", "2", "3", "4"], index=0, key="lesson")
    c2.selectbox("Week", options=["—", "1", "2", "3", "4", "5", "6", "7", "8"], index=0, key="week")
    st.markdown('<div class="btn-row mt-8">', unsafe_allow_html=True)
    colb1, colb2 = st.columns(2)
    with colb1:
        st.button("Pull → MCQs", use_container_width=True, key="pull_mcq")
    with colb2:
        st.button("Pull → Activities", use_container_width=True, key="pull_act")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Activity params + Bloom
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Activity Parameters")
    cc1, cc2 = st.columns(2)
    cc1.number_input("Activities", min_value=1, value=3, step=1, key="acts")
    cc2.number_input("Duration (mins)", min_value=5, value=45, step=5, key="dur")
    st.caption("ADI Bloom tiers used for MCQs:")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Low tier**")
        st.markdown('<div class="pills">' + ''.join([f'<span class="pill low">{w}</span>' for w in ["define","identify","list","recall","describe","label"]]) + '</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown("**Medium tier**")
        st.markdown('<div class="pills">' + ''.join([f'<span class="pill med">{w}</span>' for w in ["apply","demonstrate","solve","illustrate"]]) + '</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown("**High tier**")
        st.markdown('<div class="pills">' + ''.join([f'<span class="pill hi">{w}</span>' for w in ["evaluate","synthesize","design","justify"]]) + '</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # /sidebar

# ------------------------ RIGHT (changes with tab) ------------------------
with right:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)

    if st.session_state.active_tab.startswith("Knowledge"):
        st.markdown("### Generate MCQs - Policy Blocks (Low → Medium → High)")
        topic = st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        source = st.text_area("Source text (optional, editable)", height=160, placeholder="Paste or edit source text here...")
        st.markdown('<div class="step-row">', unsafe_allow_html=True)
        st.caption("How many MCQ blocks? (×3 questions)")
        blocks = st.number_input(label="", min_value=1, value=1, step=1, key="mcq_blocks")
        st.markdown('</div>', unsafe_allow_html=True)
        st.button("Generate MCQ Blocks")

    else:
        st.markdown("### Build Skills Activities")
        act_type = st.selectbox("Activity type", ["Case Study", "Role Play", "Scenario MCQ", "Group Discussion", "Practical Demo"])
        goal = st.text_input("Learning goal", placeholder="What should learners be able to do?")
        materials = st.text_area("Materials / Inputs", height=120, placeholder="Links, readings, slides, equipment...")
        outcols = st.columns(2)
        with outcols[0]:
            groups = st.number_input("Groups", min_value=1, value=4)
        with outcols[1]:
            time = st.number_input("Duration (mins)", min_value=5, value=30, step=5, key="skill_dur")
        st.button("Generate Activity Plan", key="gen_act")

    st.markdown('</div>', unsafe_allow_html=True)

