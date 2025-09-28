
# ADI Builder — Stable Build
import os, io, re, random, hashlib
from typing import List
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

ADI_GREEN = "#245a34"; ADI_GREEN_DARK = "#1a4426"; ADI_GOLD = "#C8A85A"; ADI_STONE = "#f4f4f2"

CSS = """
<style>
:root { --adi-green:%s; --adi-green-dark:%s; --adi-gold:%s; --adi-stone:%s; }
html, body { background: var(--adi-stone) !important; }
.adi-ribbon { height:6px; background:linear-gradient(90deg,var(--adi-green),var(--adi-green-dark) 70%%, var(--adi-gold)); border-radius:0 0 12px 12px; box-shadow:0 2px 8px rgba(0,0,0,.08); margin-bottom:8px; }
.adi-title { font-size:1.6rem; font-weight:900; color:var(--adi-green); }
.adi-sub { color:#3f4a54; font-weight:600; }
.adi-card { background:#fff; border:1px solid rgba(0,0,0,.06); border-radius:20px; padding:20px; box-shadow:0 8px 24px rgba(10,24,18,.08); }
.adi-section { border-top:3px solid var(--adi-gold); margin:8px 0 16px; box-shadow:0 -1px 0 rgba(0,0,0,.02) inset; }
.stTabs [role="tablist"]{ gap:10px; }
.stTabs [role="tab"]{ background:#fff; border:2px solid rgba(0,0,0,.08); border-radius:999px; padding:8px 14px; font-weight:700; color:#1f2937; box-shadow:0 1px 2px rgba(0,0,0,.04); }
.stTabs [role="tab"][aria-selected="true"]{ border-color:var(--adi-green); box-shadow:inset 0 0 0 3px var(--adi-gold), 0 1px 6px rgba(0,0,0,.06); }
.stButton > button[kind="primary"]{ background:linear-gradient(135deg,var(--adi-green),var(--adi-green-dark))!important; color:#fff!important; border:none!important; border-radius:16px!important; font-weight:800!important; box-shadow:0 6px 16px rgba(10,24,18,.2); }
.stButton > button:not([kind="primary"]){ background:#fff!important; color:var(--adi-green)!important; border:2px solid var(--adi-green)!important; border-radius:14px!important; font-weight:700!important; }
.stRadio input[type='radio']{ accent-color: var(--adi-green); }
.stRadio > div{ gap:12px; flex-wrap:wrap; }
.stRadio [role="radiogroup"] > div label{ border:2px solid var(--adi-green); border-radius:999px; padding:10px 16px; background:#fff; color:#1f2937; font-weight:700; cursor:pointer; box-shadow:0 1px 2px rgba(0,0,0,.04); }
.stRadio [role="radiogroup"] > div [aria-checked="true"] label{ background:#f7faf8; box-shadow:inset 0 0 0 3px var(--adi-gold); }

.chip.low{box-shadow:inset 0 0 0 3px rgba(36,90,52,.12);}
.chip.medium{box-shadow:inset 0 0 0 3px rgba(200,168,90,.18);}
.chip.high{box-shadow:inset 0 0 0 3px rgba(200,168,90,.32);}
/* Chip state by policy match */
.chip.ok{background:#e8f5ee!important;border-color:#1f7a4c!important;color:#14532d!important;box-shadow:0 1px 2px rgba(0,0,0,.04), inset 0 0 0 2px rgba(31,122,76,.15)!important;}.chip.warn{background:#fff;border-color:#c89a4a;box-shadow:inset 0 0 0 2px rgba(200,168,90,.25);}
/* Make top inputs pop */
.stNumberInput > div > div, .stTextInput > div > div, .stSelectbox > div > div{ border:3px solid rgba(36,90,52,.25); border-radius:14px; background:#fff; box-shadow:0 2px 8px rgba(10,24,18,.06);}.stNumberInput:focus-within > div > div, .stTextInput:focus-within > div > div, .stSelectbox:focus-within > div > div{ box-shadow:0 0 0 3px rgba(200,168,90,.55) inset, 0 2px 10px rgba(10,24,18,.10); border-color: var(--adi-green);}
[data-testid="stFileUploaderDropzone"]{ border:2px dashed var(--adi-green)!important; background:#f7faf8; border-radius:14px; transition:box-shadow .15s ease, background .15s ease; }
[data-testid="stFileUploaderDropzone"]:hover{ background:#eef7f1; box-shadow:0 0 0 3px rgba(36,90,52,.15) inset; }
.badge-ok{ display:inline-block; background:#e8f5ee; border:2px solid #1f7a4c; color:#14532d; padding:6px 10px; border-radius:999px; font-weight:800; margin-top:8px; }
.badge-warn{ display:inline-block; background:#fff7ed; border:2px solid #fed7aa; color:#7c2d12; padding:6px 10px; border-radius:999px; font-weight:800; margin-top:8px; }
.adi-banner{ display:block; background:#ffffff; border-left:6px solid var(--adi-gold); color:#1f2937; font-weight:900; letter-spacing:.04em; text-transform:uppercase; padding:8px 16px; border-radius:8px; margin:0 auto 10px auto; width:max-content; box-shadow:0 2px 8px rgba(0,0,0,.06); }

""" % (ADI_GREEN, ADI_GREEN_DARK, ADI_GOLD, ADI_STONE)


