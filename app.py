import io, re, random
import streamlit as st

# ---------------- PAGE & BRANDING ----------------
st.set_page_config(page_title="ADI Builder", page_icon="🧩", layout="centered")

PRIMARY = "#003a8c"     # ADI deep blue
ACCENT_ACT = "#e8f7ee"  # light green for Activities
ACCENT_MCQ = "#e9f2ff"  # light blue for MCQs

# Logo (put logo.png in the repo)
st.image("logo.png", width=140)
st.markdown(
    f"""
    <style>
      .adi-title {{ font-weight:700; font-size:1.4rem; color:{PRIMARY}; margin-bottom:8px; }}
      .adi-card {{ background:#fff; border:1px solid #d0d7de; border-radius:12px; padding:16px; 
                   box-shadow:0 3px 10px rgba(0,0,0,.06); }}
      .preview {{ border:1px solid #d0d7de; border-radius:10px; padding:12px; white-space:pre-wrap; 
                  font-family: ui-monospace, Menlo, Consolas, monospace; }}
      .small {{ color:#555; font-size:.92rem; }}
      .badge {{ display:inline-block; padding:6px 10px; border-radius:8px; font-weight:600; }}
    </style>
    <div class="adi-title">ADI Knowledge & Activity Builder</div>
    <div class="small">Upload one file (PDF / DOCX / PPTX) → pick Week & Lesson (optional) → Generate → Download .docx</div>
    """,
    unsafe_allow_html=True
)

# ---------------- FILE READERS ----------------
def read_pdf_text(file_bytes: bytes) -> str:
    import fitz  # PyMuPDF
    out = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for p in doc: out.append(p.get_text("text"))
    return "\n".join(out)

def read_docx_text(file_bytes: bytes) -> str:
    from docx import Document
    d = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in d.paragraphs)

def read_pptx_text(file_bytes: bytes) -> str:
    from pptx import Presentation
    prs = Presentation(io.BytesIO(file_bytes))
    lines = []
    for s in prs.slides:
        for sh in s.shapes:
            if hasattr(sh, "text") and sh.text:
                lines.extend(sh.text.splitlines())
    return "\n".join(lines)

def load_text_any(uploaded):
    if not uploaded: return ""
    name = (uploaded.name or "").lower()
    data = uploaded.read()
    if name.endswith(".pdf"): return read_pdf_text(data)
    if name.endswith(".docx"): return read_docx_text(data)
    if name.endswith(".pptx") or name.endswith(".ppt"): return read_pptx_text(data)
    try: return data.decode("utf-8", errors="ignore")
    except: return ""

# ---------------- TEXT HELPERS ----------------
def lines_from_text(raw: str):
    keep = []
    for ln in raw.splitlines():
        s = re.sub(r"^\s*[\d•\-–\.]+\s*", "", ln).strip()
        if not s: continue
        w = len(s.split())
        if 2 <= w <= 24: keep.append(s)
    return keep

def simplify(s: str) -> str:
    t = s.strip().strip("“”\"'").rstrip(",;:")
    def _paren(m):
        items = [x.strip() for x in m.group(1).split(",") if x.strip()]
        if len(items)==1: return items[0]
        if len(items)==2: return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"
    t = re.sub(r"\(([^)]+)\)", _paren, t)
    replace = [
        (r"utili[sz]e","use"), (r"implement","carry out"), (r"stakeholders?","people involved"),
        (r"constraints?","limits"), (r"mitigate","reduce"), (r"objective(s)?",r"goal\\1"),
        (r"deliverable(s)?",r"result\\1"), (r"outcome(s)?",r"result\\1"), (r"scope","what is included"),
        (r"facilitate","help"), (r"evaluate","judge"), (r"assess","check"), (r"analy[sz]e","look at"),
        (r"synthesi[sz]e","bring together"), (r"initiation","start"), (r"execution","doing"),
        (r"monitoring and controlling","checking and adjusting"), (r"feasible","workable"),
        (r"determine","decide"), (r"establish","set up"), (r"identify","find"), (r"demonstrate","show")
    ]
    for pat, rep in replace: t = re.sub(pat, rep, t, flags=re.I)
    words = t.split()
    if len(words)>20: t = " ".join(words[:20])
    return t

def detect_week_lesson(lines):
    reW, reL = re.compile(r"\b(week|wk)\s*(\d{1,2})\b", re.I), re.compile(r"\b(lesson|lsn|l)\s*(\d{1,2})\b", re.I)
    w = l = None
    for ln in lines[:200]:
        if w is None:
            m = reW.search(ln)
            if m: w = int(m.group(2))
        if l is None:
            m = reL.search(ln)
            if m: l = int(m.group(2))
        if w and l: break
    return w, l

