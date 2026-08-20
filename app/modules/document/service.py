from uuid import uuid4

from fastapi import UploadFile, HTTPException

from app.modules.document.constants import ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES
from app.modules.document.chunker import TokenAwareChunker
from app.modules.document.schemas import DocumentUploadResponse
from app.modules.document.document_parser import DocumentParser
from app.modules.document.data_model import DocumentBlock
from app.modules.users.models import Document, Chunk
from app.modules.rag.service import rag_service


class DocumentService:

    @classmethod
    async def embed_chunks(cls, chunked_blocks: list[DocumentBlock]) -> list[dict]:
        embeddings = await rag_service.get_embeddings([block.text for block in chunked_blocks])
        return [
            {
                "text": block.text,
                "embedding": embedding,
                "metadata": block.metadata,
            }
            for block, embedding in zip(chunked_blocks, embeddings)
        ]

    @classmethod
    async def save_chunks_to_db(cls, session, embeddings: list[dict], document_id: str, user_id: str):
        chunks = [
            Chunk(
                document_id=document_id,
                user_id=user_id,
                content=item["text"],
                embedding=item["embedding"],
                chunk_index=index,
                metadata_=item["metadata"],
                section="",
            )
            for index, item in enumerate(embeddings)
        ]
        session.add_all(chunks)

    @classmethod
    async def upload_document(cls, file: UploadFile, user: str, session) -> DocumentUploadResponse:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        filename = file.filename.lower()
        extension = "." + filename.split(".")[-1] if "." in filename else ""

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only PDF, DOCX and XLSX files are supported")

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="Invalid document content type")

        try:
            new_document = Document(
                user_id=user,
                title=file.filename,
                source="upload",
                description="Uploaded document",
                metadata_={},
            )
            session.add(new_document)
            session.flush()

            file_bytes = await file.read()
            chunked_blocks = DocumentParser.parse(
                filename=file.filename,
                file_bytes=file_bytes,
                doc_id=str(new_document.id),
                chunker=TokenAwareChunker(),
            )

            if not chunked_blocks:
                raise HTTPException(status_code=400, detail="Could not extract any text from the document")

            embeddings = await cls.embed_chunks(chunked_blocks)
            await cls.save_chunks_to_db(session, embeddings, str(new_document.id), user)

            session.commit()
            return DocumentUploadResponse(
                id=str(new_document.id),
                filename=file.filename,
                content_type=file.content_type,
                message="Document uploaded and parsed successfully",
            )

        except HTTPException:
            session.rollback()
            raise
        except Exception as exc:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to process document: {str(exc)}")


document_service = DocumentService()
