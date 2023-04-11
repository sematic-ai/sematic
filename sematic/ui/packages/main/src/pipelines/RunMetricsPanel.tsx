import { Timeline } from "@mui/icons-material";
import { Box, Typography, useTheme } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Loading from "src/components/Loading";
import { TimeseriesMetric } from "src/components/Metrics";
import { METRIC_SCOPES } from "src/constants";
import { MetricsFilter, useListMetrics } from "src/hooks/metricsHooks";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { getChartColor } from "src/utils";
import {
  MetricPoint,
  runIsInTerminalState,
} from "@sematic/common/lib/src/Models";
import { metricsSocket } from "src/sockets";

export default function RunMetricsPanel() {
  const theme = useTheme();

  const { selectedRun } = usePipelinePanelsContext();

  let run = selectedRun!;

  const [latestBroadcastEvent, setLatestBroadcastEvent] = useState<
    MetricPoint[] | undefined
  >();

  useEffect(() => {
    if (runIsInTerminalState(run)) return;
    metricsSocket.removeAllListeners("update");
    metricsSocket.on("update", (args: { metric_points: MetricPoint[] }) => {
      const currentRunMetricPoints = args.metric_points.filter(
        (point) =>
          point.labels["run_id"] === run.id && point.labels["__scope__"] === 0
      );

      if (currentRunMetricPoints.length > 0)
        setLatestBroadcastEvent(currentRunMetricPoints);
    });
  }, [run.id]);

  const labels = useMemo(() => {
    return { run_id: run.id, __scope__: METRIC_SCOPES.run };
  }, [run.id]);

  const [payload, loading, error] = useListMetrics(labels);

  const metricFilters = useMemo(() => {
    if (payload === undefined) return undefined;

    return payload.content.reduce((accumulator, item) => {
      if (!item.startsWith("sematic.")) {
        const filter: MetricsFilter = {
          metricName: item,
          labels: labels,
          groupBys: ["timestamp"],
        };
        accumulator.push(filter);
      }

      return accumulator;
    }, new Array<MetricsFilter>());
  }, [payload, labels]);

  return (
    <>
      <Loading isLoaded={!loading} error={error} />
      {!loading &&
        metricFilters !== undefined &&
        metricFilters.length === 0 && (
          <Box sx={{ textAlign: "center", py: 20 }}>
            <Timeline sx={{ fontSize: 100, color: theme.palette.grey[300] }} />
            <Typography sx={{ color: "gray" }}>
              No metrics were logged for this run.
              <br />
              Read the <Link to="">documentation</Link> to get started.
            </Typography>
          </Box>
        )}
      {!loading &&
        metricFilters !== undefined &&
        metricFilters.map((metricFilter, idx) => (
          <Box sx={{ mt: 10, float: "left", width: 500 }} key={idx}>
            <Typography variant="h4">{metricFilter.metricName}</Typography>
            <TimeseriesMetric
              metricsFilter={metricFilter}
              color={getChartColor(idx)}
              broadcastEvent={latestBroadcastEvent}
            />
          </Box>
        ))}
    </>
  );
}
