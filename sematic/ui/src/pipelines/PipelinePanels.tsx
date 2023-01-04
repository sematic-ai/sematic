import { Box } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import Loading from "../components/Loading";
import MenuPanel from "./MenuPanel";
import NotesPanel from "./NotesPanel";
import RunPanel from "./RunPanel";
import { ExtractContextType } from "../components/utils/typings";
import { usePipelineRunContext } from "../hooks/pipelineHooks";
import { Run } from "../Models";
import PipelinePanelsContext from "./PipelinePanelsContext";
import PipelineRunViewContext from "./PipelineRunViewContext";
import GraphContext from "./graph/graphContext";
import { useGraph } from "../hooks/graphHooks";

export default function PipelinePanels() {
  const { rootRun }
    = usePipelineRunContext() as ExtractContextType<typeof PipelineRunViewContext> 
    & {
      rootRun: Run
    };

  const [selectedPanelItem, setSelectedPanelItem] = useState("run");
  const [selectedRun, setSelectedRun] = useState<Run>(rootRun);
  const pipelinePanelsContext = useMemo<ExtractContextType<typeof PipelinePanelsContext>>(() => ({
    selectedPanelItem, setSelectedPanelItem,
    selectedRun, setSelectedRun
  }), [selectedPanelItem, setSelectedPanelItem, selectedRun, setSelectedRun]);

  const [graph, isGraphLoading, error] = useGraph(rootRun.id);
  const graphContext = useMemo<ExtractContextType<typeof GraphContext>>(() => ({
    graph,
    isLoading: isGraphLoading
  }), [graph, isGraphLoading]);

  // Update the selectedRun with the data coming from the graph
  useEffect(() => {
    if (!graph) {
      return;
    }
    if (selectedRun && graph.runs) {
      let newSelectedRun = graph.runsById.get(selectedRun.id);
      if (!newSelectedRun) {
        newSelectedRun = rootRun;
        graph.runs.forEach((run: Run) => {
          if (run.calculator_path === selectedRun.calculator_path) {
            newSelectedRun = run;
          }
        });
      }
      setSelectedRun(newSelectedRun);
    }
  }, [graph, graph?.runs, rootRun, selectedRun]);

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
