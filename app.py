
# ADI Builder — Gradio v1 (no Streamlit required)
# Works on Hugging Face Spaces (SDK: Gradio), Render, Railway, Replit, etc.
import os
import gradio as gr
from docx import Document
from io import BytesIO
from typing import List, Dict
import tempfile

ADI_GREEN = "#245a34"
ADI_GOLD = "#C8A85A"

BLOOM_VERBS = {
    "Low": ["define", "list", "identify", "recall", "describe", "label", "match", "name", "state", "select"],
    "Medium": ["explain", "classify", "apply", "analyze", "compare", "summarize", "illustrate", "solve", "organize", "differentiate"],
    "High": ["evaluate", "design", "construct", "hypothesize", "justify", "critique", "propose", "formulate", "synthesize", "optimize"],
}

def bloom_for_week(week: int) -> str:
    if 1 <= week <= 4: return "Low"
    if 5 <= week <= 9: return "Medium"
    return "High"

def generate_mcqs(verbs: List[str], source_text: str, n: int = 5) -> List[Dict]:
    base_topic = (source_text.strip().split("\n")[0] if source_text.strip() else "the lesson topic").strip()
    if not base_topic:
        base_topic = "the lesson topic"
    qs = []
    for i in range(n):
        verb = verbs[i % max(1, len(verbs))].capitalize() if verbs else "Understand"
        stem = f"{verb} {base_topic}: Which option best fits?"
        correct = f"Correct application of {verb.lower()} on {base_topic}"
        distractors = [
            f"Irrelevant detail about {base_topic}",
            f"Common misconception about {base_topic}",
            f"Partially true but incomplete about {base_topic}",
        ]
        qs.append({
            "question": stem,
            "options": [correct] + distractors,
            "answer_index": 0,
            "rationale": f"The best choice shows a proper {verb.lower()}-level response on {base_topic}.",
        })
    return qs

def generate_activities(verbs: List[str], base_topic: str, n: int = 5) -> List[str]:
    topic = base_topic or "the lesson topic"
    templates = [
        "Create a one-page brief explaining {} in your own words.",
        "Design a simple infographic that compares key aspects of {}.",
        "Develop a short case study applying {} to a real scenario.",
        "Critique a peer's answer about {}, suggesting two improvements.",
        "Propose an improvement plan to enhance understanding of {}.",
        "Construct a concept map connecting subtopics within {}.",
        "Justify your choice of methods for assessing {} in class.",
        "Formulate three open-ended questions that probe {} deeply."
    ]
    out = []
    for i in range(min(n, len(templates))):
        verb = (verbs[i % max(1, len(verbs))] if verbs else "explain")
        out.append(templates[i].format(topic) + f" (Use the verb: {verb})")
    return out

def docx_from_mcqs(mcqs: List[Dict], title: str) -> bytes:
    doc = Document()
    doc.add_heading(title, level=1)
    for idx, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"{idx}. {q['question']}")
        letters = ["A","B","C","D"]
        for j, opt in enumerate(q["options"]):
            doc.add_paragraph(f"   {letters[j]}) {opt}")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def docx_answer_key(mcqs: List[Dict]) -> bytes:
    doc = Document()
    doc.add_heading("Answer Key", level=1)
    letters = ["A","B","C","D"]
    for idx, q in enumerate(mcqs, 1):
        doc.add_paragraph(f"Q{idx}: {letters[q['answer_index']]}")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def docx_activities(acts: List[str], title: str = "Activity Sheet") -> bytes:
    doc = Document()
    doc.add_heading(title, level=1)
    for idx, a in enumerate(acts, 1):
        doc.add_paragraph(f"{idx}. {a}")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def gift_from_mcqs(mcqs: List[Dict]) -> bytes:
    lines = []
    letters = ["A","B","C","D"]
    for idx, q in enumerate(mcqs, 1):
        correct = q["options"][q["answer_index"]]
        distractors = [opt for j, opt in enumerate(q["options"]) if j != q["answer_index"]]
        body = f"::{f'Q{idx}'}:: {q['question']} {{ = {correct} ~ {distractors[0]} ~ {distractors[1]} ~ {distractors[2]} }}"
        lines.append(body)
    return ("\n\n".join(lines)).encode("utf-8")

