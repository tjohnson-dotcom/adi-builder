from docx import Document
from datetime import datetime

def export_to_word(course_info, verbs):
    doc = Document()
    doc.add_heading("ADI Builder Output", 0)
    doc.add_paragraph(f"Course: {course_info['course']}")
    doc.add_paragraph(f"Instructor: {course_info['instructor']}")
    doc.add_paragraph(f"Date: {course_info['date'].strftime('%Y-%m-%d')}")
    doc.add_heading("Selected Verbs", level=1)
    for verb in verbs:
        doc.add_paragraph(f"- {verb}")
    filename = f"ADI_Output_{course_info['course'].replace(' ', '_')}.docx"
    doc.save(filename)
