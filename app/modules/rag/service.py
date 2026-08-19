from app.core.config import settings

from google import genai
from google.genai import types
from typing import List
import asyncio

from app.core.config import settings


class RAGService:
    def __init__(self, model: str = "gemini-embedding-001"):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.model = model
        self.dimension = 768

    async def get_embeddings(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            response = await asyncio.to_thread(
                self.client.models.embed_content,
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=self.dimension,
                ),
            )
            all_embeddings.extend([embedding.values for embedding in response.embeddings])

        return all_embeddings

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()

        def batch_call():
            return self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.dimension,
            ),
        )

        response = await loop.run_in_executor(None, batch_call)

        return [embedding.values for embedding in response.embeddings]

    def add_to_vector_store(self, text: str, doc_id: str, user_id: str):
        print(f"Adding document with ID {doc_id} to vector store...", user_id)
        embedding = self.get_embedding(text)
        print(f"Embedding for document ID {doc_id}: {embedding}")

rag_service = RAGService()
