import logging
import traceback

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.models.schemas import ConversionRequest
from app.services.conversion.conversion import ConversionFile

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/convert", status_code=202)
async def convert_file(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    logger: logging.Logger = Depends(lambda: logging.getLogger(__name__)),
):
    try:
        logger.info(f"Received conversion request for document ID: {request.docId}")

        background_tasks.add_task(run_conversion_task, request)

        logger.info("Scheduled background task for file conversion.")
        return {
            "message": "File conversion has been accepted and is processing.",
            "docId": request.docId,
        }
    except Exception as e:
        logger.error(
            f"Error scheduling background task: {str(e)}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Error starting file conversion.")


async def run_conversion_task(request: ConversionRequest):
    try:
        logger.info(
            f"Starting background conversion task for document ID: {request.docId}"
        )
        conversion = ConversionFile()
        await conversion.process_file(request)
        logger.info(f"Completed file conversion for document ID: {request.docId}")
    except Exception as e:
        logger.error(
            (
                f"Error in conversion task for document ID: {request.docId}:"
                f"{str(e)}\n{traceback.format_exc()}"
            )
        )
