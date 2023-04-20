-- migrate:up
-- Schema inspired by https://github.com/CrunchyData/postgresql-prometheus-adapter/blob/main/pkg/postgresql/client.go

CREATE TABLE metric_labels (
    metric_id TEXT NOT NULL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_labels JSONB NOT NULL DEFAULT '{}',
    metric_type SMALLINT NOT NULL
);

CREATE UNIQUE INDEX metric_labels_name_labels_idx ON metric_labels(metric_name, metric_labels);

CREATE TABLE metric_values (
    metric_id TEXT NOT NULL,
    value FLOAT NOT NULL,
    metric_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX metric_values_id_time_idx ON metric_values(metric_id, metric_time DESC);
CREATE INDEX metric_values_time_idx ON metric_values(metric_time DESC);

-- migrate:down

DROP TABLE metric_labels;
DROP TABLE metric_values;
