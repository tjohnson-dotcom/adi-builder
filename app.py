# app.py — ADI Learning Tracker Question Generator (rebuilt, ADI styled)

import io, os, re, base64, random
from io import BytesIO
import pandas as pd
import streamlit as st

# -------- Page config --------
st.set_page_config(page_title="ADI Learning Tracker", page_icon="🧭", layout="centered")

# -------- ADI Theme / CSS --------
CSS = r'''
<style>
:root{
  --adi:#245a34;       /* ADI green */
  --gold:#C8A85A;      /* ADI gold */
  --stone:#f6f8f7;
  --ink:#0f172a;
  --muted:#667085;
  --border:#e7ecea;
}
html, body { background:var(--stone); }
main .block-container { padding-top:.75rem; max-width: 960px; }
.card{ background:#fff; border:1px solid var(--border); border-radius:16px; padding:18px; box-shadow:0 6px 20px rgba(36,90,52,0.08); margin-bottom:1rem; }
.h1{ font-size:28px; font-weight:900; color:var(--ink); margin:0 0 2px 0; }
.small{ color:var(--muted); font-size:14px; }
.h2{ font-size:19px; font-weight:800; color:var(--ink); margin:2px 0 10px 0; }
.stTabs [role="tablist"] { gap:.5rem; }
.stTabs [role="tab"] { font-weight:800; padding:.6rem .8rem; border-radius:10px 10px 0 0; }
.stTabs [data-baseweb="tab-highlight"]{ height:3px; background:linear-gradient(90deg,var(--adi),var(--gold)) !important; }
.stTabs [aria-selected="true"] { color: var(--adi) !important; }
.stButton>button{
  background: linear-gradient(180deg, #2a6a3f, var(--adi));
  color:#fff; border:1px solid #1e4e2e; font-weight:800;
  border-radius:12px; padding:.6rem 1rem; box-shadow:0 6px 18px rgba(36,90,52,0.20);
}
.stButton>button:hover{ filter: brightness(1.05); }
.stDownloadButton>button{
  background:linear-gradient(180deg,#fafafa,#f1f5f2); color:#1b1b1b; border:1px solid #e1e7e3;
  border-radius:12px; font-weight:800;
}
.chip{ display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; margin:2px; }
.low{ background:#245a34; color:#fff; }
.med{ background:#C8A85A; color:#111; }
.high{ background:#333; color:#fff; }
.highlight{ outline:2px solid var(--adi); box-shadow:0 0 6px rgba(36,90,52,0.4); }
.badge{ display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border-radius:999px; color:#fff; font-weight:800; font-size:12px; margin-right:10px; }
.badge.g{ background:#245a34; } .badge.a{ background:#C8A85A; color:#111; } .badge.r{ background:#333; }
.qcard{ border:1px solid var(--border); border-radius:12px; padding:10px 12px; background:#fff; }
.qitem{ display:flex; gap:10px; align-items:flex-start; padding:6px 0; }
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)

# -------- Logo helper --------
_FALLBACK_LOGO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABABAAAAACqG3XIAAACMElEQVR4nM2WsW7TQBiFf6a0H5yq"
    "zF0y2y5hG0c6zF4k1u5u9m3JHqz4dM7M9kP3C0k1bC0bC2A1vM9Y7mY0JgVv8uJbVYy0C4d6i3gC"
    "9b4n2QxgE7iTnk9z9k9w4rH4g6YyKc3H5rW3q2m8Qw3wUuJKGkqQ8jJr1h3v9J0o9l6zQn9qV2mN"
    "2l8c1mXi5Srgm2cG3wYQz7a1nS0CkqgkQz0o4Kx5l9yJc8KEMt8h2tqfWm0y8x2T8Jw0+o8S8b8"
    "Jw3emcQ0n9Oq7dZrXw9kqgk5yA9iO1l0wB7mQxI3o3eV+o3oM2v8YUpbG6c6WcY8B6bZ9FfQLQ+"
    "s5n8n4Zb3T3w9y7K0gN4d8c4sR4mxD9j8c+J6o9+3yCw1o0b7YpAAAAAElFTkSuQmCC"
)
def _load_logo_bytes() -> bytes:
    try:
        if os.path.exists("Logo.png"):
            with open("Logo.png", "rb") as f:
                return f.read()
    except Exception:
        pass
    return base64.b64decode(_FALLBACK_LOGO_B64)

# -------- Bloom policy --------
LOW_VERBS  = ["define","identify","list","describe","recall","label"]
MED_VERBS  = ["apply","demonstrate","solve","illustrate","analyze","interpret","compare"]
HIGH_VERBS = ["evaluate","synthesize","design","justify","formulate","critique"]
def bloom_focus_for_week(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

# -------- App state --------
st.session_state.setdefault("lesson", 1)
st.session_state.setdefault("week", 1)
st.session_state.setdefault("mcq_total", 10)
st.session_state.setdefault("act_n", 1)
st.session_state.setdefault("act_dur", 30)
st.session_state.setdefault("topic", "")
st.session_state.setdefault("logo_bytes", _load_logo_bytes())
st.session_state.setdefault("src_text", "")
st.session_state.setdefault("src_edit", "")

# -------- Header --------
col_logo, col_title = st.columns([1,4])
with col_logo:
    if st.session_state.logo_bytes:
        b64 = base64.b64encode(st.session_state.logo_bytes).decode()
        st.image(f"data:image/png;base64,{b64}", use_container_width=True)
with col_title:
    st.markdown("<div class='h1'>ADI Learning Tracker</div>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Transform lessons into measurable learning</div>", unsafe_allow_html=True)
st.divider()

# -------- Tabs --------
tab1, tab2, tab3, tab4 = st.tabs(["① Upload","② Setup","③ Generate","④ Export"])

# ===== Upload =====
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Upload Lesson File</div>", unsafe_allow_html=True)
    up = st.file_uploader("Upload .pptx / .pdf / .docx", type=["pptx","pdf","docx"])
    if up:
        st.session_state.src_text = "Dummy parsed text from file..."  # placeholder for parser
        st.session_state.src_edit = st.session_state.src_text
        st.success("File uploaded and parsed.")
    st.caption("Optional: upload ADI/School logo")
    logo = st.file_uploader("Logo", type=["png","jpg","jpeg"])
    if logo is not None:
        st.session_state.logo_bytes = logo.read()
        st.success("Logo updated.")
    st.markdown("</div>", unsafe_allow_html=True)

# ===== Setup =====
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Setup</div>", unsafe_allow_html=True)

    c1,c2 = st.columns([1,1])
    with c1: st.session_state.lesson = st.selectbox("Lesson", [1,2,3,4], index=st.session_state.lesson-1)
    with c2: st.session_state.week   = st.selectbox("Week", list(range(1,15)), index=st.session_state.week-1)

    st.markdown("---")
    st.write("### MCQ Setup")
    st.session_state.mcq_total = st.radio("Number of MCQs", [5,10,20,30], index=[5,10,20,30].index(st.session_state.mcq_total) if st.session_state.mcq_total in [5,10,20,30] else 1, horizontal=True)

    st.markdown("---")
    st.write("### Activity Setup")
    c3,c4 = st.columns([1,2])
    with c3:
        st.session_state.act_n = st.radio("Activities", [1,2,3], index=st.session_state.act_n-1, horizontal=True)
    with c4:
        st.session_state.act_dur = st.slider("Duration per Activity (mins)", 10, 60, st.session_state.act_dur, 5)

    st.markdown("---")
    st.write("### Bloom’s Verbs (ADI Policy)")
    focus = bloom_focus_for_week(st.session_state.week)
    def bloom_row(label, verbs):
        cls = "low" if label=="Low" else "med" if label=="Medium" else "high"
        highlight = " highlight" if label==focus else ""
        chips = " ".join([f"<span class='chip {cls}{highlight}'>{v}</span>" for v in verbs])
        st.markdown(f"**{label} (Weeks {'1–4' if label=='Low' else '5–9' if label=='Medium' else '10–14'})**<br>{chips}", unsafe_allow_html=True)
    bloom_row("Low", LOW_VERBS)
    bloom_row("Medium", MED_VERBS)
    bloom_row("High", HIGH_VERBS)

    st.markdown("</div>", unsafe_allow_html=True)

# ===== Generate =====
with tab3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Generate Questions & Activities</div>", unsafe_allow_html=True)
    if st.button("📝 Generate MCQs", use_container_width=True):
        st.session_state.mcq_df = pd.DataFrame({"Question":[f"Sample Q{i}" for i in range(1,st.session_state.mcq_total+1)]})
        st.success("MCQs generated.")
    if st.button("🧩 Generate Activities", use_container_width=True):
        st.session_state.act_df = pd.DataFrame({"Activity":[f"Activity {i}" for i in range(1,st.session_state.act_n+1)]})
        st.success("Activities generated.")
    if "mcq_df" in st.session_state:
        st.write("**MCQs (preview)**")
        st.dataframe(st.session_state.mcq_df)
    if "act_df" in st.session_state:
        st.write("**Activities (preview)**")
        st.dataframe(st.session_state.act_df)
    st.markdown("</div>", unsafe_allow_html=True)

# ===== Export =====
with tab4:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Export</div>", unsafe_allow_html=True)
    if "mcq_df" in st.session_state:
        st.download_button("Download MCQs (CSV)", st.session_state.mcq_df.to_csv(index=False).encode("utf-8"), "mcqs.csv", "text/csv")
    if "act_df" in st.session_state:
        st.download_button("Download Activities (CSV)", st.session_state.act_df.to_csv(index=False).encode("utf-8"), "activities.csv", "text/csv")
    st.markdown("</div>", unsafe_allow_html=True)
