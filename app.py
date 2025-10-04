# app.py — ADI Builder (stable baseline, API-free)
# Look: ADI green bar, shaded LOW/MED/HIGH bands, highlight pills
# Features: Upload (PDF/PPTX/DOCX), Deep scan, MCQ + MSQ, Activities, Revision
# Exports: DOCX, GIFT, Moodle XML, Course Pack JSON
# No experimental_rerun. No NLTK downloads (safe for Render).

import io, os, re, json, math, random, hashlib
from datetime import datetime
from typing import List, Dict, Tuple

import streamlit as st

# ---------- optional deps guarded ----------
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from pptx import Presentation
except Exception:
    Presentation = None

try:
    import docx  # python-docx
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except Exception:
    docx = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:
    TfidfVectorizer = None

# ---------- brand / policy ----------
ADI_GREEN = "#245a34"
ADI_GREEN_SOFT = "#e9f2ec"
BORDER = "#ececec"
TEXT_SUBTLE = "#667085"

BLOOM = {
    "LOW" : ["define","identify","list","recall","describe","label"],
    "MED" : ["apply","demonstrate","solve","illustrate","classify","compare"],
    "HIGH": ["evaluate","synthesize","design","justify","critique","create"],
}
WEEK_FOCUS = {"LOW": range(1,5), "MED": range(5,10), "HIGH": range(10,15)}

# ---------- utils ----------
def clean_text(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()

def week_to_focus(week: int) -> str:
    if week in WEEK_FOCUS["LOW"]:  return "LOW"
    if week in WEEK_FOCUS["MED"]:  return "MED"
    return "HIGH"

def seeded_rng(seed_items: List[str]) -> random.Random:
    base = "|".join(map(str, seed_items)) + "|" + datetime.utcnow().strftime("%Y%m%d%H")
    h = hashlib.sha256(base.encode()).hexdigest()
    return random.Random(int(h[:16], 16))

def split_sentences(txt: str) -> List[str]:
    # simple sentence splitter (no NLTK)
    txt = txt.replace("\n", " ")
    parts = re.split(r"(?<=[.!?])\s+", txt)
    return [p.strip() for p in parts if len(p.strip()) > 30]

def top_keywords(text: str, k: int = 12) -> List[str]:
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text)]
    if not words:
        return []
    if TfidfVectorizer:
        try:
            vec = TfidfVectorizer(stop_words="english", max_features=max(100, k*5))
            X = vec.fit_transform([text])
            inds = X.toarray().argsort()[0][::-1]
            feats = vec.get_feature_names_out()
            uniq = []
            for i in inds:
                w = feats[i]
                if w not in uniq:
                    uniq.append(w)
                if len(uniq) >= k:
                    break
            return uniq
        except:
            pass
    # fallback: simple frequency
    from collections import Counter
    stop = set("""
        the of and to a in is for on as by with from at this that be are or it an if
        into about under over between more most each other which whose than may can
        would should could also have has had were been being you we they them their
        our us its such these those not no yes do does did done using use used
    """.split())
    freq = Counter([w for w in words if w not in stop])
    return [w for (w, _) in freq.most_common(k)]

# ---------- parsing ----------
def extract_pdf(data: bytes, deep: bool) -> str:
    # try PyMuPDF
    if fitz:
        try:
            doc = fitz.open(stream=data, filetype="pdf")
            pages = range(len(doc)) if deep else range(min(12, len(doc)))
            out = []
            for i in pages:
                try:
                    out.append(doc[i].get_text("text") or "")
                except:
                    pass
            doc.close()
            return clean_text(" ".join(out))
        except:
            pass
    # fallback pypdf
    if PdfReader:
        try:
            r = PdfReader(io.BytesIO(data))
            pages = range(len(r.pages)) if deep else range(min(12, len(r.pages)))
            out = []
            for i in pages:
                try:
                    out.append(r.pages[i].extract_text() or "")
                except:
                    pass
            return clean_text(" ".join(out))
        except:
            pass
    return ""

