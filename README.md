# Scalable Distributed Task & Recommendation System — Persistence & Domain Models (MVP)

This repository defines the core persistence layer and pure domain models for an MVP
that stores users, items, append-only events, and precomputed per-user recommendations.

Files created in this step:

- schema/schema.sql — Postgres schema (users, items, events, recommendations) with indexes
- src/app/models_domain.py — Pure domain dataclasses (User, Item, Event, Recommendation)
- src/app/models_db.py — SQLAlchemy ORM models mapping to the schema
- src/app/db.py — SQLAlchemy engine and session factory; helpers to apply schema
- src/app/mappings.py — Conversion helpers between ORM objects and domain dataclasses
- src/app/repositories.py — Repository layer encapsulating DB operations
- src/seed.py — Optional script to seed sample data
- tests/test_repositories.py — Pytest tests validating key repository behavior

Prerequisites
-------------
- Python 3.8+
- PostgreSQL (tested with Postgres 12+)
- Python packages (recommended to use a virtualenv):
  - sqlalchemy
  - psycopg2-binary
  - pytest

Install requirements (example):

  python -m venv .venv
  source .venv/bin/activate
  pip install sqlalchemy psycopg2-binary pytest

Database setup
--------------
Set the DATABASE_URL environment variable to point to your Postgres instance. Example:

  export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/reccore

The Postgres role must be able to create extensions (pgcrypto) and create tables in the
specified database (or you can create the database separately).

Apply the schema
----------------
You can apply the schema using psql or let the helper apply it for you.

Using psql (example):

  psql "$DATABASE_URL" -f schema/schema.sql

Or using the helper function in Python:

  from app.db import apply_schema_sql
  apply_schema_sql("schema/schema.sql")

Running tests
-------------
Run the tests with pytest. The tests will apply the schema, run checks, and drop tables when
finished to keep the DB clean.

  pytest -q

Notes and implementation details
--------------------------------
- The schema uses UUID primary keys with gen_random_uuid() (pgcrypto extension) and JSONB
  for flexible item metadata and event payloads.
- Events are append-only; a retention policy can be implemented by running a single
  DELETE statement like:

    DELETE FROM events WHERE created_at < now() - interval '30 days';

  The EventRepository.delete_older_than(days) method executes this pattern.
- Recommendations table has a composite primary key (user_id, item_id) and an index on
  (user_id, score DESC) to support efficient top-N queries per user.
- Domain dataclasses are intentionally kept free from SQLAlchemy imports so business logic
  and unit tests can operate on pure objects.
- Upsert for recommendations is implemented in a simple way (delete existing for user,
  bulk insert new). For large-scale deployments consider using Postgres ON CONFLICT
  for more efficient upserts.

If you encounter issues
-----------------------
- Ensure DATABASE_URL is set and reachable from your environment.
- Ensure the Postgres user has permission to create the pgcrypto extension or create it
  as a superuser beforehand.

