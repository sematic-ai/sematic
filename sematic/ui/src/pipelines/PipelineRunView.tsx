import Box from "@mui/material/Box";
import { useMemo } from "react";
import { useParams } from "react-router-dom";
import Loading from "../components/Loading";
import PipelineBar from "./PipelineBar";
import PipelinePanels from "./PipelinePanels";
import { ExtractContextType } from "../components/utils/typings";
import { useFetchResolution, useFetchRun } from "../hooks/pipelineHooks";
import PipelineRunViewContext from './PipelineRunViewContext'

export default function PipelineRunView() {
  const { pipelinePath, rootId } = useParams();

  for (const [key, value] of Object.entries({pipelinePath, rootId})) {
    if (!value) {
      throw new Error(
        `\`${key}\` is expected from the URL. This component might be used with wrong route.`);
    }
  }

  const [rootRun, isRootRunLoading, rootRunLoadError] = useFetchRun(rootId!);
  const [resolution, isResolutionLoading, resolutionLoadError] = useFetchResolution(rootId!);

  const isLoading = useMemo(() => isRootRunLoading || isResolutionLoading, 
    [isRootRunLoading, isResolutionLoading])
  
  const error = useMemo(() => rootRunLoadError || resolutionLoadError, 
    [rootRunLoadError, resolutionLoadError])

  const context = useMemo<ExtractContextType<typeof PipelineRunViewContext>>(() => ({
    rootRun, resolution, isLoading, pipelinePath: pipelinePath!
  }), [rootRun, resolution, isLoading, pipelinePath]);

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
          height: "100vh",
        }}
      >
        <PipelineBar />
        <PipelinePanels />
      </Box>
    </PipelineRunViewContext.Provider>
  );
}
