-- migrate:up

CREATE TABLE artifacts (
    -- sha1 hex digest are 40 characters
    id character(40) NOT NULL,
    json_summary JSONB NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,

    PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE artifacts;
