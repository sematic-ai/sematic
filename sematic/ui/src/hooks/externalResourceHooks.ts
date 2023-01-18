import { useEffect, useRef } from "react";
import useAsyncRetry from "react-use/lib/useAsyncRetry";
import { ExternalResource, ExternalResourceState, Run } from "../Models";
import { useHttpClient } from "./httpHooks";

export const TERMINATE_STATE: ExternalResourceState = 'DEACTIVATED';
const PULL_EXTERNAL_RESOURCE_INTERVAL = 1000;

export function useExternalResource(run: Run) {
    const {fetch} = useHttpClient();

    const {value, loading, retry, error} = useAsyncRetry(async ()=> {
        const response = await fetch({
            url: `/api/v1/runs/${run.id}/external_resources`
        });

        if (!response['content']) {
            throw Error('external_resources response is not in the correct format.')
        }

        return response['content'] as Array<ExternalResource>
    }, [fetch, run]);

    const timerHandler = useRef<number>();
    useEffect(() => {
        if (!loading && !!value) {
            if (value.length === 0 || value[0].resource_state !== TERMINATE_STATE) {
                timerHandler.current = window.setTimeout(retry, PULL_EXTERNAL_RESOURCE_INTERVAL);
            }
        }

        return () => {
            // clean up
            if (timerHandler.current) {
                clearTimeout(timerHandler.current);
            }
        }
    }, [timerHandler, loading, value, retry]);

    return {value, loading, error};
}
