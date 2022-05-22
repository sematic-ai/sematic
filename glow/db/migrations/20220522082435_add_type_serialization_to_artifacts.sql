-- migrate:up

ALTER TABLE artifacts ADD COLUMN type_serialization JSONB NOT NULL;

-- migrate:down

ALTER TABLE artifacts DROP COLUMN type_serialization;
