import { Run } from "@sematic/common/src/Models";
import { usePipelineRunContext } from "src/hooks/pipelineHooks";
import useBasicMetrics from "src/hooks/metricsHooks";
import Loading from "src/components/Loading";
import {
  Alert,
  Box,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useMemo } from "react";
import { durationSecondsToString } from "src/utils";
import CalculatorPath from "src/components/CalculatorPath";
import HelpIcon from "@mui/icons-material/Help";
import { BasicMetricsPayload } from "src/Payloads";
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

function TopMetric(props: { value: string; label: string; help?: string }) {
  const { value, label, help } = props;
  const theme = useTheme();

  return (
    <MetricBox>
      <MetricValue sx={{ fontSize: 70, fontWeight: 500, lineHeight: 1 }}>
        {value}
      </MetricValue>
      <MetricLabel>
        <Typography>{label}</Typography>
        {help !== undefined && (
          <Tooltip title={help}>
            <HelpIcon fontSize="small" />
          </Tooltip>
        )}
      </MetricLabel>
    </MetricBox>
  );
}

export function runSuccessRate(payload: BasicMetricsPayload, run: Run): string {
  const totalCount = payload.content.total_count;
  const percentRate =
    ((payload.content.count_by_state["RESOLVED"] || 0) / (totalCount || 1)) *
    100;
  return `${Math.floor(percentRate)}%`;
}

export function runAvgRunTime(payload: BasicMetricsPayload, run: Run): string {
  return durationSecondsToString(
    payload.content.avg_runtime_children[run.calculator_path] || 0
  );
}

export default function BasicMetricsPanel() {
  const { rootRun } = usePipelineRunContext() as { rootRun: Run };

  const [payload, loading, error] = useBasicMetrics({ runId: rootRun!.id });

  const totalCount = useMemo(() => payload?.content.total_count, [payload]);

  const successRate = useMemo(
    () => (payload ? runSuccessRate(payload, rootRun) : "0%"),
    [payload, rootRun]
  );

  const avgRuntime = useMemo(
    () => (payload ? runAvgRunTime(payload, rootRun) : "0s"),
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
                help={`${totalCount} runs of ${rootRun.calculator_path}`}
              />
            </Grid>
            <Grid item xs={4}>
              <TopMetric
                value={successRate}
                label="success rate"
                help={`Success rate of ${rootRun.calculator_path}`}
              />
            </Grid>
            <Grid item xs={4}>
              <TopMetric
                value={avgRuntime}
                label="avg. run time"
                help="Only successfull runs are included."
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
