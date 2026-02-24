from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    occupation_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    occupation_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    input_payload: Mapped[dict] = mapped_column(JSON)
    output_summary: Mapped[str] = mapped_column(Text)
    risk_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int | None] = mapped_column(ForeignKey("assessments.id"), nullable=True)
    version: Mapped[str] = mapped_column(String(16), default="v1")
    config: Mapped[dict] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ToolCatalog(Base):
    __tablename__ = "tools_catalog"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(512))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(64), default="apify")
    raw_payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ToolEmbedding(Base):
    __tablename__ = "tool_embeddings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools_catalog.id", ondelete="CASCADE"), unique=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    model: Mapped[str] = mapped_column(String(128))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OnetCache(Base):
    __tablename__ = "onet_cache"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    occupation_code: Mapped[str] = mapped_column(String(32), unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
