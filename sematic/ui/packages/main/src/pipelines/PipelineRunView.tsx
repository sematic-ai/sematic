import Box from "@mui/material/Box";
import { Run } from "@sematic/common/src/Models";
import { useFetchResolution } from "@sematic/common/src/hooks/resolutionHooks";
import { createRunRouter } from "@sematic/common/src/pages/RunDetails/RunRouter";
import { ExtractContextType } from "@sematic/common/src/utils/typings";
import { useMemo } from "react";
import { useParams } from "react-router-dom";
import Loading from "src/components/Loading";
import PipelineBar from "src/pipelines/PipelineBar";
import PipelinePanels from "src/pipelines/PipelinePanels";
import PipelineRunViewContext from "src/pipelines/PipelineRunViewContext";

interface RunViewPresentationProps {
    rootRun: Run
}
export function RunViewPresentation({
    rootRun
}: RunViewPresentationProps ) {
    const { id: rootId } = rootRun;

    const [resolution, isLoading, error] = useFetchResolution(rootId!);

    const context = useMemo<ExtractContextType<typeof PipelineRunViewContext>>(() => ({
        rootRun, resolution, isLoading,
    }), [rootRun, resolution, isLoading]);

    if (error || isLoading) {
        return <Loading error={error} isLoaded={!isLoading} />
    }

    return (
        <PipelineRunViewContext.Provider value={context}>
            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns: "250px 1fr 350px",
                    gridTemplateRows: "70px 1fr",
                    height: "100%",
                }}
            >
                <PipelineBar />
                <PipelinePanels />
            </Box>
        </PipelineRunViewContext.Provider>
    );
}

const RunViewRouter = createRunRouter(RunViewPresentation);

export default function RunViewWraper() {
    const { rootId } = useParams();
    return <RunViewRouter key={rootId}/>
}

