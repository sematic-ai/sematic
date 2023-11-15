-- migrate:up

ALTER TABLE resolutions ADD COLUMN resource_requirements_json JSONB;

-- migrate:down

ALTER TABLE resolutions DROP COLUMN resource_requirements_json;
