import { useRefFn } from "@sematic/common/lib/src/utils/hooks";
import { Job } from "@sematic/common/src/Models";
import { useCallback, useEffect } from "react";
import useAsyncFn from "react-use/lib/useAsyncFn";
import useLatest from "react-use/lib/useLatest";
import { RunJobPayload } from "src/Payloads";
import { useHttpClient } from "src/hooks/httpHooks";
import { jobSocket } from "src/sockets";
import { AsyncInvocationQueue } from "src/utils";


export function useRunJobHistory(runId: string) {
    const {fetch} = useHttpClient();

    const [{value, loading, error}, reload] = useAsyncFn(async ()=> {
        const response = await fetch({
            url: `/api/v1/runs/${runId}/jobs`
        });

        const payload: RunJobPayload = await response.json();

        if (!payload['content']) {
            throw Error('jobs response is not in the correct format.')
        }

        return payload['content'] as Array<Job>
    }, [fetch, runId]);

    const latestReload = useLatest(reload);

    const asyncInvocationManager = useRefFn(() => new AsyncInvocationQueue());
    const abortController = useRefFn(() => new AbortController());

    const reloadWithQueue = useCallback(async () => {
        if (abortController.signal.aborted) {
            return;
        }
        const release = await asyncInvocationManager.acquire();
        if (abortController.signal.aborted) {
            return;
        }

        await latestReload.current();
        release();
        //eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const onJobUpdate = useCallback((args: {run_id: string}) => {
        if (args.run_id === runId) {
            reloadWithQueue();
        };
        //eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    
    useEffect(() => {
        latestReload.current();
        jobSocket.on("update", onJobUpdate);

        return () => {
            jobSocket.removeListener("update", onJobUpdate);
            if (!abortController.signal.aborted) {
                abortController.abort();
            }
        }
        //eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);


    return {value, loading, error};
}
