from fastapi import Depends, APIRouter, HTTPException, status, File, UploadFile

from app.core.deps import get_current_user
from app.core.db import get_db


from app.modules.document.schemas import DocumentUploadResponse
from app.modules.document.service import document_service


router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post( "/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), user: str = Depends(get_current_user), session=Depends(get_db)):
    return await document_service.upload_document(file, user, session)
