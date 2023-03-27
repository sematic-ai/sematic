import { Run } from "@sematic/common/src/Models";
import { usePipelineRunContext } from "src/hooks/pipelineHooks";
import useBasicMetrics from "src/hooks/metricsHooks";
import Loading from "src/components/Loading";
import {
  Alert,
  Box,
  ButtonBase,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from "@mui/material";
import { useMemo } from "react";
import { durationSecondsToString } from "src/utils";
import CalculatorPath from "src/components/CalculatorPath";
import HelpIcon from "@mui/icons-material/Help";
import styled from "@emotion/styled";
import { theme } from "@sematic/common/src/theme/mira/index";

const MetricBox = styled(Box)`
  text-align: center;
  padding: ${theme.spacing(10)};
`;

const MetricValue = styled(Typography)`
  font-size: 70px;
  font-weight: 500;
  line-height: 1;
`;

const MetricLabel = styled(Box)`
  display: flex;
  flex-direction: row;
  align-items: center;
  column-gap: ${theme.spacing(1)};
  justify-content: center;

  & .MuiTypography-root {
    font-size: 20px;
  }

  & .MuiSvgIcon-root {
    color: ${theme.palette.grey[300]};
  }
`;

function TopMetric(props: { value: string; label: string; docs?: string }) {
  const { value, label, docs } = props;

  return (
    <MetricBox>
      <MetricValue sx={{ fontSize: 70, fontWeight: 500, lineHeight: 1 }}>
        {value}
      </MetricValue>
      <MetricLabel>
        <Typography>{label}</Typography>
        {docs !== undefined && (
          <ButtonBase
            href={`https://docs.sematic.dev/diving-deeper/metrics#${docs}`}
            target="_blank"
          >
            <HelpIcon fontSize="small" />
          </ButtonBase>
        )}
      </MetricLabel>
    </MetricBox>
  );
}

export function runSuccessRate(countByState: {[k: string]: number}, run: Run): string {
  const numeratorStates = ["RESOLVED"];
  const denominatorStates = ["RESOLVED", "FAILED", "NESTED_FAILED"];

  const countForStates = (states: string[]) =>
    states.reduce(
      (sum: number, state: string) =>
        (sum += countByState[state] || 0),
      0
    );

  const percentRate =
    (countForStates(numeratorStates) /
      (countForStates(denominatorStates) || 1)) *
    100;

  return `${Math.floor(percentRate)}%`;
}

export function runAvgRunTime(avgRuntimeChildren: {[k: string]: number}, run: Run): string {
  return durationSecondsToString(
    avgRuntimeChildren[run.calculator_path] || 0
  );
}

export default function BasicMetricsPanel() {
  const { rootRun } = usePipelineRunContext() as { rootRun: Run };

  const [payload, loading, error] = useBasicMetrics({ runId: rootRun!.id });

  const totalCount = useMemo(() => payload?.content.total_count, [payload]);

  const successRate = useMemo(
    () => (payload ? runSuccessRate(payload.content.count_by_state, rootRun) : "0%"),
    [payload, rootRun]
  );

  const avgRuntime = useMemo(
    () => (payload ? runAvgRunTime(payload.content.avg_runtime_children, rootRun) : "0s"),
    [payload, rootRun]
  );

  const sortedAvgRuntimeChildren = useMemo(
    () =>
      Object.entries(payload?.content.avg_runtime_children || {}).sort((a, b) =>
        a[1] > b[1] ? -1 : 1
      ),
    [payload]
  );

  return (
    <Box sx={{ p: 5 }}>
      {loading === true && <Loading isLoaded={false} />}
      {!loading && error !== undefined && (
        <Alert severity="error">Unable to load metrics: {error.message}</Alert>
      )}
      {!loading && !error && payload !== undefined && (
        <>
          <Typography variant="h1">Pipeline Metrics</Typography>
          <Grid container sx={{ my: 10 }}>
            <Grid item xs={4}>
              <TopMetric
                value={`${totalCount}`}
                label="runs"
                docs="run-count"
              />
            </Grid>
            <Grid item xs={4}>
              <TopMetric
                value={successRate}
                label="success rate"
                docs="success-rate"
              />
            </Grid>
            <Grid item xs={4}>
              <TopMetric
                value={avgRuntime}
                label="avg. run time"
                docs="average-run-time"
              />
            </Grid>
          </Grid>
          <Typography variant="h3">Average run time by function</Typography>
          <Box sx={{ my: 10 }}>
            <Table>
              <TableBody>
                {sortedAvgRuntimeChildren.map(
                  ([calculatorPath, runtimeS], idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <CalculatorPath calculatorPath={calculatorPath} />
                      </TableCell>
                      <TableCell>{durationSecondsToString(runtimeS)}</TableCell>
                    </TableRow>
                  )
                )}
              </TableBody>
            </Table>
          </Box>
        </>
      )}
    </Box>
  );
}
