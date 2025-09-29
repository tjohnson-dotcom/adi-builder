port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)

import os
import io
from flask import Flask, render_template_string, request
from werkzeug.utils import secure_filename
from pptx import Presentation

app = Flask(__name__)

# HTML template for the interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ADI Learning Tracker Question Generator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2A4B7C; }
        input[type=file], button { margin-top: 10px; }
        ul { margin-top: 20px; }
    </style>
</head>
<body>
    <h1>ADI Learning Tracker Question Generator</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="ppt_file" accept=".pptx" required>
        <button type="submit">Generate Questions</button>
    </form>
    {% if questions %}
        <h2>Generated Questions:</h2>
        <ul>
        {% for q in questions %}
            <li>{{ q }}</li>
        {% endfor %}
        </ul>
    {% endif %}
</body>
</html>
"""

# Extract text from PowerPoint slides
def extract_text_from_ppt(file_stream):
    prs = Presentation(file_stream)
    text_runs = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text_runs.append(shape.text.strip())
    return [text for text in text_runs if text]

# Generate simple questions from slide text
def generate_questions(text_list):
    return [f"What is the meaning of: '{text}'?" for text in text_list][:10]

@app.route('/', methods=['GET', 'POST'])
def index():
    questions = []
    if request.method == 'POST':
        ppt_file = request.files['ppt_file']
        if ppt_file:
            filename = secure_filename(ppt_file.filename)
            file_stream = io.BytesIO(ppt_file.read())
            text_list = extract_text_from_ppt(file_stream)
            questions = generate_questions(text_list)
    return render_template_string(HTML_TEMPLATE, questions=questions)

# Bind to the correct port for Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
