import os, base64
import streamlit as st

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# -------- Optional logo (put your file at assets/adi-logo.png) --------
LOGO_PATH = os.path.join("assets", "adi-logo.png")
logo_data_uri = None
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_data_uri = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

# ------------------------ Global CSS ------------------------
st.markdown("""
<style>
:root{
  --adi-green:#245a34; --adi-green-600:#1f4c2c; --adi-green-50:#EEF5F0;
  --adi-gold:#C8A85A; --adi-sand:#f8f3e8; --adi-sand-text:#6a4b2d;
  --adi-stone:#f3f1ee; --adi-stone-text:#4a4a45;
  --adi-ink:#1f2937; --adi-muted:#6b7280; --border:#d9dfda; --bg:#FAFAF7;
  --radius-pill:999px; --shadow:0 10px 24px rgba(0,0,0,.06);
}
html,body{background:var(--bg)}
main .block-container{max-width:1220px; padding-top:1rem; padding-bottom:2rem}

/* Header */
.adi-hero{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));
  color:#fff; border-radius:20px; padding:18px 20px; box-shadow:var(--shadow)}
.adi-hero-row{display:flex; align-items:center; gap:16px}
.logo-box{width:48px; height:48px; border-radius:12px; background:rgba(0,0,0,.08);
  display:flex; align-items:center; justify-content:center; overflow:hidden}
.logo-box img{width:100%; height:100%; object-fit:contain}
.logo-fallback{font-weight:800; font-size:20px}
.adi-title{font-weight:800; font-size:22px; margin:0}
.adi-sub{opacity:.92; font-size:12px; margin-top:2px}

/* Tabs – subtle so header remains hero */
.stTabs [data-baseweb="tab-list"]{gap:8px; border-bottom:1px solid #ecefee}
.stTabs [data-baseweb="tab"]{background:transparent; border:none; color:var(--adi-ink);
  border-radius:10px; padding:8px 12px; font-weight:700}
.stTabs [aria-selected="true"]{color:#fff!important; background:var(--adi-green)!important}

/* Inputs (pill style) */
input, textarea, select{
  border:1px solid var(--border)!important; border-radius:var(--radius-pill)!important;
  background:var(--adi-stone)!important; padding:.55rem .9rem!important
}
textarea{border-radius:28px!important}
input:hover, textarea:hover, select:hover{box-shadow:0 0 0 2px rgba(36,90,52,.10)}
input:focus, textarea:focus, select:focus{
  outline:none!important; border-color:var(--adi-green)!important;
  box-shadow:0 0 0 3px rgba(36,90,52,.25)!important; background:#fff!important
}
input::placeholder, textarea::placeholder{color:var(--adi-muted); font-style:italic; opacity:.95}

/* Number inputs */
.stNumberInput > div{
  border-radius:var(--radius-pill)!important; border:1px solid var(--border)!important;
  background:var(--adi-stone)!important
}
.stNumberInput > div:focus-within{
  border-color:var(--adi-green)!important; box-shadow:0 0 0 3px rgba(36,90,52,.25)!important
}
.stNumberInput button{background:transparent!important; border:none!important; box-shadow:none!important}

/* Pills for Bloom */
.pills{display:flex; flex-wrap:wrap; gap:8px}
.pill{padding:6px 12px; border-radius:999px; border:1px solid #e3e7e3; background:#f3f7f3; font-size:13px}
.pill.low{background:#eaf5ec; color:#1f4c2c}
.pill.med{background:var(--adi-sand); color:var(--adi-sand-text)}
.pill.hi{background:#f2f2f2; color:#4a4a45}
.pill.active{box-shadow:0 0 0 3px rgba(36,90,52,.25); border-color:var(--adi-green-600)}

/* Buttons */
div.stButton>button{
  background:var(--adi-green); color:#fff; border:none; border-radius:var(--radius-pill);
  padding:.75rem 1.15rem; font-weight:600; box-shadow:0 4px 12px rgba(31,76,44,.22); transition:all .25s
}
div.stButton>button:hover{filter:brightness(.97); box-shadow:0 0 0 3px rgba(200,168,90,.45)}
.btn-gold button{background:var(--adi-gold)!important; color:#1f2a1f!important}
.btn-sand button{background:var(--adi-sand)!important; color:var(--adi-sand-text)!important}

/* ADI dashed uploader wrapper (reliable) */
.adi-up{border:2px dashed var(--adi-green); background:var(--adi-green-50);
  border-radius:14px; padding:14px; display:flex; align-items:center; gap:12px}
.adi-up-badge{width:36px; height:36px; border-radius:8px; background:var(--adi-green);
  color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center}
</style>
""", unsafe_allow_html=True)

