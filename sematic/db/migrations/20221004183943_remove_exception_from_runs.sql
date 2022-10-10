-- migrate:up

ALTER TABLE runs DROP COLUMN exception;

-- migrate:down

ALTER TABLE runs ADD COLUMN exception TEXT;
