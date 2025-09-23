# app.py  (Streamlit)
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADI Builder", page_icon="📘", layout="centered")

ADI_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ADI Builder</title>
  <style>
    :root {
      --adi-green: #245a34;
      --adi-green-600: #1f4c2c;
      --adi-green-50: #EEF5F0;
      --adi-gold: #C8A85A;
      --adi-ink: #1f2937;
      --adi-muted: #6b7280;
      --bg: #FAFAF7;
      --card: #ffffff;
      --border: #e5e7eb;
      --radius-xl: 16px;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
      --focus: 0 0 0 3px rgba(36,90,52,0.25);
      --badge-low-bg: #eaf5ec;
      --badge-low-fg: #1f4c2c;
      --badge-med-bg: #e8f0fb;
      --badge-med-fg: #1e3a8a;
      --badge-hi-bg: #fff1e6;
      --badge-hi-fg: #7c2d12;
    }
    html, body { height:100%; }
    body { margin:0; padding:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Inter, Arial, sans-serif; color: var(--adi-ink); background: var(--bg); }
    .wrap { padding: 18px; max-width: 980px; margin: 0 auto; }
    .brand-head { background: linear-gradient(90deg, var(--adi-green), var(--adi-green-600)); color:#fff; border-radius: var(--radius-xl); padding:18px; box-shadow: var(--shadow-sm); display:flex; align-items:center; gap:12px; }
    .brand-head .logo { width:34px; height:34px; border-radius:8px; background: rgba(255,255,255,0.2); display:inline-flex; align-items:center; justify-content:center; font-weight:700; font-size:16px; }
    .brand-head h1 { font-size:18px; margin:0; font-weight:700; }
    .brand-sub { font-size:12px; opacity:0.95; margin-top:4px; }
    .grid { display:grid; grid-template-columns: 300px 1fr; gap: 14px; margin-top:14px; }
    .card { background: var(--card); border-radius: var(--radius-xl); box-shadow: var(--shadow-sm); padding:14px; border:1px solid var(--border); }
    .card h2 { font-size:12px; color: var(--adi-green); letter-spacing:0.04em; text-transform: uppercase; margin:0 0 10px; }
    label { font-size:12px; color: var(--adi-muted); margin-bottom:6px; display:block; }
    .row { display:flex; gap:10px; }
    .row > .col { flex:1; }
    .input, select, textarea { width:100%; border:1px solid var(--border); background:#fff; border-radius:999px; padding:10px 12px; font-size:13px; outline:none; transition: box-shadow .15s ease, border-color .15s ease, background .15s ease; }
    textarea { border-radius:12px; min-height:120px; resize:vertical; }
    .input:focus, select:focus, textarea:focus { box-shadow: var(--focus); border-color: var(--adi-green); }
    .upload { border:2px dashed var(--adi-green); background: var(--adi-green-50); border-radius: var(--radius-xl); padding:14px; display:flex; align-items:center; gap:10px; cursor:pointer; transition: background .2s ease; }
    .upload:hover { background:#e6efe8; }
    .upload .icon { width:28px; height:28px; border-radius:8px; background: var(--adi-green); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; }
    .upload p { margin:0; font-size:13px; }
    .upload small { color: var(--adi-muted); display:block; margin-top:2px; }
    .upload input[type=file] { display:none; }
    .pills { display:flex; flex-wrap: wrap; gap:8px; }
    .pill { font-size:12px; padding:6px 10px; border-radius:999px; border:1px solid transparent; user-select:none; }
    .pill.low { background: var(--badge-low-bg); color: var(--badge-low-fg); }
    .pill.med { background: var(--badge-med-bg); color: var(--badge-med-fg); }
    .pill.hi { background: var(--badge-hi-bg); color: var(--badge-hi-fg); }
    .stepper { display:inline-flex; align-items:center; border:1px solid var(--border); border-radius:999px; overflow:hidden; }
    .stepper button { appearance:none; border:none; background:#fff; padding:6px 10px; cursor:pointer; font-size:14px; }
    .stepper input { width:44px; text-align:center; border:none; outline:none; font-size:13px; padding:8px 6px; }
    .btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; background: var(--adi-green); color:#fff; border:none; border-radius:999px; padding:10px 14px; font-weight:600; cursor:pointer; box-shadow: var(--shadow-sm); transition: transform .02s ease, background .15s ease; }
    .btn:hover { background: var(--adi-green-600); }
    .caption { font-size:11px; color: var(--adi-muted); }
    .space { height:10px; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand-head">
      <div class="logo" aria-hidden="true">A</div>
      <div>
        <h1>ADI Builder</h1>
        <div class="brand-sub">Lesson Activities and Questions - Professional - Branded - Export ready</div>
      </div>
    </div>

    <div class="grid">
      <!-- Left Column (Sidebar) -->
      <div class="left">
        <div class="card">
          <h2>Upload eBook / Lesson Plan / PPT</h2>
          <label class="caption">Accepted: PDF . DOCX . PPTX (<=200MB)</label>
          <label class="upload" for="fileInput">
            <div class="icon" aria-hidden="true">UP</div>
            <div>
              <p><strong>Drag and drop</strong> your file here, or <u>Browse</u></p>
              <small>We recommend eBooks (PDF) as source for best results.</small>
            </div>
          </label>
          <input id="fileInput" type="file" accept=".pdf,.docx,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation" />
        </div>

        <div class="card">
          <h2>Pick from eBook / Plan / PPT</h2>
          <div class="row">
            <div class="col">
              <label>Lesson</label>
              <select id="lesson"><option value="">-</option></select>
            </div>
            <div class="col">
              <label>Week</label>
              <select id="week"><option value="">-</option></select>
            </div>
          </div>
          <div style="margin-top:10px; display:flex; gap:8px;">
            <button class="btn" id="pullMcq">Pull -> MCQs</button>
            <button class="btn" id="pullAct" style="background:var(--adi-gold); color:#1f2a1f;">Pull -> Activities</button>
          </div>
        </div>

        <div class="card">
          <h2>Activity Parameters</h2>
          <div class="row">
            <div class="col">
              <label>Number of Activities</label>
              <input id="activities" class="input" type="number" min="1" value="3" />
            </div>
            <div class="col">
              <label>Duration (mins)</label>
              <input id="duration" class="input" type="number" min="5" step="5" value="45" />
            </div>
          </div>
          <div style="margin-top:10px">
            <div class="caption">ADI Bloom tiers for MCQs</div>
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:6px; margin-top:6px;">
              <div>
                <div class="caption"><strong>Low</strong></div>
                <div class="pills">
                  <span class="pill low">define</span>
                  <span class="pill low">identify</span>
                  <span class="pill low">list</span>
                  <span class="pill low">recall</span>
                  <span class="pill low">describe</span>
                  <span class="pill low">label</span>
                </div>
              </div>
              <div>
                <div class="caption"><strong>Medium</strong></div>
                <div class="pills">
                  <span class="pill med">apply</span>
                  <span class="pill med">demonstrate</span>
                  <span class="pill med">solve</span>
                  <span class="pill med">illustrate</span>
                </div>
              </div>
              <div>
                <div class="caption"><strong>High</strong></div>
                <div class="pills">
                  <span class="pill hi">evaluate</span>
                  <span class="pill hi">synthesize</span>
                  <span class="pill hi">design</span>
                  <span class="pill hi">justify</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column (Main) -->
      <div class="right">
        <div class="card">
          <h2>Generate MCQs - Policy Blocks (Low -> Medium -> High)</h2>
          <label>Topic / Outcome (optional)</label>
          <input class="input" id="topic" placeholder="Module description, knowledge and skills outcomes" />
          <label style="margin-top:10px;">Source text (optional, editable)</label>
          <textarea id="source"></textarea>
          <div style="display:flex; align-items:center; gap:10px; margin-top:10px;">
            <span class="caption">How many MCQ blocks? (x3 questions)</span>
            <div class="stepper" role="group" aria-label="MCQ block count">
              <button type="button" id="minus">-</button>
              <input id="mcqBlocks" type="text" value="1" inputmode="numeric" />
              <button type="button" id="plus">+</button>
            </div>
          </div>
          <div class="space"></div>
          <button class="btn" id="generate">Generate MCQ Blocks</button>
        </div>
      </div>
    </div>
  </div>

  <script>
    const input = document.getElementById("mcqBlocks");
    document.getElementById("minus").addEventListener("click", function(){
      var n = Math.max(1, (parseInt(input.value || "1", 10) - 1));
      input.value = String(n);
    });
    document.getElementById("plus").addEventListener("click", function(){
      var n = Math.min(20, (parseInt(input.value || "1", 10) + 1));
      input.value = String(n);
    });
    document.getElementById("generate").addEventListener("click", function(){
      alert("Generate clicked - wire to Streamlit backend next.");
    });
    document.getElementById("pullMcq").addEventListener("click", function(){
      alert("Pull MCQs - wire later.");
    });
    document.getElementById("pullAct").addEventListener("click", function(){
      alert("Pull Activities - wire later.");
    });
  </script>
</body>
</html>
"""

# Render the HTML as a component
components.html(ADI_HTML, height=1200, scrolling=True)
