import Box from "@mui/material/Box";
import { useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import Loading from "../components/Loading";
import PipelineBar from "./PipelineBar";
import PipelinePanels from "./PipelinePanels";
import { ExtractContextType } from "../components/utils/typings";
import { selectedRunHashAtom, useFetchResolution, useFetchRun, usePipelineNavigation } from "../hooks/pipelineHooks";
import PipelineRunViewContext from './PipelineRunViewContext'
import { Run } from "../Models";
import { useAtom } from "jotai";
interface PipelineRunViewPresentationProps {
  pipelinePath: string
  rootRun: Run
}
export function PipelineRunViewPresentation({
  pipelinePath, rootRun
}: PipelineRunViewPresentationProps ) {
  const { id: rootId } = rootRun;

  const [resolution, isLoading, error] = useFetchResolution(rootId!);

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

export default function PipelineRunViewRouter() {
  const { pipelinePath, rootId } = useParams();

  for (const [key, value] of Object.entries({pipelinePath, rootId})) {
    if (!value) {
      throw new Error(
        `\`${key}\` is expected from the URL. This component might be used with wrong route.`);
    }
  }
  const navigate = usePipelineNavigation(pipelinePath!);
  const [run, isLoading, error] = useFetchRun(rootId!);
  const [_, setSelectedRunId] = useAtom(selectedRunHashAtom);

  useEffect(() => {
    // The new run might be loading, so we have to wait for run.id == rootId
    // to get the updated `run`
    if (!run || run.id !== rootId) {
      return;
    }
    if (rootId !== run.root_id) { 
      // in case `rootId` is actually a nested run. Navigate to new URL
      const nestedRunId = rootId!;
      setSelectedRunId(nestedRunId);
      setTimeout(() => { // use `setTimeout` so setSelectedRunId has a chance to update URL hash.
        navigate(run.root_id);
      });
    }
  }, [run, rootId, isLoading, navigate, setSelectedRunId]);

  if (error || isLoading) {
    return <Loading error={error} isLoaded={!isLoading} />
  }

  if (rootId !== run!.root_id) { 
    // in case `rootId` is actually a nested run. Render nothing. Page
    // will be redirected soon.
    return <></>;
  }

  // Otherwise, load `PipelineRunViewPresentation` to actually render root run.
  return <PipelineRunViewPresentation pipelinePath={pipelinePath!} rootRun={run!} />
}
