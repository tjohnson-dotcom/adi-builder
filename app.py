# -*- coding: utf-8 -*-
# app.py — ADI Builder (Safe on Streamlit 1.36 • Radio-only Bloom)
import os, io, json, hashlib, random, re
from typing import List, Dict
import pandas as pd
import streamlit as st

try:
    from pptx import Presentation
except Exception:
    Presentation = None
try:
    from docx import Document
except Exception:
    Document = None
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

USE_ICONS = os.getenv("ADI_ICONS", "1") != "0"
def I(sym: str) -> str: return sym if USE_ICONS else ""

ADI_GREEN="#245a34"; ADI_GREEN_DARK="#1a4426"; ADI_GOLD="#C8A85A"; ADI_STONE="#f4f4f2"
CSS = f"""
<style>
:root{{--adi-green:{ADI_GREEN};--adi-green-dark:{ADI_GREEN_DARK};--adi-gold:{ADI_GOLD};--adi-stone:{ADI_STONE};}}
html,body{{background:var(--adi-stone)!important;}}
.adi-ribbon{{height:6px;background:linear-gradient(90deg,var(--adi-green),var(--adi-green-dark)70%,var(--adi-gold));border-radius:0 0 12px 12px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:8px;}}
.adi-title{{font-size:1.6rem;font-weight:900;color:var(--adi-green);}}
.adi-sub{{color:#3f4a54;font-weight:600;}}
.adi-card{{background:#fff;border:1px solid rgba(0,0,0,.06);border-radius:20px;padding:20px;box-shadow:0 8px 24px rgba(10,24,18,.08);}}
.adi-section{border-top:3px solid var(--adi-gold);margin:8px 0 16px;}
.adi-banner{display:inline-block;background:#ffffff;border-left:6px solid var(--adi-gold);color:#1f2937;font-weight:900;letter-spacing:.04em;text-transform:uppercase;padding:6px 12px;border-radius:6px;margin:0 0 8px 0;}
/* Buttons */
.stButton > button[kind="primary"]{{background:linear-gradient(135deg,var(--adi-green),var(--adi-green-dark))!important;color:#fff!important;border:none!important;border-radius:16px!important;font-weight:800!important;box-shadow:0 6px 16px rgba(10,24,18,.2);}}
.stButton > button:not([kind="primary"]){{background:#fff!important;color:var(--adi-green)!important;border:2px solid var(--adi-green)!important;border-radius:14px!important;font-weight:700!important;}}
/* Radio-as-chips */
.stRadio > div{{gap:12px;flex-wrap:wrap;}}
.stRadio [role="radiogroup"] > div label{{border:2px solid var(--adi-green);border-radius:999px;padding:10px 16px;background:#fff;color:#1f2937;font-weight:700;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,.04);}}
.stRadio [role="radiogroup"] > div [aria-checked="true"] label{{background:#f7faf8;box-shadow:inset 0 0 0 3px var(--adi-gold);}}
.stDataFrame thead{{background:#f3faf5!important;}}
.ok{{color:#065f46;font-weight:800;}} .warn{{color:#991b1b;font-weight:800;}}
.badge-ok{display:inline-block;background:#e8f5ee;border:2px solid #1f7a4c;color:#14532d;padding:6px 10px;border-radius:999px;font-weight:800;margin-top:8px;}
.badge-warn{display:inline-block;background:#fff7ed;border:2px solid #fed7aa;color:#7c2d12;padding:6px 10px;border-radius:999px;font-weight:800;margin-top:8px;}
.badge-ok{display:inline-block;background:#e8f5ee;border:2px solid #1f7a4c;color:#14532d;padding:6px 10px;border-radius:999px;font-weight:800;margin-top:8px;}
</style>
"""
st.set_page_config(page_title="ADI Builder — Clean ADI", page_icon="✅", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<div class='adi-ribbon'></div>", unsafe_allow_html=True)

c1, c2 = st.columns([1,6], vertical_alignment="center")
with c1:
    if os.path.exists("Logo.png"): st.image("Logo.png", width=78)
    else: st.markdown("**ADI**")
with c2:
    st.markdown("<div class='adi-title'>ADI Builder</div>", unsafe_allow_html=True)
    st.markdown("<div class='adi-sub'>Clean, polished ADI look · Strict colors · Logo required</div>", unsafe_allow_html=True)

def have_api()->bool:
    try:
        from streamlit.runtime.secrets import secrets
        if secrets.get("OPENAI_API_KEY"): return True
    except Exception: pass
    return bool(os.getenv("OPENAI_API_KEY",""))

BLOOM_LEVELS=["Remember","Understand","Apply","Analyze","Evaluate","Create"]
BLOOM_TIER={"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}
BLOOM_STEMS={
    "Remember":["Define","List","Identify","Match","Name"],
    "Understand":["Explain","Summarize","Classify","Describe"],
    "Apply":["Apply","Use","Compute","Demonstrate"],
    "Analyze":["Differentiate","Organize","Compare","Critique"],
    "Evaluate":["Justify","Assess","Prioritize","Choose"],
    "Create":["Design","Compose","Develop","Propose"],
}
MCQ_COLS=["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"]

def policy_tier(week:int)->str:
    if week<=4: return "Low"
    if week<=9: return "Medium"
    return "High"

def weighted_bloom_sequence(selected:str,n:int,rng:random.Random)->list:
    idx=BLOOM_LEVELS.index(selected); weights=[]
    for i,_ in enumerate(BLOOM_LEVELS):
        dist=abs(i-idx); weights.append({0:5,1:3,2:2,3:1}[min(dist,3)])
    seq=[]
    for _ in range(n):
        x=rng.uniform(0,sum(weights)); acc=0
        for lv,w in zip(BLOOM_LEVELS,weights):
            acc+=w
            if x<=acc: seq.append(lv); break
    return seq

def stable_seed(teacher_id,klass,lesson,week,src_text)->int:
    h=hashlib.md5((str(teacher_id)+"|"+str(klass)+"|"+str(lesson)+"|"+str(week)+"|"+(src_text or "")[:5000]).encode()).hexdigest()
    return int(h[:8],16)

def dedup(df:pd.DataFrame)->pd.DataFrame:
    if df.empty: return df
    df=df[df["Question"].astype(str).str.len()>0]
    df=df.loc[~df["Question"].str.lower().duplicated()].copy()
    df["Answer"]=df["Answer"].map(lambda s: s if s in list("ABCD") else "A")
    for c in ["Option A","Option B","Option C","Option D"]:
        df[c]=df[c].fillna("").replace("","—")
    df["Q#"]=range(1,len(df)+1); return df

def offline_mcqs(src_text,lesson,week,blooms,teacher_seed,n=10):
    rng=random.Random(stable_seed(teacher_seed,"default",lesson,week,src_text or ""))
    base=[s.strip() for s in re.split(r'[.\n]', src_text or "") if s.strip()] or ["This unit covers core concepts and applied practice."]
    rows=[]
    for i in range(1,n+1):
        bloom=blooms[(i-1)%len(blooms)]; tier=BLOOM_TIER.get(bloom,"Medium")
        stem=BLOOM_STEMS[bloom][i % len(BLOOM_STEMS[bloom]) - 1]; fact=base[i % len(base) - 1]
        key_index=rng.randrange(4)
        opts=[f"Distractor {j+1}: {base[(i+j)%len(base)][:60]}" for j in range(4)]; opts[key_index]=f"Correct: {fact[:60]}"
        rows.append({"Bloom":bloom,"Tier":tier,"Q#":i,"Question":f"{stem}: {fact}","Option A":opts[0],"Option B":opts[1],"Option C":opts[2],"Option D":opts[3],"Answer":"ABCD"[key_index],"Explanation":f"The correct answer reflects: {fact[:80]}"})
    return dedup(pd.DataFrame(rows,columns=MCQ_COLS))

def extract_pptx(b:bytes)->str:
    if not Presentation: return ""
    prs=Presentation(io.BytesIO(b)); out=[]
    for s in prs.slides:
        for sh in s.shapes:
            if hasattr(sh,"text"): out.append(sh.text)
    return "\n".join(out)
def extract_docx(b:bytes)->str:
    if not Document: return ""
    doc=Document(io.BytesIO(b)); return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
def extract_pdf(b:bytes)->str:
    # Try pdfplumber -> PyPDF2 -> pymupdf (fitz)
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            text = "
".join(pages)
    except Exception:
        pass
    if not text:
        try:
            import PyPDF2 as _P2
            reader = _P2.PdfReader(io.BytesIO(b))
            text = "
".join([p.extract_text() or "" for p in reader.pages])
        except Exception:
            text = ""
    if not text:
        try:
            import fitz  # pymupdf
            doc = fitz.open(stream=b, filetype="pdf")
            text = "
".join([page.get_text() or "" for page in doc])
        except Exception:
            text = ""
    return text
    try:
        reader=PyPDF2.PdfReader(io.BytesIO(b)); return "\n".join([p.extract_text() or "" for p in reader.pages])
    except Exception: return ""

if "mcq_df" not in st.session_state: st.session_state.mcq_df=pd.DataFrame(columns=MCQ_COLS)
if "activities" not in st.session_state: st.session_state.activities=[]

tabs=st.tabs([f"① {I('📤 ')}Upload",f"② {I('⚙️ ')}Setup",f"③ {I('⚡️ ')}Generate",f"④ {I('📦 ')}Export"])

with tabs[0]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader(f"{I('📤 ')}Upload source"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    up=st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)", type=["pdf","pptx","docx"])
    pasted=st.text_area("Or paste source text manually", height=180, placeholder="Paste any relevant lesson/topic text here…")
    src_text=""
    if up is not None:
        data=up.read(); name=up.name.lower()
        if name.endswith(".pptx"): src_text=extract_pptx(data)
        elif name.endswith(".docx"): src_text=extract_docx(data)
        elif name.endswith(".pdf"): src_text=extract_pdf(data)
    if not src_text and pasted.strip(): src_text=pasted.strip()
    st.session_state["src_text"]=src_text
    # Immediate feedback: file selected
    if up is not None:
        label = up.name
        size = f" · {up.size/1e6:.1f} MB" if hasattr(up, "size") else ""
        st.markdown(f"<span class='badge-ok'>✓ Selected: {label}{size}</span>", unsafe_allow_html=True)

    # Characters loaded + processed badges
    st.caption(f"Characters loaded: {len(src_text)}")
    if src_text:
        st.markdown(f"<span class='badge-ok'>✓ Processed: {len(src_text):,} chars</span>", unsafe_allow_html=True)
    elif up is not None:
        st.markdown("<span class='badge-warn'>Uploaded but no text detected — try a text PDF, DOCX/PPTX, or paste text below.</span>", unsafe_allow_html=True)
    else:
        st.info('Upload a PDF/PPTX/DOCX or paste text to continue.')
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[1]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader(f"{I('⚙️ ')}Setup"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    cA,cB,cC,cD=st.columns(4)
    lesson=cA.number_input("Lesson",1,20,1,1)
    week=cB.number_input("Week",1,20,1,1)
    teacher_id=cC.text_input("Teacher ID","teacher_001")
    klass=cD.text_input("Class/Section","class_A")
    st.markdown(f"**{I('🧠 ')}Bloom’s taxonomy**")
    bloom_level=st.radio("Pick focus level",BLOOM_LEVELS,index=1,horizontal=True,label_visibility="collapsed")

    mode=st.radio(f"{I('🎛️ ')}Sequence mode",["Auto by Focus","Target level(s)"],horizontal=True)
    if mode=="Auto by Focus":
        count=st.slider(f"{I('#️⃣ ')}How many MCQs?",4,30,10,1)
        rng=random.Random(week*100+lesson); blooms=weighted_bloom_sequence(bloom_level,count,rng)
    else:
        sel=st.multiselect("Pick Bloom levels (will cycle)",BLOOM_LEVELS,default=["Understand","Apply","Analyze"])
        count=st.slider(f"{I('#️⃣ ')}How many MCQs?",4,30,10,1)
        if not sel: sel=["Understand"]
        blooms=(sel*((count//len(sel))+1))[:count]
    st.write("Sequence preview:",", ".join(blooms))
    current_policy=policy_tier(int(week)); selected_tier=BLOOM_TIER[bloom_level]
    st.markdown(f"Policy: **{current_policy}** · Selected: **<span class='{'ok' if selected_tier==current_policy else 'warn'}'>{selected_tier}</span>**" + (" ✓" if selected_tier==current_policy else " (mismatch)"), unsafe_allow_html=True)
    st.write("---")
    use_ai=st.checkbox(f"{I('🤖 ')}Use AI generator (if key available)",value=have_api())
    if use_ai and not have_api(): st.info("No API key found; will use offline generator.")
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[2]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader(f"{I('⚡️ ')}Generate MCQs & Activities"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    src_text=st.session_state.get("src_text","")
    ctl1,ctl2,ctl3,ctl4=st.columns(4)
    with ctl1: activity_count=st.slider("Activities (per class)",1,4,2,1)
    with ctl2: activity_style=st.selectbox(f"Style {I('🎨')}",["Mixed","Quick tasks","Pair/Group","Project","Assessment"],index=0)
    with ctl3: activity_difficulty=st.radio(f"Difficulty {I('🎚️')}",["Low","Medium","High"],index=1,horizontal=True)
    with ctl4: duration=st.selectbox(f"{I('⏱️ ')}Duration (mins)",[15,20,25,30,35,40,45,50,55,60],index=1)
    use_bloom_verbs=st.checkbox(f"Use Bloom verbs {I('🧠')}",value=True)
    colA,colB=st.columns(2)
    with colA:
        if st.button(f"{I('📝 ')}Generate Activities",type="primary",key="btn_acts"):
            base_stems={"Quick tasks":["Do-now:","Exit ticket:","3-minute write:","Sketch-note:","One-sentence summary:"],
                        "Pair/Group":["Think–Pair–Share:","Mini-debate:","Jigsaw teach-back:","Peer review:","Gallery walk:"],
                        "Project":["Prototype:","Mini-project:","Concept map:","Storyboard:","Case design:"],
                        "Assessment":["Quiz item:","Short answer:","Spot the error:","Classify:","Rank & justify:"],
                        "Mixed":["Pair-share on","Mini-poster:","Role-play:","Think–Pair–Share:","Quick debate:","Case critique:"]}
            diff_suffix={"Low":" (recall)","Medium":" (apply/analyze)","High":" (create/evaluate)"}
            chosen=base_stems.get(activity_style,base_stems["Mixed"])
            base=[s.strip() for s in re.split(r'[.\n]', src_text) if s.strip()] or ["today's topic"]
            acts=[]
            for i in range(activity_count):
                stem=chosen[i%len(chosen)]; topic=base[i%len(base)]
                if use_bloom_verbs:
                    lv=blooms[i%len(blooms)]; verbs=BLOOM_STEMS.get(lv,["Explore"]); verb=verbs[i%len(verbs)]
                    prompt=f"{stem} {verb} {topic}{diff_suffix.get(activity_difficulty,'')}"
                else:
                    prompt=f"{stem} {topic}{diff_suffix.get(activity_difficulty,'')}"
                acts.append(f"[{duration} min] "+prompt)
            st.session_state.activities=acts
    with colB:
        if st.button(f"{I('❓ ')}Generate MCQs",type="primary",key="btn_mcq"):
            with st.spinner("Generating (offline)…"):
                df=offline_mcqs(src_text,lesson,week,blooms,teacher_id,n=len(blooms))
            st.session_state.mcq_df=df

    st.write(""); st.markdown("**Quick Editor**"); st.caption("Edit inline. Your exports will use this exact table.")
    st.session_state.mcq_df=st.data_editor(st.session_state.mcq_df,num_rows="dynamic",use_container_width=True,key="editor_mcq")
    st.write(""); st.markdown("**Activities (editable)**")
    acts_text="\n".join(st.session_state.get("activities",[]))
    acts_text=st.text_area("One per line",value=acts_text,height=140,key="acts_text")
    st.session_state.activities=[a.strip() for a in acts_text.split("\n") if a.strip()]
    st.markdown("</div>", unsafe_allow_html=True)

def to_gift(df:pd.DataFrame)->str:
    lines=[]
    for _,r in df.iterrows():
        q=r["Question"].replace("\n"," "); opts=[r["Option A"],r["Option B"],r["Option C"],r["Option D"]]
        ans_idx="ABCD".index(r["Answer"]); gift=[]
        for i,opt in enumerate(opts):
            opt=opt.replace("}","\\}"); gift.append(("=" if i==ans_idx else "~")+opt)
        lines.append("{"+q+"}{"+" ".join(gift)+"}")
    return "\n\n".join(lines)

def activities_docx(acts:List[str])->bytes:
    if not Document: return b""
    doc=Document(); doc.add_heading("Activities",level=1)
    for i,a in enumerate(acts,start=1): doc.add_paragraph(f"{i}. {a}")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

with tabs[3]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("📦 Export"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
st.markdown("<div class='adi-banner'>Export</div>", unsafe_allow_html=True)
    df=st.session_state.mcq_df.copy()
    c1,c2,c3,c4=st.columns(4)
    with c1:
        if not df.empty:
            st.download_button(f"{I('⬇️ ')}MCQs CSV",data=df.to_csv(index=False).encode("utf-8"),file_name="mcqs.csv",mime="text/csv",use_container_width=True)
    with c2:
        if not df.empty:
            st.download_button(f"{I('⬇️ ')}MCQs GIFT",data=to_gift(df).encode("utf-8"),file_name="mcqs.gift.txt",mime="text/plain",use_container_width=True)
    with c3:
        if st.session_state.get("activities"):
            st.download_button(f"{I('⬇️ ')}Activities CSV",data=("\n".join(st.session_state["activities"])).encode("utf-8"),file_name="activities.csv",mime="text/csv",use_container_width=True)
    with c4:
        if st.session_state.get("activities") and Document:
            st.download_button(f"{I('⬇️ ')}Activities DOCX",data=activities_docx(st.session_state["activities"]),file_name="activities.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
        elif st.session_state.get("activities"):
            st.info("Install python-docx to enable DOCX export.")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Security: API keys (if used) stay server-side (env or .streamlit/secrets). Never accept keys via UI.")
