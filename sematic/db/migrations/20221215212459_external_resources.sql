-- migrate:up

CREATE TABLE external_resources (
    id character(32) NOT NULL,
    resource_state TEXT NOT NULL,
    locally_allocated BOOLEAN NOT NULL,
    status_message TEXT NOT NULL,
    last_updated_epoch_seconds int8 NOT NULL,
    type_serialization JSONB NOT NULL,
    value_serialization JSONB NOT NULL,
    history_serializations JSONB NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE run_external_resources (
    resource_id character(32) NOT NULL,
    run_id character(32) NOT NULL,
    PRIMARY KEY (resource_id, run_id),
    FOREIGN KEY(resource_id) REFERENCES external_resources (id),
    FOREIGN KEY(run_id) REFERENCES runs (id)
);

-- migrate:down

DROP TABLE run_external_resources;
DROP TABLE external_resources;
