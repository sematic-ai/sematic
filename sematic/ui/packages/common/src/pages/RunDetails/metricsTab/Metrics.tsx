import { Alert } from "@mui/material";
import {
    CategoryScale,
    ChartData,
    Chart as ChartJS,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    Title,
    Tooltip,
} from "chart.js";
import { useEffect, useMemo, useRef } from "react";
import { Line } from "react-chartjs-2";
import useCounter from "react-use/lib/useCounter";
import { MetricPoint } from "src/Models";
import { MetricsFilter, useMetrics } from "src/hooks/metricsHooks";

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

    const dataStore = useRef({
        labels: [] as string[],
        labelSet: new Set<string>(),
        data: [] as number[],
    });

    const [dataVersion, { inc: bumpDataVersion }] = useCounter();

    useEffect(() => {
        if (payload === undefined) return;
        const labels: string[] = [];
        const data: number[] = [];
        let existingDataReadCursor = 0;
        payload.content.series.forEach((item) => {
            let label = (new Date(item[1][0] * 1000)).toLocaleString();
            labels.push(label.toLocaleString());

            if (dataStore.current.labelSet.has(label)) {
                data.push(dataStore.current.data[existingDataReadCursor++]);
            } else {
                data.push(item[0]);
                dataStore.current.labelSet.add(label);
            }
        });


        dataStore.current.labels = labels;
        dataStore.current.data = data;

        bumpDataVersion();
    }, [payload, bumpDataVersion]);

    const cData: ChartData<"line", number[], string> = useMemo(() => ({
        labels: dataStore.current.labels,
        datasets: [
            {
                label: metricsFilter.metricName,
                data: dataStore.current.data,
                backgroundColor: color,
                borderColor: color,
            },
        ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }), [dataVersion, color, metricsFilter.metricName]);

    return (
        <>
            {error && (
                <Alert severity="error">
                    Unable to load metric: {error.message}
                </Alert>
            )}
            {error === undefined && <Line data={cData} options={{
                animation: {
                    duration: 2000
                }
            }} />}
        </>
    );
}
