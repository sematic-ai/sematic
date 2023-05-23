import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";
import { BasicMetricsPayload } from "@sematic/common/src/ApiContracts";
import { useMemo } from "react";
import { durationSecondsToString } from "@sematic/common/src/utils/datetime";

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
