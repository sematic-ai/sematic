-- migrate:up

ALTER TABLE runs ADD COLUMN root_id character(32) NOT NULL;

-- migrate:down

ALTER TABLE runs DROP COLUMN root_id;
