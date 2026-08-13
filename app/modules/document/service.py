from uuid import uuid4

from fastapi import UploadFile, HTTPException

from app.modules.document.constants import ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES
from app.modules.document.schemas import DocumentUploadResponse
from app.modules.document.parser import DocumentParser


class DocumentService:

    async def upload_document( self, file: UploadFile, user: str ) -> DocumentUploadResponse:

        if not file.filename:
            raise HTTPException( status_code=400, detail="Filename is required")

        filename = file.filename.lower()
        extension = "." + filename.split(".")[-1]

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException( status_code=400, detail="Only PDF, DOCX and XLSX files are supported")

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException( status_code=400, detail="Invalid document content type")

        document_id = str(uuid4())

        file_bytes = await file.read()

        try:
            text = DocumentParser.parse( filename=file.filename, file_bytes=file_bytes)
        except Exception as exc:
            raise HTTPException( status_code=400, detail=f"Failed to parse document: {str(exc)}")

        if not text.strip():
            raise HTTPException( status_code=400, detail="Could not extract any text from the document")

        document_id = str(uuid4())

        # TODO:
        # Save document
        # Chunk text
        # Generate embeddings
        # Store embeddings in pgvector

        print(text)

        return DocumentUploadResponse(
            id=document_id,
            filename=file.filename,
            content_type=file.content_type,
            message="Document uploaded and parsed successfully",
        )

document_service = DocumentService()
