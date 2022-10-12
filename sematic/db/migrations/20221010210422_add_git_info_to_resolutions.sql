-- migrate:up

ALTER TABLE resolutions ADD COLUMN git_info_json JSONB;

-- migrate:down

ALTER TABLE resolutions DROP COLUMN git_info_json;
