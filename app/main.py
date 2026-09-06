from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import Base, engine

from app.modules.users.router import router as users_router
from app.modules.rag.router import router as rag_router
from app.modules.document.router import router as document_router

from app.core import db_models as user_models

from sqlalchemy import text

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
print(f"API documentation available at http://localhost:8000{settings.API_V1_STR}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("Starting up the application...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)
        conn.commit()

app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(rag_router, prefix=settings.API_V1_STR)
app.include_router(document_router, prefix=settings.API_V1_STR)

@app.get(f"/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": f"Welcome to {settings.PROJECT_NAME}"}
