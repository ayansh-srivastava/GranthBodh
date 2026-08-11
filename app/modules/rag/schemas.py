from pydantic import BaseModel
from typing import List

class EmbedRequest(BaseModel):
    text: str
    document_id: str

class EmbedResponse(BaseModel):
    status: str
    message: str

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    message: str
