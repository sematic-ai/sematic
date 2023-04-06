-- migrate:up

-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
-- ALTER TABLE runs DROP COLUMN external_jobs_json;
-- ALTER TABLE resolutions DROP COLUMN external_jobs_json;

-- Once we are relying on the jobs table, we will query
-- jobs by run id quite often.
CREATE INDEX jobs_run_id ON jobs (run_id);

-- migrate:down

DROP INDEX jobs_run_id;
-- TODO #302: implement sustainable way to upgrade sqlite3 DBs
--ALTER TABLE resolutions ADD COLUMN external_jobs_json JSONB;
--ALTER TABLE runs ADD COLUMN external_jobs_json JSONB;