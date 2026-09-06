from pydantic import BaseModel
from typing import List, Any, Dict

class EmbedRequest(BaseModel):
    text: str
    document_id: str

class EmbedResponse(BaseModel):
    status: str
    message: str

class QueryRequest(BaseModel):
    question: str
    conversation_id: str = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    conversation_id: str

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    message: str

class ConversationItem(BaseModel):
    id: str
    title: str
    created_at: str

class MessageItem(BaseModel):
    id: str
    created_at: str
    conversation_id: str
    user_id: str

    role: str
    content: str