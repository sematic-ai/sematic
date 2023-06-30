import { useCallback, useState, useMemo } from "react";
import TwoColumns from "src/layout/TwoColumns";
import RunList from "src/pages/RunSearch/RunList";
import SearchFilters from "src/pages/RunSearch/SearchFilters";
import { AllFilters } from "src/pages/RunTableCommon/filters";

const RunSearch = () => {
    const [filters, setFilters] = useState<AllFilters>({});

    const onFiltersChanged = useCallback((filters: AllFilters) => {
        setFilters(filters);
    }, []);

    const onRenderLeft = useCallback(() => {
        return <SearchFilters onFiltersChanged={onFiltersChanged} />;
    }, [onFiltersChanged]);

    const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);

    const onRenderRight = useCallback(() => {
        return <RunList key={filtersKey} filters={filters} />;
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filtersKey]);


    return <TwoColumns onRenderLeft={onRenderLeft} onRenderRight={onRenderRight} />;
}

export default RunSearch;
