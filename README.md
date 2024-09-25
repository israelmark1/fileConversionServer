# Word to PDF Conversion Service

A Python service using FastAPI to convert Word documents to PDF.

## Features

- Receives conversion requests via HTTP.
- Downloads Word documents from Firebase Storage.
- Converts documents to PDF.
- Uploads PDFs to Firebase Storage.
- Updates Firestore with conversion status.

## Technologies

- FastAPI
- Firebase Admin SDK
- docx2pdf