st.markdown("""<style>
.seq-row{margin-top:4px;margin-bottom:6px;}
.chip{margin:2px 6px;padding:6px 12px;border-radius:999px;border:2px solid #d1d5db;background:#fff;color:#1f2937;font-weight:700;}
.chip.ok{background:#e8f5ee!important;border-color:#1f7a4c!important;color:#14532d!important;box-shadow:0 1px 2px rgba(0,0,0,.04), inset 0 0 0 2px rgba(31,122,76,.15)!important;}
.chip.warn{background:#fff7ed!important;border-color:#f59e0b!important;color:#7c2d12!important;box-shadow:0 1px 2px rgba(0,0,0,.04), inset 0 0 0 2px rgba(245,158,11,.25)!important;}
.stNumberInput > div > div, .stTextInput > div > div, .stSelectbox > div > div{border:3px solid rgba(36,90,52,.25); border-radius:14px; background:#fff; box-shadow:0 2px 8px rgba(10,24,18,.06);}
.stNumberInput:focus-within > div > div, .stTextInput:focus-within > div > div, .stSelectbox:focus-within > div > div{box-shadow:0 0 0 3px rgba(200,168,90,.55) inset, 0 2px 10px rgba(10,24,18,.10); border-color: #1f7a4c;}
</style>""", unsafe_allow_html=True)

