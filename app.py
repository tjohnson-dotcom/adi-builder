
import io, os, base64, random, re, json, hashlib
from datetime import date
import streamlit as st

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None

try:
    from pptx import Presentation as PptxPresentation
except Exception:
    PptxPresentation = None

st.set_page_config(page_title="ADI Builder (E‑book Safe)", page_icon="📘", layout="wide")

def pdf_to_text(file_like, quick_pages=15, deep=False):
    if fitz is None:
        return ""
    try:
        doc = fitz.open(stream=file_like.read(), filetype="pdf")
    except Exception:
        try:
            file_like.seek(0)
            doc = fitz.open(stream=file_like.read(), filetype="pdf")
        except Exception:
            return ""
    N = doc.page_count
    if not deep:
        N = min(N, quick_pages)
    out = []
    prog = st.progress(0.0, text="Reading PDF…")
    for i in range(N):
        try:
            page = doc.load_page(i)
            out.append(page.get_text())
        except Exception as e:
            st.warning(f"Skipped page {i+1}: {e}")
        prog.progress((i+1)/N, text=f"Reading PDF… {i+1}/{N}")
    return "\n".join(out).strip()

def docx_to_text(file_like):
    if DocxDocument is None:
        return ""
    try:
        data = file_like.read()
        bio = io.BytesIO(data)
        d = DocxDocument(bio)
        return "\n".join([p.text for p in d.paragraphs]).strip()
    except Exception:
        return ""

def pptx_to_text(file_like):
    if PptxPresentation is None:
        return ""
    try:
        data = file_like.read()
        bio = io.BytesIO(data)
        p = PptxPresentation(bio)
        out = []
        for slide in p.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    t = (shape.text or "").strip()
                    if t:
                        out.append(t)
        return "\n".join(out).strip()
    except Exception:
        return ""

def txt_to_text(file_like):
    data = file_like.read()
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc, errors="ignore")
        except Exception:
            continue
    return ""

def detect_ext(name):
    return (os.path.splitext(name)[1] or "").lower()

def safe_file_text(upload, deep=False):
    ext = detect_ext(upload.name)
    upload.seek(0)
    if ext == ".pdf":
        return pdf_to_text(upload, deep=deep)
    elif ext == ".docx":
        return docx_to_text(upload)
    elif ext == ".pptx":
        return pptx_to_text(upload)
    elif ext in (".txt", ".md", ".rtf"):
        return txt_to_text(upload)
    else:
        return txt_to_text(upload)

def b64_logo(path="adi_logo.png"):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""

st.markdown('<div style="background:#245a34;color:#fff;border-radius:14px;padding:12px 14px;margin-bottom:10px;"><b>ADI Builder — E‑book Safe Uploads</b><br/>Large PDFs, DOCXs and PPTXs won’t crash the app. Quick scan vs Deep scan supported.</div>', unsafe_allow_html=True)

with st.sidebar:
    deep = st.toggle("Deep scan e‑books (full document)", value=False, help="Off = quick scan (~15 pages). On = full PDF.")
    upload = st.file_uploader("Upload e‑book or source (PDF/DOCX/PPTX/TXT)", type=["pdf","docx","pptx","txt","md","rtf"], key="ebook_upl")

    if upload is not None:
        size_kb = (getattr(upload, "size", 0) or 0)/1024
        st.info(f"Selected: **{upload.name}** ({size_kb:.1f} KB) • Deep scan: {'On' if deep else 'Off'}")
        if st.button("Process source", type="primary"):
            try:
                text = safe_file_text(upload, deep=deep) or ""
                if text.strip():
                    st.session_state["source_text"] = text
                    st.success("✅ Upload processed and indexed. You can generate Activities / MCQs / Revision now.")
                else:
                    st.warning("Processed the file but couldn’t extract readable text. If this is a scanned PDF, consider an OCR’d copy.")
                st.session_state["ebook_upl"] = None
            except Exception as e:
                st.error(f"Could not process file safely: {e}")

st.subheader("Source preview (first 1200 chars)")
src = st.session_state.get("source_text","")
if src:
    st.text(src[:1200] + ("..." if len(src)>1200 else ""))
else:
    st.caption("No source loaded yet. Upload in the left sidebar.")
