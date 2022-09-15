-- migrate:up

ALTER TABLE resolutions ADD COLUMN external_jobs_json JSONB;

-- migrate:down

ALTER TABLE resolutions DROP COLUMN external_jobs_json;
