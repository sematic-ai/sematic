-- migrate:up

ALTER TABLE runs ADD COLUMN resource_requirements_json JSONB;

-- migrate:down

ALTER TABLE runs DROP COLUMN resource_requirements_json;