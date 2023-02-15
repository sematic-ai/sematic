import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import useAsync from "react-use/lib/useAsync";
import useAsyncFn from "react-use/lib/useAsyncFn";
import { Resolution, Run } from "../Models";
import { Filter, ResolutionPayload, RunListPayload, RunViewPayload } from "../Payloads";
import PipelinePanelsContext from "../pipelines/PipelinePanelsContext";
import PipelineRunViewContext from "../pipelines/PipelineRunViewContext";
import { useHttpClient } from "./httpHooks";
import { atomWithHashCustomSerialization } from "../utils";

export type QueryParams = {[key: string]: string};

export const selectedRunHashAtom = atomWithHashCustomSerialization('run', '')
export const selectedTabHashAtom = atomWithHashCustomSerialization('tab', '')

export function usePipelineRunContext() {
    const contextValue = useContext(PipelineRunViewContext);

    if (!contextValue) {
        throw new Error('usePipelineRunContext() should be called under a provider.')
    }

    return contextValue;
}

export function usePipelinePanelsContext() {
    const contextValue = useContext(PipelinePanelsContext);

    if (!contextValue) {
        throw new Error('usePipelinePanelsContext() should be called under a provider.')
    }

    return contextValue;
}

export function useFetchRunsFn(runFilters: Filter | undefined = undefined,
    otherQueryParams: QueryParams = {}) {
    const [isLoaded, setIsLoaded] = useState(false);

    const queryParams = useMemo(() => {
        let params = {...otherQueryParams};
        if (!!runFilters) {
            params.filters = JSON.stringify(runFilters)
        }
        return params;
    }, [otherQueryParams, runFilters]);

    const {fetch} = useHttpClient();

    const [state, load] = useAsyncFn(async (overrideQueryParams: QueryParams = {}) => {
        const finalQueryParams = {
            ...queryParams,
            ...overrideQueryParams
        }
        const qString = (new URLSearchParams(finalQueryParams)).toString();
        const response = await fetch({
            url: `/api/v1/runs?${qString}`
        });
        setIsLoaded(true);
        return response as RunListPayload;
    }, [queryParams, fetch]);

    const {loading: isLoading, error, value: runs} = state;

    return {isLoaded, isLoading, error, runs: runs as RunListPayload, load};
}

export function useFetchRuns(runFilters: Filter | undefined = undefined,
    otherQueryParams: {[key: string]: string} = {}) {
    const {isLoaded, isLoading, error, runs, load} = useFetchRunsFn(runFilters, otherQueryParams);

    const reloadRuns = useCallback(async () => {
        const payload = await load();
        return payload.content;
    }, [load]);

    useEffect(() => {
        load();
    }, [load])

    return {isLoaded, isLoading, error, runs: runs?.content, reloadRuns};
}

export function useFetchRun(runID: string): [
    Run | undefined, boolean, Error | undefined
] {
    const {fetch} = useHttpClient();

    const {value, loading, error} = useAsync(async () => {
        const response: RunViewPayload = await fetch({
            url: `/api/v1/runs/${runID}`
        });
        return response.content
    }, [runID]);
    
    return [value, loading, error];
}

export function useFetchResolution(resolutionId: string): [
    Resolution | undefined, boolean, Error | undefined
] {
    const {fetch} = useHttpClient();

    const {value, loading, error} = useAsync(async () => {
        const response: ResolutionPayload = await fetch({
            url: `/api/v1/resolutions/${resolutionId}`
        });
        return response.content;
    }, [resolutionId]);
    
    return [value, loading, error];
}

export function getRunUrlPattern(requestedRootId: string) {
    return `/runs/${requestedRootId}`;
}

export function useRunNavigation() {
    const navigate = useNavigate();
    const { rootId } = useParams();
    const { hash } = useLocation();

    return useCallback((requestedRootId: string, replace: boolean = false,
        hashOverrideValues: Record<string, string> | undefined = undefined) => {
        if ( rootId === requestedRootId ) {
            return
        }

        let newHashValue = hash;

        if (hashOverrideValues) {
            const searchParams = new URLSearchParams(hash);
            for (const key of Object.keys(hashOverrideValues)) {
                searchParams.set(key, hashOverrideValues[key]);
            }
            newHashValue = searchParams.toString();
        }

        navigate({
            pathname: getRunUrlPattern(requestedRootId),
            hash: newHashValue
        }, {
            replace
        });
    }, [rootId, hash, navigate]);
}
