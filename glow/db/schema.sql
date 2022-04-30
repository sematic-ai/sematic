CREATE TABLE IF NOT EXISTS "schema_migrations" (version varchar(255) primary key);
CREATE TABLE runs (
    id character(32) NOT NULL,
    future_state TEXT NOT NULL,
    name TEXT,
    calculator_path TEXT,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    resolved_at timestamp without time zone,
    failed_at timestamp without time zone,
    parent_id character(32),

    PRIMARY KEY (id)
);
-- Dbmate schema migrations
INSERT INTO "schema_migrations" (version) VALUES
  ('20220424062956');
