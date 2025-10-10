
# ADI Builder — Lesson Activities & Questions

This Streamlit app helps instructors at the Academy of Defense Industries (ADI) generate lesson activities, MCQs, and revision prompts aligned with Bloom's Taxonomy.

## 🚀 Features
- Upload lesson materials (PDF, DOCX, PPTX)
- Select verbs by week and cognitive level
- Generate editable MCQs, skills, and revision prompts
- Export to TXT and DOCX
- ADI branding and hover effects
- Reset session button
- Placeholder for future AI-powered question generation

## 🧠 AI Integration Roadmap
- Extract content from uploaded files
- Use NLP to identify key concepts
- Send structured prompts to GPT API
- Display editable AI-generated questions

## ⚙️ Deployment on Render.com
1. Push this repo to GitHub
2. Create a new **Web Service** on Render
3. Use `render.yaml` for configuration
4. Build command: `pip install -r requirements.txt`
5. Start command: `streamlit run app.py`
6. Add environment variable for `OPENAI_API_KEY` (future use)

## 📦 Requirements
See `requirements.txt` for dependencies.

## 📂 Folder Structure
