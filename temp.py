from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from docxtpl import DocxTemplate
import io
import os
import uvicorn

app = FastAPI()


from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}


# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def generate_docx_from_data(data: dict) -> io.BytesIO:
    try:
        # Provide default empty list if missing
        if 'docSections' not in data:
            data['docSections'] = []

        template_path = os.path.join('templates', 'FU_TEMPLATE_Klickovich.docx')
        if not os.path.exists(template_path):
            raise HTTPException(status_code=500, detail="Template file not found.")
        doc = DocxTemplate(template_path)
        doc.render(data)
        byte_io = io.BytesIO()
        doc.save(byte_io)
        byte_io.seek(0)
        return byte_io
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating DOCX: {str(e)}")

# @app.post("/generate-doc")
# async def generate_doc(request: Request):
#     data = await request.json()
#     print("Data received for DOCX generation:", data)
#     file_stream = generate_docx_from_data(data)
#     file_name = data.get("fileName") or data.get("patientName", "follow_up_visit")
#     headers = {
#         'Content-Disposition': f'attachment; filename="{file_name}.docx"'
#     }
#     return StreamingResponse(
#         file_stream,
#         media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
#         headers=headers
#     )

@app.post("/generate-doc")
async def generate_doc(request: Request):
    data = await request.json()
    print("Data received for DOCX generation:", data)

    # 🔍 Log fileName and patientName
    print("Received fileName:", data.get("fileName"))
    print("Received patientName:", data.get("patientName"))

    file_stream = generate_docx_from_data(data)

    file_name = data.get("fileName") or data.get("patientName", "follow_up")

    print("Final filename used:", file_name)

    headers = {
        # 'Content-Disposition': f'attachment; filename="TEST_FILENAME.docx"'
        'Content-Disposition': f'attachment; filename="{file_name}.docx"'
    }

    return StreamingResponse(
        file_stream,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers=headers
    )

# Print backend URL on startup
if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    print(f"Starting FastAPI server at http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
