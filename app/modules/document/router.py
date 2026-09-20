from fastapi import Depends, APIRouter, HTTPException, status, File, UploadFile

from app.core.deps import get_current_user
from app.core.db import get_db


from app.modules.document.schemas import DocumentUploadResponse, GetDocumentsResponse
from app.modules.document.service import document_service


router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post( "/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), user: str = Depends(get_current_user), session=Depends(get_db)):
    return await document_service.upload_document(file, user, session)

@router.get("", response_model=GetDocumentsResponse, status_code=status.HTTP_200_OK)
async def get_documents(page: int, user: str = Depends(get_current_user), session=Depends(get_db)):
    return await document_service.get_documents(page, user, session)

@router.post("/delete/{document_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_document(document_id: str, user: str = Depends(get_current_user), session=Depends(get_db)):
    return await document_service.delete_document(document_id, user, session)
