import asyncio
import logging
import os
import re
from datetime import timedelta
from functools import partial

from docx2pdf import convert
from fastapi import HTTPException

from app.core.firebase import bucket, db, firestore
from app.models.schemas import ConversionRequest

logger = logging.getLogger(__name__)


class ConversionService:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.downloads_dir = os.path.join(self.base_dir, "downloads")
        self.converted_dir = os.path.join(self.base_dir, "converted")

        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.converted_dir, exist_ok=True)

    async def download_file(self, file_name, file_path, local_doc_path, doc_id):
        try:
            logger.info(
                f"Downloading file '{file_name}'",
                f"from cloud storage to '{local_doc_path}'",
            )
            blob = bucket.blob(file_path)
            if not blob.exists():
                error_message = f"File '{file_name}' not found in cloud storage."
                logger.error(error_message)
                await self.update_status(doc_id, "error", errorMessage=error_message)
                raise HTTPException(status_code=404, detail=error_message)

            blob.download_to_filename(local_doc_path)
            logger.info(
                f"File '{file_name}' downloaded successfully to '{local_doc_path}'"
            )
        except Exception as e:
            logger.error(f"Error downloading file '{file_name}': {str(e)}")
            await self.update_status(doc_id, "error", errorMessage=str(e))
            raise HTTPException(
                status_code=500, detail=f"Failed to download file '{file_name}'"
            )

    async def convert_to_pdf(self, file_name, doc_id, local_doc_path, local_pdf_path):
        try:
            logger.info(f"Converting '{local_doc_path}' to PDF at '{local_pdf_path}'")
            convert(local_doc_path, local_pdf_path)
            logger.info(f"File converted successfully to '{local_pdf_path}'")
        except Exception as e:
            logger.error(f"Error converting file '{file_name}' to PDF: {str(e)}")
            await self.update_status(doc_id, "error", errorMessage=str(e))
            raise HTTPException(
                status_code=500, detail=f"Failed to convert file '{file_name}' to PDF"
            )

    async def upload_to_storage(self, doc_id, local_pdf_name, local_pdf_path):
        try:
            pdf_blob = bucket.blob(f"converted-files/{local_pdf_name}")
            logger.info(
                f"Uploading converted PDF to cloud storage at '{pdf_blob.name}'"
            )
            pdf_blob.upload_from_filename(local_pdf_path)
            logger.info(
                "Converted PDF uploaded successfully to cloud storage:",
                f"'{pdf_blob.name}'",
            )
            return pdf_blob
        except Exception as e:
            logger.error(f"Error uploading converted PDF '{local_pdf_name}': {str(e)}")
            await self.update_status(doc_id, "error", errorMessage=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload converted file '{local_pdf_name}'",
            )

    async def generate_signed_url(self, blob, expiration=timedelta(minutes=5)):
        loop = asyncio.get_running_loop()
        url = await loop.run_in_executor(
            None,
            partial(
                blob.generate_signed_url,
                version="v4",
                expiration=expiration,
                method="GET",
            ),
        )
        return url

    async def update_status(self, doc_id, status, errorMessage=None, pdfUrl=None):
        try:
            update_data = {
                "status": status,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
            if errorMessage:
                update_data["errorMessage"] = errorMessage
            if pdfUrl:
                update_data["pdfUrl"] = pdfUrl

            await db.collection("conversions").document(doc_id).update(update_data)
            logger.info(
                f"Firestore document '{doc_id}' updated with status: '{status}'"
            )
        except Exception as e:
            logger.error(
                f"Failed to update Firestore status for doc ID '{doc_id}': {str(e)}"
            )

    def cleanup_files(self, *file_paths):
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted temporary file: '{file_path}'")
                except Exception as e:
                    logger.warning(f"Failed to delete file '{file_path}': {str(e)}")

    async def process_conversion(self, request: ConversionRequest):
        doc_id = request.docId
        file_name = os.path.basename(request.fileName)
        file_path = re.sub(r"^gs://[^/]+/", "", request.filePath)

        logger.info(f"Received conversion request for doc ID: {doc_id}")

        local_doc_path = os.path.join(self.downloads_dir, os.path.basename(file_name))
        local_pdf_name = f"{os.path.splitext(file_name)[0]}.pdf"
        local_pdf_path = os.path.join(self.converted_dir, local_pdf_name)

        await self.download_file(file_name, file_path, local_doc_path, doc_id)
        await self.convert_to_pdf(file_name, doc_id, local_doc_path, local_pdf_path)
        pdf_blob = await self.upload_to_storage(doc_id, local_pdf_name, local_pdf_path)

        try:
            pdf_url = await self.generate_signed_url(pdf_blob)
            logger.info(f"Generated signed URL for PDF: {pdf_url}")
            await self.update_status(doc_id, "completed", pdfUrl=pdf_url)
            logger.info(f"Conversion completed successfully for document ID: {doc_id}")
        except Exception as e:
            logger.error(
                "Error generating signed URL or updating Firestore for doc ID ",
                f"'{doc_id}': {str(e)}",
            )
            await self.update_status(doc_id, "error", errorMessage=str(e))
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to complete the conversion process for doc ID ",
                    f"'{doc_id}'",
                ),
            )
        finally:
            self.cleanup_files(local_doc_path, local_pdf_path)