# ------------------------ Header ------------------------
st.markdown(f"""
<div class="adi-hero">
  <div class="adi-hero-row">
    <div class="logo-box">{('<img src="'+logo_data_uri+'" alt="ADI"/>') if logo_data_uri else '<div class="logo-fallback">A</div>'}</div>
    <div>
      <div class="adi-title">ADI Builder - Lesson Activities & Questions</div>
      <div class="adi-sub">Professional, branded, editable and export-ready.</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ------------------------ Tabs (no radio dots) ------------------------
tab_mcq, tab_skills = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities"])

with tab_mcq:
    left, right = st.columns([0.95, 2.05], gap="large")

    # -------- LEFT --------
    with left:
        st.markdown("### Upload eBook / Lesson Plan / PPT")
        st.caption("Accepted: PDF · DOCX · PPTX (≤200MB)")
        # Green dashed wrapper + uploader inside
        with st.container(border=False):
            st.markdown('<div class="adi-up"><div class="adi-up-badge">UP</div><div>', unsafe_allow_html=True)
            st.file_uploader("Drag and drop your file", type=["pdf", "docx", "pptx"], label_visibility="collapsed", key="u1")
            st.markdown("</div></div>", unsafe_allow_html=True)
        st.caption("We recommend eBooks (PDF) as source for best results.")

        st.markdown("### Pick from eBook / Plan / PPT")
        c1, c2 = st.columns(2)
        # robust & simple: number inputs (1–5) and (1–14)
        lesson = c1.number_input("Lesson", min_value=1, max_value=5, value=1, step=1, key="lesson_num")
        week   = c2.number_input("Week",   min_value=1, max_value=14, value=1, step=1, key="week_num")
        st.caption("**ADI policy:** Weeks 1–4 → Low, 5–9 → Medium, 10–14 → High. The appropriate Bloom tier will be auto-highlighted below.")

        b1, b2 = st.columns(2)
        with b1:
            st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
            st.button("Pull → MCQs", use_container_width=True, key="pull_mcq")
            st.markdown("</div>", unsafe_allow_html=True)
        with b2:
            st.markdown('<div class="btn-sand">', unsafe_allow_html=True)
            st.button("Pull → Activities", use_container_width=True, key="pull_act")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Activity Parameters")
        cc1, cc2 = st.columns(2)
        num_activities = cc1.number_input("Activities", min_value=1, value=3, step=1, key="num_acts")
        duration_mins  = cc2.number_input("Duration (mins)", min_value=5, value=45, step=5, key="dur_mins")

        # Bloom highlight rule by week
        if   1 <= week <= 4:  tier = "low"
        elif 5 <= week <= 9:  tier = "med"
        else:                 tier = "hi"

        st.caption("ADI Bloom tiers used for MCQs:")
        cA, cB, cC = st.columns(3)
        with cA:
            st.markdown("**Low tier**")
            st.markdown('<div class="pills">' + ''.join(
                f'<span class="pill low {"active" if tier=="low" else ""}">{w}</span>'
                for w in ["define","identify","list","recall","describe","label"]
            ) + '</div>', unsafe_allow_html=True)
        with cB:
            st.markdown("**Medium tier**")
            st.markdown('<div class="pills">' + ''.join(
                f'<span class="pill med {"active" if tier=="med" else ""}">{w}</span>'
                for w in ["apply","demonstrate","solve","illustrate"]
            ) + '</div>', unsafe_allow_html=True)
        with cC:
            st.markdown("**High tier**")
            st.markdown('<div class="pills">' + ''.join(
                f'<span class="pill hi {"active" if tier=="hi" else ""}">{w}</span>'
                for w in ["evaluate","synthesize","design","justify"]
            ) + '</div>', unsafe_allow_html=True)

    # -------- RIGHT --------
    with right:
        st.markdown("### Generate MCQs (Low → Medium → High)")
        st.text_input("Topic / Outcome (optional)", placeholder="Module description, knowledge & skills outcomes")
        st.text_area("Source text (optional, editable)", height=140, placeholder="Paste or edit source text here…")
        st.caption("How many MCQ blocks? (×3 questions)")
        blocks = st.number_input("", min_value=1, value=1, step=1, key="mcq_blocks")
        st.button("Generate MCQ Blocks")

with tab_skills:
    st.markdown("### Build Skills Activities")
    st.selectbox("Activity type", ["Case Study", "Role Play", "Scenario MCQ", "Group Discussion", "Practical Demo"])
    st.text_input("Learning goal", placeholder="What should learners be able to do?")
    st.text_area("Materials / Inputs", height=120, placeholder="Links, readings, slides, equipment…")
    s1, s2 = st.columns(2)
    s1.number_input("Groups", min_value=1, value=4)
    s2.number_input("Duration (mins)", min_value=5, value=30, step=5)
    st.button("Generate Activity Plan", key="gen_act")
