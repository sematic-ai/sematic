-- migrate:up

ALTER TABLE runs ADD COLUMN user_id character(32) REFERENCES users(email);

-- migrate:down

ALTER TABLE runs DROP COLUMN user_id;