def extract_pptx(data: bytes) -> str:
    if not Presentation: return ""
    try:
        prs = Presentation(io.BytesIO(data))
        texts = []
        for s in prs.slides:
            for shp in s.shapes:
                if hasattr(shp, "text") and shp.text:
                    texts.append(shp.text)
                if getattr(shp, "table", None):
                    for r in shp.table.rows:
                        for c in r.cells:
                            if c.text: texts.append(c.text)
        return clean_text(" ".join(texts))
    except:
        return ""

def extract_docx(data: bytes) -> str:
    if not docx: return ""
    try:
        d = docx.Document(io.BytesIO(data))
        texts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for r in t.rows:
                for c in r.cells:
                    texts.append(c.text)
        return clean_text(" ".join(texts))
    except:
        return ""

def extract_any(upload, deep: bool) -> str:
    data = upload.read()
    name = upload.name.lower()
    if name.endswith(".pdf"):  return extract_pdf(data, deep)
    if name.endswith((".ppt",".pptx")): return extract_pptx(data)
    if name.endswith((".doc",".docx")): return extract_docx(data)
    return ""

# ---------- session-state init to avoid ValueAssignmentNotAllowed ----------
def ensure_verb_state(level: str, verbs: List[str]):
    for v in verbs:
        k = f"sel_{level}_{v}"
        if k not in st.session_state:
            st.session_state[k] = False

# ---------- question generation ----------
def make_distractors(correct: str, vocab: List[str], rng: random.Random, n: int = 3) -> List[str]:
    # near-miss distractors from vocab; ensure different from correct
    pool = [w for w in vocab if w.lower() != correct.lower()]
    rng.shuffle(pool)
    outs = []
    for w in pool:
        if len(outs) >= n: break
        # small tweaks to create plausible wording
        if len(w) > 3 and w not in outs:
            outs.append(w.capitalize())
    # pad if needed
    while len(outs) < n:
        outs.append(correct[::-1].capitalize())
    return outs[:n]

def synthesize_mcqs(sentences: List[str], vocab: List[str], verbs: List[str],
                    n_q: int, topic: str, allow_multi: bool, rng: random.Random):
    """
    Build a mix of MCQs (single) and MSQs (multi select) from sentences & keywords.
    """
    items = []
    if not sentences:
        sentences = [f"{topic} involves several key principles and terminology relevant to the course."]
    if not vocab:
        vocab = top_keywords(" ".join(sentences), 20)

    rng.shuffle(sentences)
    picked = sentences[: max(10, n_q*3)]

    for s in picked:
        # choose a verb to steer the stem
        verb = rng.choice(verbs or ["identify"])
        # choose a keyword as the "focus" concept
        focus = rng.choice(vocab) if vocab else "concept"
        stem = f"{verb.capitalize()} the best answer related to '{focus}': {s}"
        # decide MSQ or MCQ
        is_msq = allow_multi and (rng.random() < 0.35)
        # choose correct(s)
        if is_msq:
            # two correct options
            corrects = rng.sample(vocab[: min(8,len(vocab))] or [focus], k=min(2, max(1, len(vocab[:8]))))
            distract = []
            for c in corrects:
                distract += make_distractors(c, vocab, rng, n=1)
            # ensure total 4–5 options
            while len(corrects) + len(distract) < 4:
                distract += make_distractors(focus, vocab, rng, n=1)
            # sample to 5 options max
            all_opts = list(set(corrects + distract))
            rng.shuffle(all_opts)
            options = all_opts[:5]
            correct_idx = [options.index(c) for c in options if c in corrects]
            items.append({
                "type":"msq",
                "stem": stem,
                "options": options,
                "answer_index": correct_idx,
                "verb": verb
            })
        else:
            correct = rng.choice(vocab) if vocab else focus
            distract = make_distractors(correct, vocab, rng, n=3)
            options = [correct.capitalize()] + distract
            rng.shuffle(options)
            items.append({
                "type":"mcq",
                "stem": stem,
                "options": options,
                "answer_index": options.index(correct.capitalize()),
                "verb": verb
            })
        if len(items) >= n_q:
            break

    # final shuffle
    rng.shuffle(items)
    return items[:n_q]

