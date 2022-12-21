import { Box } from "@mui/material";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { UserContext } from "..";
import Loading from "./Loading";
import MenuPanel from "./MenuPanel";
import NotesPanel from "./NotesPanel";
import RunPanel, { Graph } from "./RunPanel";
import { ExtractContextType } from "./utils/typings";
import { usePipelineRunContext } from "../hooks/pipelineHooks";
import { Run } from "../Models";
import { RunGraphPayload } from "../Payloads";
import { fetchJSON, graphSocket } from "../utils";
import PipelinePanelsContext from "../pipelines/PipelinePanelsContext";
import PipelineRunViewContext from "../pipelines/PipelineRunViewContext";

export default function PipelinePanels() {
  const [graphsByRootId, setGraphsByRootId] = useState<Map<string, Graph>>(
    new Map()
  );
  const { rootRun }
    = usePipelineRunContext() as ExtractContextType<typeof PipelineRunViewContext> 
    & {
      rootRun: Run
    };
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);

  const [selectedPanelItem, setSelectedPanelItem] = useState("run");
  const [selectedRun, setSelectedRun] = useState<Run>(rootRun);
  const context = useMemo<ExtractContextType<typeof PipelinePanelsContext>>(() => ({
    selectedPanelItem, setSelectedPanelItem,
    selectedRun, setSelectedRun
  }), [selectedPanelItem, setSelectedPanelItem, selectedRun, setSelectedRun])

  const { user } = useContext(UserContext);

  const loadGraph = useCallback(() => {
    fetchJSON({
      url: "/api/v1/runs/" + rootRun.id + "/graph?root=1",
      apiKey: user?.api_key,
      callback: (payload: RunGraphPayload) => {
        let graph = {
          runs: new Map(payload.runs.map((run) => [run.id, run])),
          edges: payload.edges,
          artifacts: payload.artifacts,
        };
        setGraphsByRootId((currentMap) => {
          currentMap.set(rootRun.id, graph);
          return new Map(currentMap);
        });
        setIsLoaded(true);
      },
      setError: setError,
    });
  }, [rootRun.id]);

  useEffect(() => {
    if (!graphsByRootId.has(rootRun.id)) {
      setIsLoaded(false);
      loadGraph();
    }
  }, [rootRun.id]);

  useEffect(() => {
    graphSocket.removeAllListeners();
    graphSocket.on("update", (args: { run_id: string }) => {
      if (args.run_id === rootRun.id) {
        loadGraph();
      }
    });
  }, [rootRun.id]);

  const runs = useMemo(
    () => graphsByRootId.get(rootRun.id)?.runs,
    [graphsByRootId, rootRun]
  );

  // Update the selectedRun with the data coming from the graph
  useEffect(() => {
    if (selectedRun && runs) {
      let newSelectedRun = runs.get(selectedRun.id);
      if (!newSelectedRun) {
        newSelectedRun = rootRun;
        runs.forEach((run: Run) => {
          if (run.calculator_path === selectedRun.calculator_path) {
            newSelectedRun = run;
          }
        });
      }
      setSelectedRun(newSelectedRun);
    }
  }, [runs, rootRun, selectedRun]);

  const runsByParentId = useMemo(() => {
    if (runs === undefined) return;
    let map: Map<string | null, Run[]> = new Map();
    Array.from(runs.values()).forEach((run) => {
      map.set(run.parent_id, [...(map.get(run.parent_id) || []), run]);
    });
    return map;
  }, [runs]);

  const graph = useMemo(
    () => graphsByRootId.get(rootRun.id),
    [graphsByRootId, rootRun]
  );

  if (error || !isLoaded) {
    return (
      <Box sx={{ p: 5, gridColumn: "1 / 4" }}>
        <Loading error={error} isLoaded={isLoaded} />
      </Box>
    );
  } else if (runs && runsByParentId && graph) {
    return (
      <PipelinePanelsContext.Provider value={context}>
        <MenuPanel runsById={runs} />
        <RunPanel graph={graph} />
        <NotesPanel />
      </PipelinePanelsContext.Provider>
    );
  }
  return <></>;
}