def find_section(lines, week=None, lesson=None):
    start, end, note = 0, min(200, len(lines)), ""
    if week or lesson:
        reW = re.compile(rf"\b(week|wk)\s*{week}\b", re.I) if week else None
        reL = re.compile(rf"\b(lesson|lsn|l)\s*{lesson}\b", re.I) if lesson else None
        if week and lesson:
            for i, ln in enumerate(lines):
                if reW.search(ln) and reL.search(ln): start = i; break
        elif week:
            idx = next((i for i,ln in enumerate(lines) if reW.search(ln)), -1)
            if idx>=0: start = idx
        elif lesson:
            idx = next((i for i,ln in enumerate(lines) if reL.search(ln)), -1)
            if idx>=0: start = idx
    for k in range(start+1, len(lines)):
        if re.search(r"\b(week|wk)\s*\d+\b", lines[k], re.I) or re.search(r"\b(lesson|lsn|l)\s*\d+\b", lines[k], re.I):
            end = k; break
    return start, end, note

# ---------------- ACTIVITIES ----------------
def activity_steps(obj):
    return [
        f"Break {obj} into 4–6 steps.",
        "Practise once with a timer and self-check.",
        "Repeat once to reduce errors.",
        "Capture a photo or file of the output.",
        "Write a 3-line reflection."
    ]

def build_activities(text, week=None, lesson=None, variant=2):
    lines = lines_from_text(text)
    note = ""
    if week is None or lesson is None:
        aw, al = detect_week_lesson(lines)
        week = week or aw or 1
        lesson = lesson or al or 1
        if not (aw and al): note = "ℹ️ Used detected/default Week/Lesson."

    start, end, n2 = find_section(lines, week, lesson)
    if n2: note = (note + " " + n2).strip()
    seg = lines[start:end] if start<end else lines[:200]

    topics, seen = [], set()
    for ln in seg:
        s = simplify(ln)
        if s and s not in seen: seen.add(s); topics.append(s)
    if not topics: return "⚠️ Couldn’t find short, usable lines in that section.", note

    random.seed(2025 + int(variant))
    random.shuffle(topics)
    picked = topics[:min(3, len(topics))]

    blocks=[]
    for t in picked:
        obj = re.sub(r"^(plan(ning)?|analyse|analyze|evaluate|assess|design|create|prepare|document|monitor|control|coordinate)\b", "", t, flags=re.I).strip() or "the task"
        steps = "\n".join(f"- {s}" for s in activity_steps(obj))
        crit  = "\n".join(f"- {c}" for c in [
            "Steps are complete and consistent",
            "Choices are justified for the task",
            "Output is clear and usable (one page max)",
            "Checks/evidence included",
            "Finished within the time"
        ])
        block = (
            f"## Week {week} — Lesson {lesson}\n"
            f"### Practical Task — {t}\n"
            f"**Task:** Complete a one-page worksheet that plans {obj} for a short scenario.\n"
            f"**Inputs:** eBook/slides excerpt + simple worksheet.\n"
            f"**Steps:**\n{steps}\n"
            f"**Success criteria:**\n{crit}\n"
            f"**Output:** One-page worksheet + 3-line reflection.\n"
            f"**Estimated time:** 30 minutes."
        )
        blocks.append(block)
    return "\n\n---\n\n".join(blocks), note

# ---------------- MCQs ----------------
BLOOM_VERBS = {
    "Remember":["define","list","identify","recall"],
    "Understand":["explain","summarise","classify","describe","give an example"],
    "Apply":["apply","use","demonstrate","implement"],
    "Analyse":["compare","contrast","differentiate","categorise","prioritise"],
    "Evaluate":["justify","critique","assess","defend","select"],
    "Create":["design","formulate","compose","propose","develop"]
}

def stem_from_line(line, level="Understand"):
    verb = random.choice(BLOOM_VERBS.get(level, BLOOM_VERBS["Understand"]))
    base = simplify(line)
    return f"{verb.capitalize()} {base}."

