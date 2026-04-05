"""
Pytest-based unit tests for repository layer. These tests require a reachable Postgres
instance pointed to by the DATABASE_URL environment variable.

They perform the following:
- Apply schema/schema.sql to ensure DB has expected structure (including indexes)
- Insert a user, items, recommendations
- Validate get_top_n_for_user returns top-N ordered by score desc
- Insert an event with an old created_at and verify delete_older_than(days) deletes it

Note: Ensure the Postgres user in DATABASE_URL has privileges to create extensions & tables.
"""
import os
import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.db import SessionLocal, apply_schema_sql, engine
from app.repositories import UserRepository, ItemRepository, RecommendationRepository, EventRepository
from app.models_domain import User, Item, Recommendation, Event


@pytest.fixture(scope="module")
def prepare_db():
    """Apply schema once per test module using the provided schema/sql file."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    schema_path = os.path.join(base_dir, "schema", "schema.sql")
    apply_schema_sql(schema_path)
    yield
    # Teardown: drop tables to keep DB clean for subsequent runs.
    # Dropping by reflecting/making raw SQL that mirrors schema.sql's drop ordering.
    with engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS recommendations;")
        conn.execute("DROP TABLE IF EXISTS events;")
        conn.execute("DROP TABLE IF EXISTS items;")
        conn.execute("DROP TABLE IF EXISTS users;")
        conn.commit()


def test_recommendations_top_n_and_event_retention(prepare_db):
    session = SessionLocal()
    try:
        user_repo = UserRepository(session)
        item_repo = ItemRepository(session)
        rec_repo = RecommendationRepository(session)
        event_repo = EventRepository(session)

        # Create a test user
        user = user_repo.create(User(id=None, email="tester@example.com"))
        assert user.id is not None

        # Create some items
        items = []
        for i in range(5):
            item = item_repo.create(Item(id=None, metadata={"index": i}))
            items.append(item)

        # Insert recommendations with different scores (unsorted input)
        recs_input = [
            Recommendation(user_id=user.id, item_id=items[0].id, score=0.1),
            Recommendation(user_id=user.id, item_id=items[1].id, score=0.9),
            Recommendation(user_id=user.id, item_id=items[2].id, score=0.5),
            Recommendation(user_id=user.id, item_id=items[3].id, score=0.75),
        ]

        # Upsert for the user
        rec_repo.upsert_many_for_user(user.id, recs_input)

        # Fetch top 3 recommendations and verify order is score desc
        top3 = rec_repo.get_top_n_for_user(user.id, 3)
        assert len(top3) == 3
        scores = [r.score for r in top3]
        assert scores == sorted(scores, reverse=True)
        # Highest score should be 0.9
        assert scores[0] == pytest.approx(0.9)

        # --- Test event retention ---
        # Append a recent event (should remain) and an old event (should be deleted)
        recent_event = Event(id=None, user_id=user.id, item_id=items[0].id, event_type="view", value={"k": "v"})
        ev_recent = event_repo.append(recent_event)
        assert ev_recent.id is not None

        # Create an old event manually by constructing an Event with old created_at and inserting via ORM
        old_created_at = datetime.utcnow() - timedelta(days=90)
        old_event = Event(id=None, user_id=user.id, item_id=items[1].id, event_type="view", value={"old": True}, created_at=old_created_at)
        ev_old = event_repo.append(old_event)

        # Now ensure delete_older_than with threshold 30 days removes the old event but not the recent one
        deleted_count = event_repo.delete_older_than(days=30)
        # At least one row (the old event) should be deleted. Depending on DB timezone/etc other rows shouldn't be older.
        assert deleted_count >= 1

        # Verify the recent event still exists by trying to fetch it via raw SQL
        # Use a simple select to ensure it's present
        from sqlalchemy import select
        from app.models_db import EventORM

        stmt = select(EventORM).where(EventORM.id == ev_recent.id)
        res = session.execute(stmt).scalars().first()
        assert res is not None

    finally:
        session.close()
