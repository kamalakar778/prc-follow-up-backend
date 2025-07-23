# === main.py (Updated) ===
import os
import io
import json
import re
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docxtpl import DocxTemplate
from docx2pdf import convert
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium_uploader import upload_document
import uvicorn

# === Constants ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHYSICIAN_FILE = os.path.join(BASE_DIR, "data", "physicians.json")
TEMPLATE_FILE = os.path.join(BASE_DIR, "templates", "FU_TEMPLATE_Klickovich.docx")
PRC_FOLDER = os.path.join(BASE_DIR, "PRC_Files_Folder")
RAW_FOLDER = os.path.join(PRC_FOLDER, "RAW")

# === FastAPI App ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Ensure Folders Exist ===
os.makedirs(os.path.dirname(PHYSICIAN_FILE), exist_ok=True)
os.makedirs(os.path.dirname(TEMPLATE_FILE), exist_ok=True)
os.makedirs(PRC_FOLDER, exist_ok=True)
os.makedirs(RAW_FOLDER, exist_ok=True)

# === Models ===
class Physician(BaseModel):
    name: str

class GenerateDocRequest(BaseModel):
    fileName: str
    patientName: str
    dateOfEvaluation: str
    signature: str = ""

class UploadRequest(BaseModel):
    dateOfEvaluation: str
    patientId: str
    patientName: str

# === Utilities ===
def load_physicians():
    if not os.path.exists(PHYSICIAN_FILE):
        return []
    try:
        with open(PHYSICIAN_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_physicians(physicians):
    with open(PHYSICIAN_FILE, "w") as f:
        json.dump(physicians, f, indent=2)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', name)

# === Endpoints ===
@app.get("/")
def root():
    return {"message": "Welcome to the Follow-up Document Generator API"}

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
        raise HTTPException(status_code=400, detail="Physician name is required.")

    physicians = load_physicians()
    if any(p.get("name", "").lower() == name.lower() for p in physicians):
        return JSONResponse(content={"message": "Physician already exists"}, status_code=200)

    physicians.append({"name": name})
    save_physicians(physicians)
    return {"message": "Physician added successfully", "name": name}

@app.post("/generate-doc")
async def generate_doc(data: GenerateDocRequest):
    try:
        print("\ud83d\udcc5 Generating DOCX for:", data.dict())

        if not os.path.exists(TEMPLATE_FILE):
            raise HTTPException(status_code=500, detail="Template file not found.")

        safe_filename = sanitize_filename(data.fileName.strip())
        docx_path = os.path.join(PRC_FOLDER, f"{safe_filename}.docx")
        pdf_path = os.path.join(PRC_FOLDER, f"{safe_filename}.pdf")

        doc = DocxTemplate(TEMPLATE_FILE)
        context = data.dict()
        doc.render(context)
        doc.save(docx_path)
        print(f"\ud83d\udcc4 DOCX created: {docx_path}")

        try:
            convert(docx_path, pdf_path)
            print(f"\u2705 PDF saved: {pdf_path}")
        except Exception as e:
            print("\u26a0\ufe0f PDF conversion failed:", e)

        byte_io = io.BytesIO()
        with open(docx_path, "rb") as f:
            byte_io.write(f.read())
        byte_io.seek(0)

        return StreamingResponse(
            byte_io,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}.docx"'}
        )

    except Exception as e:
        print("[ERROR] Failed to generate DOCX:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Document generation failed.")

@app.post("/upload-documents/")
async def upload_generated_documents(payload: UploadRequest):
    try:
        print("\ud83d\udce4 Uploading PDFs for:", payload.dict())

        filename = f"RAWTRANSCIBED-CKOUT-{payload.dateOfEvaluation}--{payload.patientId} {payload.patientName}.PDF"
        raw_path = os.path.join(RAW_FOLDER, filename)
        transcribed_path = os.path.join(PRC_FOLDER, filename)

        if not os.path.isfile(raw_path):
            raise HTTPException(status_code=404, detail=f"RAW PDF not found: {raw_path}")
        if not os.path.isfile(transcribed_path):
            raise HTTPException(status_code=404, detail=f"Transcribed PDF not found: {transcribed_path}")

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)

        upload_document(driver, f"RAW DATA FOLLOW UP VISIT NOTE ON {payload.dateOfEvaluation}", raw_path, f"RAW DATA FOLLOW UP VISIT NOTE ON {payload.dateOfEvaluation}")
        upload_document(driver, f"TRANSCRIBED DATA FOLLOW UP VISIT NOTE ON {payload.dateOfEvaluation}", transcribed_path, f"TRANSCRIBED DATA FOLLOW UP VISIT NOTE ON {payload.dateOfEvaluation}")

        driver.quit()
        return {"message": "\u2705 Both RAW and Transcribed PDFs uploaded successfully"}

    except Exception as e:
        print("[ERROR] Upload failed:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)