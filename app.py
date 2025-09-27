
import io, re, random, hashlib
from typing import List, Tuple
import pandas as pd
import streamlit as st

# =====================
# Page & State
# =====================
st.set_page_config(
    page_title="ADI Learning Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Safe state initialization ----
for key, factory in {
    "seen_q_sigs": set,
    "seen_q_sigs_global": set,
    "undo_mcq": list,
    "undo_act": list,
    "mcq_df": pd.DataFrame(),
    "act_df": pd.DataFrame(),
}.items():
    if key not in st.session_state:
        st.session_state[key] = factory()

# =====================
# Constants
# =====================
MCQ_COLS = ["Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]
ACT_COLS = ["Title","Objective","Steps","Materials","Assessment","Duration (mins)","Policy focus"]
ANSWER_LETTERS = ["A","B","C","D"]

# =====================
# Utilities
# =====================
def _strip_noise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()

def _keywords(text: str, top_n: int = 24) -> List[str]:
    # Light keyworder using unigram & bigram counts.
    t = re.sub(r"[^A-Za-z0-9\- ]+", " ", (text or "").lower())
    words = [w for w in t.split() if len(w) >= 3]
    if not words:
        return []
    from collections import Counter
    uni = Counter(words)
    bi = Counter([" ".join(p) for p in zip(words, words[1:]) if all(len(w)>=3 for w in p)])
    merged = uni | bi
    items = list(merged.items())
    items.sort(key=lambda kv: (-kv[1], -len(kv[0])))
    stop = {"the","and","with","from","into","that","this","those","these","for","are","was","were","your","their","its","our"}
    return [k for k,_ in items if k not in stop][:top_n]

def _seed_salt() -> int:
    # Stable numeric salt derived from Teacher ID (optional).
    try:
        seed_txt = (st.session_state.get("teacher_seed") or st.session_state.get("teacher_id") or "").strip()
    except Exception:
        seed_txt = ""
    if not seed_txt:
        return 0
    h = hashlib.md5(seed_txt.encode("utf-8")).hexdigest()[:8]
    return int(h, 16)

def _quality_gate(options: List[str]) -> bool:
    options = [o.strip() for o in options]
    if any(not o for o in options):
        return False
    if len(set(options)) < len(options):
        return False
    if sum(1 for o in options if len(o.split()) <= 1) >= 2:
        return False
    return True

def _distractors_for_sentence(sent: str) -> Tuple[List[str], str]:
    # Return (distractors, correct) using local/global keywords (offline).
    corpus = (st.session_state.get("src_edit") or st.session_state.get("src_text") or "")
    s = _strip_noise(sent or "")
    if not s:
        return [], ""
    loc_kws = _keywords(s, top_n=10)
    correct = ""
    for kw in loc_kws:
        if " " in kw and len(kw) >= 8:
            correct = kw
            break
    if not correct:
        correct = (loc_kws[0] if loc_kws else s.split(".")[0])[:160]
    correct = correct.strip().capitalize()

    glob_kws = _keywords(corpus, top_n=60) if corpus else []
    cset = set(correct.lower().split())
    d = []
    for kw in glob_kws:
        if kw == correct.lower():
            continue
        if set(kw.split()).intersection(cset):
            continue
        if kw.strip() and kw.lower() not in {"none", "all", "above", "below"}:
            d.append(kw.capitalize())
        if len(d) >= 6:
            break
    while len(d) < 3:
        extra = correct.split()
        extra = extra[::-1] if len(extra) > 1 else extra
        cand = " ".join(extra).capitalize() or (correct + " policy").capitalize()
        if cand not in d and cand != correct:
            d.append(cand)
        else:
            d.append((correct + " guideline").capitalize())
    return d[:3], correct

def _explain_choice(correct: str, options: List[str], topic: str = "") -> str:
    return "Correct because it matches the source facts." if not topic else f"Correct because it matches {topic}."

def _seen_pool(text: str) -> set:
    # Stub for any banned strings; extend if you want to avoid certain words.
    return set()

# =====================
# File reading (robust)
# =====================
def _read_upload(file) -> str:
    # Read text from uploaded file; returns '' if parsing fails.
    if not file:
        return ""
    name = file.name.lower()
    data = file.read()
    try:
        if name.endswith(".txt"):
            return data.decode("utf-8", errors="ignore")
        if name.endswith(".docx"):
            try:
                import docx
                doc = docx.Document(io.BytesIO(data))
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception:
                return ""
        if name.endswith(".pptx"):
            try:
                from pptx import Presentation
                prs = Presentation(io.BytesIO(data))
                txt = []
                for slide in prs.slides:
                    for shp in slide.shapes:
                        if hasattr(shp, "text"):
                            txt.append(shp.text)
                return "\n".join(txt)
            except Exception:
                return ""
        if name.endswith(".pdf"):
            # Leave PDF disabled in this baseline to avoid heavy deps
            return ""
    except Exception:
        return ""
    return ""

# =====================
# Generators
# =====================
def generate_mcqs(src: str, lesson: int, week: int, focus: str, source_type: str) -> pd.DataFrame:
    if not src or len(_strip_noise(src)) < 40:
        return pd.DataFrame(columns=MCQ_COLS)

    rnd = random.Random(int(week) * 100 + int(lesson) + (_seed_salt() % 100000))
    sents = re.split(r'(?<=[.!?])\s+', _strip_noise(src))
    sents = [s for s in sents if 25 <= len(s) <= 220]
    if not sents:
        sents = [src]

    tiers = ["Low","Medium","High"]
    rows = []
    sig_seen = st.session_state.setdefault("seen_q_sigs_global", set())
    kws_global = _keywords(src, top_n=40)

    qn = 1
    for s in sents[:12]:
        if kws_global:
            idx = (qn + week + _seed_salt()) % len(kws_global)
            anchor = kws_global[idx]
        else:
            anchor = s.split()[0].lower()

        distractors, correct = _distractors_for_sentence(s)
        opts = [correct] + distractors
        rnd.shuffle(opts)
        if not _quality_gate(opts):
            continue

        tier = rnd.choice(tiers)
        if tier == "Low":
            stem = f"Which statement is most accurate about {anchor}?"
        elif tier == "High":
            stem = f"Identify the best justification related to {anchor}."
        else:
            stem = f"According to the text, what should be done regarding {anchor}?"

        sig = (tier, stem.split("?")[0][:90].lower())
        if sig in sig_seen:
            continue
        sig_seen.add(sig)

        answer_letter = ANSWER_LETTERS[opts.index(correct)] if correct in opts else "A"
        rows.append({
            "Tier": tier,
            "Q#": qn,
            "Question": stem,
            "Option A": opts[0],
            "Option B": opts[1],
            "Option C": opts[2],
            "Option D": opts[3] if len(opts) > 3 else "None of the above",
            "Answer": answer_letter,
            "Explanation": _explain_choice(correct, opts, topic=anchor),
        })
        qn += 1

    return pd.DataFrame(rows, columns=MCQ_COLS) if rows else pd.DataFrame(columns=MCQ_COLS)

def generate_activities(lesson: int, week: int, focus: str) -> pd.DataFrame:
    rnd = random.Random(week * 1000 + lesson * 7 + (_seed_salt() % 9999))
    focus = (focus or "Focus Medium").split()[-1].capitalize()
    templates = [
        ("Think-Pair-Share", "Discuss and refine understanding of the core idea.", 15),
        ("Case Study", "Analyze a scenario and propose recommendations.", 30),
        ("Concept Mapping", "Map key concepts and relationships.", 20),
        ("Gallery Walk", "Create posters then circulate and give feedback.", 25),
        ("Peer Review", "Critique sample answers using a rubric.", 20),
        ("Scenario Cards", "Respond to short scenarios and justify choices.", 25),
        ("Design Sprint", "Prototype a quick solution and demo.", 35),
    ]
    rnd.shuffle(templates)
    rows = []
    for title, obj, duration in templates[:3]:
        steps = [
            "Starter (5m). Activate prior knowledge.",
            f"Main ({max(10, duration-10)}m). Team task focused on {focus}.",
            "Plenary (5m). Share one insight and one question."
        ]
        rows.append({
            "Title": title,
            "Objective": obj + f" (Lesson {lesson}, Week {week}, focus: {focus}).",
            "Steps": " ".join(steps),
            "Materials": "Timer; A3 paper; markers; student handout",
            "Assessment": f"Rubric aligned to {focus} (clarity, correctness, application).",
            "Duration (mins)": duration,
            "Policy focus": focus,
        })
    return pd.DataFrame(rows, columns=ACT_COLS)

# =====================
# Exporters
# =====================
def export_mcqs_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def export_mcqs_gift(df: pd.DataFrame) -> bytes:
    # Simple Moodle GIFT exporter.
    lines = []
    for _, r in df.iterrows():
        stem = _strip_noise(str(r.get("Question","")))
        opts = [str(r.get("Option A","")), str(r.get("Option B","")), str(r.get("Option C","")), str(r.get("Option D",""))]
        ans = str(r.get("Answer","A")).strip().upper()
        correct = {"A":0,"B":1,"C":2,"D":3}.get(ans, 0)
        gift = f"::{_strip_noise(stem)[:50]}:: {stem} {{"
        for i, o in enumerate(opts):
            gift += (" =" if i==correct else " ~") + o
        gift += " }\n"
        lines.append(gift)
    return ("\n".join(lines)).encode("utf-8")

def export_acts_docx(df: pd.DataFrame) -> bytes:
    try:
        import docx
        doc = docx.Document()
        doc.add_heading("Activities", level=1)
        for _, r in df.iterrows():
            doc.add_heading(str(r.get("Title","Activity")), level=2)
            doc.add_paragraph(f"Objective: {r.get('Objective','')}")
            doc.add_paragraph(f"Steps: {r.get('Steps','')}")
            doc.add_paragraph(f"Materials: {r.get('Materials','')}")
            doc.add_paragraph(f"Assessment: {r.get('Assessment','')}")
            doc.add_paragraph(f"Duration (mins): {r.get('Duration (mins)', '')}")
            doc.add_paragraph(f"Policy focus: {r.get('Policy focus','')}")
            doc.add_paragraph("")
        bio = io.BytesIO()
        doc.save(bio)
        return bio.getvalue()
    except Exception:
        # Fallback to CSV if docx isn't available
        return df.to_csv(index=False).encode("utf-8")

# =====================
# UI
# =====================
st.title("ADI Learning Tracker")
st.caption("Transform lessons into measurable learning")

tabs = st.tabs(["① Upload", "② Setup", "③ ✨ Generate", "④ Export"])

# --- Upload ---
with tabs[0]:
    st.subheader("Upload Lesson File or Paste Text")
    up = st.file_uploader("Upload .pptx / .docx / .txt (PDF disabled in baseline).", type=["pptx","docx","txt","pdf"])
    st.session_state.src_text = _read_upload(up)
    st.session_state.src_text = st.text_area("Or paste lesson content below", value=st.session_state.get("src_text",""), height=220)

# --- Setup ---
with tabs[1]:
    st.subheader("Setup")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.session_state.lesson = st.number_input("Lesson", min_value=1, max_value=30, value=int(st.session_state.get("lesson",1)), step=1)
    with c2: st.session_state.week = st.number_input("Week", min_value=1, max_value=52, value=int(st.session_state.get("week",1)), step=1)
    with c3: st.session_state.source_type = st.radio("Source", ["PPT","E-book","Lesson plan"], horizontal=True,
                                                    index=(["PPT","E-book","Lesson plan"].index(st.session_state.get("source_type","E-book"))))
    with c4: st.session_state.focus = st.radio("Focus", ["Focus Low","Focus Medium","Focus High"], horizontal=True,
                                              index=(["Focus Low","Focus Medium","Focus High"].index(st.session_state.get("focus","Focus Medium"))))
    with c5: st.session_state.teacher_seed = st.text_input("Teacher ID (variation seed)", value=st.session_state.get("teacher_seed",""))
    st.caption(f"Context: Lesson {st.session_state.lesson} • Week {st.session_state.week} • {st.session_state.source_type}")
    st.button("Reset MCQ uniqueness memory", on_click=lambda: st.session_state.setdefault("seen_q_sigs_global", set()).clear())

# --- Generate ---
with tabs[2]:
    st.subheader("Generate Questions & Activities")
    chip1, chip2, chip3, chip4 = st.columns(4)
    with chip1: st.button(f"Lesson {st.session_state.lesson}", disabled=True)
    with chip2: st.button(f"Week {st.session_state.week}", disabled=True)
    with chip3: st.button(f"{st.session_state.source_type}", disabled=True)
    with chip4: st.button(f"{st.session_state.focus}", disabled=True)

    lc1, lc2 = st.columns([1,1])
    with lc1:
        if st.button("📝 Generate MCQs", use_container_width=True):
            try:
                st.session_state.mcq_df = generate_mcqs(
                    st.session_state.get("src_text",""),
                    int(st.session_state.get("lesson",1)),
                    int(st.session_state.get("week",1)),
                    st.session_state.get("focus","Focus Medium"),
                    st.session_state.get("source_type","E-book"),
                )
                if len(st.session_state.mcq_df) == 0:
                    st.warning("No MCQs generated — add more text in Step 1.")
            except Exception as e:
                st.error(f"Couldn't generate MCQs: {e}")
    with lc2:
        if st.button("🧩 Generate Activities", use_container_width=True):
            try:
                st.session_state.act_df = generate_activities(
                    int(st.session_state.get("lesson",1)),
                    int(st.session_state.get("week",1)),
                    st.session_state.get("focus","Focus Medium"),
                )
            except Exception as e:
                st.error(f"Couldn't generate Activities: {e}")

    st.markdown("### MCQs Preview")
    if isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df) > 0:
        st.dataframe(st.session_state.mcq_df, use_container_width=True)
    else:
        st.info("No MCQs to show yet — choose **MCQs** and click **Generate** above.")

    st.markdown("### Activities Preview")
    if isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df) > 0:
        st.dataframe(st.session_state.act_df, use_container_width=True)
    else:
        st.info("No Activities to show yet — choose **Activities** and click **Generate** above.")

    # Sidebar Editor (if visible)
    try:
        st.sidebar.header("Edit panel")
        edit_mode = st.sidebar.radio("Edit", ["MCQs","Activities"], horizontal=True, key="sidebar_mode")
        if edit_mode == "MCQs" and isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df) > 0:
            df = st.session_state.mcq_df
            row = st.sidebar.number_input("Row", 0, len(df)-1, 0, step=1, key="sb_mcq_row")
            st.sidebar.text_area("Question", df.loc[row,"Question"], key="sb_q")
            st.sidebar.text_input("A", df.loc[row,"Option A"], key="sb_oa")
            st.sidebar.text_input("B", df.loc[row,"Option B"], key="sb_ob")
            st.sidebar.text_input("C", df.loc[row,"Option C"], key="sb_oc")
            st.sidebar.text_input("D", df.loc[row,"Option D"], key="sb_od")
            st.sidebar.selectbox("Answer", ANSWER_LETTERS, index=ANSWER_LETTERS.index(str(df.loc[row,"Answer"])) if str(df.loc[row,"Answer"]) in ANSWER_LETTERS else 0, key="sb_ans")
            st.sidebar.text_area("Explanation", df.loc[row,"Explanation"], key="sb_expl")
            cA, cB, cC = st.sidebar.columns(3)
            if cA.button("Apply"):
                df.loc[row, ["Question","Option A","Option B","Option C","Option D","Answer","Explanation"]] = [
                    st.session_state.sb_q, st.session_state.sb_oa, st.session_state.sb_ob, st.session_state.sb_oc, st.session_state.sb_od,
                    st.session_state.sb_ans, st.session_state.sb_expl
                ]
                st.session_state.mcq_df = df; st.toast("Applied MCQ changes")
            if cB.button("Duplicate"):
                st.session_state.mcq_df = pd.concat([df.iloc[:row+1], df.iloc[row:row+1], df.iloc[row+1:]], ignore_index=True); st.toast("Duplicated")
            if cC.button("Delete") and len(df) > 1:
                st.session_state.mcq_df = df.drop(index=row).reset_index(drop=True); st.toast("Deleted")

        if edit_mode == "Activities" and isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df) > 0:
            df = st.session_state.act_df
            row = st.sidebar.number_input("Row", 0, len(df)-1, 0, step=1, key="sb_act_row")
            title = st.sidebar.text_input("Title", df.loc[row,"Title"])
            objective = st.sidebar.text_area("Objective", df.loc[row,"Objective"])
            steps = st.sidebar.text_area("Steps", df.loc[row,"Steps"])
            materials = st.sidebar.text_area("Materials", df.loc[row,"Materials"])
            assessment = st.sidebar.text_area("Assessment", df.loc[row,"Assessment"])
            duration = st.sidebar.number_input("Duration (mins)", int(df.loc[row,"Duration (mins)"]), step=5)
            focus = st.sidebar.text_input("Policy focus", df.loc[row,"Policy focus"])
            cA, cB, cC = st.sidebar.columns(3)
            if cA.button("Apply", key="act_apply"):
                df.loc[row, ["Title","Objective","Steps","Materials","Assessment","Duration (mins)","Policy focus"]] = [
                    title, objective, steps, materials, assessment, int(duration), focus
                ]
                st.session_state.act_df = df; st.toast("Applied Activity changes")
            if cB.button("Duplicate", key="act_dup"):
                st.session_state.act_df = pd.concat([df.iloc[:row+1], df.iloc[row:row+1], df.iloc[row+1:]], ignore_index=True); st.toast("Duplicated")
            if cC.button("Delete", key="act_del") and len(df) > 1:
                st.session_state.act_df = df.drop(index=row).reset_index(drop=True); st.toast("Deleted")
    except Exception:
        pass

    # Inline editor fallback
    st.divider()
    st.subheader("✏️ Editor (Inline)")
    mode = st.radio("Edit", ["MCQs","Activities"], horizontal=True, key="inline_mode")
    if mode == "MCQs" and isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df) > 0:
        df = st.session_state.mcq_df
        c1, c2 = st.columns([1,3])
        with c1:
            row = st.number_input("Row", 0, len(df)-1, 0, step=1, key="in_mcq_row")
            if st.button("🧬 Duplicate", key="in_mcq_dup"):
                st.session_state.mcq_df = pd.concat([df.iloc[:row+1], df.iloc[row:row+1], df.iloc[row+1:]], ignore_index=True); st.toast("Duplicated")
            if st.button("🗑 Delete", key="in_mcq_del") and len(df) > 1:
                st.session_state.mcq_df = df.drop(index=row).reset_index(drop=True); st.toast("Deleted")
        with c2:
            qtxt = st.text_area("Question", str(df.loc[row,"Question"]), height=120)
            colA, colB = st.columns(2)
            with colA:
                oa = st.text_area("Option A", str(df.loc[row,"Option A"]), height=70)
                oc = st.text_area("Option C", str(df.loc[row,"Option C"]), height=70)
            with colB:
                ob = st.text_area("Option B", str(df.loc[row,"Option B"]), height=70)
                od = st.text_area("Option D", str(df.loc[row,"Option D"]), height=70)
            ans = st.selectbox("Answer", ANSWER_LETTERS, index=ANSWER_LETTERS.index(str(df.loc[row,"Answer"])) if str(df.loc[row,"Answer"]) in ANSWER_LETTERS else 0)
            expl = st.text_area("Explanation", str(df.loc[row,"Explanation"]), height=90)
            if st.button("Apply changes", key="in_mcq_apply"):
                df.loc[row, ["Question","Option A","Option B","Option C","Option D","Answer","Explanation"]] = [qtxt, oa, ob, oc, od, ans, expl]
                st.session_state.mcq_df = df; st.toast("Applied MCQ changes")

    if mode == "Activities" and isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df) > 0:
        df = st.session_state.act_df
        c1, c2 = st.columns([1,3])
        with c1:
            row = st.number_input("Row", 0, len(df)-1, 0, step=1, key="in_act_row")
            if st.button("🧬 Duplicate", key="in_act_dup"):
                st.session_state.act_df = pd.concat([df.iloc[:row+1], df.iloc[row:row+1], df.iloc[row+1:]], ignore_index=True); st.toast("Duplicated")
            if st.button("🗑 Delete", key="in_act_del") and len(df) > 1:
                st.session_state.act_df = df.drop(index=row).reset_index(drop=True); st.toast("Deleted")
        with c2:
            title = df.loc[row,"Title"]; objective = df.loc[row,"Objective"]
            steps = df.loc[row,"Steps"]; materials = df.loc[row,"Materials"]
            assessment = df.loc[row,"Assessment"]; duration_val = int(df.loc[row,"Duration (mins)"])
            title = st.text_input("Title", str(title))
            objective = st.text_area("Objective", str(objective), height=90)
            steps = st.text_area("Steps", str(steps), height=140)
            materials = st.text_area("Materials", str(materials), height=80)
            assessment = st.text_area("Assessment", str(assessment), height=100)
            duration = st.number_input("Duration (mins)", duration_val, step=5)
            focus_txt = st.text_input("Policy focus", str(df.loc[row,"Policy focus"]))
            if st.button("Apply changes", key="in_act_apply"):
                df.loc[row, ["Title","Objective","Steps","Materials","Assessment","Duration (mins)","Policy focus"]] = [title,objective,steps,materials,assessment,int(duration), focus_txt]
                st.session_state.act_df = df; st.toast("Applied Activity changes")

# --- Export ---
with tabs[3]:
    st.subheader("Export")
    c1, c2, c3 = st.columns(3)
    if isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df) > 0:
        with c1:
            st.download_button("Download MCQs (CSV)", export_mcqs_csv(st.session_state.mcq_df), file_name="mcqs.csv", mime="text/csv", use_container_width=True)
        with c2:
            st.download_button("Download MCQs (GIFT)", export_mcqs_gift(st.session_state.mcq_df), file_name="mcqs_gift.txt", mime="text/plain", use_container_width=True)
    else:
        st.info("No MCQs to export yet.")
    if isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df) > 0:
        data = export_acts_docx(st.session_state.act_df)
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if data[:2] != b"Ti" else "text/csv"
        st.download_button("Download Activities (DOCX/CSV)", data, file_name="activities.docx", mime=mime, use_container_width=True)
    else:
        st.info("No Activities to export yet.")

