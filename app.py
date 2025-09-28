# app_fixed.py — ADI Builder (patched with policy pills + verbs + pill radios)
import io, re, random, os
from typing import List
import pandas as pd
import streamlit as st

# --- Page config
st.set_page_config(page_title="ADI Builder — Patched", page_icon="✅", layout="wide")

# --- Theme / CSS
ADI_GREEN = "#245a34"; ADI_GREEN_DARK = "#1a4426"; ADI_GOLD = "#C8A85A"; ADI_STONE = "#f4f4f2"
CSS = f"""
<style>
:root {{ --adi-green:{ADI_GREEN}; --adi-green-dark:{ADI_GREEN_DARK}; --adi-gold:{ADI_GOLD}; --adi-stone:{ADI_STONE}; }}
html, body {{ background: var(--adi-stone) !important; }}
.adi-ribbon {{ height:6px; background:linear-gradient(90deg,var(--adi-green),var(--adi-green-dark) 70%, var(--adi-gold)); border-radius:0 0 12px 12px; box-shadow:0 2px 8px rgba(0,0,0,.08); margin-bottom:8px; }}
.adi-title {{ font-size:1.6rem; font-weight:900; color:var(--adi-green); }}
.adi-sub {{ color:#3f4a54; font-weight:600; }}
.adi-card {{ background:#fff; border:1px solid rgba(0,0,0,.06); border-radius:20px; padding:20px; box-shadow:0 8px 24px rgba(10,24,18,.08); }}
.adi-section {{ border-top:3px solid var(--adi-gold); margin:8px 0 16px; box-shadow:0 -1px 0 rgba(0,0,0,.02) inset; }}
/* Radios as pills */
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
/* Data editor width */
.block-container {{ max-width: 1200px; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<div class='adi-ribbon'></div>", unsafe_allow_html=True)

# --- Header
c1,c2 = st.columns([1,6], vertical_alignment="center")
with c1:
    if os.path.exists("Logo.png"): st.image("Logo.png", width=78)
    else: st.markdown("**ADI**")
with c2:
    st.markdown("<div class='adi-title'>ADI Builder</div>", unsafe_allow_html=True)
    st.markdown("<div class='adi-sub'>Clean ADI look · Pill radios · Policy pills · Verb picker</div>", unsafe_allow_html=True)

# --- Constants
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

def policy_pills(required:str, selected_tier:str)->str:
    p={"Low":"pill","Medium":"pill","High":"pill"}
    p[required]+=" current"
    if selected_tier==required:
        p[selected_tier]+=" match"; badge="<div class='badge-ok'>✓ ADI policy matched</div>"
    else:
        p[selected_tier]+=" mismatch"; badge=f"<div class='badge-warn'>Week requires {required}. Selected is {selected_tier}.</div>"
    return f"<div class='pills'><span class='{p['Low']}'>Low</span><span class='{p['Medium']}'>Medium</span><span class='{p['High']}'>High</span></div>{badge}"

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

# --- Simple parsers (text only; keep your richer ones if you prefer)
def extract_pdf(b:bytes)->str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            return "\\n".join([(p.extract_text() or "") for p in pdf.pages])
    except Exception:
        return ""

def extract_pptx(b:bytes)->str:
    try:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(b)); out=[]
        for s in prs.slides:
            for sh in s.shapes:
                if hasattr(sh,"text"): out.append(sh.text)
        return "\\n".join(out)
    except Exception:
        return ""

def extract_docx(b:bytes)->str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(b))
        return "\\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""

# --- Generators using selected verbs
def offline_mcqs(src_text:str, blooms:list, verbs:List[str] , n:int):
    base=[s.strip() for s in re.split(r'[.\\n]', src_text or "") if s.strip()] or ["This unit covers core concepts and applied practice."]
    if not verbs: verbs=["identify"]
    vcycle=(verbs*((n//max(1,len(verbs)))+1))[:n]
    rows=[]
    for i in range(n):
        b=blooms[i]; tier=BLOOM_TIER[b]
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
    base=[s.strip() for s in re.split(r'[.\\n]', src_text or "") if s.strip()] or ["today's topic"]
    vcycle=(verbs*((n//max(1,len(verbs)))+1))[:n] if verbs else ["discuss"]*n
    acts=[]
    for i in range(n):
        lv=blooms[i%len(blooms)]; vt=vcycle[i].capitalize(); topic=base[i%len(base)]
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
        q=str(r.get("Question","")).replace("\\n"," ")
        opts=[r.get("Option A",""),r.get("Option B",""),r.get("Option C",""),r.get("Option D","")]
        ans="ABCD".index(r.get("Answer","A"))
        parts=[]
        for i,o in enumerate(opts):
            s=str(o).replace("}","\\}")
            parts.append(("=" if i==ans else "~")+s)
        out.append("{"+q+"}{"+" ".join(parts)+"}")
    return "\\n\\n".join(out)

def mcqs_docx(df:pd.DataFrame)->bytes:
    try:
        from docx import Document
    except Exception:
        return b""
    doc=Document(); doc.add_heading("MCQs",level=1)
    tbl=doc.add_table(rows=1,cols=9); hdr=tbl.rows[0].cells
    for i,c in enumerate(["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer"]): hdr[i].text=c
    for _,r in df.iterrows():
        row=tbl.add_row().cells
        vals=[r.get("Bloom",""),r.get("Tier",""),str(r.get("Q#","")),r.get("Question",""),r.get("Option A",""),r.get("Option B",""),r.get("Option C",""),r.get("Option D",""),r.get("Answer","")]
        for i,v in enumerate(vals): row[i].text=str(v)
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def activities_docx(acts:List[str])->bytes:
    try:
        from docx import Document
    except Exception:
        return b""
    doc=Document(); doc.add_heading("Activities",level=1)
    for i,a in enumerate(acts, start=1): doc.add_paragraph(f"{i}. {a}")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

# --- Session
if "mcq_df" not in st.session_state: st.session_state.mcq_df=pd.DataFrame(columns=["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"])
if "activities" not in st.session_state: st.session_state.activities=[]
if "src_text" not in st.session_state: st.session_state.src_text=""
if "verbs" not in st.session_state: st.session_state.verbs=[]

# --- Tabs
tabs=st.tabs(["① Upload","② Setup","③ Generate","④ Export"])

# Upload
with tabs[0]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("📤 Upload source"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    up=st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)", type=["pdf","pptx","docx"])
    pasted=st.text_area("Or paste source text manually", height=180, placeholder="Paste any relevant lesson/topic text here…")
    text=""
    if up is not None:
        data=up.read(); low=up.name.lower()
        if low.endswith(".pptx"): text=extract_pptx(data)
        elif low.endswith(".docx"): text=extract_docx(data)
        elif low.endswith(".pdf"): text=extract_pdf(data)
        st.caption(f"Selected: {up.name}")
    if not text and pasted.strip(): text=pasted.strip()
    st.session_state.src_text=text
    st.caption(f"Characters loaded: {len(text)}")
    st.markdown("</div>", unsafe_allow_html=True)

# Setup
with tabs[1]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("⚙️ Setup"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    a,b,c = st.columns([1.2,1.6,2.2])
    with a:
        lesson = st.radio("Lesson", [1,2,3,4,5], index=0, horizontal=True, key="lesson_radio")
        week = st.radio("Week", list(range(1,15)), index=0, horizontal=True, key="week_radio",
                        help="ADI policy: Weeks 1–4 Low, 5–9 Medium, 10–14 High")
    with b:
        focus = st.radio("Bloom’s Level", BLOOM_LEVELS, index=1, horizontal=True, key="level_radio")
        # Verb picker for this level (5–10)
        level_verbs = BLOOM_VERBS.get(focus, [])
        default_take = min(5, len(level_verbs))
        st.session_state.verbs = st.multiselect("Choose 5–10 verbs", options=level_verbs,
                                                default=level_verbs[:default_take], key="verbs_select")
        if not (5 <= len(st.session_state.verbs) <= 10):
            st.warning(f"Select between 5 and 10 verbs. Currently: {len(st.session_state.verbs)}")
        else:
            st.success("Verb count looks good ✅")
    with c:
        mode = st.radio("Sequence mode", ["Auto by Focus","Target level(s)"], horizontal=True)
        if mode=="Auto by Focus":
            count=st.slider("How many MCQs?",4,30,10,1,key="count_auto")
            rng=random.Random(week*100+lesson); blooms=weighted_bloom_sequence(focus,count,rng)
        else:
            sel=st.multiselect("Target Bloom level(s)", BLOOM_LEVELS, default=["Understand","Apply","Analyze"], key="sel_levels")
            count=st.slider("How many MCQs?",4,30,10,1,key="count_sel"); sel=sel or ["Understand"]
            blooms=(sel*((count//len(sel))+1))[:count]
        chip_map={"Low":"low","Medium":"medium","High":"high"}
        chips=" ".join([f"<span class='pill'>{b}</span>" for b in blooms])
        st.markdown("**Sequence preview:** "+chips, unsafe_allow_html=True)
        required = policy_tier(int(week)); selected_tier = BLOOM_TIER[focus]
        st.markdown(policy_pills(required, selected_tier), unsafe_allow_html=True)
    # Save for next tab
    st.session_state.blooms = blooms
    st.session_state.week = week
    st.markdown("</div>", unsafe_allow_html=True)

# Generate
with tabs[2]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("⚡️ Generate"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    src = st.session_state.src_text
    g1,g2,g3,g4 = st.columns(4)
    with g1: act_count=st.slider("Activities (per class)",1,4,2,1)
    with g2: act_diff=st.radio("Difficulty",["Low","Medium","High"], index=1, horizontal=True)
    with g3: duration=st.selectbox("Duration (mins)",[15,20,25,30,35,40,45,50,55,60], index=1)
    with g4:
        st.write(" ")  # spacer
        if st.button("❓ Generate MCQs", type="primary"):
            st.session_state.mcq_df = offline_mcqs(src, st.session_state.get('blooms', ["Understand"]*8), st.session_state.verbs, len(st.session_state.get('blooms', [])) or 8)
        if st.button("📝 Generate Activities", type="primary"):
            st.session_state.activities = build_activities(src, st.session_state.get('blooms', ["Understand"]*act_count), st.session_state.verbs, duration, act_diff, n=act_count)

    st.markdown("**MCQs (editable table)**")
    st.session_state.mcq_df = st.data_editor(st.session_state.mcq_df, num_rows="dynamic", use_container_width=True, key="mcq_editor")

    st.markdown("**Activities (editable)**")
    acts_text="\\n".join(st.session_state.activities)
    acts_text = st.text_area("One per line", value=acts_text, height=140, key="acts_text")
    st.session_state.activities = [a.strip() for a in acts_text.split("\\n") if a.strip()]
    st.markdown("</div>", unsafe_allow_html=True)

# Export
def download_buttons():
    df=st.session_state.mcq_df.copy()
    c1,c2,c3,c4,c5=st.columns(5)
    with c1:
        if not df.empty:
            st.download_button("Export · MCQs CSV", df.to_csv(index=False).encode("utf-8"), file_name="mcqs.csv", mime="text/csv", use_container_width=True)
    with c2:
        if not df.empty:
            st.download_button("Export · MCQs GIFT", to_gift(df).encode("utf-8"), file_name="mcqs.gift.txt", mime="text/plain", use_container_width=True)
    with c5:
        try:
            from docx import Document  # noqa: F401
            docx_ok = True
        except Exception:
            docx_ok = False
        if not df.empty and docx_ok:
            st.download_button("Export · MCQs DOCX", mcqs_docx(df), file_name="mcqs.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        elif not df.empty:
            st.caption("Install python-docx to enable MCQs DOCX export.")
    with c3:
        if st.session_state.activities:
            st.download_button("Export · Activities CSV", ("\\n".join(st.session_state.activities)).encode("utf-8"), file_name="activities.csv", mime="text/csv", use_container_width=True)
    with c4:
        try:
            from docx import Document  # noqa: F401
            docx_ok = True
        except Exception:
            docx_ok = False
        if st.session_state.activities and docx_ok:
            st.download_button("Export · Activities DOCX", activities_docx(st.session_state.activities), file_name="activities.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        elif st.session_state.activities:
            st.caption("Install python-docx to enable Activities DOCX.")

with st.tabs(["④ Export"])[0]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("📦 Export"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    download_buttons()
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Security: API keys (if used) stay server-side (env or .streamlit/secrets). Never accept keys via UI.")
