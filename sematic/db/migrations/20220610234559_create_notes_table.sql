-- migrate:up

CREATE TABLE notes (
    id character(32) NOT NULL,
    author_id TEXT NOT NULL,
    note TEXT NOT NULL,
    run_id character(32) NOT NULL,
    root_id character(32) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,

    PRIMARY KEY(id),

    FOREIGN KEY(run_id) REFERENCES runs (id),
    FOREIGN KEY(root_id) REFERENCES runs (id)
);

-- migrate:down

DELETE TABLE notes;
