import uvicorn
from backend import app_archive  # import FastAPI app from your package

if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=5000, reload=True)
