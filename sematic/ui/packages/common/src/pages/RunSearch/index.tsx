import { useCallback, useEffect, useState, useMemo } from "react";
import TwoColumns from "src/layout/TwoColumns";
import RunList from "src/pages/RunSearch/RunList";
import SearchFilters from "src/pages/RunSearch/SearchFilters";
import { AllFilters } from "src/pages/RunTableCommon/filters";
import useLatest from "react-use/lib/useLatest";

const RunSearch = () => {
    const [filters, setFilters] = useState<AllFilters | null>(null);

    const latestFilters = useLatest(filters);

    const onFiltersChanged = useCallback((filters: AllFilters) => {
        setFilters(filters);
        (latestFilters.current as any) = filters;
    }, [latestFilters]);

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
