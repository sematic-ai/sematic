import { useAtom } from "jotai";
import { RESET } from "jotai/utils";
import isEmpty from "lodash/isEmpty";
import { useCallback, useEffect, useMemo, useState } from "react";
import useLatest from "react-use/lib/useLatest";
import { searchAtom } from "src/hooks/runHooks";
import TwoColumns from "src/layout/TwoColumns";
import RunList from "src/pages/RunSearch/RunList";
import SearchFilters from "src/pages/RunSearch/SearchFilters";
import { AllFilters, FilterType } from "src/pages/RunTableCommon/filters";

const RunSearch = () => {
    const [filters, setFilters] = useState<AllFilters | null>(null);

    const latestFilters = useLatest(filters);
    const [, setSearchHash] = useAtom(searchAtom);


    const onFiltersChanged = useCallback((filters: AllFilters) => {
        setFilters(filters);
        if (!isEmpty(filters[FilterType.SEARCH])) {
            setSearchHash(filters[FilterType.SEARCH]![0]);
        }else {
            setSearchHash(RESET);
        }
        (latestFilters.current as any) = filters;
    }, [latestFilters, setSearchHash]);

    const onRenderLeft = useCallback(() => {
        return <SearchFilters onFiltersChanged={onFiltersChanged} />;
    }, [onFiltersChanged]);

    const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);

    const onRenderRight = useCallback(() => {
        if (filters === null) {
            return null;
        }
        return <RunList key={filtersKey} filters={filters} />;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filtersKey]);

    useEffect(() => {
        if (latestFilters.current === null) {
            setFilters({});
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return <TwoColumns onRenderLeft={onRenderLeft} onRenderRight={onRenderRight} />;
}

export default RunSearch;
