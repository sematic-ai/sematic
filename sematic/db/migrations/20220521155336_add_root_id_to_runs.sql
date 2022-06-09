-- migrate:up

ALTER TABLE runs ADD COLUMN root_id character(32);

-- migrate:down

ALTER TABLE runs DROP COLUMN root_id;
