-- migrate:up
ALTER TABLE runs ADD COLUMN exception_json JSONB;

-- migrate:down

ALTER TABLE runs DROP COLUMN exception_json;
