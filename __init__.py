import uvicorn
from backend import app  # import FastAPI app from your package

if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
