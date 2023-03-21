-- migrate:up

CREATE TABLE jobs (
    name TEXT NOT NULL,
    namespace TEXT NOT NULL,
    run_id character(32) NOT NULL,
    last_updated_epoch_seconds double precision NOT NULL,
    state TEXT NOT NULL,
    kind TEXT NOT NULL,
    message TEXT NOT NULL,
    detail_serialization JSONB NOT NULL,
    status_history_serialization JSONB NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,

    PRIMARY KEY(name, namespace),

    FOREIGN KEY(run_id) REFERENCES runs (id)
);

-- migrate:down
drop table jobs;
