import { useHttpClient } from "src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";
import { BasicMetricsPayload } from "src/Payloads";

export default function useBasicMetrics({ runId }: {runId?: string}): [
  BasicMetricsPayload | undefined,
  boolean,
  Error | undefined
] {
  const { fetch } = useHttpClient();

  const { value, loading, error } = useAsync(async () => {
    const response  = await fetch({url: `/api/v1/runs/${runId}/metrics`});
    return ((await response.json()) as BasicMetricsPayload);
  }, [runId]);

    return [value, loading, error];
}
