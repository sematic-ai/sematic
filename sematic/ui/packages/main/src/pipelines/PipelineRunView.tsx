import Box from "@mui/material/Box";
import { Run } from "@sematic/common/src/Models";
import { useAtom } from "jotai";
import { useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import Loading from "src/components/Loading";
import { ExtractContextType } from "@sematic/common/src/utils/typings";
import { selectedRunHashAtom, useFetchResolution, useFetchRun, useRunNavigation } from "src/hooks/pipelineHooks";
import PipelineBar from "src/pipelines/PipelineBar";
import PipelinePanels from "src/pipelines/PipelinePanels";
import PipelineRunViewContext from 'src/pipelines/PipelineRunViewContext';

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
          height: "100vh",
        }}
      >
        <PipelineBar />
        <PipelinePanels />
      </Box>
    </PipelineRunViewContext.Provider>
  );
}

export function RunViewRouter() {
  const { rootId } = useParams();

    if (!rootId) {
      throw new Error(
        `\`rootId\` is expected from the URL. This component might be used with wrong route.`);
    }
  const navigate = useRunNavigation();
  const [run, isLoading, error] = useFetchRun(rootId!);
  const [, setSelectedRunId] = useAtom(selectedRunHashAtom);

  useEffect(() => {
    if (!run) {
      return;
    }
    if (rootId !== run.root_id) { 
      // in case `rootId` is actually a nested run. Navigate to new URL
      const nestedRunId = rootId!;
      navigate(run.root_id, true, {'run': nestedRunId});
    }
  }, [run, rootId, navigate, setSelectedRunId]);

  if (error || isLoading) {
    return <Loading error={error} isLoaded={!isLoading} />
  }

  if (rootId !== run!.root_id) { 
    // in case `rootId` is actually a nested run. Render nothing. Page
    // will be redirected soon.
    return <></>;
  }

  // Otherwise, load `PipelineRunViewPresentation` to actually render root run.
  return <RunViewPresentation rootRun={run!} />
}

export default function RunViewWraper() {
  const { rootId } = useParams();
  return <RunViewRouter key={rootId}/>
}

