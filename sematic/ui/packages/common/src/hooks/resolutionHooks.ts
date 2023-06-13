import useAsync from "react-use/lib/useAsync";
import useAsyncFn from "react-use/lib/useAsyncFn";
import { ResolutionPayload } from "src/ApiContracts";
import { Resolution } from "src/Models";
import { useHttpClient } from "src/hooks/httpHooks";

export function useFetchResolution(resolutionId: string): [
    Resolution | undefined, boolean, Error | undefined
] {
    const {fetch} = useHttpClient();

    const {value, loading, error} = useAsync(async () => {
        const response  = await fetch({
            url: `/api/v1/resolutions/${resolutionId}`
        });
        return ((await response.json()) as ResolutionPayload).content;
    }, [resolutionId]);
    
    return [value, loading, error];
}


export function useRerun(rootRunId?: string, rerunFrom?: string) {
    const { fetch } = useHttpClient();

    return useAsyncFn(async () => {
        return await fetch({
            url: `/api/v1/resolutions/${rootRunId}/rerun`,
            method: "POST",
            body: {
                rerun_from: rerunFrom,
            }
        });
    }, [fetch]);
}

export function useCancelRun(rootRunId: string) {
    const { fetch } = useHttpClient();

    return useAsyncFn(async () => {
        return await fetch({
            url: `/api/v1/resolutions/${rootRunId}/cancel`,
            method: "PUT"
        });
    }, [fetch]);
}
