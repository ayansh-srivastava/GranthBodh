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

    def get_embedding(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.dimension,
            ),
        )

        embedding = response.embeddings[0].values

        if len(embedding) != self.dimension:
            raise ValueError(
                f"Expected {self.dimension} dimensions, "
                f"got {len(embedding)}"
            )

        return embedding

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
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

        response = loop.run_in_executor(None, batch_call)

        return [embedding.values for embedding in response.embeddings]

    def add_to_vector_store(self, text: str, doc_id: str, user_id: str):
        print(f"Adding document with ID {doc_id} to vector store...", user_id)
        embedding = self.get_embedding(text)
        print(f"Embedding for document ID {doc_id}: {embedding}")

rag_service = RAGService()
