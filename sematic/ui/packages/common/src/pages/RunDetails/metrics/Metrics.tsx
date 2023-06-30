import { MetricsFilter, useMetrics } from "src/hooks/metricsHooks";
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
import { MetricPoint } from "src/Models";

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
    latestMetricPoints?: MetricPoint[];
}) {
    const { metricsFilter, color, latestMetricPoints } = props;
    const [payload, , error] = useMetrics(metricsFilter, latestMetricPoints);

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
        let labels: string[] = [];
        let data: number[] = [];
        payload.content.series.forEach((item) => {
            let label = (new Date(item[1][0] * 1000)).toLocaleString();
            labels.push(label.toLocaleString());
            data.push(item[0]);
        });

        const cData: ChartData<"line", number[], string> = {
            labels: labels,
            datasets: [
                {
                    label: metricsFilter.metricName,
                    data: data,
                    backgroundColor: color,
                    borderColor: color,
                },
            ],
        };
        setChartData(cData);
    }, [payload, color, metricsFilter.metricName, setChartData]);

    return (
        <>
            {error && (
                <Alert severity="error">
                    Unable to load metric: {error.message}
                </Alert>
            )}
            {error === undefined && <Line data={chartData} options={{animation: false}}/>}
        </>
    );
}
