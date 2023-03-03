import { RESET } from "jotai/utils";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
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
export const selectedPanelHashAtom = atomWithHashCustomSerialization('panel', '')

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
    const { hash } = useLocation();

    return useCallback((requestedRootId: string, replace: boolean = false,
        hashOverrideValues: Record<string, string | Symbol> | undefined = undefined) => {

        let newHashValue = hash.replace(/^#/, '');

        if (hashOverrideValues) {
            newHashValue = updateHash(hash, hashOverrideValues);
        }

        navigate({
            pathname: getRunUrlPattern(requestedRootId),
            hash: newHashValue
        }, {
            replace
        });
    }, [hash, navigate]);
}

export function useHashUpdater() {
    const { hash } = useLocation();
    const navigate = useNavigate();

    return useCallback((
        hashOverrideValues: Record<string, string | Symbol>, replace: boolean = false) => {
        let newHashValue = hash.replace(/^#/, '');

        newHashValue = updateHash(newHashValue, hashOverrideValues);

        navigate({
            hash: newHashValue
        }, {
            replace
        });
    }, [hash, navigate]);
}

function updateHash(currentHash: string, hashOverrideValues: Record<string, string | Symbol>) {
    let newHashValue = currentHash.replace(/^#/, '');

    const searchParams = new URLSearchParams(newHashValue);
    for (const key of Object.keys(hashOverrideValues)) {
        const value = hashOverrideValues[key]; 
        if (value === RESET) {
            searchParams.delete(key);
        } else {
            searchParams.set(key, value as string);
        }
    }
    return searchParams.toString();
}
