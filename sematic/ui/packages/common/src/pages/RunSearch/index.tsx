import { useCallback, useState, useMemo } from "react";
import { useLocation } from "react-router-dom";
import TwoColumns from "src/layout/TwoColumns";
import RunList from "src/pages/RunSearch/RunList";
import SearchFilters from "src/pages/RunSearch/SearchFilters";
import { AllFilters, FilterType } from "src/pages/RunSearch/filters/common";

const RunSearch = () => {
    const location = useLocation();
    const params = new URLSearchParams(location.hash.replace("#", "?"));
    const defaultSearchString = !!params.get("search") ? params.get("search") as string : undefined;
    const defaultFilters: AllFilters = useMemo(() => {
        const filters: AllFilters = {}
        if(!!defaultSearchString){
            filters[FilterType.SEARCH] = [defaultSearchString];
        }
        return filters;
    }, [defaultSearchString]);
    const [filters, setFilters] = useState<AllFilters>(defaultFilters);

    const onFiltersChanged = useCallback((filters: AllFilters) => {
        setFilters(filters);
    }, []);

    const onRenderLeft = useCallback(() => {
        return <SearchFilters onFiltersChanged={onFiltersChanged} defaultFilters={defaultFilters} />;
    }, [onFiltersChanged, defaultFilters]);

    const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);

    const onRenderRight = useCallback(() => {
        return <RunList key={filtersKey} filters={filters} />;
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filtersKey]);


    return <TwoColumns onRenderLeft={onRenderLeft} onRenderRight={onRenderRight} />;
}

export default RunSearch;
