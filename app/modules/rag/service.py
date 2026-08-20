from app.core.config import settings

from google import genai
from google.genai import types
from typing import List
import asyncio
from sqlalchemy import select

from app.core.config import settings
from app.modules.users.models import Chunk

class RAGService:
    def __init__(self, model: str = "gemini-embedding-001"):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.model = model
        self.dimension = 768

    async def get_embedding(self, text: str) -> List[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=[text],
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.dimension,
            ),
        )
        return response.embeddings[0].values

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

    def add_to_vector_store(self, text: str, doc_id: str, user_id: str):
        print(f"Adding document with ID {doc_id} to vector store...", user_id)
        embedding = self.get_embedding(text)
        print(f"Embedding for document ID {doc_id}: {embedding}")

    async def retrieve_chunks( self, session, query: str, top_k: int = 5 ):

        query_embedding = await self.get_embedding(query)

        if len(query_embedding) != 768:
            raise ValueError(f"Expected 768 dimensions, got {len(query_embedding)}")

        distance = Chunk.embedding.cosine_distance(query_embedding)

        db_query = (
            select(
                Chunk,
                distance.label("distance"),
            )
            .order_by(distance)
            .limit(top_k)
        )

        result = session.execute(db_query)

        chunks = []

        for chunk, distance_value in result.all():
            chunks.append({
                "text": chunk.content,
                "metadata": chunk.metadata_,
                "similarity": 1 - float(distance_value),
            })

        return chunks

    async def generate_rag_response(self, prompt: str, chunks: list[dict]):
        response = await self.client.aio.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.2,
                top_p=0.8,
                stop_sequences=["\n\n"],
            ),
        )

        answer = response.text.strip() if response.text else ""
        print(f"Generated answer: {answer}")

        sources = [chunk["metadata"] for chunk in chunks]

        return {
            "answer": answer,
            "sources": sources,
        }

    async def answer_question(self, session, question: str, user_id: str) -> dict:
        chunks = await self.retrieve_chunks(session=session, query=question, top_k=5)

        if not chunks:
            return {
                "answer": "I don't know.",
                "sources": [],
            }

        context = "\n---\n".join([f"Content: {chunk['text']}" for chunk in chunks])

        prompt = f"""You are an AI assistant answering questions strictly based on the context below.

            Context:
            {context}

            Question: {question}

            Instructions:
            1. Provide a concise answer based ONLY on the context above.
            2. If the answer is not in the context, reply strictly with "I don't know."
            3. Do not assume or invent facts outside the context.
            4. Answer as short as possible, ideally in one or two sentences.
        """

        return await self.generate_rag_response(prompt=prompt, chunks=chunks)


rag_service = RAGService()
