# app.py — ADI Builder (stable CSS block, pill inputs, policy legend, Bloom auto‑highlight)
# Run:  pip install streamlit
#       streamlit run app.py

import base64
import os
import streamlit as st

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# ------------------------ Logo (optional) ------------------------
LOGO_PATH = os.path.join("assets", "adi-logo.png")
logo_data_uri = None
try:
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_data_uri = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
except Exception:
    logo_data_uri = None

# ------------------------ THEME CSS (keep entire block INSIDE this string) ------------------------
ADI_CSS = """
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-green-50:#EEF5F0;
  --adi-gold:#C8A85A; --adi-sand:#f8f3e8; --adi-sand-text:#6a4b2d;
  --adi-stone:#f3f1ee; --adi-stone-text:#4a4a45;
  --adi-ink:#1f2937; --adi-muted:#6b7280;
  --bg:#FAFAF7; --card:#ffffff; --border:#d9dfda;
  --shadow:0 10px 24px rgba(0,0,0,.06);
  --radius:18px; --radius-pill:999px;
}
html,body{background:var(--bg)}
main .block-container{padding-top:1rem; padding-bottom:2rem; max-width:1220px;}

/* Header */
.adi-hero{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600)); color:#fff; border-radius:20px; padding:18px 20px; box-shadow:var(--shadow);} 
.adi-hero-row{display:flex; align-items:center; gap:16px;} 
.logo-box{width:48px; height:48px; border-radius:12px; background:rgba(0,0,0,.08); overflow:hidden; display:flex; align-items:center; justify-content:center;} 
.logo-box img{width:100%; height:100%; object-fit:contain;} 
.logo-fallback{font-weight:800; font-size:20px;} 
.adi-title{font-weight:800; font-size:22px; margin:0;} 
.adi-sub{opacity:.92; font-size:12px; margin-top:2px;}

/* Tabs */
.adi-tabs [role=\"radiogroup\"]{ gap:10px; display:flex; flex-wrap:wrap; }
.adi-tabs label{ background:#f3f7f3; border:2px solid var(--adi-green-50); color:var(--adi-green-600); border-radius:14px; padding:10px 18px; cursor:pointer; font-weight:600; transition:all .2s; }
.adi-tabs label:hover{ background:#eaf5ec; }
.adi-tabs label[aria-checked=\"true\"]{ background:var(--adi-green); color:#fff; border-color:var(--adi-green-600); box-shadow:0 6px 14px rgba(36,90,52,.25); }

/* Force radio dots to ADI green */
input[type=radio], .stRadio input[type=radio], [role=\"radiogroup\"] input[type=radio]{ accent-color: var(--adi-green) !important; }
.stRadio [role=\"radio\"]:focus-visible{ outline:2px solid var(--adi-gold); outline-offset:2px; }

/* Inputs pill style (stone bg, green glow on focus) */
input, textarea, select{ border:1px solid var(--border) !important; border-radius:var(--radius-pill) !important; background:var(--adi-stone) !important; padding:.5rem .9rem !important; }
textarea{ border-radius:28px !important; }
input:hover, textarea:hover, select:hover{ box-shadow:0 0 0 2px rgba(36,90,52,.10); }
input:focus, textarea:focus, select:focus{ outline:none !important; border-color:var(--adi-green) !important; box-shadow:0 0 0 3px rgba(36,90,52,.25) !important; background:#fff !important; }

/* Streamlit selectbox (BaseWeb) pill style to prevent red outline */
.stSelectbox [data-baseweb="select"] > div{
  border-radius: var(--radius-pill) !important;
  border: 1px solid var(--border) !important;
  background: var(--adi-stone) !important;
  box-shadow: none !important;
}
.stSelectbox [data-baseweb="select"] > div:focus-within{
  outline: none !important;
  border-color: var(--adi-green) !important;
  box-shadow: 0 0 0 3px rgba(36,90,52,.25) !important;
}
.stSelectbox [data-baseweb="select"] div[aria-expanded="true"]{
  border-color: var(--adi-green) !important;
}

/* Number inputs wrapper for consistent pill style */
.stNumberInput > div{
  border-radius: var(--radius-pill) !important;
  border: 1px solid var(--border) !important;
  background: var(--adi-stone) !important;
}
.stNumberInput > div:focus-within{
  border-color: var(--adi-green) !important;
  box-shadow: 0 0 0 3px rgba(36,90,52,.25) !important;
}

/* Placeholders readable */
input::placeholder, textarea::placeholder{ color: var(--adi-muted); opacity:.95; font-style:italic; font-weight:500; }

/* Pills */
.pills{ display:flex; flex-wrap:wrap; gap:8px; }
.pill{ padding:6px 12px; border-radius:999px; border:1px solid #e3e7e3; background:#f3f7f3; font-size:13px; color:#25402b; }
.pill.low{ background:#eaf5ec; color:#1f4c2c; }
.pill.med{ background:var(--adi-sand); color:var(--adi-sand-text); }
.pill.hi{ background:var(--adi-stone); color:var(--adi-stone-text); }
.pill.active{ box-shadow:0 0 0 3px rgba(36,90,52,.25); border-color:var(--adi-green-600); }

/* Buttons */
div.stButton>button{ background:var(--adi-green); color:#fff; border:none; border-radius:var(--radius-pill); padding:.75rem 1.15rem; font-weight:600; box-shadow:0 4px 12px rgba(31,76,44,.22); transition:all .25s; }
div.stButton>button:hover{ filter:brightness(.97); box-shadow:0 0 0 3px rgba(200,168,90,.45); }
.btn-gold button{ background:var(--adi-gold) !important; color:#1f2a1f !important; box-shadow:0 4px 12px rgba(200,168,90,.32) !important; }
.btn-sand button{ background:var(--adi-sand) !important; color:var(--adi-sand-text) !important; box-shadow:0 4px 12px rgba(106,75,45,.25) !important; }
</style>
"""

