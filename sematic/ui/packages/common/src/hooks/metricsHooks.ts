import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";
import { BasicMetricsPayload, MetricsPayload } from "@sematic/common/src/ApiContracts";
import { useMemo } from "react";
import { durationSecondsToString } from "@sematic/common/src/utils/datetime";
import { MetricPoint } from "src/Models";

export function runSuccessRate(
    countByState: { [k: string]: number },
): string {
    const numeratorStates = ["RESOLVED"];
    const denominatorStates = ["RESOLVED", "FAILED", "NESTED_FAILED"];

    const countForStates = (states: string[]) =>
        states.reduce(
            (sum: number, state: string) => (sum += countByState[state] || 0),
            0
        );

    const percentRate =
        (countForStates(numeratorStates) /
            (countForStates(denominatorStates) || 1)) *
        100;

    return `${Math.floor(percentRate)}%`;
}

export function runAvgRunTime(
    avgRuntimeChildren: { [k: string]: number },
    functionPath: string
): string {
    return durationSecondsToString(avgRuntimeChildren[functionPath] || 0);
}

interface useBasicMetricsResult {
    payload: BasicMetricsPayload | undefined;
    loading: boolean;
    error: Error | undefined;
    totalCount: number | undefined;
    successRate: string;
    avgRuntime: string;
}

export default function useBasicMetrics({ runId, rootFunctionPath }: {
    runId?: string,
    rootFunctionPath: string,
}): useBasicMetricsResult {
    const { fetch } = useHttpClient();

    const { value, loading, error } = useAsync(async () => {
        const response = await fetch({ url: `/api/v1/runs/${runId}/metrics` });
        return ((await response.json()) as BasicMetricsPayload);
    }, [runId]);

    const totalCount = useMemo(() => value && value.content.total_count, [value]);

    const successRate = useMemo(
        () =>
            value ? runSuccessRate(value.content.count_by_state) : "0%",
        [value]
    );

    const avgRuntime = useMemo(
        () =>
            value
                ? runAvgRunTime(value.content.avg_runtime_children, rootFunctionPath)
                : "0s",
        [value, rootFunctionPath]
    );

    return { payload: value, loading, error, totalCount, successRate, avgRuntime };
}

export type MetricsFilter = {
    metricName: string;
    labels: { [k: string]: any };
    groupBys: string[];
};

function eventMatchesFilter(metricsFilter: MetricsFilter, latestMetricPoints?: MetricPoint[]) {
    return latestMetricPoints &&
        !!latestMetricPoints.find(
            (metricPoint) =>
                metricPoint.name === metricsFilter.metricName &&
                [
                    "run_id",
                    "function_path",
                    "root_id",
                    "root_function_path",
                ].every(
                    (key) =>
                        // Filter does not filter on key
                        metricsFilter.labels[key] === undefined ||
                        // or it does and the value matches
                        metricsFilter.labels[key] ===
                            metricPoint.labels[key]
                )
        )
};

export function useMetrics(
    metricsFilter: MetricsFilter,
    latestMetricPoints?: MetricPoint[]
): [MetricsPayload | undefined, boolean, Error | undefined] {
    const { fetch } = useHttpClient();

    const { value, loading, error } = useAsync(async () => {
        if (latestMetricPoints && !eventMatchesFilter(metricsFilter, latestMetricPoints)) return;
        const labelsJSON = JSON.stringify(metricsFilter.labels);
        const groupBysStr = metricsFilter.groupBys.join(",");
        const response = await fetch({
            url: `/api/v1/metrics/${metricsFilter.metricName}?labels=${labelsJSON}&group_by=${groupBysStr}&rollup=auto`,
        });
        return (await response.json()) as MetricsPayload;
    }, [latestMetricPoints, metricsFilter, eventMatchesFilter]);

    return [value, loading, error];
}

export function useListMetrics(labels: {
    [k: string]: any;
}, broadcastEvent?: MetricPoint[]): [{ content: string[] } | undefined, boolean, Error | undefined] {
    const { fetch } = useHttpClient();

    const { value, loading, error } = useAsync(async () => {
        const labelsJSON = JSON.stringify(labels);
        const response = await fetch({
            url: `/api/v1/metrics?labels=${labelsJSON}`,
        });
        return (await response.json()) as { content: string[] };
    }, [labels, broadcastEvent]);

    return [value, loading, error];
}
