-- migrate:up
ALTER TABLE runs ADD COLUMN exception_json JSONB;

UPDATE runs SET exception_json = '{"repr": "' || exception || '", "name": "Exception", "module": "exceptions"}' WHERE exception IS NOT NULL;

ALTER TABLE runs DROP COLUMN exception;

-- migrate:down

ALTER TABLE runs ADD COLUMN exception TEXT;

UPDATE runs SET exception = exception_json->>'repr' WHERE exception_json IS NOT NULL;

ALTER TABLE runs DROP COLUMN exception_json;