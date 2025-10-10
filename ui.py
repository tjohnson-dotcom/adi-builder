import streamlit as st

def render_sidebar():
    st.sidebar.title("ADI Builder Settings")
    st.sidebar.markdown("Customize your session and export options.")

def render_bloom_panels(week_range):
    if "1–4" in week_range:
        st.info("Low Level: Remember / Understand")
        return ["define", "identify", "list", "describe", "recall"]
    elif "5–9" in week_range:
        st.warning("Medium Level: Apply / Analyze")
        return ["solve", "apply", "analyze", "compare", "examine"]
    else:
        st.success("High Level: Evaluate / Create")
        return ["evaluate", "synthesize", "design", "create", "justify"]
