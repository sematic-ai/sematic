import { useHttpClient } from "src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";
import { AggregatedMetricsPayload, BasicMetricsPayload } from "src/Payloads";
import { MetricPoint } from "@sematic/common/lib/src/Models";
import { useCallback } from "react";

export default function useBasicMetrics({
  runId,
}: {
  runId?: string;
}): [BasicMetricsPayload | undefined, boolean, Error | undefined] {
  const { fetch } = useHttpClient();

  const { value, loading, error } = useAsync(async () => {
    const response = await fetch({ url: `/api/v1/runs/${runId}/metrics` });
    return (await response.json()) as BasicMetricsPayload;
  }, [runId]);

  return [value, loading, error];
}

export type MetricsFilter = {
  metricName: string;
  labels: { [k: string]: any };
  groupBys: string[];
};

export function useAggregatedMetrics(
  metricsFilter: MetricsFilter,
  broadcastEvent?: MetricPoint[]
): [AggregatedMetricsPayload | undefined, boolean, Error | undefined] {
  const { fetch } = useHttpClient();

  const eventMatchesFilter = useCallback(
    () =>
      broadcastEvent &&
      !!broadcastEvent.find(
        (metricPoint) =>
          metricPoint.name === metricsFilter.metricName &&
          [
            "run_id",
            "calculator_path",
            "root_id",
            "root_calculator_path",
          ].every(
            (key) =>
              // Filter does not filter on key
              metricsFilter.labels[key] === undefined ||
              // or it does and the value matches
              metricsFilter.labels[key] === metricPoint.labels[key]
          )
      ),
    [metricsFilter, broadcastEvent]
  );

  const { value, loading, error } = useAsync(async () => {
    console.log("useAsync", broadcastEvent);
    if (broadcastEvent && !eventMatchesFilter()) return;
    const labelsJSON = JSON.stringify(metricsFilter.labels);
    const groupBysStr = metricsFilter.groupBys.join(",");
    const response = await fetch({
      url: `/api/v1/metrics/${metricsFilter.metricName}?labels=${labelsJSON}&group_by=${groupBysStr}`,
    });
    return (await response.json()) as AggregatedMetricsPayload;
  }, [broadcastEvent]);

  return [value, loading, error];
}

export function useListMetrics(labels: {
  [k: string]: any;
}): [{ content: string[] } | undefined, boolean, Error | undefined] {
  const { fetch } = useHttpClient();

  const { value, loading, error } = useAsync(async () => {
    const labelsJSON = JSON.stringify(labels);
    const response = await fetch({
      url: `/api/v1/metrics?labels=${labelsJSON}`,
    });
    return (await response.json()) as { content: string[] };
  }, [labels]);

  return [value, loading, error];
}
