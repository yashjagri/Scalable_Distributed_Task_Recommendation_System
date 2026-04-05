-- Schema for Scalable Distributed Task & Recommendation System (MVP)
-- This file creates the core tables: users, items, events, recommendations.
-- It is written to be idempotent for test/dev flows by dropping objects if they already exist
-- (drop order respects foreign key dependencies).

-- Enable pgcrypto to provide gen_random_uuid(); this is available in modern Postgres.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop tables if they exist so tests can re-run the SQL file cleanly.
DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;

-- Users table: id is UUID primary key, email unique, created_at timestamp with timezone
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Items table: id is UUID PK, metadata stored as JSONB for flexibility
CREATE TABLE items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Events table: append-only raw events. item_id nullable to allow events not tied to an item.
CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  item_id UUID REFERENCES items(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  value JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Indexes to support common event query patterns:
-- - query recent events per user (user_id, created_at DESC)
-- - filter events by type per user (user_id, event_type)
CREATE INDEX IF NOT EXISTS idx_events_user_created_at ON events (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_user_event_type ON events (user_id, event_type);

-- Recommendations table: precomputed per-user scores for items.
-- Composite PK (user_id, item_id). Index on (user_id, score DESC) supports fast top-N queries.
CREATE TABLE recommendations (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  score DOUBLE PRECISION NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, item_id)
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user_score_desc ON recommendations (user_id, score DESC);

-- Retention pattern (example):
-- To delete events older than a given retention period (e.g. 30 days) run:
-- DELETE FROM events WHERE created_at < now() - interval '30 days';

-- End of schema
