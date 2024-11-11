from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.schemas import ConversionRequest

# Mock Firebase initialization
with patch("firebase_admin.credentials.Certificate", return_value=MagicMock()), patch(
    "firebase_admin.initialize_app", MagicMock()
), patch("firebase_admin.firestore.client", return_value=MagicMock()), patch(
    "firebase_admin.storage.bucket", return_value=MagicMock()
):

    from fileConversionServer.app.services.conversion.conversion import (
        process_conversion,
    )


def test_process_conversion_success():
    mock_request = ConversionRequest(
        docId="doc123", fileName="test.docx", filePath="uploads/test.docx"
    )

    mock_blob = MagicMock()
    mock_blob.download_to_filename = MagicMock()
    mock_blob.upload_from_filename = MagicMock()
    mock_blob.generate_signed_url = MagicMock(return_value="https://example.com/pdf")

    mock_bucket = MagicMock()
    mock_bucket.blob = MagicMock(return_value=mock_blob)

    mock_db = MagicMock()
    mock_db.collection.return_value.document.return_value.update = MagicMock()

    with patch("app.services.conversion.bucket", mock_bucket), patch(
        "app.services.conversion.db", mock_db
    ), patch("app.services.conversion.convert", MagicMock()), patch(
        "os.remove", MagicMock()
    ):

        process_conversion(mock_request)

    mock_blob.download_to_filename.assert_called_once()
    mock_blob.upload_from_filename.assert_called_once()
    mock_db.collection.return_value.document.return_value.update.assert_called_with(
        {"status": "completed", "pdfUrl": "https://example.com/pdf", "updatedAt": ANY}
    )


def test_process_conversion_failure():

    mock_request = ConversionRequest(
        docId="doc123", fileName="test.docx", filePath="uploads/test.docx"
    )

    def mock_convert(*args, **kwargs):
        raise Exception("Conversion error")

    mock_blob = MagicMock()
    mock_blob.download_to_filename = MagicMock()
    mock_blob.upload_from_filename = MagicMock()
    mock_blob.generate_signed_url = MagicMock()

    mock_bucket = MagicMock()
    mock_bucket.blob = MagicMock(return_value=mock_blob)

    mock_db = MagicMock()
    mock_db.collection.return_value.document.return_value.update = MagicMock()

    with patch("app.services.conversion.bucket", mock_bucket), patch(
        "app.services.conversion.db", mock_db
    ), patch("app.services.conversion.convert", mock_convert), patch(
        "os.remove", MagicMock()
    ):
        with pytest.raises(HTTPException) as exc_info:
            process_conversion(mock_request)

        assert exc_info.value.status_code == 500
        assert "Failed to convert file 'test.docx' to PDF" in str(exc_info.value.detail)

    mock_db.collection.return_value.document.return_value.update.assert_called_with(
        {"status": "error", "errorMessage": "Conversion error", "updatedAt": ANY}
    )
