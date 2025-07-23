# --- main.py ---

import os
import time
import io
import json
import traceback
import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docxtpl import DocxTemplate
from docx2pdf import convert
import uvicorn
# from backend.selenium_uploader import upload_both_files

# Constants
PROVIDER_NAME = "KLICKOVICH MD, ROBERT"
DOCUMENT_TYPE = "Consults"
UPLOAD_URL = "https://txn2.healthfusionclaims.com/electronic/pm/patient_doc.jsp"

# App setup
app = FastAPI()
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
PRC_FOLDER = "PRC_Files_Folder"

os.makedirs("data", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs(PRC_FOLDER, exist_ok=True)

# --- Physician Management ---
def load_physicians():
    if not os.path.exists(PHYSICIAN_FILE):
        return []
    with open(PHYSICIAN_FILE, "r") as f:
        return json.load(f)

def save_physicians(physicians):
    with open(PHYSICIAN_FILE, "w") as f:
        json.dump(physicians, f, indent=2)

class Physician(BaseModel):
    name: str

@app.get("/physicians")
def get_physicians():
    try:
        return load_physicians()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load physicians: {e}")

@app.post("/physicians")
def add_physician(physician: Physician):
    name = physician.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    physicians = load_physicians()
    if any(p.get("name", "").lower() == name.lower() for p in physicians):
        return JSONResponse(content={"message": "Physician already exists"}, status_code=200)
    physicians.append({"name": name})
    save_physicians(physicians)
    return {"message": "Physician added", "name": name}

# --- Document Generation ---
@app.post("/generate-doc")
async def generate_doc(request: Request):
    try:
        data = await request.json()
        print("📥 Received data:", data)

        required_fields = ["fileName", "patientName", "dateOfEvaluation"]
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(status_code=422, detail=f"Missing required field: {field}")

        if not os.path.exists(TEMPLATE_FILE):
            raise HTTPException(status_code=500, detail="Template file not found.")

        def sanitize_filename(filename):
            return re.sub(r'[<>:"/\\|?*]', '', filename)

        base_file_name = sanitize_filename(data.get("fileName", "follow_up").strip())
        docx_path = os.path.join(PRC_FOLDER, f"{base_file_name}.docx")
        pdf_path = os.path.join(PRC_FOLDER, f"{base_file_name}.pdf")

        doc = DocxTemplate(TEMPLATE_FILE)
        doc.render(data)
        doc.save(docx_path)

        try:
            convert(docx_path, pdf_path)
            print(f"✅ PDF created at: {pdf_path}")
        except Exception as e:
            print("⚠️ PDF conversion failed:", e)

        byte_io = io.BytesIO()
        with open(docx_path, "rb") as f:
            byte_io.write(f.read())
        byte_io.seek(0)

        headers = {
            "Content-Disposition": f'attachment; filename="{base_file_name}.docx"'
        }
        return StreamingResponse(byte_io, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] Failed to generate document:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Generation failed.")

# --- Upload Endpoint ---
class UploadRequest(BaseModel):
    dateOfEvaluation: str
    rawFolderPath: str
    rawFileName: str
    transcribedFolderPath: str
    transcribedFileName: str

@app.post("/upload-documents/")
def upload_documents(request: UploadRequest):
    try:
        upload_both_files(
            date_of_evaluation=request.dateOfEvaluation,
            raw_folder_path=request.rawFolderPath,
            raw_file_name=request.rawFileName,
            transcribed_folder_path=request.transcribedFolderPath,
            transcribed_file_name=request.transcribedFileName
        )
        return {"message": "✅ Upload triggered successfully."}
    except Exception as e:
        print("[UPLOAD ERROR]", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Upload failed.")

# --- Root ---
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
