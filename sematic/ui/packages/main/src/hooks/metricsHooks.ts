import { useHttpClient } from "src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";
import { AggregatedMetricsPayload, BasicMetricsPayload } from "src/Payloads";

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
  metricsFilter: MetricsFilter
): [AggregatedMetricsPayload | undefined, boolean, Error | undefined] {
  const { fetch } = useHttpClient();

  const { value, loading, error } = useAsync(async () => {
    const labelsJSON = JSON.stringify(metricsFilter.labels);
    const groupBysStr = metricsFilter.groupBys.join(",");
    const response = await fetch({
      url: `/api/v1/metrics/${metricsFilter.metricName}?labels=${labelsJSON}&group_by=${groupBysStr}`,
    });
    return (await response.json()) as AggregatedMetricsPayload;
  }, []);

  return [value, loading, error];
}
