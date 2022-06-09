-- migrate:up

ALTER TABLE artifacts ADD COLUMN type_serialization JSONB NOT NULL DEFAULT "{}";

-- migrate:down

ALTER TABLE artifacts DROP COLUMN type_serialization;
