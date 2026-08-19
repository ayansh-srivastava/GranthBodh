import uuid6
from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Integer, Index, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)

    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    created_at = Column( DateTime(timezone=True), server_default=func.now(), nullable=False )

    title = Column(String(255), nullable=False)
    source = Column(String(1023))
    description = Column(String(511))
    metadata_ = Column("metadata", JSON)

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete"
    )

    __table_args__ = (
        Index("idx_documents_user", "user_id"),
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    content = Column(Text, nullable=False)

    embedding = Column(Vector(768))

    chunk_index = Column(Integer)
    section = Column(String(255))
    metadata_ = Column("metadata", JSON)

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index(
            "idx_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),

        Index("idx_chunks_user", "user_id"),
        Index("idx_chunks_doc", "document_id"),
    )
