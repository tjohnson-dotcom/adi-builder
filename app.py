streamlit run "ADI_Builder_Final (2).py"

from flask import Flask, render_template_string, request, send_file
from werkzeug.utils import secure_filename
from pptx import Presentation
from docx import Document
import os
import random
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ADI branding and welcome screen
WELCOME_SCREEN = """
<!doctype html>
<html>
<head>
    <title>ADI Learning Tracker · MCQ Generator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }
        h1 { color: #2c3e50; }
        .container { background-color: white; padding: 20px; border-radius: 10px; }
        .tagline { font-style: italic; color: #7f8c8d; }
        .upload-box { margin-top: 20px; }
        .dropdowns { margin-top: 20px; }
        .btn { padding: 10px 20px; background-color: #2980b9; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background-color: #3498db; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ADI Learning Tracker · MCQ Generator</h1>
        <p class="tagline">Transforming Lessons into Measurable Learning</p>
        <form method="POST" enctype="multipart/form-data">
            <div class="upload-box">
                <label>Upload PowerPoint File:</label><br>
                <input type="file" name="pptx_file" required>
            </div>
            <div class="dropdowns">
                <label>Lesson:</label>
                <input type="text" name="lesson" required><br><br>
                <label>Week:</label>
                <input type="text" name="week" required><br><br>
                <label>Bloom's Verb:</label>
                <select name="verb">
                    <option>Explain</option>
                    <option>Classify</option>
                    <option>Compare</option>
                    <option>Analyze</option>
                    <option>Describe</option>
                    <option>Summarize</option>
                    <option>Discuss</option>
                </select><br><br>
                <label>Time:</label>
                <input type="text" name="time" required><br><br>
                <label>Activity:</label>
                <input type="text" name="activity" required><br><br>
            </div>
            <button class="btn" type="submit">Generate MCQ Paper</button>
        </form>
    </div>
</body>
</html>
"""

def extract_text_from_pptx(file_path):
    prs = Presentation(file_path)
    text_runs = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text_runs.append(shape.text)
    return text_runs

def generate_mcqs(text_runs, verb):
    mcqs = []
    for i, text in enumerate(text_runs):
        if len(text.split()) > 5:
            question = f"{verb} the MOST appropriate statement about: {text.strip()}"
            options = [
                f"A. A correct point about {text.strip()}",
                f"B. An incorrect detail about {text.strip()}",
                f"C. Another incorrect detail about {text.strip()}",
                f"D. A distractor unrelated to {text.strip()}"
            ]
            random.shuffle(options)
            mcqs.append((question, options))
    return mcqs

def create_docx(mcqs, lesson, week):
    doc = Document()
    doc.add_heading('MCQ Paper', 0)
    doc.add_paragraph(f'Lesson {lesson} · Week {week}')
    doc.add_paragraph('Student name: _______________________________    ID: ______________')
    doc.add_paragraph('')

    for i, (question, options) in enumerate(mcqs, 1):
        doc.add_paragraph(f"{i}. {question}")
        for option in options:
            doc.add_paragraph(f"   {option}")
        doc.add_paragraph("")

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pptx_file = request.files['pptx_file']
        lesson = request.form['lesson']
        week = request.form['week']
        verb = request.form['verb']
        time = request.form['time']
        activity = request.form['activity']

        filename = secure_filename(pptx_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pptx_file.save(file_path)

        text_runs = extract_text_from_pptx(file_path)
        mcqs = generate_mcqs(text_runs, verb)
        docx_file = create_docx(mcqs, lesson, week)

        return send_file(docx_file, as_attachment=True, download_name=f"MCQ_Lesson{lesson}_Week{week}.docx")

    return render_template_string(WELCOME_SCREEN)

if __name__ == '__main__':
    app.run(debug=True)
