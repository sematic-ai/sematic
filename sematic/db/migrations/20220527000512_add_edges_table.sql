-- migrate:up

CREATE TABLE edges (
    id character(32) NOT NULL,
    source_run_id character(32),
    source_name TEXT,
    destination_run_id character(32),
    destination_name TEXT,
    artifact_id character(40),
    parent_id character(32),
    created_at timestamp NOT NULL,
    updated_at timestamp NOT NULL,

    PRIMARY KEY (id),

    FOREIGN KEY(artifact_id) REFERENCES artifacts (id),
    FOREIGN KEY(parent_id) REFERENCES edges (id)
);

-- migrate:down

DROP TABLE edges;