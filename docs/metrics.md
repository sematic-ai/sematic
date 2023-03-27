# Metrics

Sematic surfaces a number of high-level metrics in the Dashboard.

## Pipeline metrics

Pipeline metrics are displayed on the pipeline index page, as well as on the
"Pipeline metrics" panel of the Run details page.

### Run count

This is the total number of runs for this pipeline. This includes all
outcomes (success, failure, cancelation, running, etc.), and counts only runs of
the pipeline's [root function](./glossary.md#root-entry-point-function).

This represents the total number of times the pipeline was submitted, either
from the CLI, the dashboard, or external systems.

### Success rate

The pipeline success rate is the percentage of successful runs among all terminated runs of the pipeline's [root function](./glossary.md#root-entry-point-function).

Terminated runs include successful and failed runs. It does not include canceled
runs as those were intentionally interrupted by users. It does not include
in-progress runs.

### Average run time

The pipeline average run time is the average of the pipeline's wall time
computed over all successful runs. Failed and canceled runs are not included.