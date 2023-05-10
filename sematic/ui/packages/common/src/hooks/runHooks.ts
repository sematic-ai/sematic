import { Filter, RunListPayload } from "@sematic/common/src/ApiContracts";
import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import { useMemo, useState, useCallback, useEffect, useRef } from "react";
import useAsyncFn from "react-use/lib/useAsyncFn";
import { Run } from "src/Models";

export type QueryParams = {[key: string]: string};
export const PAGE_SIZE = 25;

const defaultQueryParams = {};
export function useFetchRunsFn(runFilters: Filter | undefined = undefined,
    otherQueryParams: QueryParams = defaultQueryParams) {
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
        const payload: RunListPayload = await response.json();
        setIsLoaded(true);
        return payload;
    }, [queryParams, fetch]);

    const {loading: isLoading, error, value: runs} = state;

    return {isLoaded, isLoading, error, runs: runs as RunListPayload, load};
}

export function useFetchRuns(runFilters: Filter | undefined = undefined,
    otherQueryParams: {[key: string]: string} = defaultQueryParams) {
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

export function useRunsPagination(runFilters: Filter | undefined = undefined,
    otherQueryParams: {[key: string]: string} = defaultQueryParams) {
    
    const [page, setPage] = useState(0);

    const [currentPageData, setCurrentPageData] = useState<Array<Run>>([]);

    const pagesCache = useRef<Array<RunListPayload>>([]);

    const queryParams = useMemo(() => {
        return {
            ...otherQueryParams,
            limit: PAGE_SIZE.toString()
        }
    }, [otherQueryParams]);

    const {isLoaded, isLoading, error, load} = useFetchRunsFn(runFilters, queryParams);

    // Previous page should always be available in cache
    const previousPage = useCallback(async () => {
        const newPage = page - 1;
        setCurrentPageData(pagesCache.current[newPage].content);
        setPage(newPage);
    }, [page]);

    const nextPage = useCallback(async () => {
        const newPage = page + 1;
        const cacheSize = pagesCache.current.length;

        if (newPage >= cacheSize) {
            const cursor = pagesCache.current[cacheSize - 1].next_cursor!;
            const payload = await load({cursor});
            pagesCache.current.push(payload);
        } 

        setCurrentPageData(pagesCache.current[newPage].content);
        setPage(newPage);
    }, [page, load]);

    const totalRuns = useMemo(() => {
        if (isLoaded) {
            return pagesCache.current[0].after_cursor_count;
        }
    }, [isLoaded]);

    const totalPages = useMemo(() => Math.ceil((totalRuns || 0) / PAGE_SIZE), [totalRuns]);
    
    useEffect(() => {
        (async () => {
            const payload = await load();
            pagesCache.current.push(payload);
            setCurrentPageData(payload.content);
        })();        
    }, [load]);

    return { previousPage, nextPage, page, totalPages, isLoaded, isLoading, error, 
        runs: currentPageData, totalRuns };
}

export function getRunUrlPattern(runID: string) {
    return `/runs/${runID}`;
}
