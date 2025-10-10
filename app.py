# app.py — ADI Builder (production-ready)
import datetime as dt
import streamlit as st
from adi_builder.ui import (
    initialize_session_state,
    render_header,
    render_course_inputs,
    render_topic_and_verbs,
    apply_custom_styles
)
from adi_builder.generators import generate_mcqs, generate_skills, generate_revision
from adi_builder.export import mcqs_to_txt, mcqs_to_docx_bytes

# Page config
st.set_page_config(page_title="ADI Builder — Lesson Activities & Questions", page_icon="🎓", layout="wide")
BUILD_TAG = "2025-10-10 • production-ready"

# Apply custom styles
apply_custom_styles()

# Reset session button
if st.button("🔄 Reset Session"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# Initialize session state
initialize_session_state()

# Render header
render_header(BUILD_TAG)

# Layout: left (upload + course) and right (topic + verbs)
left, right = st.columns([1.2, 2.4], gap="large")
with left:
    uploaded = render_course_inputs()
with right:
    render_topic_and_verbs()

# Tabs
tabs = st.tabs(["Knowledge MCQs (Editable)", "Skills Activities", "Revision", "Print Summary"])

# ----- MCQs Tab -----
with tabs[0]:
    st.markdown("### Experimental: AI Question Generator")
    if st.button("Generate with AI (Coming Soon)"):
        st.info("AI-powered generation will be available in the next release.")

    n = st.selectbox("How many MCQs?", [5, 8, 10, 12, 15, 20], index=2, key="how_many")
    st.toggle("Answer key", value=True, key="ak")

    if st.button("Generate from verbs/topic", key="btn_gen_mcq"):
        st.session_state["mcqs"] = generate_mcqs(
            n,
            st.session_state["topic"],
            st.session_state["verbs_low"],
            st.session_state["verbs_med"],
            st.session_state["verbs_high"]
        )

    mcqs = st.session_state["mcqs"]
    if not mcqs:
        st.info("No questions yet. Click **Generate from verbs/topic**.")
    else:
        for i, q in enumerate(mcqs, start=1):
            st.write(f"**Q{i}**")
            q["stem"] = st.text_area(f"Question {i} stem", q["stem"], key=f"qstem_{i}", height=60)
            cols_qa = st.columns(2)
            with cols_qa[0]:
                q["A"] = st.text_input("A", q["A"], key=f"qa_{i}")
                q["B"] = st.text_input("B", q["B"], key=f"qb_{i}")
            with cols_qa[1]:
                q["C"] = st.text_input("C", q["C"], key=f"qc_{i}")
                q["D"] = st.text_input("D", q["D"], key=f"qd_{i}")
            if st.session_state["ak"]:
                q["correct"] = st.radio("Correct answer", ["A", "B", "C", "D"],
                                        index=["A", "B", "C", "D"].index(q["correct"]),
                                        key=f"qr_{i}", horizontal=True)
            st.divider()

        # Downloads
        txt_bytes = mcqs_to_txt(mcqs).encode("utf-8")
        st.download_button("⬇️ Download TXT (All MCQs)", txt_bytes,
                           file_name="ADI_MCQ_All.txt", mime="text/plain", key="dl_txt_all")

        docx_bytes = mcqs_to_docx_bytes(mcqs)
        st.download_button("⬇️ Download DOCX (All MCQs)", docx_bytes,
                           file_name="ADI_MCQ_All.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key="dl_docx_all")

# ----- Skills Tab -----
with tabs[1]:
    if st.button("Generate skills activities", key="btn_gen_skills"):
        st.session_state["skills"] = generate_skills(st.session_state["verbs_med"],
                                                     st.session_state["lesson"],
                                                     st.session_state["week"])
    if not st.session_state["skills"]:
        st.info("No activities yet. Click **Generate skills activities**.")
    else:
        for i, a in enumerate(st.session_state["skills"], start=1):
            st.markdown(f"**Activity {i}.** {a}")

# ----- Revision Tab -----
with tabs[2]:
    if st.button("Generate revision prompts", key="btn_gen_rev"):
        st.session_state["revision"] = generate_revision(st.session_state["verbs_low"],
                                                         st.session_state["verbs_high"])
    if not st.session_state["revision"]:
        st.info("No revision prompts yet. Click **Generate revision prompts**.")
    else:
        for i, r in enumerate(st.session_state["revision"], start=1):
            st.markdown(f"**R{i}.** {r}")

# ----- Print Summary Tab -----
with tabs[3]:
    st.subheader("Print summary")
    st.write(f"**Course:** {st.session_state['course']}")
    st.write(f"**Cohort:** {st.session_state['cohort']}  •  **Instructor:** {st.session_state['instructor']}")
    st.write(f"**Date:** {st.session_state['date']}  •  **Lesson:** {st.session_state['lesson']}  •  **Week:** {st.session_state['week']}")
    st.write(f"**Topic:** {st.session_state['topic'] or '—'}")
    st.write("**Low verbs:**", ", ".join(st.session_state["verbs_low"]) or "—")
    st.write("**Medium verbs:**", ", ".join(st.session_state["verbs_med"]) or "—")
    st.write("**High verbs:**", ", ".join(st.session_state["verbs_high"]) or "—")
    if st.session_state["mcqs"]:
        st.markdown("### MCQs")
        for i, q in enumerate(st.session_state["mcqs"], start=1):
            st.write(f"**Q{i}.** {q['stem']}")
            st.write(f"A. {q['A']}  |  B. {q['B']}  |  C. {q['C']}  |  D. {q['D']}")
            st.caption(f"Answer: {q['correct']}")
