-- migrate:up
ALTER TABLE runs ADD COLUMN cloned_from_run_id character(32);

-- migrate:down
-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
-- ALTER TABLE runs DROP COLUMN cloned_from_run_id;
