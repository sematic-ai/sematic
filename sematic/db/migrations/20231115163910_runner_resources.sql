-- migrate:up

ALTER TABLE resolutions ADD COLUMN resource_requirements_json JSONB;

-- migrate:down

-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
-- ALTER TABLE resolutions DROP COLUMN resource_requirements_json;