def distractors_from_line(line):
    base = simplify(line)
    words = [w for w in re.sub(r"[^a-zA-Z0-9\s]", " ", base).split() if len(w)>3]
    pool = list({w.lower() for w in words})[:6]
    random.shuffle(pool)
    ds=[]
    while len(ds)<3:
        if not pool: break
        cand = " ".join(random.sample(pool, min(2, max(1, len(pool)//3)))).capitalize()
        if cand.lower() not in {"all of the above","none of the above","true","false"} and cand not in ds:
            ds.append(cand)
    while len(ds)<3:
        extra = random.choice(["Operational detail","Unrelated concept","Background note"])
        if extra not in ds: ds.append(extra)
    return ds

def build_mcqs(text, week=None, lesson=None, qmin=5, qmax=10, level="Understand", variant=2):
    lines = lines_from_text(text)
    note = ""
    if week is None or lesson is None:
        aw, al = detect_week_lesson(lines)
        week = week or aw or 1
        lesson = lesson or al or 1
        if not (aw and al): note = "ℹ️ Used detected/default Week/Lesson."
    start, end, n2 = find_section(lines, week, lesson)
    if n2: note = (note + " " + n2).strip()
    seg = lines[start:end] if start<end else lines[:200]

    topics, seen = [], set()
    for ln in seg:
        s = simplify(ln)
        if s and s not in seen: seen.add(s); topics.append(s)
    if not topics: return "⚠️ Couldn’t find usable lines for MCQs.", note

    random.seed(10101 + int(variant))
    random.shuffle(topics)
    n = min(max(qmin,5), max(qmax,10), len(topics))
    qs=[]
    for i in range(n):
        line = topics[i]
        stem = stem_from_line(line, level)
        correct = simplify(line).capitalize()
        distractors = distractors_from_line(line)
        options = distractors + [correct]
        random.shuffle(options)
        options = [o for o in options if o.lower() not in {"all of the above","none of the above","true","false"}]
        while len(options)<4:
            filler = random.choice(["Operational detail","Background note","Related term"])
            if filler not in options: options.append(filler)
        qs.append((stem, options[:4], correct))

    out = [f"## Week {week} — Lesson {lesson}", f"### MCQ Bank ({len(qs)} questions)"]
    for idx,(stem,opts,correct) in enumerate(qs, start=1):
        out.append(f"\n**Q{idx}. {stem}**")
        letters="abcd"
        for j,opt in enumerate(opts):
            out.append(f"{letters[j]}) {opt}")
        out.append(f"Correct: {correct}")
    return "\n".join(out), note

# ---------------- DOCX EXPORT ----------------
def to_docx_bytes(title: str, markdown_text: str) -> bytes:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    doc = Document()
    h = doc.add_paragraph(title)
    h.style.font.size = Pt(16)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")
    for line in (markdown_text or "").splitlines():
        if line.startswith("## "): doc.add_paragraph(line[3:]).style = doc.styles["Heading 1"]
        elif line.startswith("### "): doc.add_paragraph(line[4:]).style = doc.styles["Heading 2"]
        elif line.startswith("- "): doc.add_paragraph(line[2:], style=doc.styles["List Bullet"])
        elif re.match(r"^\*\*(.+?)\:\*\*\s*(.*)$", line):
            m = re.match(r"^\*\*(.+?)\:\*\*\s*(.*)$", line); doc.add_paragraph(f"{m.group(1)}: {m.group(2)}")
        else: doc.add_paragraph(line)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0)
    return bio.getvalue()

# ---------------- UI ----------------
st.markdown('<div class="adi-card">', unsafe_allow_html=True)
uploaded = st.file_uploader("Upload file (PDF / DOCX / PPTX)", type=["pdf","docx","pptx","ppt"])

c1, c2 = st.columns(2)
mode = c1.radio("Builder", ["Activities", "Questions (MCQ)"])
variant = c2.slider("Version", 1, 5, 2, help="Pick a different version for variety")

manual = st.checkbox("Choose Week/Lesson manually (otherwise Quick Generate tries to detect)")
if manual:
    wc1, wc2 = st.columns(2)
    week = wc1.selectbox("Week", list(range(1,15)), index=0)
    lesson = wc2.selectbox("Lesson", list(range(1,5)), index=0)
else:
    week = lesson = None

gen = st.button("Generate")
st.markdown('</div>', unsafe_allow_html=True)

badge_color = ACCENT_ACT if mode=="Activities" else ACCENT_MCQ
st.markdown(f"<span class='badge' style='background:{badge_color}'>Mode: {mode}</span>", unsafe_allow_html=True)

if gen:
    raw = load_text_any(uploaded)
    if not raw.strip():
        st.warning("Please upload a readable PDF/DOCX/PPTX file.")
        st.session_state["text"] = ""
        st.session_state["note"] = ""
    else:
        if mode=="Activities":
            text, note = build_activities(raw, week, lesson, variant)
        else:
            text, note = build_mcqs(raw, week, lesson, qmin=5, qmax=10, level="Understand", variant=variant)
        st.session_state["text"] = text
        st.session_state["note"] = note

if st.session_state.get("note"): st.info(st.session_state["note"])

st.markdown('<div class="preview">', unsafe_allow_html=True)
st.write(st.session_state.get("text",""))
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.get("text"):
    # pull Week/Lesson if present
    m = re.search(r"##\s*Week\s+(\d+)\s+—\s+Lesson\s+(\d+)", st.session_state["text"])
    title = "ADI Activity Briefs" if mode=="Activities" else "ADI Knowledge MCQs"
    if m: title += f" — Week {m.group(1)} Lesson {m.group(2)}"
    docx = to_docx_bytes(title, st.session_state["text"])
    st.download_button("Download .docx", data=docx, file_name=f"{title}.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
