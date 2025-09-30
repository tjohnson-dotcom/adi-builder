[README_DEPLOY.md](https://github.com/user-attachments/files/22622442/README_DEPLOY.md)
# ADI Builder — quick start

## Local
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app_fixed.py
```

## Render/Heroku/Other PaaS
1) Upload `app_fixed.py`, `requirements.txt`, and `Procfile`.
2) Start command (or rely on Procfile):
```
streamlit run app_fixed.py --server.port=$PORT --server.address=0.0.0.0
```
