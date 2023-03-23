RUN_COUNT_BY_STATE = """
SELECT
    future_state,
    COUNT(*)
FROM runs
WHERE
    calculator_path = :calculator_path
GROUP BY future_state;
"""


AVG_RUNTIME_CHILDREN = """
SELECT
    runs.calculator_path,
    avg(strftime('%s', runs.resolved_at) - strftime('%s', runs.started_at))
FROM runs
INNER JOIN
    runs AS root_runs
    ON root_runs.id == runs.root_id
WHERE
    root_runs.calculator_path = :calculator_path
    AND runs.resolved_at IS NOT NULL
GROUP BY runs.calculator_path;
"""
