import { Filter, RunListPayload, RunViewPayload } from "@sematic/common/src/ApiContracts";
import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import { atomWithHashCustomSerialization, updateHash } from "@sematic/common/src/utils/url";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import useAsyncFn from "react-use/lib/useAsyncFn";
import { Run } from "src/Models";
import { AllFilters, FilterType, StatusFilters, convertMiscellaneousFilterToRunFilters, convertOwnersFilterToRunFilters, convertStatusFilterToRunFilters, convertTagsFilterToRunFilters } from "src/pages/RunTableCommon/filters";
import useAsync from "react-use/lib/useAsync";

export const selectedRunHashAtom = atomWithHashCustomSerialization("run", "")
export const selectedPanelAtom = atomWithHashCustomSerialization("panel", "")
export const selectedTabHashAtom = atomWithHashCustomSerialization("tab", "")
export const searchAtom = atomWithHashCustomSerialization("search", "");

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

export function useFetchLatestRun(functionPath: string) {
    const runFilters = useMemo(
        () => ({
            AND: [
                { parent_id: { eq: null } },
                { function_path: { eq: functionPath } },
            ],
        }),
        [functionPath]
    );

    const otherQueryParams = useMemo(
        () => ({
            limit: "1",
        }), []
    );

    const {load} = useFetchRunsFn(runFilters, otherQueryParams);

    const getRun = useCallback(async () => {
        const payload = await load();
        return payload.content[0];
    }, [load]);
    return getRun;
}

export function useFiltersConverter(filters: AllFilters | null) {
    const runFilter = useMemo(() => {
        const conditions = [];

        if (!filters) {
            return undefined;
        }

        if (filters[FilterType.TAGS]) {
            const statusFilters = convertTagsFilterToRunFilters(filters[FilterType.TAGS] as StatusFilters[]);
            if (statusFilters) {
                statusFilters.forEach(filter => conditions.push(filter));
            }
        }

        if (filters[FilterType.STATUS]) {
            const statusFilters = convertStatusFilterToRunFilters(filters[FilterType.STATUS] as StatusFilters[]);
            if (statusFilters) {
                conditions.push(statusFilters);
            }
        }

        if (filters[FilterType.OWNER]) {
            const ownersFilters = convertOwnersFilterToRunFilters(filters[FilterType.OWNER]!);
            if (ownersFilters) {
                conditions.push(ownersFilters);
            }
        }

        if (filters[FilterType.OTHER]) {
            const miscellaneousFilters = convertMiscellaneousFilterToRunFilters(filters[FilterType.OTHER]!);
            if (miscellaneousFilters) {
                conditions.push(miscellaneousFilters);
            }
        }

        if (conditions.length > 1) {
            return {
                "AND": conditions
            }
        }

        if (conditions.length === 0) {
            return undefined;
        }
        return conditions[0];
    }, [filters]);

    const queryParams = useMemo(() => {
        if (!filters) {
            return undefined;
        }

        if (filters[FilterType.SEARCH]) {
            return {
                "search": filters[FilterType.SEARCH]![0]
            };
        }
    }, [filters]);

    return {runFilter, queryParams};
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

    const totalPages = useMemo(() => Math.ceil((totalRuns || 0) / PAGE_SIZE) || 1, [totalRuns]);
    
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

export function getPipelineRunsPattern(functionPath: string) {
    return `/pipeline/${functionPath}`;
}

export function useRunNavigation() {
    const navigate = useNavigate();
    const { hash } = useLocation();

    return useCallback((requestedRootId: string, replace: boolean = false,
        hashOverrideValues: Record<string, string | Symbol> | undefined = undefined) => {

        let newHashValue = hash.replace(/^#/, "");

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

export function useFetchRun(runID: string): [
    Run | undefined, boolean, Error | undefined
] {
    const {fetch} = useHttpClient();

    const {value, loading, error} = useAsync(async () => {
        const response = await fetch({
            url: `/api/v1/runs/${runID}`
        });
        return (await response.json() as RunViewPayload).content
    }, [runID]);
    
    return [value, loading, error];
}

