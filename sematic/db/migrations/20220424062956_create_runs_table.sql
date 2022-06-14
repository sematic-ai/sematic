-- migrate:up

CREATE TABLE runs (
    id character(32) NOT NULL,
    future_state TEXT NOT NULL,
    name TEXT,
    calculator_path TEXT,
    created_at timestamp WITH time zone NOT NULL,
    updated_at timestamp WITH time zone NOT NULL,
    started_at timestamp,
    ended_at timestamp,
    resolved_at timestamp,
    failed_at timestamp,
    parent_id character(32),

    PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE runs;