# ---------- exports ----------
def export_docx(questions: List[Dict]) -> bytes:
    if not docx:
        return b""
    d = docx.Document()
    head = d.add_paragraph("ADI Knowledge MCQs / MSQs")
    head.runs[0].font.size = Pt(14)
    head.runs[0].bold = True
    d.add_paragraph("")

    for i,q in enumerate(questions, 1):
        p = d.add_paragraph(f"{i}. {q['stem']}")
        p_format = p.paragraph_format
        p_format.space_after = Pt(6)
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if q["type"] == "mcq":
            for j,opt in enumerate(q["options"]):
                d.add_paragraph(f"   {letters[j]}. {opt}")
            d.add_paragraph(f"   Answer: {letters[q['answer_index']]}")
        else:
            for j,opt in enumerate(q["options"]):
                d.add_paragraph(f"   {letters[j]}. {opt}")
            idxs = sorted(q["answer_index"])
            d.add_paragraph("   Answers: " + ", ".join(letters[k] for k in idxs))
        d.add_paragraph("")

    bio = io.BytesIO()
    d.save(bio)
    return bio.getvalue()

def export_gift(questions: List[Dict]) -> str:
    # GIFT supports multiple correct with partial credit using %xx%
    out = []
    for q in questions:
        stem = q["stem"].replace("\n"," ")
        if q["type"] == "mcq":
            opts = []
            for i,opt in enumerate(q["options"]):
                mark = "=" if i == q["answer_index"] else "~"
                opts.append(f"{mark}{opt}")
            out.append(f"::{q['verb']}::{stem}{{\n" + "\n".join(opts) + "\n}\n")
        else:
            # MSQ: split credit equally
            corr = set(q["answer_index"])
            n_correct = max(1, len(corr))
            each = int(100/n_correct)
            opts = []
            for i,opt in enumerate(q["options"]):
                if i in corr:
                    opts.append(f"~%{each}%{opt}")
                else:
                    opts.append(f"~%0%{opt}")
            out.append(f"::{q['verb']}::{stem}{{\n" + "\n".join(opts) + "\n}\n")
    return "\n".join(out)

def export_moodle_xml(questions: List[Dict]) -> str:
    def esc(s): 
        return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    parts = ['<?xml version="1.0" encoding="UTF-8"?>','<quiz>']
    for q in questions:
        if q["type"] == "mcq":
            parts.append("<question type=\"multichoice\">")
            parts.append("<single>true</single>")
        else:
            parts.append("<question type=\"multichoice\">")
            parts.append("<single>false</single>")
        parts.append("<name><text>"+esc(q["verb"])+"</text></name>")
        parts.append("<questiontext format=\"html\"><text>"+esc(q["stem"])+"</text></questiontext>")
        if q["type"] == "mcq":
            for i,opt in enumerate(q["options"]):
                fr = 100 if i==q["answer_index"] else 0
                parts.append(f"<answer fraction=\"{fr}\"><text>{esc(opt)}</text></answer>")
        else:
            corr = set(q["answer_index"])
            n_corr = max(1, len(corr))
            each = int(100/n_corr)
            for i,opt in enumerate(q["options"]):
                fr = each if i in corr else 0
                parts.append(f"<answer fraction=\"{fr}\"><text>{esc(opt)}</text></answer>")
        parts.append("</question>")
    parts.append("</quiz>")
    return "\n".join(parts)

def export_course_pack(course_code: str, instructor: str, lesson: int, week: int,
                       topic: str, questions: List[Dict], activities: List[Dict], revision: List[str]) -> bytes:
    pack = {
        "course": course_code,
        "instructor": instructor,
        "lesson": lesson,
        "week": week,
        "topic": topic,
        "generated_at": datetime.utcnow().isoformat()+"Z",
        "questions": questions,
        "activities": activities,
        "revision": revision,
    }
    return json.dumps(pack, indent=2).encode()

