from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="Basic FastAPI App")
BASE_DIR = Path(__file__).resolve().parent


@app.get("/")
async def read_root():
    return FileResponse(BASE_DIR / "test.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
