from fastapi import FastAPI
from app.core.config import settings
from app.core.db import Base, engine

from app.modules.users.router import router as users_router
from app.modules.rag.router import router as rag_router
from app.modules.users import models as user_models

from sqlalchemy import text

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
print(f"API documentation available at http://localhost:8000{settings.API_V1_STR}/openapi.json")

@app.on_event("startup")
async def startup_event():
    print("Starting up the application...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)
        conn.commit()

app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(rag_router, prefix=settings.API_V1_STR)

@app.get(f"/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": f"Welcome to {settings.PROJECT_NAME}"}
