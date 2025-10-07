import streamlit as st

st.set_page_config(page_title="ADI Builder — Minimal Safe Build", layout="wide")
st.caption("Build tag: 2025-10-07T23:00 minimal-safe")

# ---- SINGLE, SAFE STYLE BLOCK ----
st.markdown('''
<style>
/* Uploader */
div[data-testid="stFileUploaderDropzone"]{
  border:2px dashed #245a34 !important;
  border-radius:12px !important;
  background:#fff !important;
}

/* HOTFIX: color the first three multiselect chips (Low/Medium/High) */
div[data-testid="stMultiSelect"]:nth-of-type(1) [data-baseweb="tag"]{
  background:#cfe8d9 !important; border:1px solid #245a34 !important; color:#153a27 !important; font-weight:600;
}
div[data-testid="stMultiSelect"]:nth-of-type(2) [data-baseweb="tag"]{
  background:#f8e6c9 !important; border:1px solid #C8A85A !important; color:#3f2c13 !important; font-weight:600;
}
div[data-testid="stMultiSelect"]:nth-of-type(3) [data-baseweb="tag"]{
  background:#dfe6ff !important; border:1px solid #4F46E5 !important; color:#1E1B4B !important; font-weight:600;
}
</style>
''', unsafe_allow_html=True)
# ---- END STYLE BLOCK ----

LOW  = ["define","identify","list","recall","describe","label"]
MED  = ["apply","demonstrate","solve","illustrate","classify","compare"]
HIGH = ["evaluate","synthesize","design","justify","critique","create"]

st.sidebar.subheader("Upload (optional)")
_ = st.sidebar.file_uploader("Drag and drop file here", type=["txt","docx","pptx","pdf"])

with st.expander("Low (Weeks 1–4) — Remember / Understand", True):
    st.multiselect("Low verbs", LOW, default=LOW[:3], key="lowverbs")

with st.expander("Medium (Weeks 5–9) — Apply / Analyse", True):
    st.multiselect("Medium verbs", MED, default=MED[:3], key="medverbs")

with st.expander("High (Weeks 10–14) — Evaluate / Create", True):
    st.multiselect("High verbs", HIGH, default=HIGH[:3], key="highverbs")

st.subheader("Demo download buttons")
sample = "Hello ADI"
st.download_button("Download TXT", data=sample.encode("utf-8"), file_name="sample.txt", mime="text/plain")
