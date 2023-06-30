import Alert from "@mui/material/Alert";
import noop from "lodash/noop";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Run } from "src/Models";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import RootRunContext from "src/context/RootRunContext";
import RunDetailsSelectionContext from "src/context/RunDetailsSelectionContext";
import usePipelineSocketMonitor from "src/hooks/pipelineSocketMonitorHooks";
import { useFetchRuns } from "src/hooks/runHooks";
import ThreeColumns from "src/layout/ThreeColumns";
import PipelineInfoPane from "src/pages/PipelineRuns/PipelineInfoPane";
import PipelineRunsList from "src/pages/PipelineRuns/PipelineRunsList";
import NotesPane from "src/pages/RunDetails/NotesPane";
import { AllFilters } from "src/pages/RunTableCommon/filters";

interface PipelineRunsProps {
    rootRun: Run;
}

const PipelineRuns = (props: PipelineRunsProps) => {
    const { rootRun } = props;

    const [filters, setFilters] = useState<AllFilters>({});

    const onFiltersChanged = useCallback((filters: AllFilters) => {
        setFilters(filters);
    }, []);

    const onRenderLeft = useCallback(() => {
        return <PipelineInfoPane onFiltersChanged={onFiltersChanged} />;
    }, [onFiltersChanged]);

    const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);

    const onRenderCenter = useCallback(() => {
        return <PipelineRunsList key={filtersKey} filters={filters} />;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filtersKey]);

    const onRenderRight = useCallback(() => {
        return <NotesPane />;
    }, []);

    const rootRunContextValue = useMemo(() => ({
        rootRun,
        resolution: undefined,
        graph: undefined,
        isResolutionLoading: false,
        isGraphLoading: false,
    }), [rootRun]);

    const runSelectionContextValue = useMemo(() => ({
        selectedRun: rootRun,
        setSelectedRunId: noop,
        selectedPanel: undefined,
        setSelectedPanel: noop
    }), [rootRun]);

    usePipelineSocketMonitor(rootRun.function_path);

    return <RootRunContext.Provider value={rootRunContextValue}>
        <RunDetailsSelectionContext.Provider value={runSelectionContextValue}>
            <ThreeColumns onRenderLeft={onRenderLeft} onRenderCenter={onRenderCenter}
                onRenderRight={onRenderRight} />
        </RunDetailsSelectionContext.Provider>
    </RootRunContext.Provider>;
}

function PipelineRunsFilter() {
    const { functionPath } = useParams();

    if (!functionPath) {
        throw new Error(
            "`functionPath` is expected from the URL. This component might be used with the wrong route.");
    }

    const runFilters = useMemo(
        () => ({
            AND: [{ function_path: { eq: functionPath } }, { parent_id: { eq: null } }],
        }),
        [functionPath]
    );

    const otherQueryParams = useMemo(
        () => ({
            limit: "1",
        }), []);

    const { isLoading, runs } = useFetchRuns(runFilters, otherQueryParams);

    const { setIsLoading } = useContext(LayoutServiceContext);

    useEffect(() => {
        setIsLoading(isLoading)
    }, [setIsLoading, isLoading]);

    return useMemo(() => {
        if (!isLoading && runs !== undefined) {
            if (runs.length === 0) {
                return <Alert severity="error" >
                    {`No runs found matching ${functionPath}`}
                </Alert>;
            }

            return <PipelineRuns rootRun={runs[0]} />;
        }
        return <></>
    }, [isLoading, functionPath, runs]);
}

export default PipelineRunsFilter;
