import { useCallback } from 'react';
import TwoColumns from "src/layout/TwoColumns";
import RunList from 'src/pages/RunSearch/RunList';
import SearchFilters from 'src/pages/RunSearch/SearchFilters';

const RunSearch = () => {

    const onRenderLeft = useCallback(() => {
        return <SearchFilters />;
    }, []);

    const onRenderRight = useCallback(() => {
        return <RunList />;
    }, []);

    return <TwoColumns onRenderLeft={onRenderLeft} onRenderRight={onRenderRight} />;
}

export default RunSearch;
