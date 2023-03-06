import { Box } from "@mui/material";
import { useAtom } from "jotai";
import { RESET } from "jotai/utils";
import { useEffect, useMemo, useState } from "react";
import usePrevious from "react-use/lib/usePrevious";
import Loading from "../components/Loading";
import { ExtractContextType } from "../components/utils/typings";
import { useGraph } from "../hooks/graphHooks";
import { selectedPanelHashAtom, selectedRunHashAtom, selectedTabHashAtom, useHashUpdater, usePipelineRunContext } from "../hooks/pipelineHooks";
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
    
  const [selectedRunIdHash, setSelectedRunId] = useAtom(selectedRunHashAtom);
  const [selectedPanelItemHash, setSelectedPanelItem] = useAtom(selectedPanelHashAtom);

  const [graph, isGraphLoading, error] = useGraph(rootRun.id);
  const graphContext = useMemo<ExtractContextType<typeof GraphContext>>(() => ({
    graph,
    isLoading: isGraphLoading
  }), [graph, isGraphLoading]);

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

  const [selectedTabHash, setSelectedRunTab] = useAtom(selectedTabHashAtom);

  const selectedRunTab = useMemo(() => {
    if (!!selectedTabHash) {
      return selectedTabHash;
    }
    // in case there is no previously selected tab, decide what default tab is.
    const run = selectedRun || rootRun;
    // if there is a substential run available (either selected run or root run)
    // check its state. If it failed, show the logs for investigating failures
    // otherwise, show the output(result) tab by default.
    return run?.future_state === "FAILED" ? "logs" : "output";
  }, [selectedTabHash, selectedRun, rootRun]);

  const selectedPanelItem = useMemo(() => {
    if (!selectedPanelItemHash) {
      return 'run';
    }
    return selectedPanelItemHash;
  }, [selectedPanelItemHash]);

  const [selectedArtifactName, setSelectedArtifactName] = useState("");

  const pipelinePanelsContext = useMemo<ExtractContextType<typeof PipelinePanelsContext>>(() => ({
    selectedPanelItem, setSelectedPanelItem,
    selectedRun, setSelectedRunId,
    selectedRunTab, setSelectedRunTab,
    selectedArtifactName, setSelectedArtifactName
  }), [selectedPanelItem, setSelectedPanelItem, selectedRun, setSelectedRunId, selectedRunTab, selectedArtifactName, setSelectedRunTab]);
  
  const updateHash = useHashUpdater();

  // Clear the `run` hash when the selected run is not available in the graph or
  // the selected run is the root run.
  useEffect(()=> {
    if (selectedRunIdHash === rootRun.id || 
      (!!graph && !graph.runsById.get(selectedRunIdHash))) {
      if (!!selectedRunIdHash) {
        updateHash({'run': RESET}, true);
      }
      return;
    }
  }, [selectedRunIdHash, graph, rootRun, updateHash]);

  const prevSelectedPanelItem = usePrevious(selectedPanelItem);
  // Clear the `tab`, `run` hash when we move away from the run panel.
  useEffect(()=> {
    // Only clear the hash when the selected panel item has just changed.
    if (selectedPanelItem === prevSelectedPanelItem) {
      return;
    }
    if (selectedPanelItem !== 'run') {
        updateHash({'tab': RESET, 'run': RESET}, true);
    }
  }, [prevSelectedPanelItem, selectedPanelItem, updateHash])


  if (error || (!graph && isGraphLoading)) {
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
