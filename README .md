[README.md](https://github.com/user-attachments/files/22702793/README.md)
# ADI Builder — Curriculum‑Aware Lesson Generator

A Streamlit app that generates **Activities**, **MCQs**, and **Revision** aligned to your academy’s modules:
- Auto‑links **Week → KLO** (with optional override)
- Different **teachers** get different (seeded) versions
- Exports to **DOCX** (no external APIs)

---

## 1) Folder Layout
```
ADI_Builder/
├─ app.py
├─ adi_modules.json        # curriculum map (25 modules)
├─ adi_logo.png            # your logo (optional but recommended)
└─ requirements.txt        # you chose the full Option 2
```

**Tip:** Keep `adi_modules.json` in the same folder as `app.py`.

---

## 2) Local Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Open the printed local URL in your browser.

---

## 3) Render Deploy (recommended)
1. Push this folder to GitHub.
2. On Render:
   - **New +** → **Web Service**
   - Connect your repo.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Environment:** Python 3.11 (or 3.10).  
3. Click **Create Web Service** → first build will install packages and start the app.

> If your repo already has a `render.yaml`, ensure it uses the same **Start Command** above.

---

## 4) Using the App (Quick Guide)
1. **Sidebar → Course details**: choose Course, Cohort, Instructor, Week & Lesson.
2. **Outcome alignment**: app **auto‑links KLO** for that week. (Turn on **Override** if a class is behind/ahead.)
3. (Optional) **Upload** a source file (PDF/PPTX/DOCX/TXT) → **Process source**.
4. Select **Bloom verbs** (the highlighted band matches the Week).
5. Choose **Mode** (Activities / MCQs / Revision / Print Summary) and **Generate**.
6. **Download DOCX** for printing or sharing.

**Multiple teachers** on the same module will get different content (seeded by instructor name) while staying aligned to the same KLO and Bloom level.

---

## 5) Customisation
- **Add/Update modules:** edit `adi_modules.json`. (Each module includes `course_code`, `course_title`, `klos`, `slos`, and `weeks`.)
- **Logo:** replace `adi_logo.png` (PNG recommended, transparent background).
- **Override KLO:** Sidebar → *Outcome alignment* → tick **Override** (admin PIN optional in code).

---

## 6) Requirements
You selected the full set for e‑book/PPTX/PDF support:
```
streamlit==1.37.0
python-docx==1.1.0
pymupdf==1.24.2
python-pptx==0.6.23
pandas==2.2.2
numpy==1.26.4
pillow==10.3.0
```

---

## 7) Troubleshooting
- **“KLO?” in header / generic MCQs** → your course in `adi_modules.json` has empty `klos`. Add `KLO1…` with text or use the patched JSON.
- **Nothing happens on upload** → very large PDFs may not yield text. It’s optional; the app still generates using Topic/KLO.
- **Render build fails** → pin package versions (already done above) and ensure the **Start Command** matches this README.
- **Port error on Render** → include `--server.port $PORT --server.address 0.0.0.0` in Start Command.
- **Arabic characters** in DOCX → `python-docx` supports UTF‑8 text; if you see boxes, switch the Word font to Arial or Noto Naskh.

---

## 8) Data & Privacy
No external APIs. Inputs stay in memory of the running instance only. Delete uploaded files from the session before sharing screens if needed.

---

## 9) Maintenance
- Keep `adi_modules.json` under version control.
- For new modules, add KLOs early so Week → KLO linking works.
- Consider a quarterly content review to refresh verbs/templates.
