
# --- imports & page setup ---
import os, io, re, hashlib, random
from pathlib import Path
from datetime import datetime
import streamlit as st  # <<< this was missing

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# --- Read inputs
mode   = st.session_state.get("mode", "knowledge")  # "knowledge" | "skills" | "revision"
topic  = st.text_input("Topic / Objective (short)", key="quick_topic")
notes  = st.text_area("Key notes (optional)", key="quick_notes")
week   = st.session_state.get("week", 1)
lesson = st.session_state.get("lesson", 1)

# (Optional) resource upload – use the same stable block we’ve used before
res = st.file_uploader("Drag & drop files here or click to browse", type=["pdf","docx","pptx"], key="res_upl")

# When clicked, build content
if st.button("Generate for staff", type="primary"):
    # 1) optional: extract text from uploaded file
    src_text = (st.session_state.get("src_text","") or "").strip()
    if res is not None:
        buf = res.getbuffer()
        fhash = hashlib.sha1(buf).hexdigest()
        ext = Path(res.name).suffix.lower()
        save_path = f"/tmp/adi_{fhash}{ext}"
        with open(save_path, "wb") as f: f.write(buf)
        extracted = extract_text_from_file(save_path, ext, max_chars=8000)
        src_text = f"{topic}\n{notes}\n{extracted}".strip()
    else:
        src_text = f"{topic}\n{notes}\n{src_text}".strip()

    # 2) choose verbs by policy week
    policy_now = policy_for_week(int(week))
    verbs = POLICY_VERBS[policy_now]

    # 3) build content
    if mode == "knowledge":
        mcqs = build_mcqs(src_text, verbs, n=10, variant=0, enable_mix=True, week=int(week), lesson=int(lesson))
        st.session_state["_mcqs"] = mcqs
    elif mode == "skills":
        acts = build_activities(src_text, verbs, week=int(week), lesson=int(lesson), count=6)
        st.session_state["_acts"] = acts
    else:  # "revision"
        # quick prompts using the same verbs
        rnd = random.Random( (week, lesson) )
        prompts = [
            f"In 2–3 sentences, **{rnd.choice(verbs)}** the key idea of this lesson.",
            f"Create one MCQ that **{rnd.choice(verbs)}** the topic and include the answer.",
            f"Give a real-world example that **{rnd.choice(verbs)}** the key concept.",
        ]
        st.session_state["_rev"] = prompts

# --- Show draft outputs + download buttons
with st.container():
    if st.session_state.get("_mcqs"):
        st.success(f"Generated {len(st.session_state['_mcqs'])} MCQs.")
        for i, item in enumerate(st.session_state["_mcqs"], 1):
            st.markdown(f"**{i}. {item['q']}**")
            for key, text in item["options"]:
                st.write(f"{key}. {text}")
        # export .docx
        topic_preview = (topic or "this topic")
        data = export_mcq_docx(st.session_state["_mcqs"], int(week), int(lesson), topic_preview)
        fname = f"ADI_Lesson{lesson}_Week{week}_MCQPaper.docx"
        st.download_button("⬇️ Download MCQ Paper (.docx)", data=data, file_name=fname,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    if st.session_state.get("_acts"):
        st.success(f"Generated {len(st.session_state['_acts'])} activities.")
        for i, a in enumerate(st.session_state["_acts"], 1):
            st.markdown(f"**{i}.** {a}")

    if st.session_state.get("_rev"):
        st.success("Generated revision prompts.")
        for p in st.session_state["_rev"]:
            st.write(f"- {p}")
