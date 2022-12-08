-- migrate:up
ALTER TABLE runs ADD COLUMN cache_key TEXT;

CREATE INDEX runs_cache_key_index ON runs(cache_key);

-- migrate:down
DROP INDEX runs_cache_key_index;

-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
-- ALTER TABLE runs DROP COLUMN cache_key;
