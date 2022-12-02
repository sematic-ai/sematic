-- migrate:up
ALTER TABLE resolutions ADD COLUMN client_version TEXT;

-- migrate:down

ALTER TABLE resolutions DROP COLUMN client_version;