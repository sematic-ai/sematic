-- migrate:up

ALTER TABLE runs ADD COLUMN user_id character(32) REFERENCES users(id);

ALTER TABLE resolutions ADD COLUMN user_id character(32) REFERENCES users(id);

-- migrate:down

ALTER TABLE runs DROP COLUMN user_id;
ALTER TABLE resolutions DROP COLUMN user_id;