"""
A small seed script to populate the DB with sample data for manual testing.
Run: DATABASE_URL=... python src/seed.py
This script is optional for automated tests but handy during development.
"""
import os
from uuid import uuid4
from datetime import datetime

from app.db import SessionLocal, apply_schema_sql
from app.repositories import UserRepository, ItemRepository, RecommendationRepository, EventRepository
from app.models_domain import User, Item, Recommendation, Event


def main():
    # Ensure schema is applied (use schema/sql to get exact indexes)
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema", "schema.sql")
    # If schema.sql location changes, adjust the path above. For now ensure absolute resolution.
    apply_schema_sql(os.path.abspath(schema_path))

    session = SessionLocal()
    try:
        user_repo = UserRepository(session)
        item_repo = ItemRepository(session)
        rec_repo = RecommendationRepository(session)
        event_repo = EventRepository(session)

        # Create a sample user and items
        user = user_repo.create(User(id=None, email="alice@example.com"))
        item1 = item_repo.create(Item(id=None, metadata={"title": "Item A"}))
        item2 = item_repo.create(Item(id=None, metadata={"title": "Item B"}))

        # Upsert sample recommendations
        recs = [
            Recommendation(user_id=user.id, item_id=item1.id, score=0.9),
            Recommendation(user_id=user.id, item_id=item2.id, score=0.7),
        ]
        rec_repo.upsert_many_for_user(user.id, recs)

        # Append a sample event
        ev = Event(id=None, user_id=user.id, item_id=item1.id, event_type="click", value={"x": 1})
        event_repo.append(ev)

        print("Seed completed: user", user, "items:", item1, item2)
    finally:
        session.close()


if __name__ == "__main__":
    main()
