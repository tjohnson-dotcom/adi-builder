# app.py — ADI Builder (stable + Simple MCQ editor)
# Offline-friendly: Word (.docx) + Moodle GIFT export. Optional deps:
#   pip install streamlit pandas python-docx pdfplumber python-pptx
import io, os, re, random, datetime as dt
from typing import List, Optional
import pandas as pd
import streamlit as st

# ----------------
# Page config & CSS
# ----------------
st.set_page_config(page_title="ADI Builder", page_icon="✅", layout="wide")

ADI_GREEN = "#245a34"; ADI_GREEN_DARK = "#1a4426"; ADI_GOLD = "#C8A85A"; ADI_STONE = "#f4f4f2"
CSS = f"""
<style>
:root {{ --adi-green:{ADI_GREEN}; --adi-green-dark:{ADI_GREEN_DARK}; --adi-gold:{ADI_GOLD}; --adi-stone:{ADI_STONE}; }}
html, body {{ background: var(--adi-stone) !important; }}
.block-container {{ max-width: 1200px; }}
.adi-ribbon {{ height:6px; background:linear-gradient(90deg,var(--adi-green),var(--adi-green-dark) 70%, var(--adi-gold)); border-radius:0 0 12px 12px; box-shadow:0 2px 8px rgba(0,0,0,.08); margin-bottom:8px; }}
.adi-title {{ font-size:2.0rem; font-weight:900; color:var(--adi-green); }}
.adi-sub {{ color:#4b5563; font-weight:600; font-size:1.02rem; letter-spacing:.2px; display:block; text-align:left; margin-top:.2rem; }}
.adi-card {{ background:#fff; border:1px solid rgba(0,0,0,.06); border-radius:20px; padding:20px; box-shadow:0 8px 24px rgba(10,24,18,.08); }}
.adi-section {{ border-top:3px solid var(--adi-gold); margin:8px 0 16px; box-shadow:0 -1px 0 rgba(0,0,0,.02) inset; }}

/* Radios as pill look */
.stRadio > div[role="radiogroup"] {{ display:flex; gap:10px; flex-wrap:wrap; }}
.stRadio [role="radiogroup"] > div label {{ border:2px solid var(--adi-green); border-radius:999px; padding:8px 14px; font-weight:800; background:#fff; color:#1f2937; }}
.stRadio [role="radiogroup"] > div[aria-checked="true"] label {{ background:#f7faf8; box-shadow:inset 0 0 0 3px var(--adi-gold); }}

/* Policy pills */
.pills {{ display:flex; gap:.5rem; flex-wrap:wrap; margin:.25rem 0 .5rem; }}
.pill {{ background:#fff;border:2px solid rgba(0,0,0,.08);padding:.35rem .7rem;border-radius:999px;font-weight:800; }}
.pill.current {{ border-color:var(--adi-gold); box-shadow:inset 0 0 0 3px var(--adi-gold); }}
.pill.match {{ background:#e8f5ee; border-color:#1f7a4c; }}
.pill.mismatch {{ background:#fff7ed; border-color:#fed7aa; }}
.badge-ok,.badge-warn{{display:inline-flex;align-items:center;font-weight:800;border-radius:10px;padding:.3rem .55rem;border:1px solid transparent;}}
.badge-ok{{background:#e8f5ee;color:#14532d;border-color:#86efac;}}
.badge-warn{{background:#fff7ed;color:#7c2d12;border-color:#fdba74;}}

/* Buttons */
.stButton > button, .stDownloadButton > button[kind="primary"], .stButton > button[kind="primary"] {{
  background: var(--adi-green) !important; border-color: var(--adi-green) !important; color: #fff !important;
}}
.stButton > button:hover, .stDownloadButton > button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {{
  background: var(--adi-green-dark) !important; border-color: var(--adi-green-dark) !important;
}}
.stButton > button:focus{{ box-shadow:0 0 0 3px rgba(36,90,52,.25) !important; }}

/* Slider thumb & track */
[data-testid="stSlider"] [role="slider"]{{ background: var(--adi-green) !important; border:2px solid var(--adi-green) !important; }}
[data-testid="stSlider"] div[data-baseweb="slider"] > div > div:nth-child(3){{ background: var(--adi-green) !important; }}
[data-testid="stSlider"] div[data-baseweb="slider"] > div > div:nth-child(2){{ background: rgba(36,90,52,.15) !important; }}

/* Verbs chips */
[data-testid="stMultiSelect"] [data-baseweb="tag"]{{ background:#e8f5ee !important; color:#1a3d2f !important; border:2px solid var(--adi-green) !important; border-radius:999px !important; font-weight:700 !important; }}
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg{{ fill: var(--adi-green) !important; color: var(--adi-green) !important; }}

/* Data editor: compact input padding for options */
[data-testid="stDataEditor"] td div[data-baseweb="input"] {{ padding: 4px 8px; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<div class='adi-ribbon'></div>", unsafe_allow_html=True)

# --------------
# Header
# --------------
c1,c2 = st.columns([1,6], vertical_alignment="center")
with c1:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=120)
    else:
        st.markdown("**ADI**")
with c2:
    st.markdown("<div class='adi-title'>ADI Builder</div>", unsafe_allow_html=True)
    st.markdown("<div class='adi-sub'>Clean ADI look · Pill radios · Policy pills · Verb picker</div>", unsafe_allow_html=True)

# --------------
# Constants & helpers
# --------------
BLOOM_LEVELS = ["Remember","Understand","Apply","Analyze","Evaluate","Create"]
BLOOM_TIER = {"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}
BLOOM_VERBS = {
    "Remember": ["define","list","recall","identify","label","name","state","match","recognize","outline","select","repeat"],
    "Understand": ["explain","summarize","classify","describe","discuss","interpret","paraphrase","compare","illustrate","infer"],
    "Apply": ["apply","demonstrate","execute","implement","solve","use","calculate","perform","simulate","carry out"],
    "Analyze": ["analyze","differentiate","organize","attribute","deconstruct","compare/contrast","examine","test","investigate"],
    "Evaluate": ["evaluate","argue","assess","defend","judge","justify","critique","recommend","prioritize","appraise"],
    "Create": ["create","design","compose","construct","develop","plan","produce","propose","assemble","formulate"],
}

def policy_tier(week:int)->str:
    if 1<=week<=4: return "Low"
    if 5<=week<=9: return "Medium"
    return "High"

def weighted_bloom_sequence(selected:str, n:int, rng:random.Random):
    idx=BLOOM_LEVELS.index(selected); weights=[]
    for i in range(len(BLOOM_LEVELS)):
        dist=abs(i-idx); weights.append({0:5,1:3,2:2,3:1}[min(dist,3)])
    seq=[]
    for _ in range(n):
        x=rng.uniform(0,sum(weights)); acc=0
        for lv,w in zip(BLOOM_LEVELS,weights):
            acc+=w
            if x<=acc: seq.append(lv); break
    return seq

# Optional parsers — degrade gracefully if libs are missing
def extract_pdf(b:bytes)->str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            return "\n".join([(p.extract_text() or "") for p in pdf.pages])
    except Exception:
        return ""

def extract_pptx(b:bytes)->str:
    try:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(b)); out=[]
        for s in prs.slides:
            for sh in s.shapes:
                if hasattr(sh,"text"): out.append(sh.text)
        return "\n".join(out)
    except Exception:
        return ""

def extract_docx(b:bytes)->str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(b))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""

# Generators
def offline_mcqs(src_text:str, blooms:list, verbs:List[str] , n:int):
    base=[s.strip() for s in re.split(r'[.\n]', src_text or "") if s.strip()] or ["This unit covers core concepts and applied practice."]
    if not verbs: verbs=["identify"]
    vcycle=(verbs*((n//max(1,len(verbs)))+1))[:n]
    rows=[]
    for i in range(n):
        b=blooms[i%len(blooms)] if blooms else "Understand"
        tier=BLOOM_TIER[b]
        fact=base[i%len(base)]
        v=vcycle[i].capitalize()
        stem=f"{v} the MOST appropriate statement about: {fact}"
        opts=[f"A) A correct point about {fact}.",
              f"B) An incorrect detail about {fact}.",
              f"C) Another incorrect detail about {fact}.",
              f"D) A distractor unrelated to {fact}."]
        answer="A"
        rows.append({"Bloom":b,"Tier":tier,"Q#":i+1,"Question":stem,"Option A":opts[0],"Option B":opts[1],"Option C":opts[2],"Option D":opts[3],"Answer":answer,"Explanation":f"Verb focus: {v} · Tier: {tier}"})
    return pd.DataFrame(rows, columns=["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"])

def build_activities(src_text:str, blooms:List[str], verbs:List[str], duration:int, diff:str, n:int=3)->List[str]:
    base=[s.strip() for s in re.split(r'[.\n]', src_text or "") if s.strip()] or ["today's topic"]
    vcycle=(verbs*((n//max(1,len(verbs)))+1))[:n] if verbs else ["discuss"]*n
    acts=[]
    for i in range(n):
        lv=blooms[i%len(blooms)] if blooms else "Understand"; vt=vcycle[i].capitalize(); topic=base[i%len(base)]
        if lv in ("Evaluate","Create"):
            prompt=f"{vt} and present a structured solution/prototype for: {topic}."
        elif lv in ("Apply","Analyze"):
            prompt=f"{vt} and demonstrate/apportion key components of: {topic}."
        else:
            prompt=f"{vt} and summarize the core idea of: {topic}."
        acts.append(f"[{duration} min] {prompt} ({diff.lower()})")
    return acts

def to_gift(df:pd.DataFrame)->str:
    out=[]
    for _,r in df.iterrows():
        q=str(r.get("Question","")).replace("\n"," ")
        opts=[r.get("Option A",""),r.get("Option B",""),r.get("Option C",""),r.get("Option D","")]
        ans_letter = str(r.get("Answer","A")).strip().upper()
        if ans_letter not in "ABCD": ans_letter="A"
        ans="ABCD".index(ans_letter)
        parts=[]
        for i,o in enumerate(opts):
            s=str(o).replace("}","\\}")
            parts.append(("=" if i==ans else "~")+s)
        out.append("{"+q+"}{"+" ".join(parts)+"}")
    return "\n\n".join(out)

def export_docx(df:pd.DataFrame, activities:List[str], lesson:int, week:int)->Optional[bytes]:
    try:
        from docx import Document
    except Exception:
        return None
    doc=Document(); doc.add_heading("ADI Builder Export",level=1)
    doc.add_paragraph(f"Lesson {lesson} · Week {week}")
    if df is not None and not df.empty:
        doc.add_heading("MCQs",level=2)
        tbl=doc.add_table(rows=1,cols=9); hdr=tbl.rows[0].cells
        for i,c in enumerate(["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer"]): hdr[i].text=c
        for _,r in df.iterrows():
            row=tbl.add_row().cells
            vals=[r.get("Bloom",""),r.get("Tier",""),str(r.get("Q#","")),r.get("Question",""),
                  r.get("Option A",""),r.get("Option B",""),r.get("Option C",""),r.get("Option D",""),str(r.get("Answer",""))]
            for i,v in enumerate(vals): row[i].text=str(v)
    if activities:
        doc.add_heading("Activities",level=2)
        for i,a in enumerate(activities, start=1): doc.add_paragraph(f"{i}. {a}")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

# ----------------
# Session defaults
# ----------------
if "mcq_df" not in st.session_state: st.session_state.mcq_df=pd.DataFrame(columns=["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"])
if "activities" not in st.session_state: st.session_state.activities=[]
if "src_text" not in st.session_state: st.session_state.src_text=""
if "verbs" not in st.session_state: st.session_state.verbs=[]

# ------
# Tabs
# ------
tabs=st.tabs(["① Upload","② Setup","③ Generate","④ Export"])

# ① Upload
with tabs[0]:
    st.markdown("<div class='adi-card' id='adi-upload'>", unsafe_allow_html=True)
    st.subheader("📤 Upload source"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    st.session_state.material_type = st.radio("Material type", ["Lesson plan","E-book","PowerPoint"], horizontal=True, index=0, key="material_type_radio")
    up=st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)", type=["pdf","pptx","docx"], key="upload_file")
    pasted=st.text_area("Or paste source text manually", height=180, placeholder="Paste any relevant lesson/topic text here…")

    text=""; uploaded_name=None; uploaded_size=0
    if up is not None:
        data=up.read(); uploaded_name=up.name; uploaded_size=len(data); low=up.name.lower()
        if low.endswith(".pptx"): text=extract_pptx(data)
        elif low.endswith(".docx"): text=extract_docx(data)
        elif low.endswith(".pdf"): text=extract_pdf(data)
        st.caption(f"Selected: {up.name}")
    if not text and pasted.strip(): text=pasted.strip()
    st.session_state.src_text=text
    st.caption(f"Characters loaded: {len(text)}")

    if uploaded_name:
        kbytes = uploaded_size/1024
        st.markdown(
            f"<div style='margin-top:.5rem; display:inline-block; background:#e8f5ee; color:#14532d; "
            f"border:2px solid #1f7a4c; border-radius:999px; padding:.35rem .7rem; font-weight:800;'>"
            f"✓ Uploaded: {uploaded_name} · {kbytes:.0f} KB</div>",
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ② Setup
with tabs[1]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("⚙️ Setup"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.8, 1.6])
    with col_left:
        st.markdown("##### Lesson")
        st.session_state.lesson = st.radio("Lesson", [1,2,3,4,5], index=st.session_state.get("lesson",1)-1, horizontal=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("##### Week  <span style='font-weight:400;opacity:.75'>ADI: 1–4 Low · 5–9 Medium · 10–14 High</span>", unsafe_allow_html=True)
        st.session_state.week = st.radio("Week", list(range(1,15)), index=st.session_state.get("week",1)-1, horizontal=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("##### Bloom’s Level")
        current_level = st.session_state.get("level","Understand")
        st.session_state.level = st.radio("Choose the focal level", BLOOM_LEVELS, index=BLOOM_LEVELS.index(current_level), horizontal=True)

    with col_right:
        st.markdown("##### Sequence")
        mode = st.radio("Mode", ["Auto by Focus","Target level(s)"], horizontal=True)
        count = st.slider("How many MCQs?", 4, 30, st.session_state.get("count_auto", 10), 1)

        if mode == "Target level(s)":
            sel = st.multiselect("Target level(s)", BLOOM_LEVELS, default=["Understand","Apply","Analyze"])
            sel = sel or ["Understand"]
        else:
            sel = None

        if sel is None:
            rng = random.Random(int(st.session_state.week)*100 + int(st.session_state.lesson))
            blooms = weighted_bloom_sequence(st.session_state.level, count, rng)
        else:
            blooms = (sel * ((count // len(sel)) + 1))[:count]

        counts = {lv: blooms.count(lv) for lv in BLOOM_LEVELS}
        summary = "  ·  ".join([f"{lv} × {counts[lv]}" for lv in BLOOM_LEVELS if counts[lv]>0])
        st.caption("Sequence preview: " + (summary or "—"))

        required = policy_tier(int(st.session_state.week))
        selected_tier = BLOOM_TIER[st.session_state.level]
        p = {'Low':'pill','Medium':'pill','High':'pill'}
        p[required] += ' current'
        if selected_tier==required:
            p[selected_tier] += ' match'; badge = "<div class='badge-ok'>✓ ADI policy matched</div>"
        else:
            p[selected_tier] += ' mismatch'; badge = f"<div class='badge-warn'>Week requires {required}. Selected is {selected_tier}.</div>"
        st.markdown(f"<div class='pills'><span class='{p['Low']}'>Low</span><span class='{p['Medium']}'>Medium</span><span class='{p['High']}'>High</span></div>{badge}", unsafe_allow_html=True)

        st.session_state.blooms = blooms
        st.session_state.count_auto = count

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown("#### Choose 5–10 verbs")
    verbs_all = BLOOM_VERBS.get(st.session_state.level, [])
    if "verbs" not in st.session_state or not st.session_state.verbs:
        st.session_state.verbs = verbs_all[:5]
    st.session_state.verbs = st.multiselect("Pick verbs that fit your outcomes", options=verbs_all, default=st.session_state.verbs)
    if 5 <= len(st.session_state.verbs) <= 10:
        st.success("Verb count looks good ✅")
    else:
        st.warning(f"Select between 5 and 10 verbs. Currently: {len(st.session_state.verbs)}")
    st.caption("These verbs drive the MCQ stems and activity prompts.")
    st.markdown("</div>", unsafe_allow_html=True)

# ③ Generate — Simple/Advanced MCQ editor
with tabs[2]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("⚡️ Generate"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    src = st.session_state.src_text
    g1,g2,g3,g4 = st.columns([1,1,1,1])
    with g1: act_count=st.slider("Activities (per class)",1,4,2,1)
    with g2: act_diff=st.radio("Difficulty",["Low","Medium","High"], index=1, horizontal=True)
    with g3: duration=st.selectbox("Duration (mins)",[15,20,25,30,35,40,45,50,55,60], index=1)
    with g4:
        st.write(" ")
        if st.button("❓ Generate MCQs"):
            st.session_state.mcq_df = offline_mcqs(src, st.session_state.get('blooms', ["Understand"]*8), st.session_state.verbs, len(st.session_state.get('blooms', [])) or 8)
        if st.button("📝 Generate Activities"):
            st.session_state.activities = build_activities(src, st.session_state.get('blooms', ["Understand"]*act_count), st.session_state.verbs, duration, act_diff, n=act_count)

    st.markdown("**MCQs (editable table)**")

    simple_mode = st.toggle("Simple mode", value=True, help="Hide advanced fields for a cleaner view.")

    simple_cols   = ["Question", "Option A", "Option B", "Option C", "Option D", "Answer"]
    advanced_cols = ["Bloom", "Tier", "Q#", "Explanation"]
    column_order = simple_cols + ([] if simple_mode else advanced_cols)
    disabled_cols = ["Bloom", "Tier", "Q#"]  # read-only

    config = {
        "Question":  st.column_config.TextColumn("Question", width="large", help="Write the stem here."),
        "Option A":  st.column_config.TextColumn("A", width=220),
        "Option B":  st.column_config.TextColumn("B", width=220),
        "Option C":  st.column_config.TextColumn("C", width=220),
        "Option D":  st.column_config.TextColumn("D", width=220),
        "Answer":    st.column_config.SelectboxColumn("Correct", options=["A","B","C","D"], default="A", width=110),
        "Explanation": st.column_config.TextColumn("Explanation (optional)", width="large"),
        "Bloom":     st.column_config.TextColumn("Bloom (auto)"),
        "Tier":      st.column_config.TextColumn("Tier (auto)"),
        "Q#":        st.column_config.NumberColumn("Q#", format="%d", step=1),
    }

    st.session_state.mcq_df = st.data_editor(
        st.session_state.mcq_df,
        column_config=config,
        column_order=column_order,
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="mcq_editor_simple"
    )

    # Lightweight validation hint
    missing = []
    for i, r in st.session_state.mcq_df.iterrows():
        if not str(r.get("Question","")).strip():
            missing.append(i+1)
        else:
            for k in ["Option A","Option B","Option C","Option D"]:
                if not str(r.get(k,"")).strip():
                    missing.append(i+1); break

    if missing:
        st.caption(f"⚠️ Incomplete rows: {sorted(set(missing))}. Add a question and all options.")
    else:
        st.caption("✅ Table looks good.")

    st.markdown("**Activities (editable)**")
    acts_text="\n".join(st.session_state.activities)
    acts_text = st.text_area("One per line", value=acts_text, height=140, key="acts_text")
    st.session_state.activities = [a.strip() for a in acts_text.split("\n") if a.strip()]
    st.markdown("</div>", unsafe_allow_html=True)

# ④ Export
with tabs[3]:
    st.subheader("📦 Export")
    st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)

    df = st.session_state.get("mcq_df")
    acts = st.session_state.get("activities", [])
    lesson = st.session_state.get("lesson", 1)
    week = st.session_state.get("week", 1)

    # Check docx availability
    try:
        from docx import Document  # noqa: F401
        docx_available = True
    except Exception:
        docx_available = False

    gift_payload = to_gift(df) if (df is not None and not df.empty) else ""
    docx_bytes = export_docx(df, acts, lesson, week) if docx_available else None

    today = dt.date.today().strftime("%Y-%m-%d")
    base = f"ADI_Lesson{lesson}_Week{week}_{today}"
    docx_name = base + ".docx"; gift_name = base + ".gift"

    c1, c2 = st.columns(2)
    with c1:
        disabled_docx = not docx_available or ((df is None or df.empty) and not acts)
        st.download_button("⬇️ Download Word (.docx)",
                           data=(docx_bytes or b"placeholder"),
                           file_name=docx_name,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           disabled=disabled_docx,
                           help=("Install python-docx" if not docx_available else "Generate MCQs or Activities to enable"))
    with c2:
        disabled_gift = not bool(gift_payload)
        st.download_button("⬇️ Download Moodle GIFT (.gift)",
                           data=(gift_payload or "").encode("utf-8"),
                           file_name=gift_name, mime="text/plain",
                           disabled=disabled_gift,
                           help="Generate MCQs to enable")
