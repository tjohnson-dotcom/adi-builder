from docx import Document
import fitz  # PyMuPDF

def export_to_word(questions):
    doc = Document()
    doc.add_heading("ADI Generated Questions", 0)
    for i, q in enumerate(questions, 1):
        doc.add_paragraph(f"Q{i}: {q}")
    doc.save("ADI_Output.docx")

def export_to_pdf(questions):
    doc = fitz.open()
    page = doc.new_page()
    text = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(questions)])
    page.insert_text((72, 72), text)
    doc.save("ADI_Output.pdf")

def export_to_google_docs(questions):
    # Placeholder for Google Docs API integration
    pass
