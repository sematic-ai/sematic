-- migrate:up

ALTER TABLE runs RENAME COLUMN exception_json TO exception_metadata_json;
ALTER TABLE runs RENAME COLUMN external_exception_json TO external_exception_metadata_json;

-- migrate:down

ALTER TABLE runs RENAME COLUMN exception_metadata_json TO exception_json;
ALTER TABLE runs RENAME COLUMN external_exception_metadata_json TO external_exception_json;
