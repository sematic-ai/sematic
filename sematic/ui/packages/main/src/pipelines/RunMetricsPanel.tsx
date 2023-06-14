import { Timeline } from "@mui/icons-material";
import { Box, Typography, useTheme } from "@mui/material";
import {
    MetricPoint,
    runIsInTerminalState,
} from "@sematic/common/lib/src/Models";
import { METRIC_SCOPES } from "@sematic/common/src/constants";
import { useListMetrics } from "@sematic/common/src/hooks/metricsHooks";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Loading from "src/components/Loading";
import { TimeseriesMetric } from "src/components/Metrics";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { metricsSocket } from "src/sockets";
import { getChartColor } from "src/utils";

export default function RunMetricsPanel() {
    const theme = useTheme();

    const { selectedRun } = usePipelinePanelsContext();

    let run = selectedRun!;

    const [latestmetricPoints, setLatestMetricPoints] = useState<
    MetricPoint[] | undefined
    >();

    const metricsUpdateListener = useCallback((args: { metric_points: MetricPoint[] }) => {
        const currentRunMetricPoints = args.metric_points.filter(
            (point) =>
                point.labels["run_id"] === run.id &&
                point.labels["__scope__"] === METRIC_SCOPES.run
        );

        if (currentRunMetricPoints.length > 0)
            setLatestMetricPoints(currentRunMetricPoints);
    }, [run.id, setLatestMetricPoints]);

    useEffect(() => {
        if (runIsInTerminalState(run)) return;
        metricsSocket.on("update", metricsUpdateListener);
        return () => {
            metricsSocket.off("update", metricsUpdateListener);
        }
    }, [run, metricsUpdateListener]);

    const labels = useMemo(() => {
        return { run_id: run.id, __scope__: METRIC_SCOPES.run };
    }, [run.id]);

    const [payload, loading, error] = useListMetrics(labels, latestmetricPoints);

    const metricFilters = useMemo(() => {
        if (payload === undefined) return undefined;

        return payload.content.filter(
            item => !item.startsWith("sematic.")
        ).map(
            item => ({ metricName: item, labels, groupBys: [] })
        );
    }, [payload, labels]);

    return (
        <>
            <Loading isLoaded={!loading} error={error} />
            {!loading &&
                metricFilters !== undefined &&
                metricFilters.length === 0 && (
                <Box sx={{ textAlign: "center", py: 20 }}>
                    <Timeline
                        sx={{
                            fontSize: 100,
                            color: theme.palette.grey[300],
                        }}
                    />
                    <Typography sx={{ color: "gray" }}>
                            No metrics logged for this run.
                        <br />
                            Read the <Link to="TODO">documentation</Link> to get
                            started.
                    </Typography>
                </Box>
            )}
            {!loading &&
                metricFilters !== undefined &&
                metricFilters.map((metricFilter, idx) => (
                    <Box sx={{ mt: 10, float: "left", width: 500 }} key={idx}>
                        <Typography variant="h4">
                            {metricFilter.metricName}
                        </Typography>
                        <TimeseriesMetric
                            metricsFilter={metricFilter}
                            color={getChartColor(idx)}
                            latestMetricPoints={latestmetricPoints}
                        />
                    </Box>
                ))}
        </>
    );
}
