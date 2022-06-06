-- migrate:up

ALTER TABLE runs ADD COLUMN source_code TEXT;

-- migrate:down

ALTER TABLE runs DROP COLUMN source_code;
