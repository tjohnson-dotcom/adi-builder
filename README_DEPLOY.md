[Uploading README_DEPLOY.md…]()

# ADI Builder — Streamlit Pro v2 (Render)

## Files
- `app.py` — Streamlit app (tabs, uploader for PDF/DOCX/PPTX, MCQs, Activities)
- `requirements.txt` — pinned deps that have wheels for Python 3.11
- `render.yaml` — one-click Render config (no Procfile)

## Render steps
1. Push these files to a fresh GitHub repo.
2. In Render: **New → Web Service** → select the repo.
   - If Render sees `render.yaml`, it will prefill build/start commands.
   - If not, set:
     - **Build:** `pip install -r requirements.txt`
     - **Start:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - Health check path: `/`
3. Deploy. If you ever get a wheel build error, click **Clear build cache & deploy**.
4. If a dependency fails to build, verify the exact pinned versions in `requirements.txt`.

## Notes
- `PyMuPDF==1.24.10` and `lxml==5.2.1` are pinned to versions with manylinux wheels.
- No Procfile is needed on Render Web Services (that’s a Heroku thing).
