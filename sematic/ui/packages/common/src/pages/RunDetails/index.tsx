import { useCallback, useMemo } from "react";
import ThreeColumns from "src/layout/ThreeColumns";
import CenterPane from "src/pages/RunDetails/CenterPane";
import MetaDataPane from "src/pages/RunDetails/MetaDataPane";
import NotesPane from "src/pages/RunDetails/NotesPane";
import { createRunRouter } from "src/pages/RunDetails/RunRouter";
import { useParams } from "react-router-dom";
import { Run } from "src/Models";
import RootRunContext from "src/context/RootRunContext";
import { useFetchResolution } from "src/hooks/resolutionHooks";

interface RunDetailsProps {
    rootRun: Run;
}
const RunDetails = (props: RunDetailsProps) => {
    const { rootRun } = props;

    const [ resolution ] = useFetchResolution(rootRun.id!);

    const onRenderLeft = useCallback(() => {
        return <MetaDataPane />;
    }, []);

    const onRenderCenter = useCallback(() => {
        return <CenterPane />;
    }, []);

    const onRenderRight = useCallback(() => {
        return <NotesPane />;
    }, []);

    const contextValue = useMemo(() => {
        return {
            rootRun,
            resolution
        };
    }, [rootRun, resolution]);

    return <RootRunContext.Provider value={contextValue}>
        <ThreeColumns onRenderLeft={onRenderLeft} onRenderCenter={onRenderCenter}
            onRenderRight={onRenderRight} />
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
