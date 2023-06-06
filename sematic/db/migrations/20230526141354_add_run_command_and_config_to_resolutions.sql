-- migrate:up
ALTER TABLE resolutions ADD COLUMN run_command TEXT;
ALTER TABLE resolutions ADD COLUMN build_config TEXT;

-- migrate:down

-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
-- ALTER TABLE resolutions DROP COLUMN run_command;
-- ALTER TABLE resolutions ADD COLUMN build_config;
