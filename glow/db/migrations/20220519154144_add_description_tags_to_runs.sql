-- migrate:up
ALTER TABLE runs ADD COLUMN description TEXT;

ALTER TABLE runs ADD COLUMN tags TEXT;

-- migrate:down

ALTER TABLE DROP COLUMN description;

ALTER TABLE DROP COLUMN tags;
