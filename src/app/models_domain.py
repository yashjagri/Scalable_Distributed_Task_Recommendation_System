"""
Domain dataclasses representing pure business objects used across services.
They contain no ORM imports so domain logic can be tested in isolation.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class User:
    """Domain model for a user."""
    id: Optional[UUID]
    email: str
    created_at: Optional[datetime] = None


@dataclass
class Item:
    """Domain model for an item. Metadata is flexible JSON-like dict."""
    id: Optional[UUID]
    metadata: Dict[str, Any]
    created_at: Optional[datetime] = None


@dataclass
class Event:
    """Domain model for an append-only event.

    value is arbitrary JSON-like payload (nullable).
    item_id is optional to support events not tied to a specific item.
    """
    id: Optional[UUID]
    user_id: UUID
    item_id: Optional[UUID]
    event_type: str
    value: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class Recommendation:
    """Domain model for precomputed per-user recommendation scores."""
    user_id: UUID
    item_id: UUID
    score: float
    updated_at: Optional[datetime] = None
