-- migrate:up
ALTER TABLE runs ADD COLUMN nested_future_id character(32);

-- migrate:down
ALTER TABLE runs DROP COLUMN nested_future_id;
