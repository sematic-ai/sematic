-- migrate:up

ALTER TABLE runs ADD COLUMN exception TEXT;

-- migrate:down

ALTER TABLE runs DROP COLUMN exception;
