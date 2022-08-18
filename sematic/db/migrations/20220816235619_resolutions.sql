-- migrate:up

CREATE TABLE resolutions (
    root_id TEXT NOT NULL,
    status TEXT NOT NULL,
    kind TEXT NOT NULL,
    docker_image_uri TEXT,
    settings_env_vars JSONB NOT NULL,

    PRIMARY KEY (root_id),
    FOREIGN KEY (root_id) REFERENCES runs(id)
);

INSERT INTO resolutions (root_id, status, kind, docker_image_uri, settings_env_vars)
SELECT id, 'COMPLETE', 'LOCAL', NULL, '{}' FROM runs
WHERE parent_id is NULL;

-- migrate:down

DROP TABLE resolutions;