st.markdown(ADI_CSS, unsafe_allow_html=True)

# ------------------------ Header ------------------------
with st.container():
    st.markdown(
        f"""
        <div class=\"adi-hero\">
          <div class=\"adi-hero-row\">
            <div class=\"logo-box\">{('<img src=\"' + logo_data_uri + '\" alt=\"ADI\"/>') if logo_data_uri else '<div class=\"logo-fallback\">A</div>'}</div>
            <div>
              <div class=\"adi-title\">ADI Builder - Lesson Activities & Questions</div>
              <div class=\"adi-sub\">Professional, branded, editable and export-ready.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------ Tabs ------------------------
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

# ------------------------ Layout ------------------------
left, right = st.columns([0.9, 2.1], gap="large")

with left:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Upload eBook / Lesson Plan / PPT")
    st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
    st.file_uploader("Drag and drop your file", type=["pdf", "docx", "pptx"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Pick from eBook / Plan / PPT")
    c1, c2 = st.columns(2)
    lesson = c1.selectbox("Lesson", options=["—", "1", "2", "3", "4", "5"], index=0)
    week = c2.selectbox("Week", options=["—"] + [str(i) for i in range(1, 15)], index=0)
    st.caption("**ADI policy:** Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. The appropriate Bloom tier will be auto‑highlighted below.")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("Pull → MCQs", use_container_width=True, key="pull_mcq")
        st.markdown('</div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="btn-sand">', unsafe_allow_html=True)
        st.button("Pull → Activities", use_container_width=True, key="pull_act")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    st.markdown("### Activity Parameters")
    cc1, cc2 = st.columns(2)
    cc1.number_input("Activities", min_value=1, value=3, step=1, key="num_activities")
    cc2.number_input("Duration (mins)", min_value=5, value=45, step=5, key="num_duration")

    # Bloom tiers auto-highlight based on Week
    highlight = None
    if week in ["1", "2", "3", "4"]:
        highlight = "low"
    elif week in ["5", "6", "7", "8", "9"]:
        highlight = "med"
    elif week in ["10", "11", "12", "13", "14"]:
        highlight = "hi"

    st.caption("ADI Bloom tiers used for MCQs:")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Low tier**")
        st.markdown('<div class="pills">' + ''.join([f'<span class="pill low {"active" if highlight=="low" else ""}">{w}</span>' for w in ["define","identify","list","recall","describe","label"]]) + '</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown("**Medium tier**")
        st.markdown('<div class="pills">' + ''.join([f'<span class="pill med {"active" if highlight=="med" else ""}">{w}</span>' for w in ["apply","demonstrate","solve","illustrate"]]) + '</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown("**High tier**")
        st.markdown('<div class="pills">' + ''.join([f'<span class="pill hi {"active" if highlight=="hi" else ""}">{w}</span>' for w in ["evaluate","synthesize","design","justify"]]) + '</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="adi-card">', unsafe_allow_html=True)
    if st.session_state.active_tab.startswith("Knowledge"):
        st.markdown("### Generate MCQs - Policy Blocks (Low → Medium → High)")
        st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here...")
        st.caption("How many MCQ blocks? (×3 questions)")
        st.number_input(" ", min_value=1, value=1, step=1, key="mcq_blocks")
        st.button("Generate MCQ Blocks")
    else:
        st.markdown("### Build Skills Activities")
        st.selectbox("Activity type", ["Case Study", "Role Play", "Scenario MCQ", "Group Discussion", "Practical Demo"])
        st.text_input("Learning goal", placeholder="What should learners be able to do?")
        st.text_area("Materials / Inputs", height=120, placeholder="Links, readings, slides, equipment...")
        st.number_input("Groups", min_value=1, value=4)
        st.number_input("Duration (mins)", min_value=5, value=30, step=5, key="skill_dur")
        st.button("Generate Activity Plan", key="gen_act")
    st.markdown('</div>', unsafe_allow_html=True)
