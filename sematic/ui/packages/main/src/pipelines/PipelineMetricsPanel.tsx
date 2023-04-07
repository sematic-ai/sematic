import { Run } from "@sematic/common/src/Models";
import { usePipelineRunContext } from "src/hooks/pipelineHooks";
import { MetricsFilter } from "src/hooks/metricsHooks";
import { Box, Grid, Typography } from "@mui/material";
import { useMemo } from "react";
import { durationSecondsToString } from "src/utils";
import CalculatorPath from "src/components/CalculatorPath";
import {
  FuncAvgRuntimeMetric,
  FuncRunCountMetric,
  FuncSuccessRateMetric,
  ListMetric,
} from "src/components/Metrics";

export default function PipelineMetricsPanel() {
  const { rootRun } = usePipelineRunContext() as { rootRun: Run };

  const funcAvgRuntimeFilter = useMemo<MetricsFilter>(() => {
    return {
      metricName: "sematic.func_effective_runtime",
      labels: { root_calculator_path: rootRun.calculator_path },
      groupBys: ["calculator_path"],
    };
  }, [rootRun]);

  return (
    <Box sx={{ p: 5 }}>
      <>
        <Typography variant="h1">Pipeline Metrics</Typography>
        <Grid container sx={{ my: 20 }}>
          <Grid item xs={4}>
            <FuncRunCountMetric
              calculatorPath={rootRun.calculator_path}
              variant="large"
            />
          </Grid>
          <Grid item xs={4}>
            <FuncSuccessRateMetric
              calculatorPath={rootRun.calculator_path}
              variant="large"
            />
          </Grid>
          <Grid item xs={4}>
            <FuncAvgRuntimeMetric
              calculatorPath={rootRun.calculator_path}
              variant="large"
            />
          </Grid>
        </Grid>
        <Typography variant="h3">Average run time by function</Typography>
        <Box sx={{ my: 10 }}>
          <ListMetric
            metricsFilter={funcAvgRuntimeFilter}
            formatValue={durationSecondsToString}
            formatLabel={(_, value) => (
              <CalculatorPath calculatorPath={value} />
            )}
            sortSeries={(a, b) => (a[0] > b[0] ? -1 : 1)}
          />
        </Box>
      </>
    </Box>
  );
}
