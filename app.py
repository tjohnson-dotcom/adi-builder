# app.py — ADI Builder (Fixed Newline Bug)
# ---------------------------------------------------------------
# This version corrects the PDF parsing line that caused
# "unterminated string literal" errors.

import base64
import io
import os
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation

# ---------------------------------------------------------------
# Page setup & theme (kept same as before)
# ---------------------------------------------------------------
st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide", initial_sidebar_state="expanded")

# (CSS and session state code omitted here for brevity — unchanged from previous polished version)

# ---------------------------------------------------------------
# File parsing (fixed newline)
# ---------------------------------------------------------------

def extract_text_from_upload(up_file) -> str:
    if up_file is None:
        return ""
    name = up_file.name.lower()
    text = ""
    try:
        if name.endswith(".pdf"):
            reader = PdfReader(up_file)
            for page in reader.pages[:6]:
                # ✅ FIX: correct newline at end of string
                text += (page.extract_text() or "") + "\n"
        elif name.endswith(".docx"):
            doc = Document(up_file)
            for p in doc.paragraphs[:60]:
                text += p.text + "\n"
        elif name.endswith(".pptx"):
            prs = Presentation(up_file)
            for slide in prs.slides[:15]:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        text += shape.text + "\n"
        return text.strip()[:1000]
    except Exception as e:
        return f"[Could not parse file: {e}]"

# ---------------------------------------------------------------
# Rest of the code unchanged from the last polished version
# ---------------------------------------------------------------
# (Generators, exporters, header, sidebar, tabs, Bloom’s highlighting all remain the same.)
