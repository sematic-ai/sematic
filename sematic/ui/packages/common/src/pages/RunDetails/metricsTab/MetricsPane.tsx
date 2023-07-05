import { Timeline } from "@mui/icons-material";
import { Box, Typography, useTheme } from "@mui/material";
import Alert from "@mui/material/Alert";
import { metricsSocket } from "@sematic/common/src/sockets";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { MetricPoint, Run, runIsInTerminalState } from "src/Models";
import { METRIC_SCOPES } from "src/constants";
import { useListMetrics } from "src/hooks/metricsHooks";
import { TimeseriesMetric } from "src/pages/RunDetails/metricsTab/Metrics";
import { getChartColor } from "src/utils/color";

interface MetricsPaneProps {
    run: Run;
    setIsLoading: (isLoading: boolean) => void;
}

export default function MetricsPane(props: MetricsPaneProps) {
    const { run, setIsLoading } = props;
    const theme = useTheme();

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

    useEffect(() => {
        setIsLoading(loading);
    }, [loading, setIsLoading]);

    return (
        <>
            {error && <Alert severity="error">{error.message}</Alert> }
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
                            Read the <Link to="https://docs.sematic.dev/diving-deeper/metrics#custom-metrics">documentation</Link> to get
                            started.
                    </Typography>
                </Box>
            )}
            {
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
