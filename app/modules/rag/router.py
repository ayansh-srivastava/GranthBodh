import traceback

from fastapi import Depends, APIRouter, HTTPException, status
from app.modules.rag.schemas import EmbedRequest, EmbedResponse, QueryRequest, QueryResponse
from app.modules.rag.service import rag_service
from app.core.deps import get_current_user
from app.core.db import get_db

router = APIRouter(prefix="/rag", tags=["RAG Backend"])
# @router.post("/embed", response_model=EmbedResponse, status_code=status.HTTP_201_CREATED)
# def embed_document(payload: EmbedRequest, user: str = Depends(get_current_user)):
#     try:
#         print(f"Received request to embed document with ID {payload.document_id} and text: {payload.text}")
#         # rag_service.add_to_vector_store(text=payload.text, doc_id=payload.document_id, user_id=user)
#         return EmbedResponse(status="success", message="Text successfully embedded and indexed.")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to index text: {str(e)}")

@router.post("/getAnswer", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def get_answer(payload: QueryRequest, user: str = Depends(get_current_user), session=Depends(get_db)):
    try:
        result = await rag_service.answer_question(session=session, question=payload.question, user_id=user)
        return QueryResponse(answer=result["answer"], sources=result["sources"])
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")