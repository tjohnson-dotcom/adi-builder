/**
 * ADI Builder - single-file Apps Script (styling-focused, ASCII only)
 * Paste this whole file into Code.gs in your Apps Script project.
 * It adds a menu -> ADI Builder -> Open, and renders a branded, modern UI.
 * NOTE: This is UI & styling only; wire server actions later.
 */

function onOpen() {
  DocumentApp.getUi()
    .createMenu('ADI Builder')
    .addItem('Open', 'showAdiBuilder')
    .addToUi();
}

function showAdiBuilder() {
  var html = HtmlService.createHtmlOutput(ADI_BUILDER_HTML())
    .setTitle('ADI Builder')
    .setWidth(420);
  DocumentApp.getUi().showSidebar(html);
}

function ADI_BUILDER_HTML() {
  // Single-file HTML returned as a string. Brand & polish per spec.
  var html = '
<!DOCTYPE html>\n\
<html lang="en">\n\
<head>\n\
  <meta charset="UTF-8" />\n\
  <meta name="viewport" content="width=device-width, initial-scale=1" />\n\
  <title>ADI Builder</title>\n\
  <style>\n\
    /* =========================================\n       ADI Design System - quick tokens (ASCII only)\n       ========================================= */\n\
    :root {\n\
      --adi-green: #245a34; /* primary */\n\
      --adi-green-600: #1f4c2c;\n\
      --adi-green-50: #EEF5F0; /* tint for backgrounds */\n\
      --adi-gold: #C8A85A; /* subtle highlight */\n\
      --adi-ink: #1f2937; /* text */\n\
      --adi-muted: #6b7280; /* secondary text */\n\
      --bg: #FAFAF7; /* warm neutral background */\n\
      --card: #ffffff;\n\
      --border: #e5e7eb;\n\
      --radius-xl: 16px;\n\
      --radius-lg: 12px;\n\
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);\n\
      --shadow-md: 0 8px 20px rgba(0,0,0,0.08);\n\
      --focus: 0 0 0 3px rgba(36,90,52,0.25);\n\
      --badge-low-bg: #eaf5ec;\n\
      --badge-low-fg: #1f4c2c;\n\
      --badge-med-bg: #e8f0fb;\n\
      --badge-med-fg: #1e3a8a;\n\
      --badge-hi-bg: #fff1e6;\n\
      --badge-hi-fg: #7c2d12;\n\
    }\n\
    html, body { height: 100%; }\n\
    body {\n\
      margin: 0; padding: 0;\n\
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Inter, Arial, sans-serif;\n\
      color: var(--adi-ink);\n\
      background: var(--bg);\n\
    }\n\
    /* Sidebar layout container */\n\
    .wrap { padding: 14px; }\n\
    /* Header */\n\
    .brand-head {\n\
      background: linear-gradient(90deg, var(--adi-green), var(--adi-green-600));\n\
      color: #fff;\n\
      border-radius: var(--radius-xl);\n\
      padding: 16px 16px;\n\
      box-shadow: var(--shadow-sm);\n\
      display: flex; align-items: center; gap: 10px;\n\
    }\n\
    .brand-head .logo {\n\
      width: 28px; height: 28px; border-radius: 6px;\n\
      background: rgba(255,255,255,0.2);\n\
      display: inline-flex; align-items: center; justify-content: center;\n\
      font-weight: 700; font-size: 14px;\n\
    }\n\
    .brand-head h1 { font-size: 16px; margin: 0; font-weight: 700; }\n\
    .brand-sub { font-size: 11px; opacity: 0.95; margin-top: 4px; }\n\
    /* Section card */\n\
    .card {\n\
      background: var(--card);\n\
      border-radius: var(--radius-xl);\n\
      box-shadow: var(--shadow-sm);\n\
      padding: 14px;\n\
      margin-top: 12px;\n\
      border: 1px solid var(--border);\n\
    }\n\
    .card h2 { font-size: 12px; color: var(--adi-green); letter-spacing: 0.04em; text-transform: uppercase; margin: 0 0 10px; }\n\
    /* Inputs */\n\
    label { font-size: 12px; color: var(--adi-muted); margin-bottom: 6px; display:block; }\n\
    .row { display: flex; gap: 10px; }\n\
    .row > .col { flex: 1; }\n\
    .input, select, textarea {\n\
      width: 100%;\n\
      border: 1px solid var(--border);\n\
      background: #fff;\n\
      border-radius: 999px; /* pill */\n\
      padding: 10px 12px;\n\
      font-size: 13px;\n\
      outline: none;\n\
      transition: box-shadow .15s ease, border-color .15s ease, background .15s ease;\n\
    }\n\
    textarea {\n\
      border-radius: 12px; /* larger surface */\n\
      min-height: 96px;\n\
      resize: vertical;\n\
    }\n\
    .input:focus, select:focus, textarea:focus { box-shadow: var(--focus); border-color: var(--adi-green); }\n\
    /* Upload box */\n\
    .upload {\n\
      border: 2px dashed var(--adi-green);\n\
      background: var(--adi-green-50);\n\
      border-radius: var(--radius-xl);\n\
      padding: 14px;\n\
      display: flex; align-items: center; gap: 10px;\n\
      cursor: pointer;\n\
      transition: background .2s ease;\n\
    }\n\
    .upload:hover { background: #e6efe8; }\n\
    .upload .icon { width: 28px; height: 28px; border-radius: 8px; background: var(--adi-green); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; }\n\
    .upload p { margin: 0; font-size: 13px; }\n\
    .upload small { color: var(--adi-muted); display:block; margin-top:2px; }\n\
    .upload input[type=file] { display:none; }\n\
    /* Pills (Bloom tiers) */\n\
    .pills { display:flex; flex-wrap: wrap; gap: 8px; }\n\
    .pill { font-size: 12px; padding: 6px 10px; border-radius: 999px; border:1px solid transparent; user-select:none; }\n\
    .pill.low { background: var(--badge-low-bg); color: var(--badge-low-fg); }\n\
    .pill.med { background: var(--badge-med-bg); color: var(--badge-med-fg); }\n\
    .pill.hi  { background: var(--badge-hi-bg);  color: var(--badge-hi-fg); }\n\
    /* Stepper */\n\
    .stepper { display: inline-flex; align-items: center; border:1px solid var(--border); border-radius: 999px; overflow:hidden; }\n\
    .stepper button { appearance:none; border: none; background:#fff; padding:6px 10px; cursor:pointer; font-size:14px; }\n\
    .stepper input { width: 44px; text-align:center; border:none; outline:none; font-size: 13px; padding: 8px 6px; }\n\
    .stepper button:focus { box-shadow: var(--focus); }\n\
    /* CTA */\n\
    .btn {\n\
      display:inline-flex; align-items:center; justify-content:center; gap:8px;\n\
      background: var(--adi-green); color:#fff; border:none;\n\
      border-radius: 999px; padding: 10px 14px; font-weight:600; cursor:pointer;\n\
      box-shadow: var(--shadow-sm);\n\
      transition: transform .02s ease, background .15s ease;\n\
    }\n\
    .btn:hover { background: var(--adi-green-600); }\n\
    .btn:active { transform: translateY(1px); }\n\
    /* Tiny caption */\n\
    .caption { font-size: 11px; color: var(--adi-muted); }\n\
    /* Spacing */\n\
    .space { height: 10px; }\n\
  </style>\n\
</head>\n\
<body>\n\
  <div class="wrap">\n\
    <!-- Header with placeholder square for future ADI logo -->\n\
    <div class="brand-head">\n\
      <div class="logo" aria-hidden="true">A</div>\n\
      <div>\n\
        <h1>ADI Builder</h1>\n\
        <div class="brand-sub">Lesson Activities and Questions - Professional - Branded - Export ready</div>\n\
      </div>\n\
    </div>\n\
    <!-- Upload Card -->\n\
    <div class="card">\n\
      <h2>Upload eBook / Lesson Plan / PPT</h2>\n\
      <label class="caption">Accepted: PDF . DOCX . PPTX (<=200MB)</label>\n\
      <label class="upload" for="fileInput">\n\
        <div class="icon" aria-hidden="true">UP</div>\n\
        <div>\n\
          <p><strong>Drag and drop</strong> your file here, or <u>Browse</u></p>\n\
          <small>We recommend eBooks (PDF) as source for best results.</small>\n\
        </div>\n\
      </label>\n\
      <input id="fileInput" type="file" accept=".pdf,.docx,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation" />\n\
    </div>\n\
    <!-- Lesson and Week Card -->\n\
    <div class="card">\n\
      <h2>Pick from eBook / Plan / PPT</h2>\n\
      <div class="row">\n\
        <div class="col">\n\
          <label>Lesson</label>\n\
          <select id="lesson">\n\
            <option value="">-</option>\n\
          </select>\n\
        </div>\n\
        <div class="col">\n\
          <label>Week</label>\n\
          <select id="week">\n\
            <option value="">-</option>\n\
          </select>\n\
        </div>\n\
      </div>\n\
      <div style="margin-top:10px; display:flex; gap:8px;">\n\
        <button class="btn" id="pullMcq">Pull -> MCQs</button>\n\
        <button class="btn" id="pullAct" style="background:var(--adi-gold); color:#1f2a1f;">Pull -> Activities</button>\n\
      </div>\n\
    </div>\n\
    <!-- Activity Parameters Card -->\n\
    <div class="card">\n\
      <h2>Activity Parameters</h2>\n\
      <div class="row">\n\
        <div class="col">\n\
          <label>Number of Activities</label>\n\
          <input id="activities" class="input" type="number" min="1" value="3" />\n\
        </div>\n\
        <div class="col">\n\
          <label>Duration (mins)</label>\n\
          <input id="duration" class="input" type="number" min="5" step="5" value="45" />\n\
        </div>\n\
      </div>\n\
      <div style="margin-top:10px">\n\
        <div class="caption">ADI Bloom tiers for MCQs</div>\n\
        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:6px; margin-top:6px;">\n\
          <div>\n\
            <div class="caption"><strong>Low</strong></div>\n\
            <div class="pills">\n\
              <span class="pill low">define</span>\n\
              <span class="pill low">identify</span>\n\
              <span class="pill low">list</span>\n\
              <span class="pill low">recall</span>\n\
              <span class="pill low">describe</span>\n\
              <span class="pill low">label</span>\n\
            </div>\n\
          </div>\n\
          <div>\n\
            <div class="caption"><strong>Medium</strong></div>\n\
            <div class="pills">\n\
              <span class="pill med">apply</span>\n\
              <span class="pill med">demonstrate</span>\n\
              <span class="pill med">solve</span>\n\
              <span class="pill med">illustrate</span>\n\
            </div>\n\
          </div>\n\
          <div>\n\
            <div class="caption"><strong>High</strong></div>\n\
            <div class="pills">\n\
              <span class="pill hi">evaluate</span>\n\
              <span class="pill hi">synthesize</span>\n\
              <span class="pill hi">design</span>\n\
              <span class="pill hi">justify</span>\n\
            </div>\n\
          </div>\n\
        </div>\n\
      </div>\n\
    </div>\n\
    <!-- Generate MCQs Card (main content simplified) -->\n\
    <div class="card">\n\
      <h2>Generate MCQs - Policy Blocks (Low -> Medium -> High)</h2>\n\
      <label>Topic / Outcome (optional)</label>\n\
      <input class="input" id="topic" placeholder="Module description, knowledge and skills outcomes" />\n\
      <label style="margin-top:10px;">Source text (optional, editable)</label>\n\
      <textarea id="source"></textarea>\n\
      <div style="display:flex; align-items:center; gap:10px; margin-top:10px;">\n\
        <span class="caption">How many MCQ blocks? (x3 questions)</span>\n\
        <div class="stepper" role="group" aria-label="MCQ block count">\n\
          <button type="button" id="minus">-</button>\n\
          <input id="mcqBlocks" type="text" value="1" inputmode="numeric" />\n\
          <button type="button" id="plus">+</button>\n\
        </div>\n\
      </div>\n\
      <div class="space"></div>\n\
      <button class="btn" id="generate">Generate MCQ Blocks</button>\n\
    </div>\n\
  </div>\n\
  <script>\n\
    // Minimal JS for stepper and basic UX feedback\n\
    const input = document.getElementById("mcqBlocks");\n\
    document.getElementById("minus").addEventListener("click", () => {\n\
      const n = Math.max(1, (parseInt(input.value || "1", 10) - 1));\n\
      input.value = String(n);\n\
    });\n\
    document.getElementById("plus").addEventListener("click", () => {\n\
      const n = Math.min(20, (parseInt(input.value || "1", 10) + 1));\n\
      input.value = String(n);\n\
    });\n\
    // Placeholder handlers\n\
    document.getElementById("generate").addEventListener("click", () => {\n\
      google.script.host.toast("Generate clicked - hook up server next.");\n\
    });\n\
    document.getElementById("pullMcq").addEventListener("click", () => {\n\
      google.script.host.toast("Pull MCQs - wire later.");\n\
    });\n\
    document.getElementById("pullAct").addEventListener("click", () => {\n\
      google.script.host.toast("Pull Activities - wire later.");\n\
    });\n\
  </script>\n\
</body>\n\
</html>';\n\
  return html;\n}\n
