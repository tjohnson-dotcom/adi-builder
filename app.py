
import re, random, hashlib, io
from typing import List, Tuple
import pandas as pd
import streamlit as st

# ---------------- Page config ----------------
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
}.items():
    if key not in st.session_state:
        st.session_state[key] = factory()

# ---------------- Constants ----------------
MCQ_COLS = ["Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]
ACT_COLS = ["Title","Objective","Steps","Materials","Assessment","Duration (mins)","Policy focus"]

# ---------------- Helpers ----------------
def _strip_noise(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return text

def _keywords(text: str, top_n: int = 20) -> List[str]:
    """Very light keyworder from n-grams (unigram/bigram)."""
    t = re.sub(r"[^A-Za-z0-9\- ]+", " ", (text or "").lower())
    words = [w for w in t.split() if len(w) >= 3]
    if not words: 
        return []
    # frequency for unigrams
    from collections import Counter
    uni = Counter(words)
    # simple bigrams
    bigrams = Counter([" ".join(p) for p in zip(words, words[1:]) if all(len(w)>=3 for w in p)])
    # mix
    items = [(k, v) for k, v in (uni | bigrams).items()]
    items.sort(key=lambda kv: (-kv[1], -len(kv[0])))
    result = [k for k,_ in items if k not in {"the","and","with","from","into","that","this","those","these"}]
    return result[:top_n]

def _seed_salt() -> int:
    try:
        seed_txt = (st.session_state.get("teacher_seed") or st.session_state.get("teacher_id") or "").strip()
    except Exception:
        seed_txt = ""
    if not seed_txt:
        return 0
    h = hashlib.md5(seed_txt.encode("utf-8")).hexdigest()[:8]
    return int(h, 16)

def _distractors_for_sentence(sent: str, mode: str = "safe") -> Tuple[List[str], str]:
    """Return (distractors, correct) using local/global keywords only (offline)."""
    try:
        corpus = (st.session_state.get("src_edit") or st.session_state.get("src_text") or "")
    except Exception:
        corpus = ""
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
    # candidate distractors from the whole corpus
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
    # fill if short
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

def _quality_gate(options: List[str]) -> bool:
    options = [o.strip() for o in options]
    if any(not o for o in options): 
        return False
    if len(set(options)) < len(options):
        return False
    return True

# ---------------- Parsing ----------------
def _read_upload(file) -> str:
    """Try to read text from uploaded file. Falls back to empty string if parsing fails."""
    if not file:
        return ""
    name = file.name.lower()
    data = file.read()
    try:
        if name.endswith(".txt"):
            return data.decode("utf-8", errors="ignore")
        if name.endswith(".docx"):
            try:
                import docx  # python-docx
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
            # Avoid heavy deps; return blank with a hint
            return ""
    except Exception:
        return ""
    return ""

# ---------------- Generation ----------------
def generate_mcqs(src: str, lesson: int, week: int, focus: str, source_type: str) -> pd.DataFrame:
    if not src or len(_strip_noise(src)) < 40:
        return pd.DataFrame(columns=MCQ_COLS)

    rnd = random.Random(int(week) * 100 + int(lesson) + (_seed_salt() % 100000))
    sents = re.split(r'(?<=[.!?])\s+', _strip_noise(src))
    sents = [s for s in sents if 25 <= len(s) <= 220]
    if not sents:
        sents = [src]

    tiers = ["Low","Medium","High"]
    focus_tier = focus.split()[-1].capitalize() if focus else "Medium"

    rows = []
    sig_seen = st.session_state.setdefault("seen_q_sigs_global", set())
    kws_global = _keywords(src, top_n=40)

    qn = 1
    for s in sents[:10]:
        # anchor rotation per week+seed
        if kws_global:
            idx = (qn + week + _seed_salt()) % len(kws_global)
            anchor = kws_global[idx]
        else:
            anchor = s.split()[0].lower()

        distractors, correct = _distractors_for_sentence(s)
        opts = [correct] + distractors
        rnd.shuffle(opts)

        # ensure quality
        if not _quality_gate(opts):
            continue

        # assign answer letter
        letters = ["A","B","C","D"]
        answer_letter = letters[opts.index(correct)] if correct in opts else "A"

        # stem pattern by tier
        tier = rnd.choice(tiers)
        if tier == "Low":
            stem = f"Which statement is most accurate about {anchor}?"
        elif tier == "High":
            stem = f"Identify the best justification related to {anchor}."
        else:
            stem = f"According to the text, what should be done regarding {anchor}?"

        # prevent repeats via signature
        sig = (tier, stem.split("?")[0][:80].lower())
        if sig in sig_seen:
            continue
        sig_seen.add(sig)

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

    if not rows:
        return pd.DataFrame(columns=MCQ_COLS)
    df = pd.DataFrame(rows, columns=MCQ_COLS)
    return df

def generate_activities(lesson: int, week: int, focus: str) -> pd.DataFrame:
    rnd = random.Random(week * 1000 + lesson * 7 + (_seed_salt() % 9999))
    focus = focus.split()[-1].capitalize() if focus else "Medium"
    templates = [
        ("Think-Pair-Share", "Discuss and refine understanding of the core idea.", 15),
        ("Case Study", "Analyze a scenario and propose recommendations.", 30),
        ("Concept Mapping", "Map key concepts and relationships.", 20),
        ("Gallery Walk", "Create posters then circulate and give feedback.", 25),
        ("Peer Review", "Critique sample answers using a rubric.", 20),
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

# ---------------- UI ----------------
st.title("ADI Learning Tracker")
st.caption("Transform lessons into measurable learning")

tabs = st.tabs(["① Upload", "② Setup", "③ ✨ Generate", "④ Export"])

with tabs[0]:
    st.subheader("Upload Lesson File or Paste Text")
    up = st.file_uploader("Upload .pptx / .docx / .txt (PDF parsing disabled here for stability)", type=["pptx","docx","txt","pdf"])
    st.session_state.src_text = _read_upload(up)
    st.session_state.src_text = st.text_area("Or paste lesson content below", value=st.session_state.get("src_text",""), height=220)

with tabs[1]:
    st.subheader("Setup")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.session_state.lesson = st.number_input("Lesson", min_value=1, max_value=30, value=st.session_state.get("lesson",1), step=1)
    with c2: st.session_state.week = st.number_input("Week", min_value=1, max_value=52, value=st.session_state.get("week",1), step=1)
    with c3: st.session_state.source_type = st.radio("Source", ["PPT","E-book","Lesson plan"], horizontal=True, index=1 if st.session_state.get("source_type")=="E-book" else 0)
    with c4: st.session_state.focus = st.radio("Focus", ["Focus Low","Focus Medium","Focus High"], horizontal=True, index=1)
    with c5: st.session_state.teacher_seed = st.text_input("Teacher ID (variation seed)", value=st.session_state.get("teacher_seed",""))
    st.caption(f"Context: Lesson {st.session_state.lesson} • Week {st.session_state.week} • {st.session_state.source_type}")
    st.button("Reset MCQ uniqueness memory", on_click=lambda: st.session_state.setdefault("seen_q_sigs_global", set()).clear())

with tabs[2]:
    st.subheader("Generate Questions & Activities")
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

    # Inline editor (fallback if sidebar is unavailable)
    st.divider()
    st.subheader("✏️ Editor (Inline)")
    mode = st.radio("Edit", ["MCQs","Activities"], horizontal=True, key="inline_edit_mode")
    if mode == "MCQs" and isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df) > 0:
        df = st.session_state.mcq_df
        c1, c2 = st.columns([1,3])
        with c1:
            row = st.number_input("Row", 0, len(df)-1, 0, step=1, key="inline_mcq_row")
            if st.button("🧬 Duplicate", key="inline_mcq_dup"):
                top = df.iloc[:row+1]; mid = df.iloc[row:row+1]; bot = df.iloc[row+1:]
                st.session_state.mcq_df = pd.concat([top, mid, bot], ignore_index=True); st.toast("Duplicated question")
            if st.button("🗑 Delete", key="inline_mcq_del"):
                st.session_state.mcq_df = df.drop(index=row).reset_index(drop=True); st.toast("Deleted question")
        with c2:
            qtxt = st.text_area("Question", str(df.loc[row,"Question"]), height=120)
            colA, colB = st.columns(2)
            with colA:
                oa = st.text_area("Option A", str(df.loc[row,"Option A"]), height=70)
                oc = st.text_area("Option C", str(df.loc[row,"Option C"]), height=70)
            with colB:
                ob = st.text_area("Option B", str(df.loc[row,"Option B"]), height=70)
                od = st.text_area("Option D", str(df.loc[row,"Option D"]), height=70)
            ans = st.selectbox("Answer", ["A","B","C","D"], index=["A","B","C","D"].index(str(df.loc[row,"Answer"])) if str(df.loc[row,"Answer"]) in ["A","B","C","D"] else 0)
            expl = st.text_area("Explanation", str(df.loc[row,"Explanation"]), height=90)
            if st.button("Apply changes", key="inline_mcq_apply"):
                df.loc[row, ["Question","Option A","Option B","Option C","Option D","Answer","Explanation"]] = [qtxt, oa, ob, oc, od, ans, expl]
                st.session_state.mcq_df = df; st.toast("Applied MCQ changes")

    if mode == "Activities" and isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df) > 0:
        df = st.session_state.act_df
        c1, c2 = st.columns([1,3])
        with c1:
            row = st.number_input("Row", 0, len(df)-1, 0, step=1, key="inline_act_row")
            if st.button("🧬 Duplicate", key="inline_act_dup"):
                top = df.iloc[:row+1]; mid = df.iloc[row:row+1]; bot = df.iloc[row+1:]
                st.session_state.act_df = pd.concat([top, mid, bot], ignore_index=True); st.toast("Duplicated activity")
            if st.button("🗑 Delete", key="inline_act_del"):
                st.session_state.act_df = df.drop(index=row).reset_index(drop=True); st.toast("Deleted activity")
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
            if st.button("Apply changes", key="inline_act_apply"):
                df.loc[row, ["Title","Objective","Steps","Materials","Assessment","Duration (mins)"]] = [title,objective,steps,materials,assessment,int(duration)]
                st.session_state.act_df = df; st.toast("Applied Activity changes")

with tabs[3]:
    st.subheader("Export")
    c1, c2 = st.columns(2)
    if isinstance(st.session_state.get("mcq_df"), pd.DataFrame) and len(st.session_state.mcq_df) > 0:
        csv = st.session_state.mcq_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download MCQs (CSV)", csv, file_name="mcqs.csv", mime="text/csv")
    else:
        st.info("No MCQs to export yet.")
    if isinstance(st.session_state.get("act_df"), pd.DataFrame) and len(st.session_state.act_df) > 0:
        csv2 = st.session_state.act_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Activities (CSV)", csv2, file_name="activities.csv", mime="text/csv")
    else:
        st.info("No Activities to export yet.")

