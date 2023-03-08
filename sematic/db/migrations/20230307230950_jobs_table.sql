-- migrate:up

CREATE TABLE jobs (
    id TEXT NOT NULL,
    source_run_id character(32) NOT NULL,
    last_updated_epoch_seconds int64 NOT NULL,
    state_name TEXT NOT NULL,
    is_active int8 NOT NULL, -- int8 because sqlite doesn't have boolean
    job_type TEXT NOT NULL,
    status_message TEXT NOT NULL,
    value_serialization JSONB NOT NULL,
    status_history_serializations JSONB NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,

    PRIMARY KEY(id),

    FOREIGN KEY(source_run_id) REFERENCES runs (id)
);

-- migrate:down

DROP TABLE jobs;