import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAsyncFn } from "react-use";
import { Filter, RunListPayload } from "../Payloads";
import { useHttpClient } from "./httpHooks";

export type QueryParams = {[key: string]: string};

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

export function getPipelineUrlPattern(pipelinePath: string, requestedRootId: string) {
    return `/pipelines/${pipelinePath}/${requestedRootId}`;
}

export function usePipelineNavigation(pipelinePath: string) {
    const navigate = useNavigate();
    const { rootId } = useParams();

    return useCallback((requestedRootId: string, replace: boolean = false) => {
        if ( rootId === requestedRootId ) {
            return
        }

        navigate(getPipelineUrlPattern(pipelinePath, requestedRootId), {
            replace
        });
    }, [pipelinePath, rootId, navigate]);
}