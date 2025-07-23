from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docxtpl import DocxTemplate
import io
import os
import json
import uvicorn
import traceback

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

# DOCX generation logic
def generate_docx_from_data(data: dict) -> io.BytesIO:
    try:
        if 'docSections' not in data:
            data['docSections'] = []

        if not os.path.exists(TEMPLATE_FILE):
            raise HTTPException(status_code=500, detail="Template file not found.")

        print("[INFO] Loading template:", TEMPLATE_FILE)
        doc = DocxTemplate(TEMPLATE_FILE)

        print("[INFO] Rendering data keys:", list(data.keys()))
        doc.render(data)

        byte_io = io.BytesIO()
        doc.save(byte_io)
        byte_io.seek(0)
        return byte_io
    except Exception as e:
        print("[ERROR] Failed to generate DOCX")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating DOCX: {str(e)}")

# Route: POST /generate-doc
@app.post("/generate-doc")
async def generate_doc(request: Request):
    data = await request.json()
    print("📥 Data received:", data)

    file_stream = generate_docx_from_data(data)
    file_name = data.get("fileName") or data.get("patientName", "follow_up")

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
