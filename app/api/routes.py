from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

from app.core.config import settings
from app.models.schemas import ConversionRequest
from app.services.conversion import process_conversion

router = APIRouter()


@router.post("/convert")
async def convert_file(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
):
    if authorization != f"Bearer ${settings.API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        background_tasks.add_task(process_conversion, request)
        return {"message": "File conversion started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
