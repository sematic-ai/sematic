import { Box } from "@mui/material";
import { useAtom } from "jotai";
import { RESET } from 'jotai/utils';
import { useEffect, useMemo, useState } from "react";
import Loading from "../components/Loading";
import { ExtractContextType } from "../components/utils/typings";
import { useGraph } from "../hooks/graphHooks";
import { selectedRunHashAtom, usePipelineRunContext } from "../hooks/pipelineHooks";
import { Run } from "../Models";
import GraphContext from "./graph/graphContext";
import MenuPanel from "./MenuPanel";
import NotesPanel from "./NotesPanel";
import PipelinePanelsContext from "./PipelinePanelsContext";
import PipelineRunViewContext from "./PipelineRunViewContext";
import RunPanel from "./RunPanel";

export default function PipelinePanels() {
  const { rootRun }
    = usePipelineRunContext() as ExtractContextType<typeof PipelineRunViewContext> 
    & {
      rootRun: Run
    };
    
  const [selectedRunId, setSelectedRunId] = useAtom(selectedRunHashAtom);
  const [selectedPanelItem, setSelectedPanelItem] = useState("run");

  const [graph, isGraphLoading, error] = useGraph(rootRun.id);
  const graphContext = useMemo<ExtractContextType<typeof GraphContext>>(() => ({
    graph,
    isLoading: isGraphLoading
  }), [graph, isGraphLoading]);

  const selectedRun = useMemo(() => {
    let runId = selectedRunId;
    if (!runId) {
      runId = rootRun.id;
    }
    if (!graph) {
      return undefined;
    }
    return graph.runsById.get(runId) || rootRun;
  }, [selectedRunId, graph, rootRun]);

  const defaultTab = selectedRun?.future_state === "FAILED" ? "logs" : "output";
  const [selectedRunTab, setSelectedRunTab] = useState(defaultTab);
  const [selectedArtifactName, setSelectedArtifactName] = useState("");

  const pipelinePanelsContext = useMemo<ExtractContextType<typeof PipelinePanelsContext>>(() => ({
    selectedPanelItem, setSelectedPanelItem,
    selectedRun, setSelectedRunId,
    selectedRunTab, setSelectedRunTab,
    selectedArtifactName, setSelectedArtifactName
  }), [selectedPanelItem, selectedRun, setSelectedRunId, selectedRunTab, selectedArtifactName]);

  useEffect(()=> {
    if (selectedRunId === rootRun.id || 
      (!!graph && !graph.runsById.get(selectedRunId))) {
      setSelectedRunId(RESET);
      return;
    }
  }, [selectedRunId, graph, rootRun, setSelectedRunId])

  if (error || isGraphLoading) {
    return (
      <Box sx={{ p: 5, gridColumn: "1 / 4" }}>
        <Loading error={error} isLoaded={false} />
      </Box>
    );
  } 
  return (
    <PipelinePanelsContext.Provider value={pipelinePanelsContext}>
      <GraphContext.Provider value={graphContext}>
        <MenuPanel />
        <RunPanel />
        <NotesPanel />
      </GraphContext.Provider>
    </PipelinePanelsContext.Provider>
  );
}
