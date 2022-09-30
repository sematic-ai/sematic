-- migrate:up
ALTER TABLE runs ADD COLUMN exception_json JSONB;

-- UPDATE runs SET exception_json = '{"name": "Exception", "module": "exceptions"}' || jsonb_build_object('repr', exception) WHERE exception IS NOT NULL;

-- ALTER TABLE runs DROP COLUMN exception;

-- migrate:down

ALTER TABLE runs ADD COLUMN exception TEXT;

-- UPDATE runs SET exception = exception_json->>'repr' WHERE exception_json IS NOT NULL;

-- ALTER TABLE runs DROP COLUMN exception_json;