# ---------- activities / revision (light but stable) ----------
def generate_activities(selected_verbs: List[str], duration: int, rng: random.Random) -> List[Dict]:
    bank = {
        "apply":     "Small group problem where learners apply {topic} to a realistic scenario.",
        "demonstrate":"Pairs demonstrate a procedure or workflow related to {topic}; peers give feedback.",
        "solve":     "Timed challenge: Solve a quantitative/logic task derived from {topic}.",
        "illustrate":"Sketch / diagram the process for {topic}, label key steps.",
        "classify":  "Sort mixed examples/non-examples of {topic} into correct categories.",
        "compare":   "Tabletop compare/contrast activity with {topic} alternatives and trade-offs.",
        "evaluate":  "Critique a short case; defend judgments using criteria aligned to {topic}.",
        "synthesize":"Combine two ideas from {topic} into a single improved method; present.",
        "design":    "Design a component/process meeting constraints that relate to {topic}.",
        "justify":   "Justify a chosen approach to {topic} against two alternatives.",
        "critique":  "Peer-review artifacts; annotate strengths/risks for {topic}.",
        "create":    "Build a prototype or draft SOP related to {topic} and test with peers.",
        "define":    "Team builds a concept map of {topic} terms.",
        "identify":  "Speed-round: identify correct terms/tools from images for {topic}.",
        "list":      "List-do: generate a checklist for operators using {topic}.",
        "recall":    "Flashcard relay on key {topic} facts.",
        "describe":  "Write a 5-sentence explanation of {topic} for a new recruit.",
        "label":     "Label parts/blocks in a provided {topic} diagram.",
    }
    rng.shuffle(selected_verbs)
    verbs = selected_verbs[: min(3, len(selected_verbs))] or ["apply"]
    acts = []
    for v in verbs:
        desc = bank.get(v, "Group task aligned to {topic}.").format(topic=st.session_state.get("topic","the topic"))
        acts.append({"verb": v, "duration_min": duration, "description": desc})
    return acts

def generate_revision(selected_verbs: List[str], rng: random.Random) -> List[str]:
    prompts = {
        "define":    "Make a 12-term glossary from today’s lesson; add 1-sentence definitions.",
        "identify":  "Snap 3 photos of tools/components used in lab; annotate use & one risk.",
        "list":      "Create a 10-step checklist for the weekly lab linked to the lesson.",
        "recall":    "Write a 6-point crib sheet of facts to memorize for next session.",
        "describe":  "Describe a real-world use-case for the technique you learned.",
        "label":     "Print a diagram and label every part; bring to next class.",
        "apply":     "Solve two variant problems similar to today’s example; show workings.",
        "demonstrate":"Record a short screen capture demonstrating the software step.",
        "solve":     "Attempt the practice set 1-A; mark uncertainties.",
        "illustrate":"Draw a neat block diagram of the workflow you followed.",
        "classify":  "Collect 6 examples from manuals and classify them into categories.",
        "compare":   "Write a paragraph comparing two methods covered today.",
        "evaluate":  "Review a short case; write 5 bullet judgments with reasons.",
        "synthesize":"Combine two techniques from today into a single procedure.",
        "design":    "Sketch an improved fixture/tool to reduce error; annotate.",
        "justify":   "Write a justification for selecting one process over another.",
        "critique":  "Annotate a peer submission; highlight two strengths & one risk.",
        "create":    "Draft a one-page SOP capturing today’s process.",
    }
    rng.shuffle(selected_verbs)
    sel = selected_verbs[:3] or ["recall","apply","design"]
    return [prompts.get(v, "Review notes and summarise in five bullet points.") for v in sel]

