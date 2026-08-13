from pydantic import BaseModel

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    message: str
