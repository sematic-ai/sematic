import { useCallback, useState, useMemo } from "react";
import TwoColumns from "src/layout/TwoColumns";
import { AllFilters } from "src/pages/RunTableCommon/filters";
import PipelineListPresentation from "src/pages/PipelineList/PipelineList";
import SearchFilters from "src/pages/PipelineList/SearchFilters";

function PipelineList() {
    const [filters, setFilters] = useState<AllFilters>({});

    const onFiltersChanged = useCallback((filters: AllFilters) => {
        setFilters(filters);
    }, []);

    const onRenderLeft = useCallback(() => {
        return <SearchFilters onFiltersChanged={onFiltersChanged} />;
    }, [onFiltersChanged]);

    const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);

    const onRenderRight = useCallback(() => {
        return <PipelineListPresentation key={filtersKey} filters={filters} />;
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filtersKey]);


    return <TwoColumns onRenderLeft={onRenderLeft} onRenderRight={onRenderRight} />;
}

export default PipelineList;