# --- Gradio handlers ---
def update_verbs(bloom: str):
    choices = BLOOM_VERBS[bloom]
    default = choices[:5]
    return gr.CheckboxGroup.update(choices=choices, value=default)

def mcq_action(verbs: List[str], source_text: str):
    mcqs = generate_mcqs(verbs, source_text, n=5)
    # Preview markdown
    md = []
    letters = ["A","B","C","D"]
    for i, q in enumerate(mcqs, 1):
        md.append(f"**Q{i}.** {q['question']}")
        for j, opt in enumerate(q["options"]):
            md.append(f"- {letters[j]}) {opt}")
        md.append("")
    md_preview = "\n".join(md)
    # Files
    tmpdir = tempfile.mkdtemp()
    mcq_path = os.path.join(tmpdir, "mcq_paper.docx")
    ans_path = os.path.join(tmpdir, "answer_key.docx")
    gift_path = os.path.join(tmpdir, "mcq_questions.gift")
    with open(mcq_path, "wb") as f: f.write(docx_from_mcqs(mcqs, "MCQ Paper"))
    with open(ans_path, "wb") as f: f.write(docx_answer_key(mcqs))
    with open(gift_path, "wb") as f: f.write(gift_from_mcqs(mcqs))
    return md_preview, mcq_path, ans_path, gift_path

def activities_action(verbs: List[str], source_text: str):
    base_topic = (source_text.strip().split("\n")[0] if source_text.strip() else "").strip()
    acts = generate_activities(verbs, base_topic, n=5)
    md = []
    for i, a in enumerate(acts, 1):
        md.append(f"{i}. {a}")
    md_preview = "\n".join(md)
    tmpdir = tempfile.mkdtemp()
    act_path = os.path.join(tmpdir, "activity_sheet.docx")
    with open(act_path, "wb") as f: f.write(docx_activities(acts))
    return md_preview, act_path

with gr.Blocks(theme=gr.themes.Default(primary_hue="green")) as demo:
    gr.Markdown(f"<div style='display:flex;gap:8px;align-items:center'><div style='background:{ADI_GREEN};color:#fff;padding:6px 10px;border-radius:999px;font-weight:600'>ADI Builder</div><div class='muted'>Gradio Edition</div></div>")
    gr.Markdown("### Simple, stable app (no Streamlit).")

    with gr.Row():
        with gr.Column(scale=1):
            lesson = gr.Radio([1,2,3,4,5], value=1, label="Lesson", interactive=True)
            week = gr.Radio(list(range(1,15)), value=1, label="Week", interactive=True)
            bloom_default = bloom_for_week(1)
            bloom = gr.Radio(["Low","Medium","High"], value=bloom_default, label="Bloom level")
            verbs = gr.CheckboxGroup(choices=BLOOM_VERBS[bloom_default], value=BLOOM_VERBS[bloom_default][:5], label="Choose verbs (5–10)")
            source_text = gr.Textbox(lines=8, placeholder="Optional source text...", label="Source text (optional)")
            bloom.change(fn=update_verbs, inputs=bloom, outputs=verbs)

        with gr.Column(scale=2):
            with gr.Row():
                btn_mcq = gr.Button("⚡ Auto-fill MCQs")
                btn_act = gr.Button("🧩 Generate Activities")
            with gr.Row():
                with gr.Column():
                    mcq_preview = gr.Markdown("MCQ preview will appear here...")
                    mcq_doc = gr.File(label="MCQ Paper (.docx)", interactive=False)
                    ans_doc = gr.File(label="Answer Key (.docx)", interactive=False)
                    gift_file = gr.File(label="Moodle GIFT (.gift)", interactive=False)
                with gr.Column():
                    act_preview = gr.Markdown("Activities preview will appear here...")
                    act_doc = gr.File(label="Activity Sheet (.docx)", interactive=False)
            btn_mcq.click(mcq_action, inputs=[verbs, source_text], outputs=[mcq_preview, mcq_doc, ans_doc, gift_file])
            btn_act.click(activities_action, inputs=[verbs, source_text], outputs=[act_preview, act_doc])

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
