"""
Database bootstrap and session factory. Reads DATABASE_URL from environment.
Provides helpers to create tables from ORM metadata or apply a raw SQL schema file.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .models_db import Base

# Read DATABASE_URL from env, default is a local Postgres placeholder.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/reccore")

# Create an engine. Using future=True to opt-in to SQLAlchemy 2.0 style where reasonable.
engine = create_engine(DATABASE_URL, future=True)

# Session factory to be used by repositories. autocommit/autoflush kept False for transactional control.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_tables_from_orm():
    """
    Create tables using SQLAlchemy ORM metadata. This is convenient for local dev and tests.
    It will create tables if they do not already exist. Note: indexes defined in schema.sql are
    not created here unless expressed on the ORM models; for exact index control prefer applying
    the schema/sql file.
    """
    Base.metadata.create_all(bind=engine)


def apply_schema_sql(path: str):
    """
    Apply raw SQL schema file. This executes the SQL statements in the given file directly
    against the database. Use this to ensure the schema exactly matches schema/schema.sql,
    including indexes and extensions.
    """
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Use a single connection to execute the whole file. Some SQL files may contain multiple
    # statements; SQLAlchemy's connection.execute(text(sql)) will handle them for Postgres.
    with engine.connect() as conn:
        # Use autocommit/execute for raw DDL
        conn.execute(text(sql))
        conn.commit()
