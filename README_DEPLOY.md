[README_DEPLOY.md](https://github.com/user-attachments/files/22633411/README_DEPLOY.md)
# ADI Builder — Render deploy (v2.5.6)

## Build
pip install -r requirements.txt

## Start
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --browser.gatherUsageStats=false --server.headless=true

## Notes
- Python 3.11 is recommended.
- Uploads up to 200MB.
