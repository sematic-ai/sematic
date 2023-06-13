import { MetricsFilter, useMetrics } from "@sematic/common/src/hooks/metricsHooks";
import { Alert} from "@mui/material";
import { useMemo, useState } from "react";
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

    const [chartData, setChartData] = useState<ChartData<"line", number[], string>>({
        labels: [],
        datasets: [
            {
                label: metricsFilter.metricName,
                data: [],
                backgroundColor: color,
                borderColor: color,
            },
        ],
    });


    useMemo(() => {
        if (payload === undefined) return;
        payload.content.series.forEach((item) => {
            let label = (new Date(item[1][0] * 1000)).toLocaleString();
            if (!chartData.labels?.includes(label)) {
                chartData.labels?.push(label);
                chartData.datasets[0].data.push(item[0]);
            }
        });

    }, [payload, color, metricsFilter.metricName, chartData]);

    return (
        <>
            {error && (
                <Alert severity="error">
                    Unable to load metric: {error.message}
                </Alert>
            )}
            {error === undefined && <Line data={chartData} />}
        </>
    );
}
