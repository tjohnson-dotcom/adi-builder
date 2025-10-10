import streamlit as st

# Inject custom CSS
st.markdown("""
<style>
body { font-family: 'Segoe UI', sans-serif; }
header, .adi-header {
    background: #004d40;
    color: #fff;
    padding: 15px;
    font-size: 24px;
    font-weight: bold;
}
.sidebar .sidebar-content {
    background: #004d40;
    color: #fff;
}
.upload-box, .bloom-panels, .export {
    background: #fff;
    margin-bottom: 20px;
    padding: 20px;
    border-radius: 8px;
}
.drag-drop {
    border: 2px dashed #004d40;
    padding: 20px;
    text-align: center;
    border-radius: 8px;
}
.panel.low { background: #e8f5e9; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
.panel.medium { background: #fffde7; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
.panel.high { background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
.tag {
    display: inline-block;
    background: #004d40;
    color: #fff;
    padding: 5px 10px;
    border-radius: 4px;
    margin: 5px;
    cursor: pointer;
}
.export-btn {
    padding: 10px 20px;
    background: #004d40;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='adi-header'>ADI Builder — Lesson Activities & Questions</div>", unsafe_allow_html=True)

# Upload section
st.markdown("<div class='upload-box'><h3>Upload (optional)</h3><div class='drag-drop'>Drag and drop file here<br><br><button class='browse-btn'>Browse files</button></div></div>", unsafe_allow_html=True)

# Bloom panels
st.markdown("<div class='bloom-panels'><h3>Bloom's Taxonomy Levels</h3>", unsafe_allow_html=True)
st.markdown("<div class='panel low'><h4>Low (Weeks 1–4)</h4><span class='tag'>define ✕</span><span class='tag'>identify ✕</span></div>", unsafe_allow_html=True)
st.markdown("<div class='panel medium'><h4>Medium (Weeks 5–9)</h4><span class='tag'>apply ✕</span><span class='tag'>analyze ✕</span></div>", unsafe_allow_html=True)
st.markdown("<div class='panel high'><h4>High (Weeks 10–14)</h4><span class='tag'>evaluate ✕</span><span class='tag'>design ✕</span></div>", unsafe_allow_html=True)

# Export button
st.markdown("<div class='export'><button class='export-btn'>Export to Word</button></div>", unsafe_allow_html=True)