st.set_page_config(page_title="ADI Builder — Clean ADI", page_icon="✅", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<div class='adi-ribbon'></div>", unsafe_allow_html=True)

# Header
c1,c2 = st.columns([1,6], vertical_alignment="center")
with c1:
    if os.path.exists("Logo.png"): st.image("Logo.png", width=78)
    else: st.markdown("**ADI**")
with c2:
    st.markdown("<div class='adi-title'>ADI Builder</div>", unsafe_allow_html=True)
    st.markdown("<div class='adi-sub'>Clean, polished ADI look · Strict colors · Logo required</div>", unsafe_allow_html=True)

BLOOM_LEVELS = ["Remember","Understand","Apply","Analyze","Evaluate","Create"]
BLOOM_TIER = {"Remember":"Low","Understand":"Low","Apply":"Medium","Analyze":"Medium","Evaluate":"High","Create":"High"}

def extract_pptx(b: bytes) -> str:
    if not Presentation: return ""
    prs = Presentation(io.BytesIO(b)); out = []
    for s in prs.slides:
        for sh in s.shapes:
            if hasattr(sh,"text"): out.append(sh.text)
    return "\n".join(out)

def extract_docx(b: bytes) -> str:
    try:
        from docx import Document as _D
    except Exception:
        return ""
    doc = _D(io.BytesIO(b))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_pdf(b: bytes) -> str:
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            text = "\n".join([(p.extract_text() or "") for p in pdf.pages])
    except Exception:
        text = ""
    if not text:
        try:
            import PyPDF2 as P2
            reader = P2.PdfReader(io.BytesIO(b))
            text = "\n".join([(p.extract_text() or "") for p in reader.pages])
        except Exception:
            text = ""
    if not text:
        try:
            import fitz
            doc = fitz.open(stream=b, filetype="pdf")
            text = "\n".join([page.get_text() or "" for page in doc])
        except Exception:
            text = ""
    return text

def policy_tier(week:int)->str:
    if week<=4: return "Low"
    if week<=9: return "Medium"
    return "High"

def weighted_bloom_sequence(selected:str, n:int, rng:random.Random):
    idx = BLOOM_LEVELS.index(selected); weights=[]
    for i in range(len(BLOOM_LEVELS)):
        dist=abs(i-idx); weights.append({0:5,1:3,2:2,3:1}[min(dist,3)])
    seq=[]
    for _ in range(n):
        x=rng.uniform(0,sum(weights)); acc=0
        for lv,w in zip(BLOOM_LEVELS,weights):
            acc+=w
            if x<=acc: seq.append(lv); break
    return seq

def offline_mcqs(src_text:str, blooms:list, n:int):
    base=[s.strip() for s in re.split(r'[.\n]', src_text or "") if s.strip()] or ["This unit covers core concepts and applied practice."]
    rows=[]
    for i in range(1,n+1):
        b=blooms[(i-1)%len(blooms)]; tier=BLOOM_TIER[b]
        fact=base[i%len(base)-1]
        opts=[f"Choice {j+1}: {base[(i+j)%len(base)][:60]}" for j in range(4)]
        key=i%4; opts[key]=f"Correct: {fact[:60]}"
        rows.append({"Bloom":b,"Tier":tier,"Q#":i,"Question":f"{b}: {fact}","Option A":opts[0],"Option B":opts[1],"Option C":opts[2],"Option D":opts[3],"Answer":"ABCD"[key],"Explanation":f"Reflects: {fact[:80]}"})
    df=pd.DataFrame(rows,columns=["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"])
    df["Q#"]=range(1,len(df)+1); return df

def to_gift(df:pd.DataFrame)->str:
    out=[]
    for _,r in df.iterrows():
        q=str(r.get("Question","")).replace("\n"," ")
        opts=[r.get("Option A",""),r.get("Option B",""),r.get("Option C",""),r.get("Option D","")]
        ans="ABCD".index(r.get("Answer","A"))
        parts=[]
        for i,o in enumerate(opts):
            s=str(o).replace("}","\}")
            parts.append(("=" if i==ans else "~")+s)
        out.append("{"+q+"}{"+" ".join(parts)+"}")
    return "\n\n".join(out)

def mcqs_docx(df:pd.DataFrame)->bytes:
    if not Document: return b""
    doc=Document(); doc.add_heading("MCQs",level=1)
    tbl=doc.add_table(rows=1,cols=9); hdr=tbl.rows[0].cells
    for i,c in enumerate(["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer"]): hdr[i].text=c
    for _,r in df.iterrows():
        row=tbl.add_row().cells
        vals=[r.get("Bloom",""),r.get("Tier",""),str(r.get("Q#","")),r.get("Question",""),r.get("Option A",""),r.get("Option B",""),r.get("Option C",""),r.get("Option D",""),r.get("Answer","")]
        for i,v in enumerate(vals): row[i].text=str(v)
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

def activities_docx(acts:List[str])->bytes:
    if not Document: return b""
    doc=Document(); doc.add_heading("Activities",level=1)
    for i,a in enumerate(acts, start=1): doc.add_paragraph(f"{i}. {a}")
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

# Session
if "mcq_df" not in st.session_state: st.session_state.mcq_df=pd.DataFrame(columns=["Bloom","Tier","Q#","Question","Option A","Option B","Option C","Option D","Answer","Explanation"])
if "activities" not in st.session_state: st.session_state.activities=[]
if "src_text" not in st.session_state: st.session_state.src_text=""

tabs=st.tabs(["① Upload","② Setup","③ Generate","④ Export (Step 4)"])

# Upload
with tabs[0]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("📤 Upload source"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    up=st.file_uploader("PDF / PPTX / DOCX (optional — you can also paste text below)", type=["pdf","pptx","docx"])
    pasted=st.text_area("Or paste source text manually", height=180, placeholder="Paste any relevant lesson/topic text here…")
    if up is not None:
        st.markdown(f"<span class='badge-ok'>✓ Selected: {up.name} · {getattr(up,'size',0)/1e6:.1f} MB</span>", unsafe_allow_html=True)
    text=""
    if up is not None:
        data=up.read(); low=up.name.lower()
        if low.endswith(".pptx"): text=extract_pptx(data)
        elif low.endswith(".docx"): text=extract_docx(data)
        elif low.endswith(".pdf"): text=extract_pdf(data)
    if not text and pasted.strip(): text=pasted.strip()
    st.session_state.src_text=text
    st.caption(f"Characters loaded: {len(text)}")
    if text:
        st.markdown(f"<span class='badge-ok'>✓ Processed: {len(text):,} chars</span>", unsafe_allow_html=True)
st.markdown("""<style>[data-testid=\"stFileUploaderDropzone\"]{border-color:#1f7a4c!important;background:#e8f5ee!important;box-shadow:0 0 0 3px rgba(36,90,52,.25) inset!important;}</style>""", unsafe_allow_html=True)

</style>", unsafe_allow_html=True)
    elif up is not None:
        st.markdown("<span class='badge-warn'>Uploaded but no text detected — try a text PDF, DOCX/PPTX, or paste text below.</span>", unsafe_allow_html=True)
    else:
        st.info("Upload a PDF/PPTX/DOCX or paste text to continue.")
    st.markdown("</div>", unsafe_allow_html=True)

# Setup
with tabs[1]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("⚙️ Setup"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    a,b,c,d=st.columns(4)
    lesson=a.number_input("Lesson",1,20,1,1); week=b.number_input("Week",1,20,1,1)
    teacher_id=c.text_input("Teacher ID","teacher_001"); klass=d.text_input("Class/Section","class_A")
    st.markdown("**🧠 Bloom's taxonomy**")
    focus=st.radio("Pick focus level", BLOOM_LEVELS, index=1, horizontal=True, label_visibility="collapsed")
    mode=st.radio("🎛️ Sequence mode", ["Auto by Focus","Target level(s)"], horizontal=True)
    if mode=="Auto by Focus":
        count=st.slider("How many MCQs?",4,30,10,1)
        rng=random.Random(week*100+lesson); blooms=weighted_bloom_sequence(focus,count,rng)
    else:
        sel=st.multiselect("Pick Bloom levels (cycles)", BLOOM_LEVELS, default=["Understand","Apply","Analyze"])
        count=st.slider("How many MCQs?",4,30,10,1); sel=sel or ["Understand"]
        blooms=(sel*((count//len(sel))+1))[:count]
    chip_map={"Low":"low","Medium":"medium","High":"high"}
    chips=" ".join([f"<span class='chip {chip_map[BLOOM_TIER[b]]}'>{b}</span>" for b in blooms])
    st.markdown("<div class='seq-row'><strong>Sequence preview:</strong> "+chips+"</div>", unsafe_allow_html=True)
    current=policy_tier(int(week)); selected=BLOOM_TIER[focus]
    if current==selected:
        st.markdown(f"<span class='badge-ok'>Policy: {current}</span> &nbsp; <span class='badge-ok'>Selected: {selected} ✓</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='badge-warn'>Policy: {current}</span> &nbsp; <span class='badge-warn'>Selected: {selected} (mismatch)</span>", unsafe_allow_html=True)
    use_ai=st.checkbox("Use AI generator (if key available)", value=False)
    if use_ai: st.info("No API integration in this build (offline generator is used).")
    st.markdown("</div>", unsafe_allow_html=True)

# Generate
with tabs[2]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("⚡️ Generate MCQs & Activities"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    src=st.session_state.src_text
    g1,g2,g3,g4=st.columns(4)
    with g1: act_count=st.slider("Activities (per class)",1,4,2,1)
    with g2: act_style=st.selectbox("Style",["Mixed","Quick tasks","Pair/Group","Project","Assessment"],index=0)
    with g3: act_diff=st.radio("Difficulty",["Low","Medium","High"],index=1,horizontal=True)
    with g4: duration=st.selectbox("Duration (mins)",[15,20,25,30,35,40,45,50,55,60],index=1)
    use_verbs=st.checkbox("Use Bloom verbs",value=True)

    ca,cb=st.columns(2)
    with ca:
        if st.button("📝 Generate Activities", type="primary"):
            base_stems={"Quick tasks":["Do-now:","Exit ticket:","3-minute write:","Sketch-note:","One-sentence summary:"],
                        "Pair/Group":["Think–Pair–Share:","Mini-debate:","Jigsaw teach-back:","Peer review:","Gallery walk:"],
                        "Project":["Prototype:","Mini-project:","Concept map:","Storyboard:","Case design:"],
                        "Assessment":["Quiz item:","Short answer:","Spot the error:","Classify:","Rank & justify:"],
                        "Mixed":["Pair-share on","Mini-poster","Role-play","Think–Pair–Share:","Quick debate:","Case critique:"]}
            base=[s.strip() for s in re.split(r'[.\n]', src or "") if s.strip()] or ["today's topic"]
            acts=[]
            for i in range(act_count):
                stem=base_stems.get(act_style,base_stems["Mixed"])[i%5]
                topic=base[i%len(base)]
                if use_verbs:
                    lv=blooms[i%len(blooms)]; verb={"Low":"List","Medium":"Analyze","High":"Create"}[BLOOM_TIER[lv]]
                    text=f"{stem} {verb} {topic}"
                else:
                    text=f"{stem} {topic}"
                acts.append(f"[{duration} min] {text} ({act_diff.lower()})")
            st.session_state.activities=acts
    with cb:
        if st.button("❓ Generate MCQs", type="primary"):
            st.session_state.mcq_df=offline_mcqs(src,blooms,len(blooms))

    st.markdown("**Quick Editor**")
    st.caption("Edit inline. Your exports will use this exact table.")
    st.session_state.mcq_df=st.data_editor(st.session_state.mcq_df,num_rows="dynamic",use_container_width=True,key="mcq_editor")

    st.markdown("**Activities (editable)**")
    acts_text="\n".join(st.session_state.activities)
    acts_text=st.text_area("One per line",value=acts_text,height=140,key="acts_text")
    st.session_state.activities=[a.strip() for a in acts_text.split("\n") if a.strip()]
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
        if not df.empty and Document:
            st.download_button("Export · MCQs DOCX", mcqs_docx(df), file_name="mcqs.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        elif not df.empty:
            st.info("Install python-docx to enable MCQs DOCX export.")
    with c3:
        if st.session_state.activities:
            st.download_button("Export · Activities CSV", ("\n".join(st.session_state.activities)).encode("utf-8"), file_name="activities.csv", mime="text/csv", use_container_width=True)
    with c4:
        if st.session_state.activities and Document:
            st.download_button("Export · Activities DOCX", activities_docx(st.session_state.activities), file_name="activities.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        elif st.session_state.activities:
            st.info("Install python-docx to enable Activities DOCX.")

with tabs[3]:
    st.markdown("<div class='adi-card'>", unsafe_allow_html=True)
    st.subheader("📦 Export"); st.markdown("<div class='adi-section'></div>", unsafe_allow_html=True)
    st.markdown("<div class='adi-banner'>Export</div>", unsafe_allow_html=True)
    download_buttons()
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Security: API keys (if used) stay server-side (env or .streamlit/secrets). Never accept keys via UI.")
