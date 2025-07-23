from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docxtpl import DocxTemplate
from docx2pdf import convert
import io
import os
import json
import uvicorn
import traceback
from backend.selenium_uploader import upload_pdf_to_portal

# Init FastAPI
app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
PHYSICIAN_FILE = "data/physicians.json"
TEMPLATE_FILE = "templates/FU_TEMPLATE_Klickovich.docx"

# Ensure required folders exist
os.makedirs("data", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Initialize physicians.json if missing
if not os.path.exists(PHYSICIAN_FILE):
    with open(PHYSICIAN_FILE, "w") as f:
        json.dump([], f)

# Utility: Load/save physicians
def load_physicians():
    with open(PHYSICIAN_FILE, "r") as f:
        return json.load(f)

def save_physicians(physicians):
    with open(PHYSICIAN_FILE, "w") as f:
        json.dump(physicians, f, indent=2)

# Model
class Physician(BaseModel):
    name: str

# Route: Get list of physicians
@app.get("/physicians")
def get_physicians():
    return load_physicians()

# Route: Add a physician to the list
@app.post("/physicians")
def add_physician(physician: Physician):
    name = physician.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    physicians = load_physicians()
    if any(p.lower() == name.lower() for p in physicians):
        return JSONResponse(content={"message": "Physician already exists"}, status_code=200)

    physicians.append(name)
    save_physicians(physicians)
    return {"message": "Physician added", "name": name}

PRC_FOLDER = "PRC_Files_Folder"
os.makedirs(PRC_FOLDER, exist_ok=True)

# DOCX generation logic
def generate_docx_from_data(data: dict) -> tuple[io.BytesIO, str | None]:
    try:
        if 'docSections' not in data:
            data['docSections'] = []

        if not os.path.exists(TEMPLATE_FILE):
            raise HTTPException(status_code=500, detail="Template file not found.")

        doc = DocxTemplate(TEMPLATE_FILE)
        doc.render(data)

        file_name = data.get("fileName") or data.get("patientName", "follow_up")
        safe_file_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '_')).rstrip()

        docx_path = os.path.join(PRC_FOLDER, f"{safe_file_name}.docx")
        pdf_path = os.path.join(PRC_FOLDER, f"{safe_file_name}.pdf")

        # Save DOCX
        doc.save(docx_path)

        # Ensure DOCX exists before proceeding
        if not os.path.exists(docx_path):
            raise Exception("DOCX file was not created")

        # Convert to PDF
        try:
            convert(docx_path, pdf_path)
            if not os.path.exists(pdf_path):
                raise Exception("PDF file was not created")
        except Exception as e:
            print("[PDF ERROR] Could not convert DOCX to PDF:", e)
            raise Exception("PDF conversion failed")

        # Return DOCX stream and valid PDF path
        byte_io = io.BytesIO()
        with open(docx_path, "rb") as f:
            byte_io.write(f.read())
        byte_io.seek(0)

        return byte_io, pdf_path

    except Exception as e:
        print("[ERROR] Failed to generate DOCX/PDF")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating files: {str(e)}")


# Route: POST /generate-doc
@app.post("/generate-doc")
async def generate_doc(request: Request):
    data = await request.json()
    print("📥 Data received:", data)

    file_stream, pdf_path = generate_docx_from_data(data)
    file_name = data.get("fileName") or data.get("patientName", "follow_up")

    # Upload PDF only if it exists and was generated correctly
    if pdf_path and os.path.exists(pdf_path):
        try:
            upload_pdf_to_portal(pdf_path, data.get("dateOfEvaluation", ""))
        except Exception as upload_err:
            print("⚠️ PDF upload automation failed:", upload_err)

    headers = {
        'Content-Disposition': f'attachment; filename="{file_name}.docx"'
    }

    return StreamingResponse(
        file_stream,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers=headers
    )


# Root test endpoint
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

# Run app with: python main.py
if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    print(f"🚀 Server running at http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
