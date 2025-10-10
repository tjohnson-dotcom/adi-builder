from docx import Document

def export_to_word(topic, questions, activities):
    doc = Document()
    doc.add_heading(f"ADI Builder Output for {topic}", 0)
    doc.add_heading("Questions", level=1)
    for q in questions:
        doc.add_paragraph(q)
    doc.add_heading("Activities", level=1)
    for a in activities:
        doc.add_paragraph(a)
    doc.save("ADI_Output.docx")

def export_to_gdocs(topic, questions, activities):
    # Placeholder for Google Docs export logic
    print("Export to Google Docs is not implemented in this demo.")
