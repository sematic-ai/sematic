-- migrate:up
ALTER TABLE runs ADD COLUMN description TEXT;

ALTER TABLE runs ADD COLUMN tags TEXT;

-- migrate:down

ALTER TABLE runs DROP COLUMN description;

ALTER TABLE runs DROP COLUMN tags;
