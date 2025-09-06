import os
import json
import io
import string
import sys
import traceback
import subprocess
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docxtpl import DocxTemplate
from docx2pdf import convert
from fastapi import UploadFile, File

# --- App Setup ---
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Constants & Directories ---
PHYSICIAN_FILE = "data/physicians.json"
TEMPLATE_FILE = "templates/FU_TEMPLATE_Klickovich.docx"

# User-specified path for PRC_FOLDER (can be changed directly)
PRC_FOLDER = "F:/PRC 2025/SEPT-2025/09-06-2025"  # Example path
PDF_FOLDER = os.path.join(PRC_FOLDER, "PDF")

# Ensure PDF folder exists
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("templates", exist_ok=True)

print(f"✅ PDF folder created at: {PDF_FOLDER}")

# --- Ensure Physicians File Exists ---
if not os.path.exists(PHYSICIAN_FILE):
    with open(PHYSICIAN_FILE, "w") as f:
        json.dump([], f)

# --- Load/Save Helpers ---
def load_physicians():
    with open(PHYSICIAN_FILE, "r") as f:
        return json.load(f)

def save_physicians(physicians):
    with open(PHYSICIAN_FILE, "w") as f:
        json.dump(physicians, f, indent=2)

# --- Model ---
class Physician(BaseModel):
    name: str

# --- Physician Routes ---
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

# --- Global Dictionary to Store fileName ---
file_name_storage = {}

# --- Generate DOCX and PDF ---
def generate_docx_from_data(data: dict) -> tuple[io.BytesIO, str, str]:
    try:
        print("➡️ Starting document generation...")

        if not os.path.exists(TEMPLATE_FILE):
            raise HTTPException(status_code=500, detail="Template file not found.")

        doc = DocxTemplate(TEMPLATE_FILE)
        data.setdefault('docSections', [])
        doc.render(data)

        file_name = data.get("fileName") or data.get("patientName", "follow_up")

        # Clear previous fileName value and store the new one
        file_name_storage.clear()  # Clear existing stored fileName
        file_name_storage["last_used"] = file_name  # Store the new fileName

        allowed_punctuation = "-_.,()[]"
        safe_file_name = "".join(c for c in file_name if c.isalnum() or c in string.whitespace or c in allowed_punctuation).strip()

        docx_path = os.path.join(PDF_FOLDER, f"{safe_file_name}.docx")
        pdf_path = os.path.join(PDF_FOLDER, f"{safe_file_name}.pdf")

        doc.save(docx_path)
        print(f"✅ DOCX saved: {docx_path}")

        try:
            convert(docx_path, pdf_path)
            print(f"✅ PDF converted: {pdf_path}")
        except Exception as e:
            print("⚠️ PDF conversion failed:", e)

        byte_io = io.BytesIO()
        with open(docx_path, "rb") as f:
            byte_io.write(f.read())
        byte_io.seek(0)

        return byte_io, pdf_path, data.get("dateOfEvaluation", "")

    except Exception as e:
        print("[❌ ERROR] Failed to generate DOCX/PDF")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating DOCX/PDF: {str(e)}")

# --- /generate-doc Endpoint ---
@app.post("/generate-doc")
async def generate_doc(request: Request):
    print("🔔 /generate-doc triggered")
    data = await request.json()
    print("📥 Data received:", data)

    # Generate DOCX and PDF
    file_stream, pdf_path, date_of_eval = generate_docx_from_data(data)
    file_name = data.get("fileName") or data.get("patientName", "follow_up")

    # Optional PDF upload
    if pdf_path and os.path.exists(pdf_path):
        try:
            title = f"TRANSCRIBED DATA FOLLOW UP VISIT NOTE ON {date_of_eval}"
            print(f"📤 Would upload PDF with title: {title}")
            # upload_pdf_to_portal(file_path=pdf_path, document_title=title, notes=title)
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

# --- /upload-documents Endpoint ---
class FileUploadRequest(BaseModel):
    fileName: str
    path: str   # "path1" or "path2"

@app.post("/upload-documents")
async def upload_documents(request: FileUploadRequest):
    try:
        file_name = request.fileName.strip()
        path_choice = request.path

        # Clear and store the new fileName for upload
        file_name_storage.clear()  # Clear existing stored fileName
        file_name_storage["last_uploaded"] = file_name  # Store the new fileName

        # Define paths
        path1 = os.path.join(PDF_FOLDER, "path1")
        path2 = os.path.join(PDF_FOLDER, "path2")

        # Ensure directories exist
        os.makedirs(path1, exist_ok=True)
        os.makedirs(path2, exist_ok=True)

        # Choose correct folder
        if path_choice == "path1":
            base_path = path1
        elif path_choice == "path2":
            base_path = path2
        else:
            raise HTTPException(status_code=400, detail=f"Invalid path: {path_choice}")

        file_path = os.path.join(base_path, file_name)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        print(f"📤 Triggering upload for file: {file_name} from {path_choice}")

        # Run selenium uploader with single path
        subprocess.Popen([sys.executable, "selenium_uploader.py", file_name, base_path])

        return {"message": f"Upload triggered for '{file_name}' from {path_choice}."}

    except HTTPException as e:
        print(f"❌ HTTP Error: {e.detail}")
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})

    except Exception as e:
        print(f"❌ Failed to start selenium_uploader.py: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- /last-file-name Endpoint (For debugging or use cases) ---
@app.get("/last-file-name")
def get_last_file_name():
    return {"last_used_file": file_name_storage.get("last_used"), "last_uploaded_file": file_name_storage.get("last_uploaded")}

# --- Health Check ---
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

# --- Dev Run ---
if __name__ == "__main__":
    print("🚀 Starting server at http://127.0.0.1:8000")
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
