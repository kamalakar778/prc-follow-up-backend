# # from docx import Document
# # import io

# # def generate_docx_from_data(form_data):
# #     # Create a new document
# #     doc = Document()

# #     # Add title
# #     doc.add_heading('Follow Up Report', 0)

# #     # Add patient details from form_data
# #     for key, value in form_data.items():
# #         doc.add_paragraph(f"{key.replace('_', ' ').title()}: {value}")

# #     # Save to in-memory file
# #     docx_io = io.BytesIO()
# #     doc.save(docx_io)
# #     docx_io.seek(0)
# #     return docx_io

# #  ---------------------------------- x2 ------------------------------------
# # utils.py
# from docxtpl import DocxTemplate
# import io
# import os
# from fastapi import HTTPException

# def generate_docx_from_data(data: dict) -> io.BytesIO:
#     """
#     Generate a DOCX file from a template using docxtpl,
#     rendering the data dictionary into the template placeholders.

#     Returns a BytesIO stream with the generated DOCX content.
#     """
#     try:
#         template_path = os.path.join('templates', 'FU_TEMPLATE_Klickovich.docx')
#         if not os.path.exists(template_path):
#             raise HTTPException(status_code=500, detail="Template file not found.")

#         doc = DocxTemplate(template_path)
#         doc.render(data)

#         byte_io = io.BytesIO()
#         doc.save(byte_io)
#         byte_io.seek(0)  # Important: reset buffer position before returning
#         return byte_io
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating DOCX: {str(e)}")



