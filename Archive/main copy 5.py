from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docxtpl import DocxTemplate
from docx2pdf import convert
import io
import os
import json
import traceback
import subprocess
# from selenium_uploader import upload_pdf_to_portal

# Initialize app
app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
PHYSICIAN_FILE = "data/physicians.json"
TEMPLATE_FILE = "templates/FU_TEMPLATE_Klickovich.docx"
PRC_FOLDER = "PRC_Files_Folder"
os.makedirs("data", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs(PRC_FOLDER, exist_ok=True)

# Ensure physicians.json exists
if not os.path.exists(PHYSICIAN_FILE):
    with open(PHYSICIAN_FILE, "w") as f:
        json.dump([], f)

# Load/save physicians
def load_physicians():
    with open(PHYSICIAN_FILE, "r") as f:
        return json.load(f)

def save_physicians(physicians):
    with open(PHYSICIAN_FILE, "w") as f:
        json.dump(physicians, f, indent=2)

# Model
class Physician(BaseModel):
    name: str

# Routes: Get/Add physicians
@app.get("/physicians")
def get_physicians():
    return load_physicians()

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

# Document generation (DOCX + PDF)
def generate_docx_from_data(data: dict) -> tuple[io.BytesIO, str, str]:
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

        doc.save(docx_path)

        try:
            convert(docx_path, pdf_path)
        except Exception as e:
            print("[PDF ERROR] Could not convert DOCX to PDF:", e)

        byte_io = io.BytesIO()
        with open(docx_path, "rb") as f:
            byte_io.write(f.read())
        byte_io.seek(0)

        return byte_io, pdf_path, data.get("dateOfEvaluation", "")

    except Exception as e:
        print("[ERROR] Failed to generate DOCX/PDF")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating DOCX/PDF: {str(e)}")

# Endpoint: Generate and optionally upload document
@app.post("/generate-doc")
async def generate_doc(request: Request):
    data = await request.json()
    print("📥 Data received:", data)

    file_stream, pdf_path, date_of_eval = generate_docx_from_data(data)
    file_name = data.get("fileName") or data.get("patientName", "follow_up")

    if pdf_path and os.path.exists(pdf_path):
        try:
            title = f"TRANSCRIBED DATA FOLLOW UP VISIT NOTE ON {date_of_eval}"
            upload_pdf_to_portal(
                file_path=pdf_path,
                document_title=title,
                notes=title
            )
        except Exception as e:
            print("⚠️ Upload failed:", e)

    headers = {
        'Content-Disposition': f'attachment; filename="{file_name}.docx"'
    }

    return StreamingResponse(
        file_stream,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers=headers
    )

# Endpoint: Trigger upload automation separately
@app.post("/upload-documents")
async def upload_documents(request: Request):
    data = await request.json()
    file_name = data.get("fileName", "").strip()
    if not file_name:
        raise HTTPException(status_code=400, detail="fileName is required.")

    try:
        print(f"📤 Triggering upload for file: {file_name}")
        subprocess.Popen(["python", "upload_automation.py", file_name])
        return {"message": f"Upload triggered for '{file_name}'."}
    except Exception as e:
        print("❌ Failed to start upload_automation.py:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Health check
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

# Run server
if __name__ == "__main__":
    print("🚀 Starting server at http://127.0.0.1:8000")
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
