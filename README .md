[README_DEPLOY (1).md](https://github.com/user-attachments/files/22748273/README_DEPLOY.1.md)
# ADI Builder — Quick Deploy (Render.com or local)

## 1) Files you need in the repo
- `app.py` (your uploaded Streamlit app)
- `requirements.txt` (included here)
- `.streamlit/config.toml` (included here)
- (optional) `adi_logo.png`

## 2) Render.com
- **Environment:** Python 3.10 or 3.11
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- **Instance type:** Starter is fine
- **Health check path:** `/`

If you see a fullscreen modal saying *"Bad message format — Tried to use SessionInfo before it was initialized"*, it usually means the server threw an exception **before Streamlit finished initializing**.
Check the Render logs; typical fixes:
- Make sure your Python version matches the wheel for PyMuPDF (or temporarily remove PyMuPDF if PDFs aren’t required yet).
- Use the provided `requirements.txt` to pin versions.
- Ensure `app.py` imports succeed on boot (no missing packages).

## 3) Local (quick test)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 4) Tips
- If PDFs aren't critical right now, comment out the PyMuPDF import in `app.py` and redeploy (the app gracefully degrades).
- If you add more libraries, pin them in `requirements.txt` to avoid platform build issues.
