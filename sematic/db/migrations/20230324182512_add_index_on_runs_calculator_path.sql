-- migrate:up

CREATE INDEX runs_calculator_path ON runs (calculator_path);

-- migrate:down

DROP INDEX runs_calculator_path;