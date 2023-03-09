import { useHttpClient } from "src/hooks/httpHooks";
import useAsyncRetry from "react-use/lib/useAsyncRetry";
import { CompactMetricsPayload } from "src/Payloads";
import { useCallback, useEffect, useRef } from "react";
import { metricsSocket } from "src/sockets";

export default function useMetrics({
  runId, calculatorPath
}: {runId?: string, calculatorPath?: string}): [
  CompactMetricsPayload | undefined,
  boolean,
  Error | undefined
] {
  const { fetch } = useHttpClient();

  const { value, loading, error, retry } = useAsyncRetry(async () => {
    let url = "/api/v1/metrics?";
    if (runId !== undefined) {
      url += `run_id=${runId}`;
    }
    if (calculatorPath !== undefined) {
      url += `calculator_path=${calculatorPath}`
    }
    const response  = await fetch({url: url + "&format=compact"});
    return ((await response.json()) as CompactMetricsPayload);
  }, [runId]);

  const metricsSocketUpdateHandler = useCallback(async (args: {
    run_id?: string, calculator_path?: string
  }) => {
    if (
      (runId !== undefined && args.run_id === runId) ||
      (calculatorPath !== undefined && args.calculator_path === calculatorPath)
    ) {
      if (!loading) {
        retry();
      }
    }
  }, [runId, loading, retry]); 

  const metricsSocketCallbackRef = useRef<(args: {
    run_id?: string, calculator_path?: string
  })=> Promise<void>>(
    async() => {}
  );

  const onNewMetrics = useCallback((args: { run_id: string, calculator_path?: string }) => {
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

    return [value, loading, error];
}