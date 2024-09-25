# conversion.py
import os
from datetime import timedelta

from docx2pdf import convert

from app.core.firebase import bucket, db, firestore


def process_conversion(doc_id, filename, file_path):
    try:
        blob = bucket.blob(file_path)
        local_doc_path = f"/tmp/download/{filename}"
        blob.download_to_filename(local_doc_path)

        local_pdf_name = f"{os.path.splitext(filename)[0]}.pdf"
        local_pdf_path = f"/tmp/uploads/{local_pdf_name}"
        convert(local_doc_path, local_pdf_path)

        pdf_blob = bucket.blob(f"converted/{local_pdf_name}")
        pdf_blob.upload_from_filename(local_pdf_path)

        pdf_url = pdf_blob.generate_signed_url(
            version="v4", expiration=timedelta(hours=1), method="GET"
        )

        db.collection("conversions").document(doc_id).update(
            {
                "status": "completed",
                "pdfUrl": pdf_url,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )

        os.remove(local_doc_path)
        os.remove(local_pdf_path)

        print(f"Conversion completed for {filename}")

    except Exception as e:

        db.collection("conversions").document(doc_id).update(
            {
                "status": "error",
                "errorMessage": str(e),
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        print(f"Error processing docId: {doc_id}", e)
