-- migrate:up

-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
-- ALTER TABLE runs DROP COLUMN exception;

-- migrate:down

ALTER TABLE runs ADD COLUMN exception TEXT;