# ---------- UI helpers ----------
def header():
    st.markdown(
        f"""
        <div style="background:{ADI_GREEN}; color:#fff; padding:14px 16px; border-radius:12px;">
            <div style="font-weight:700; font-size:18px;">ADI Builder — Lesson Activities & Questions</div>
            <div style="opacity:.85; font-size:12px;">Sleek, professional and engaging. Print-ready handouts for your instructors.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def band_title(level:str)->str:
    return "LOW (Weeks 1–4): Remember / Understand" if level=="LOW" else \
           "MEDIUM (Weeks 5–9): Apply / Analyse" if level=="MED" else \
           "HIGH (Weeks 10–14): Evaluate / Create"

def verb_pill(level: str, verb: str):
    key = f"sel_{level}_{verb}"
    selected = st.session_state.get(key, False)
    pill_bg = "#dfece6" if selected else "#f6f6f6"
    style = f"background:{pill_bg}; border:1px solid {BORDER}; border-radius:999px; padding:8px 16px; display:inline-block; margin:6px 10px 6px 0; color:#333; font-weight:500;"
    # Use checkbox for state, but render the pill label ourselves
    c1, c2 = st.columns([1,8])
    with c1:
        st.checkbox("", key=key, value=selected, label_visibility="collapsed")
    with c2:
        st.markdown(f"<div style='{style}'>{verb}</div>", unsafe_allow_html=True)

def render_band(level: str, focus: str):
    # band highlight by week focus
    band_bg = "#eef6f1" if level == focus else "#f9fafb"
    st.markdown(
        f"<div style='background:{band_bg}; border:1px solid {BORDER}; border-radius:12px; padding:10px 14px; margin:12px 0 6px; color:#0f2b1a; font-weight:700;'>{band_title(level)}</div>",
        unsafe_allow_html=True
    )
    # draw pills
    row = st.container()
    with row:
        for v in BLOOM[level]:
            verb_pill(level, v)

def selected_verbs()->List[str]:
    out=[]
    for lvl, vs in BLOOM.items():
        for v in vs:
            if st.session_state.get(f"sel_{lvl}_{v}", False):
                out.append(v)
    return out

# ---------- page ----------
st.set_page_config(page_title="ADI Builder", page_icon="🧰", layout="wide")
header()

# Tabs
tab_mcq, tab_act, tab_rev = st.tabs(["Knowledge MCQs (ADI Policy)", "Skills Activities", "Revision"])

with st.sidebar:
    st.markdown("### Upload (optional)")
    deep = st.checkbox("Deep scan (all pages, slower)", value=True, help="PDF: scan all pages with PyMuPDF/PyPDF. DOCX/PPTX read fully.")
    up = st.file_uploader("Drag and drop file here", type=["pdf","pptx","ppt","docx","doc"])
    parsed_text = ""
    if up is not None:
        try:
            parsed_text = extract_any(up, deep)
            if parsed_text:
                st.success("Parsed successfully")
            else:
                st.warning("No extractable text found (scanned image PDF? Try DOCX/PPTX).")
        except Exception as e:
            st.error(f"Parsing error: {e}")

    st.markdown("---")
    st.markdown("### Course context")
    lesson = st.selectbox("Lesson", list(range(1,15)), index=0)
    week = st.selectbox("Week", list(range(1,15)), index=0)
    topic = st.text_input("Topic / outcome", placeholder="Module description, knowledge & skills outcomes")
    st.session_state["topic"] = topic

    st.markdown("### Number of MCQs")
    n_mcq = st.selectbox("How many questions?", [5,10,15,20,30], index=1)

    st.markdown("---")
    st.markdown("### Activities")
    duration = st.selectbox("Activity duration (minutes)", [5,10,15,20,30,40,50,60], index=1)

    st.markdown("---")
    st.markdown("### Instructor filter (optional)")
    instructor = st.text_input("Instructor name", value="")

    st.markdown("---")
    st.markdown("### Export")

# init verb state (prevents Streamlit assignment error)
for lvl in BLOOM:
    ensure_verb_state(lvl, BLOOM[lvl])

auto_focus = week_to_focus(week)

with tab_mcq:
    # ribbon progress area / source text box (editable)
    st.markdown(
        f"<div style='border:1px solid {BORDER}; border-radius:10px; padding:10px; background:#f6f7f8; color:{TEXT_SUBTLE};'>"
        f"We've uploaded your file. If this is empty, the PDF may be scanned. Try DOCX/PPTX or paste text.</div>",
        unsafe_allow_html=True
    )
    source_text = st.text_area("Source text (editable)", value=parsed_text, height=160, label_visibility="collapsed")

    # Bloom header + bands
    render_band("LOW", auto_focus)
    render_band("MED", auto_focus)
    render_band("HIGH", auto_focus)

    # question type selector
    qtype = st.radio("Question types", ["Single-answer MCQ only", "Mix MCQ + MSQ (multi-select)"], horizontal=True)

    cgen, cregen = st.columns([1,1])
    with cgen:
        go = st.button("✨ Generate MCQs", type="primary")
    with cregen:
        regen = st.button("↻ Regenerate")

    st.markdown("---")

    if go or regen:
        rng = seeded_rng([lesson, week, topic, instructor or ""])
        verbs = selected_verbs()
        if not verbs:
            # nudge to band verbs
            if auto_focus == "LOW": verbs = BLOOM["LOW"]
            elif auto_focus == "MED": verbs = BLOOM["MED"]
            else: verbs = BLOOM["HIGH"]
        sents = split_sentences(source_text) if source_text else []
        vocab = top_keywords(source_text, 24) if source_text else []
        allow_multi = (qtype == "Mix MCQ + MSQ (multi-select)")
        qs = synthesize_mcqs(sents, vocab, verbs, n_mcq, topic or "the topic", allow_multi, rng)
        st.session_state["qs"] = qs

    qs = st.session_state.get("qs", [])
    if qs:
        st.markdown("#### Preview")
        for i, q in enumerate(qs, 1):
            typ = "MSQ" if q["type"]=="msq" else "MCQ"
            st.markdown(f"**{i}. ({typ})** {q['stem']}")
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            for j,opt in enumerate(q["options"]):
                st.markdown(f"- {letters[j]}. {opt}")
            if q["type"]=="mcq":
                st.caption(f"Answer: {letters[q['answer_index']]}")
            else:
                idxs = sorted(q["answer_index"])
                st.caption("Answers: " + ", ".join(letters[k] for k in idxs))

        # downloads
        st.markdown("#### Download")
        colA, colB, colC, colD = st.columns(4)
        with colA:
            docx_bytes = export_docx(qs)
            st.download_button("Word (DOCX)", data=docx_bytes, file_name="adi_mcqs.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with colB:
            gift_text = export_gift(qs)
            st.download_button("GIFT", data=gift_text, file_name="adi_mcqs.gift", mime="text/plain")
        with colC:
            moodle_xml = export_moodle_xml(qs)
            st.download_button("Moodle XML", data=moodle_xml, file_name="adi_mcqs.xml", mime="application/xml")
        with colD:
            # course pack now (questions only for this tab)
            pack = export_course_pack(st.session_state.get("course",""), instructor, lesson, week, topic, qs, [], [])
            st.download_button("Course Pack (JSON)", data=pack, file_name="course_pack.json", mime="application/json")
    else:
        st.info("Please select verbs and click **Generate MCQs**.")

with tab_act:
    st.markdown("#### Activities")
    verbs = selected_verbs()
    rng = seeded_rng([lesson, week, topic, instructor or ""])
    acts = generate_activities(verbs, duration, rng)
    st.session_state["acts"] = acts

    for i,a in enumerate(acts, 1):
        st.markdown(f"**{i}. ({a['verb']}, {a['duration_min']} min)** {a['description']}")

    col1, col2 = st.columns(2)
    with col1:
        pack = export_course_pack(st.session_state.get("course",""), instructor, lesson, week, topic,
                                  st.session_state.get("qs", []), acts, [])
        st.download_button("Download Course Pack (JSON)", data=pack, file_name="course_pack.json", mime="application/json")

with tab_rev:
    st.markdown("#### Revision")
    rng = seeded_rng([lesson, week, topic, instructor or ""])
    verbs = selected_verbs()
    rev = generate_revision(verbs, rng)
    st.session_state["rev"] = rev
    for i,r in enumerate(rev,1):
        st.markdown(f"**{i}.** {r}")

    col1, col2 = st.columns(2)
    with col1:
        pack = export_course_pack(st.session_state.get("course",""), instructor, lesson, week, topic,
                                  st.session_state.get("qs", []), st.session_state.get("acts", []), rev)
        st.download_button("Download Course Pack (JSON)", data=pack, file_name="course_pack.json", mime="application/json")

# ---------- footer hint ----------
st.markdown(
    f"<div style='margin-top:18px; color:{TEXT_SUBTLE}; font-size:12px;'>"
    f"Tip: Change Week to auto-highlight Bloom band. Select verbs as rounded pills, then Generate.</div>",
    unsafe_allow_html=True
)

