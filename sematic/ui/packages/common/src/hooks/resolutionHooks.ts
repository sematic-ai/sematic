import useAsync from "react-use/lib/useAsync";
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
