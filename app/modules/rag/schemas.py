from pydantic import BaseModel
from typing import List, Any, Dict

class EmbedRequest(BaseModel):
    text: str
    document_id: str

class EmbedResponse(BaseModel):
    status: str
    message: str

class MessageItem(BaseModel):
    id: str
    created_at: str
    conversation_id: str
    user_id: str

    role: str
    content: str
    rewritten_content: str = None

class QueryRequest(BaseModel):
    question: str
    conversation_id: str|None = None

class QueryResponse(BaseModel):
    answer: MessageItem
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

class GetConversationsResponse(BaseModel):
    conversations: List[ConversationItem]
    total_pages: int

class GetMessageResaponse(BaseModel):
    messages: List[MessageItem]
    total_pages: int
