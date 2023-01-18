-- migrate:up
ALTER TABLE resolutions ADD COLUMN cache_namespace TEXT;

-- migrate:down
-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
-- ALTER TABLE resolutions DROP COLUMN cache_namespace;
