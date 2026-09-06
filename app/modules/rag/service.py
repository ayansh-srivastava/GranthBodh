from app.core.config import settings

from google import genai
from google.genai import types
from typing import List
import asyncio
from sqlalchemy import select

from app.core.config import settings
from app.core.db_models import Chunk, Message, Conversation
from app.modules.rag.schemas import QueryRequest

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
        # print(f"Adding document with ID {doc_id} to vector store...", user_id)
        embedding = self.get_embedding(text)
        # print(f"Embedding for document ID {doc_id}: {embedding}")

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

    async def save_message(self, session, conversation_id: str, role: str, content: str, rewritten_content: str | None = None):
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            rewritten_content=rewritten_content,
        )

        session.add(message)
        session.flush()

    async def rewrite_query(
        self,
        question: str,
        history: list[dict],
    ) -> str:

        if not history:
            return question

        conversation = "\n".join(
            f"{message['role']}: {message['rewritten_content'] if message.get('rewritten_content') else message['content']}"
            for message in history
        )

        prompt = f"""
            You are a search query rewriting assistant.

            Given the conversation history and the latest user question,
            rewrite the latest question into a standalone search query.

            Rules:
            1. Resolve pronouns and references using the conversation history.
            2. Preserve important entities, products, models, names, etc.
            3. Do not answer the question.
            4. Do not add information that isn't present in the conversation.
            5. If the question is already standalone, return it unchanged.
            6. Return ONLY the rewritten search query.

            Conversation:
            {conversation}

            Latest question:
            {question}

            Standalone search query:
        """

        response = await self.client.aio.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=400,
            ),
        )

        return response.text.strip() if response.text else question

    async def generate_rag_response(self, conversation_id: str, prompt: str, chunks: list[dict], history: list[dict] = []) -> dict:
        contents = []

        for message in history:
            contents.append(
                types.Content(
                    role=message["role"],
                    parts=[types.Part(text=message["content"])],
                    rewritten_content=message.get("rewritten_content", None),
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )
        )

        response = await self.client.aio.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.5,
                top_p=0.8,
                stop_sequences=["\n\n"],
            ),
        )

        answer = response.text.strip() if response.text else ""
        # print(f"Generated answer: {answer}")
        sources = [chunk["metadata"] for chunk in chunks]

        return {
            "answer": answer,
            "sources": sources,
            "conversation_id": conversation_id,
        }

    async def get_conversation_history(self, session, conversation_id: str, user_id: str) -> list[dict]:
        messages = (
            session.query(Message)
            .filter_by(conversation_id=conversation_id, user_id=user_id)
            .order_by(Message.timestamp.asc())
            .limit(5)
        )

        history = [
            {"role": message.role, "content": message.content, "rewritten_content": message.rewritten_content if message.rewritten_content else None}
            for message in messages
        ]

        return history

    async def answer_question(self, session, payload: QueryRequest, user_id: str) -> dict:

        history = []
        conversation_id = None
        if payload.conversation_id:
            conversation_id = payload.conversation_id
            history = await self.get_conversation_history(session=session, conversation_id=payload.conversation_id, user_id=user_id)
        else:
            save_conversation = Conversation(
                user_id=user_id,
                title=payload.question[:30] + ("..." if len(payload.question) > 30 else "")
            )
            session.add(save_conversation)
            session.flush()
            conversation_id = str(save_conversation.id)

        question = await self.rewrite_query(question=payload.question, history=history)



        chunks = await self.retrieve_chunks(session=session, query=question, top_k=5)

        if not chunks:
            return {
                "answer": "I don't know. Please upload relevant documents or provide more context.",
                "sources": [],
                "conversation_id": conversation_id,
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
            4. Answer as short as possible, ideally in one or two sentences not more than one paragraph.
        """
        res = await self.generate_rag_response(conversation_id=conversation_id, prompt=prompt, chunks=chunks, history=history)
        await self.save_message(session=session, conversation_id=conversation_id, role="user", content=payload.question, rewritten_content=question)
        await self.save_message(session=session, conversation_id=conversation_id, role="assistant", content=res["answer"])
        return res

    async def get_conversations(self, page, session, user_id: str) -> list[dict]:
        conversations = (
            session.query(Conversation)
            .filter_by(user_id=user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(20)
            .offset((page-1) * 20)
        )

        return [
            {
                "id": str(conversation.id),
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
            }
            for conversation in conversations
        ]

    async def get_messages(self, session, conversation_id: str, page: int, user_id: str) -> list[dict]:
        messages = (
            session.query(Message)
            .filter_by(conversation_id=conversation_id, user_id=user_id)
            .order_by(Message.timestamp.asc())
            .limit(20)
            .offset((page - 1) * 20)
        )

        return [
            {
                "id": str(message.id),
                "created_at": message.timestamp.isoformat(),
                "conversation_id": str(message.conversation_id),
                "user_id": str(message.user_id),
                "role": message.role,
                "content": message.content,
                "rewritten_content": message.rewritten_content if message.rewritten_content else None,
            }
            for message in messages
        ]

rag_service = RAGService()
