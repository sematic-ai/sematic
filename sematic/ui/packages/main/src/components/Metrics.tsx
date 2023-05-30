import { MetricsFilter, useMetrics } from "@sematic/common/src/hooks/metricsHooks";
import { Alert, Skeleton } from "@mui/material";
import { useMemo } from "react";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ChartData,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { MetricPoint } from "@sematic/common/lib/src/Models";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

export function TimeseriesMetric(props: {
    metricsFilter: MetricsFilter;
    color: string;
    broadcastEvent?: MetricPoint[];
}) {
    const { metricsFilter, color, broadcastEvent } = props;
    const [payload, loading, error] = useMetrics(metricsFilter, broadcastEvent);

    const chartData = useMemo(() => {
        const cData: ChartData<"line", number[], string> = {
            labels: [],
            datasets: [
                {
                    label: metricsFilter.metricName,
                    data: [],
                    backgroundColor: color,
                    borderColor: color,
                },
            ],
        };
        if (payload === undefined) return cData;

        payload.content.series.forEach((item) => {
            let label = new Date(item[1][0]);
            cData.labels?.push(label.toLocaleString());
            cData.datasets[0].data.push(item[0]);
        });

        return cData;
    }, [payload, color, metricsFilter.metricName]);

    return (
        <>
            {loading && <Skeleton />}
            {error && (
                <Alert severity="error">
                    Unable to load metric: {error.message}
                </Alert>
            )}
            {payload !== undefined && <Line data={chartData} />}
        </>
    );
}
