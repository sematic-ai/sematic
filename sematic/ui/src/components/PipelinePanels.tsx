import { Box } from "@mui/material";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { UserContext } from "..";
import { Run, Resolution } from "../Models";
import { RunGraphPayload } from "../Payloads";
import { fetchJSON, graphSocket } from "../utils";
import Loading from "./Loading";
import MenuPanel from "./MenuPanel";
import NotesPanel from "./NotesPanel";
import RunPanel, { Graph } from "./RunPanel";

export default function PipelinePanels(props: {
  rootRun: Run;
  resolution: Resolution;
  onRootRunUpdate: (run: Run) => void;
  onRootIdChange: (rootId: string) => void;
}) {
  const { rootRun, resolution, onRootRunUpdate, onRootIdChange } = props;
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
        for (let i = 0; i < payload.runs.length; i++) {
          if (payload.runs[i].id == rootRun.id) {
            onRootRunUpdate(payload.runs[i]);
            break;
          }
        }
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
          resolution={resolution}
          onSelectRun={(run) => {
            setSelectedRun(run);
            setSelectedPanelItem("run");
          }}
        />
        <NotesPanel
          rootRun={rootRun}
          selectedRun={selectedRun}
          onRootIdChange={onRootIdChange}
        />
      </>
    );
  }
  return <></>;
}
