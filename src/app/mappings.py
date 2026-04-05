"""
Mapping utilities converting between domain dataclasses and ORM objects.
Keeping mapping centralized avoids sprinkling ORM logic across business code.
"""
from typing import Optional, List
from uuid import UUID

from .models_domain import User, Item, Event, Recommendation
from .models_db import UserORM, ItemORM, EventORM, RecommendationORM


# User mappings
def orm_user_to_domain(orm: UserORM) -> User:
    """Convert UserORM to domain User dataclass."""
    return User(id=orm.id, email=orm.email, created_at=orm.created_at)


def domain_user_to_orm(domain: User) -> UserORM:
    """Create a UserORM from a domain User. This does not add it to a session."""
    return UserORM(id=domain.id, email=domain.email, created_at=domain.created_at)


# Item mappings
def orm_item_to_domain(orm: ItemORM) -> Item:
    return Item(id=orm.id, metadata=orm.metadata or {}, created_at=orm.created_at)


def domain_item_to_orm(domain: Item) -> ItemORM:
    return ItemORM(id=domain.id, metadata=domain.metadata or {}, created_at=domain.created_at)


# Event mappings
def orm_event_to_domain(orm: EventORM) -> Event:
    return Event(
        id=orm.id,
        user_id=orm.user_id,
        item_id=orm.item_id,
        event_type=orm.event_type,
        value=orm.value,
        created_at=orm.created_at,
    )


def domain_event_to_orm(domain: Event) -> EventORM:
    return EventORM(
        id=domain.id,
        user_id=domain.user_id,
        item_id=domain.item_id,
        event_type=domain.event_type,
        value=domain.value,
        created_at=domain.created_at,
    )


# Recommendation mappings
def orm_recommendation_to_domain(orm: RecommendationORM) -> Recommendation:
    return Recommendation(user_id=orm.user_id, item_id=orm.item_id, score=orm.score, updated_at=orm.updated_at)


def domain_recommendation_to_orm(domain: Recommendation) -> RecommendationORM:
    return RecommendationORM(user_id=domain.user_id, item_id=domain.item_id, score=domain.score, updated_at=domain.updated_at)
