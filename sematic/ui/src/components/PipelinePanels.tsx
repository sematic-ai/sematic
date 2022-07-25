import { Box } from "@mui/material";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { UserContext } from "..";
import { Run } from "../Models";
import { RunGraphPayload } from "../Payloads";
import { fetchJSON, graphSocket } from "../utils";
import Loading from "./Loading";
import MenuPanel from "./MenuPanel";
import NotesPanel from "./NotesPanel";
import RunPanel, { Graph } from "./RunPanel";

export default function PipelinePanels(props: { rootRun: Run }) {
  const { rootRun } = props;
  const [selectedPanelItem, setSelectedPanelItem] = useState("run");
  const [graphsByRootId, setGraphsByRootId] = useState<Map<string, Graph>>(
    new Map()
  );
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [selectedRun, setSelectedRun] = useState<Run>(rootRun);
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
        //setSelectedPanelItem("run");
        setIsLoaded(true);
      },
      setError: setError,
    });
  }, [rootRun]);

  useEffect(() => {
    if (!graphsByRootId.has(rootRun.id)) {
      setIsLoaded(false);
      loadGraph();
    }
  }, [rootRun]);

  useEffect(() => {
    graphSocket.removeAllListeners();
    graphSocket.on("update", (args: { run_id: string }) => {
      if (args.run_id === rootRun.id) {
        loadGraph();
      }
    });
  }, [rootRun]);

  const runs = useMemo(
    () => graphsByRootId.get(rootRun.id)?.runs,
    [graphsByRootId, rootRun]
  );

  useEffect(() => {
    if (selectedRun && runs) {
      runs.forEach((run) => {
        if (run.calculator_path === selectedRun.calculator_path) {
          setSelectedRun(run);
        }
      });
    }
  }, [runs]);

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
      <>
        <MenuPanel
          runsById={runs}
          selectedRun={selectedRun}
          selectedPanel={selectedPanelItem}
          onPanelSelect={setSelectedPanelItem}
          onRunSelect={setSelectedRun}
        />
        <RunPanel
          selectedPanel={selectedPanelItem}
          graph={graph}
          selectedRun={selectedRun}
          onSelectRun={(run) => {
            setSelectedRun(run);
            setSelectedPanelItem("run");
          }}
        />
        <NotesPanel rootRun={rootRun} selectedRun={selectedRun} />
      </>
    );
  }
  return <></>;
}
