from fastapi import FastAPI

from app.api.routes import router
from app.core.logging_config import setup_logging

app: FastAPI = FastAPI(title="File Conversion Server", version="0.1.0")


@app.get("/health_check")
async def root():
    return {"message": "Hello World"}


app.include_router(router)

setup_logging()
