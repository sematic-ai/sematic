-- migrate:up
CREATE INDEX ix_edges_source_run_id ON edges (source_run_id);
CREATE INDEX ix_edges_destination_run_id ON edges (destination_run_id);

-- migrate:down
DROP INDEX ix_edges_source_run_id;
DROP INDEX ix_edges_destination_run_id;
