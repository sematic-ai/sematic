-- migrate:up
ALTER TABLE resolutions ADD COLUMN client_version TEXT;

-- migrate:down
-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
-- ALTER TABLE resolutions DROP COLUMN client_version;