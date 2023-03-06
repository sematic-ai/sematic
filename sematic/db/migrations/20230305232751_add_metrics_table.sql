-- migrate:up

CREATE TABLE metrics (
    name TEXT NOT NULL,
    value FLOAT NOT NULL,
    run_id character(32) NOT NULL,
    root_id character(32) NOT NULL,
    scope TEXT NOT NULL,
    annotations JSONB NOT NULL DEFAULT '{}',
    created_at timestamp WITH time zone NOT NULL
);

-- migrate:down

DROP TABLE metrics;