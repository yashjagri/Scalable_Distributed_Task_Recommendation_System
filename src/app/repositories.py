"""
Repository layer that encapsulates database access. Repositories accept a SQLAlchemy
Session and return/consume domain dataclasses so business logic stays decoupled from ORM.

Methods implemented:
- UserRepository.create
- ItemRepository.create / get
- EventRepository.append / delete_older_than
- RecommendationRepository.upsert_many_for_user / get_top_n_for_user

Note: transactional control is left to callers/tests; methods will commit where it makes
sense for simplicity in this MVP.
"""
from typing import Optional, List
from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import delete, insert, select, text

from .models_db import UserORM, ItemORM, EventORM, RecommendationORM
from .models_domain import User, Item, Event, Recommendation
from .mappings import (
    orm_user_to_domain,
    domain_user_to_orm,
    orm_item_to_domain,
    domain_item_to_orm,
    domain_event_to_orm,
    orm_recommendation_to_domain,
    domain_recommendation_to_orm,
)


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, user: User) -> User:
        """Create a new user and return the populated domain object (including generated id).

        Commits the transaction for simplicity in this MVP.
        """
        orm = domain_user_to_orm(user)
        self.session.add(orm)
        self.session.commit()
        # Refresh to pull DB-generated defaults (id, created_at)
        self.session.refresh(orm)
        return orm_user_to_domain(orm)

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        orm = self.session.get(UserORM, user_id)
        return orm_user_to_domain(orm) if orm is not None else None


class ItemRepository:
    """Repository for item CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, item: Item) -> Item:
        orm = domain_item_to_orm(item)
        self.session.add(orm)
        self.session.commit()
        self.session.refresh(orm)
        return orm_item_to_domain(orm)

    def get_by_id(self, item_id: UUID) -> Optional[Item]:
        orm = self.session.get(ItemORM, item_id)
        return orm_item_to_domain(orm) if orm is not None else None


class EventRepository:
    """Repository for append-only events and retention/deletion operations."""

    def __init__(self, session: Session):
        self.session = session

    def append(self, event: Event) -> Event:
        """Append a new event. Commits and returns the persisted event with DB-generated fields."""
        orm = domain_event_to_orm(event)
        self.session.add(orm)
        self.session.commit()
        self.session.refresh(orm)
        # Map back to domain if caller needs it
        return Event(
            id=orm.id,
            user_id=orm.user_id,
            item_id=orm.item_id,
            event_type=orm.event_type,
            value=orm.value,
            created_at=orm.created_at,
        )

    def delete_older_than(self, *, days: int) -> int:
        """Delete events older than the specified number of days.

        Executes a single DELETE statement against the events table and returns
        the number of deleted rows.
        """
        # Use raw SQL to express interval arithmetic in Postgres-friendly way.
        # We use SQLAlchemy text() to run a parametrized statement.
        sql = text("DELETE FROM events WHERE created_at < now() - (:days || ' days')::interval")
        result = self.session.execute(sql, {"days": str(days)})
        # Commit the deletion
        self.session.commit()
        # result.rowcount may be available depending on the DB driver
        return result.rowcount if result is not None else 0


class RecommendationRepository:
    """Repository to upsert and query per-user precomputed recommendations."""

    def __init__(self, session: Session):
        self.session = session

    def upsert_many_for_user(self, user_id: UUID, recommendations: List[Recommendation]) -> None:
        """
        Upsert (replace) the set of recommendations for a given user.

        Simpler approach used for MVP: delete existing recommendations for the user
        and bulk insert the provided recommendations. This avoids dialect-specific
        ON CONFLICT logic and is acceptable for small-to-medium batch sizes.
        """
        # Delete existing recommendations for the user
        self.session.execute(delete(RecommendationORM).where(RecommendationORM.user_id == user_id))

        # Prepare ORM objects for bulk save
        orm_objs = [domain_recommendation_to_orm(r) for r in recommendations]
        # Use bulk_save_objects for faster inserts; commit after.
        if orm_objs:
            self.session.bulk_save_objects(orm_objs)
        self.session.commit()

    def get_top_n_for_user(self, user_id: UUID, n: int) -> List[Recommendation]:
        """Return top-N recommendations for a given user ordered by score DESC.

        The recommendations table has an index on (user_id, score DESC) to support
        this query pattern efficiently.
        """
        stmt = select(RecommendationORM).where(RecommendationORM.user_id == user_id).order_by(RecommendationORM.score.desc()).limit(n)
        rows = self.session.execute(stmt).scalars().all()
        return [orm_recommendation_to_domain(r) for r in rows]
