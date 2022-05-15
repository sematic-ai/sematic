-- migrate:up

CREATE TABLE run_artifacts (
    run_id character(32) NOT NULL,
    artifact_id character(40) NOT NULL,
    name TEXT,
    relationship TEXT,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,

    FOREIGN KEY(artifact_id) REFERENCES artifacts (id),
    FOREIGN KEY(run_id) REFERENCES runs (id),

    PRIMARY KEY(run_id, artifact_id, name)
);

-- migrate:down

DROP TABLE run_artifacts;
