import { useAtom } from "jotai";
import { RESET } from "jotai/utils";
import { useCallback, useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import { Run } from "src/Models";
import RootRunContext from "src/context/RootRunContext";
import RunDetailsSelectionContext from "src/context/RunDetailsSelectionContext";
import { useGraph } from "src/hooks/graphHooks";
import useHashUpdater from "src/hooks/hashHooks";
import { useFetchResolution } from "src/hooks/resolutionHooks";
import { selectedPanelAtom, selectedRunHashAtom } from "src/hooks/runHooks";
import ThreeColumns from "src/layout/ThreeColumns";
import CenterPane from "src/pages/RunDetails/CenterPane";
import MetaDataPane from "src/pages/RunDetails/MetaDataPane";
import NotesPane from "src/pages/RunDetails/NotesPane";
import { createRunRouter } from "src/pages/RunDetails/RunRouter";
import { ExtractContextType } from "src/utils/typings";

interface RunDetailsProps {
    rootRun: Run;
}
const RunDetails = (props: RunDetailsProps) => {
    const { rootRun } = props;

    const [selectedRunIdHash, setSelectedRunId] = useAtom(selectedRunHashAtom);
    const [selectedPanel, setSelectedPanel] = useAtom(selectedPanelAtom);

    const [resolution, isResolutionLoading] = useFetchResolution(rootRun.id!);
    const [graph, isGraphLoading] = useGraph(rootRun.id!);

    const onRenderLeft = useCallback(() => {
        return <MetaDataPane />;
    }, []);

    const onRenderCenter = useCallback(() => {
        return <CenterPane />;
    }, []);

    const onRenderRight = useCallback(() => {
        return <NotesPane />;
    }, []);

    const selectedRun = useMemo(() => {
        let runId = selectedRunIdHash;
        if (!runId) {
            runId = rootRun.id;
        }
        if (!graph) {
            return undefined;
        }
        return graph.runsById.get(runId) || rootRun;
    }, [selectedRunIdHash, graph, rootRun]);

    const rootRunContextValue = useMemo<ExtractContextType<typeof RootRunContext>>(() => ({
        rootRun,
        resolution,
        graph,
        isResolutionLoading,
        isGraphLoading
    }), [rootRun, resolution, graph, isResolutionLoading, isGraphLoading]);

    const runDetailsSelectionContext = useMemo(() => ({
        selectedRun,
        setSelectedRunId,
        selectedPanel,
        setSelectedPanel: setSelectedPanel as (panel: string | typeof RESET | undefined) => void
    }), [selectedRun, selectedPanel, setSelectedRunId, setSelectedPanel]);

    const updateHash = useHashUpdater();

    // Clear the `run` hash when the selected run is not available in the graph or
    // the selected run is the root run.
    useEffect(() => {
        if (selectedRunIdHash === rootRun.id ||
            (!!graph && !graph.runsById.get(selectedRunIdHash))) {
            if (!!selectedRunIdHash) {
                updateHash({ "run": RESET }, true);
            }
            return;
        }
    }, [selectedRunIdHash, graph, rootRun, updateHash]);

    return <RootRunContext.Provider value={rootRunContextValue}>
        <RunDetailsSelectionContext.Provider value={runDetailsSelectionContext}>
            <ThreeColumns onRenderLeft={onRenderLeft} onRenderCenter={onRenderCenter}
                onRenderRight={onRenderRight} />
        </RunDetailsSelectionContext.Provider>
    </RootRunContext.Provider>;
}

const RunDetailsRouter = createRunRouter(RunDetails);

/**
 * This component adds an additional layer to prevent RunDetailsRouter from being
 * reused when the rootId changes. Otherwise, maintaining a consistent state after
 * the rootId changes becomes difficult. After all, when the rootId changes, most of
 * the content in RunDetailsRouter should be redrawn.
 */
const RunDetailsIndex = () => {
    const { rootId } = useParams();
    return <RunDetailsRouter key={rootId} />
}

export default RunDetailsIndex;
