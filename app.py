# app.py — ADI Builder (Streamlit, ADI-branded colors + logo + finalized layout)
# Run:  pip install streamlit
#       streamlit run app.py

import base64
import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="wide")

# --- Optional logo embedding (put your logo at ./assets/adi-logo.png) ---
LOGO_PATH = os.path.join("assets", "adi-logo.png")
logo_data_uri = None
try:
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            logo_data_uri = f"data:image/png;base64,{b64}"
except Exception:
    logo_data_uri = None

# --- ADI-branded HTML/CSS ---
ADI_HTML = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>ADI Builder</title>
  <style>
    :root{{
      /* Core ADI palette from logo */
      --adi-green:#245a34; 
      --adi-green-600:#1f4c2c; 
      --adi-green-50:#EEF5F0;
      --adi-gold:#C8A85A;          /* secondary accent */
      --adi-stone:#f3f1ee;         /* stone for High tier */
      --adi-stone-text:#4a4a45;    /* text on stone */
      --adi-sand:#f8f3e8;          /* sand for Medium tier */
      --adi-sand-text:#6a4b2d;     /* text on sand */
      --adi-ink:#1f2937;           /* body text */
      --adi-muted:#6b7280;         /* captions */
      --bg:#FAFAF7;                /* warm background */
      --card:#ffffff;               
      --border:#d9dfda;             
      --radius:14px;                
      --shadow:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);
    }}
    html,body{{height:100%}}
    body{{margin:0;padding:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,Arial,sans-serif;color:var(--adi-ink);background:var(--bg)}}
    .container{{max-width:1180px;margin:0 auto;padding:18px}}

    /* Hero */
    .hero{{background:linear-gradient(90deg,var(--adi-green),var(--adi-green-600));color:#fff;border-radius:16px;padding:18px 20px;box-shadow:var(--shadow)}}
    .hero-row{{display:flex;align-items:center;gap:14px}}
    .logo-box{{width:44px;height:44px;border-radius:10px;background:rgba(0,0,0,0.08);display:flex;align-items:center;justify-content:center;overflow:hidden}}
    .logo-box img{{width:100%;height:100%;object-fit:contain}}
    .logo-fallback{{font-weight:800;font-size:18px;}}
    .hero-title{{font-size:22px;font-weight:800;margin:0}}
    .hero-sub{{font-size:12px;opacity:.95;margin-top:2px}}

    /* Tabs */
    .tabs{{display:flex;gap:8px;align-items:center;margin:12px 0 6px}}
    .tab{{background:#e9efe9;border:1px solid #c9d7cb;color:#204A2C;padding:8px 12px;border-radius:10px;font-size:13px;cursor:pointer}}
    .tab.active{{background:#ffffff;border-color:#b9ccb9}}

    /* Grid */
    .grid{{display:grid;grid-template-columns:320px 1fr;gap:16px;margin-top:10px}}

    /* Cards */
    .card{{background:var(--card);border:1px solid var(--border);border-radius:16px;box-shadow:var(--shadow);padding:14px}}
    .card h3{{margin:0 0 8px 0;color:var(--adi-green);font-size:13px;text-transform:uppercase;letter-spacing:.04em}}

    /* Upload */
    .upload{{border:2px dashed var(--adi-green);background:var(--adi-green-50);border-radius:16px;padding:14px;display:flex;gap:10px;align-items:center}}
    .upload .icon{{width:32px;height:32px;border-radius:8px;background:var(--adi-green);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700}}
    .upload p{{margin:0}}
    .upload small{{color:var(--adi-muted)}}
    .upload input[type=file]{{display:none}}

    /* Inputs */
    label{{display:block;font-size:12px;color:var(--adi-muted);margin-bottom:6px}}
    .row{{display:flex;gap:10px}}
    .row>.col{{flex:1}}
    .input,select,textarea{{width:100%;border:1.5px solid #98b29d;background:#fff;border-radius:999px;padding:10px 12px;font-size:13px;outline:none}}
    .input:focus,select:focus,textarea:focus{{border-color:var(--adi-green);box-shadow:0 0 0 3px rgba(36,90,52,.18)}}
    textarea{{border-radius:12px;min-height:120px;resize:vertical}}

    /* Pills (ADI brand - no blues) */
    .pills{{display:flex;flex-wrap:wrap;gap:8px}}
    .pill{{padding:6px 10px;border-radius:999px;border:1px solid #e3e7e3;background:#f3f7f3;font-size:12px;color:#25402b}}
    .pill.low{{background:#eaf5ec;color:#1f4c2c}}
    .pill.med{{background:var(--adi-sand);color:var(--adi-sand-text)}}
    .pill.hi{{background:var(--adi-stone);color:var(--adi-stone-text)}}

    /* Buttons */
    .btn{{background:var(--adi-green);color:#fff;border:none;border-radius:999px;padding:10px 14px;font-weight:600;cursor:pointer}}
    .btn.gold{{background:var(--adi-gold);color:#1f2a1f}}
    .btn:hover{{filter:brightness(.95)}}

    /* Stepper */
    .stepper{{display:inline-flex;align-items:center;border:1px solid #cbd5cb;border-radius:999px;overflow:hidden}}
    .stepper button{{border:none;background:#fff;padding:6px 10px;cursor:pointer}}
    .stepper input{{width:50px;border:none;text-align:center;padding:8px 6px}}
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"hero\">
      <div class=\"hero-row\">
        <div class=\"logo-box\">{('<img src=\"' + logo_data_uri + '\" alt=\"ADI\"/>') if logo_data_uri else '<div class=\"logo-fallback\">A</div>'}</div>
        <div>
          <div class=\"hero-title\">ADI Builder - Lesson Activities & Questions</div>
          <div class=\"hero-sub\">Professional, branded, editable and export-ready.</div>
        </div>
      </div>
    </div>

    <div class=\"tabs\">
      <div class=\"tab active\">Knowledge MCQs (ADI Policy)</div>
      <div class=\"tab\">Skills Activities</div>
      <span style=\"margin-left:auto;font-size:11px;color:#4b5563\">Branded</span>
    </div>

    <div class=\"grid\">
      <!-- LEFT -->
      <div>
        <div class=\"card\">
          <h3>Upload eBook / Lesson Plan / PPT</h3>
          <div class=\"adi-caption\" style=\"font-size:12px;color:#6b7280;margin-bottom:6px\">Accepted: PDF . DOCX . PPTX (<=200MB)</div>
          <label class=\"upload\" for=\"fileInput\">
            <div class=\"icon\">UP</div>
            <div>
              <p><strong>Drag and drop</strong> your file here, or <u>Browse</u></p>
              <small>We recommend eBooks (PDF) as source for best results.</small>
            </div>
          </label>
          <input id=\"fileInput\" type=\"file\" accept=\".pdf,.docx,.pptx\" />
        </div>

        <div class=\"card\">
          <h3>Pick from eBook / Plan / PPT</h3>
          <div class=\"row\">
            <div class=\"col\">
              <label>Lesson</label>
              <select><option>—</option></select>
            </div>
            <div class=\"col\">
              <label>Week</label>
              <select><option>—</option></select>
            </div>
          </div>
          <div style=\"display:flex;gap:8px;margin-top:10px\">
            <button class=\"btn\">Pull -> MCQs</button>
            <button class=\"btn gold\">Pull -> Activities</button>
          </div>
        </div>

        <div class=\"card\">
          <h3>Activity Parameters</h3>
          <div class=\"row\">
            <div class=\"col\">
              <label>Activities</label>
              <input class=\"input\" type=\"number\" value=\"3\" min=\"1\" />
            </div>
            <div class=\"col\">
              <label>Duration (mins)</label>
              <input class=\"input\" type=\"number\" value=\"45\" min=\"5\" step=\"5\" />
            </div>
          </div>
          <div style=\"margin-top:10px;font-size:12px;color:#6b7280\">ADI Bloom tiers used for MCQs:</div>
          <div style=\"display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:6px\">
            <div>
              <div class=\"adi-caption\" style=\"font-weight:700;margin-bottom:4px\">Low tier</div>
              <div class=\"pills\">
                <span class=\"pill low\">define</span><span class=\"pill low\">identify</span><span class=\"pill low\">list</span>
                <span class=\"pill low\">recall</span><span class=\"pill low\">describe</span><span class=\"pill low\">label</span>
              </div>
            </div>
            <div>
              <div class=\"adi-caption\" style=\"font-weight:700;margin-bottom:4px\">Medium tier</div>
              <div class=\"pills\">
                <span class=\"pill med\">apply</span><span class=\"pill med\">demonstrate</span>
                <span class=\"pill med\">solve</span><span class=\"pill med\">illustrate</span>
              </div>
            </div>
            <div>
              <div class=\"adi-caption\" style=\"font-weight:700;margin-bottom:4px\">High tier</div>
              <div class=\"pills\">
                <span class=\"pill hi\">evaluate</span><span class=\"pill hi\">synthesize</span>
                <span class=\"pill hi\">design</span><span class=\"pill hi\">justify</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT -->
      <div>
        <div class=\"card\">
          <h3>Generate MCQs - Policy Blocks (Low -> Medium -> High)</h3>
          <label>Topic / Outcome (optional)</label>
          <input class=\"input\" placeholder=\"Module description, knowledge & skills outcomes\" />
          <label style=\"margin-top:10px\">Source text (optional, editable)</label>
          <textarea></textarea>
          <div style=\"display:flex;align-items:center;gap:10px;margin-top:10px\">
            <div class=\"adi-caption\" style=\"font-size:12px;color:#6b7280\">How many MCQ blocks? (x3 questions)</div>
            <div class=\"stepper\">
              <button type=\"button\" onclick=\"var i=document.getElementById('mcqs');i.value=Math.max(1,parseInt(i.value||'1',10)-1)\">-</button>
              <input id=\"mcqs\" type=\"text\" value=\"1\" inputmode=\"numeric\" />
              <button type=\"button\" onclick=\"var i=document.getElementById('mcqs');i.value=Math.min(20,parseInt(i.value||'1',10)+1)\">+</button>
            </div>
          </div>
          <div style=\"height:12px\"></div>
          <button class=\"btn\">Generate MCQ Blocks</button>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

# Render in Streamlit
components.html(ADI_HTML, height=1200, scrolling=True)
