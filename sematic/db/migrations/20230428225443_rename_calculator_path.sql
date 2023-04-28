-- migrate:up

ALTER TABLE runs RENAME COLUMN calculator_path TO function_path;

-- migrate:down

ALTER TABLE runs RENAME COLUMN function_path TO calculator_path;
