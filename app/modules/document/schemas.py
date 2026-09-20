from pydantic import BaseModel

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    message: str

class DocumentItem(BaseModel):
    id: str
    filename: str

class GetDocumentsResponse(BaseModel):
    documents: list[DocumentItem]
    total_count: int
