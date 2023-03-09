import { useHttpClient } from "src/hooks/httpHooks";
import useAsyncRetry from "react-use/lib/useAsyncRetry";
import { CompactMetricsPayload } from "src/Payloads";
import { useCallback, useEffect, useRef } from "react";
import { metricsSocket } from "src/sockets";

export default function useFetchRunMetrics(runId: string): [
  CompactMetricsPayload | undefined,
  boolean,
  Error | undefined
] {
  const { fetch } = useHttpClient();

  const { value, loading, error, retry } = useAsyncRetry(async () => {
    const response  = await fetch({
        url: `/api/v1/metrics?run_id=${runId}&format=compact`
    });
    console.log(await response.json());
    return ((await response.json()) as CompactMetricsPayload);
  }, [runId]);

  const metricsSocketUpdateHandler = useCallback(async (args: { run_id: string }) => {
    if (args.run_id === runId) {
      if (!loading) {
        retry();
      }
    }
  }, [runId, loading, retry]); 

  const metricsSocketCallbackRef = useRef<(args: { run_id: string })=> Promise<void>>(
    async() => {}
  );

  const onNewMetrics = useCallback((args: { run_id: string }) => {
    metricsSocketCallbackRef.current(args);
  }, [metricsSocketCallbackRef]);

  useEffect(() => {
    metricsSocketCallbackRef.current = metricsSocketUpdateHandler;
  }, [metricsSocketUpdateHandler])

  // Auto manage reloading by hooking up with graphSocket.
  useEffect(() => {
    metricsSocket.removeAllListeners();
    metricsSocket.on("new", onNewMetrics);
    }, [onNewMetrics]);
  console.log(value);
  return [value, loading, error];
}