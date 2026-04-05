"""
SQLAlchemy ORM models mapping to the Postgres schema defined in schema/schema.sql.
We use Postgres-specific column types (UUID, JSONB) to match the schema exactly.
"""
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func

# Declarative base for ORM models. Using a local Base allows tests to run metadata.create_all.
Base = declarative_base()


class UserORM(Base):
    """ORM mapping for users table."""
    __tablename__ = "users"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class ItemORM(Base):
    """ORM mapping for items table."""
    __tablename__ = "items"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    metadata = Column(JSONB, nullable=False, server_default='{}')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class EventORM(Base):
    """ORM mapping for events table."""
    __tablename__ = "events"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(PG_UUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(Text, nullable=False)
    value = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class RecommendationORM(Base):
    """ORM mapping for recommendations table.

    Note: composite primary key (user_id, item_id) enforced via primary_key=True on both columns.
    An index on (user_id, score DESC) is created in schema.sql for fast top-N retrieval.
    """
    __tablename__ = "recommendations"
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    item_id = Column(PG_UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    score = Column(Float, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # SQLAlchemy/ORM-side uniqueness is covered by the primary key; index is present in raw SQL schema.
