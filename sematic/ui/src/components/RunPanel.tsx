import { FileCopy, History, Insights } from "@mui/icons-material";
import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import { useCallback, useContext, useMemo } from "react";
import { Artifact, Edge, Run } from "../Models";
import CalculatorPath from "./CalculatorPath";
import RunTabs, { IOArtifacts } from "./RunTabs";
import Docstring from "./Docstring";
import { FlowWithProvider } from "./ReactFlowDag";
import RunStateChip from "./RunStateChip";
import { RunTime } from "./RunTime";
import Tags from "./Tags";
import { ActionMenu, ActionMenuItem } from "./ActionMenu";
import { fetchJSON } from "../utils";
import { UserContext } from "..";
import { ResolutionPayload } from "../Payloads";
import { redirect } from "react-router-dom";
import { SnackBarContext } from "./SnackBarProvider";

export type Graph = {
  runs: Map<string, Run>;
  edges: Edge[];
  artifacts: Artifact[];
};

export default function RunPanel(props: {
  selectedPanel: string;
  graph: Graph;
  rootRun: Run;
  selectedRun: Run;
  onSelectRun: (run: Run) => void;
}) {
  const { selectedPanel, graph, selectedRun, rootRun, onSelectRun } = props;

  const runsById = useMemo(() => graph.runs, [graph]);

  const edges = useMemo(() => graph.edges, [graph]);

  const artifactsById = useMemo(() => {
    let allArtifactsForRoot = graph.artifacts;
    return (
      allArtifactsForRoot &&
      new Map(allArtifactsForRoot.map((artifact) => [artifact.id, artifact]))
    );
  }, [graph]);

  const selectedRunArtifacts = useMemo(() => {
    if (edges === undefined) return;
    if (artifactsById === undefined) return;

    let ioArtifacts: IOArtifacts = { input: new Map(), output: new Map() };

    const setArtifact = (
      map: Map<string, Artifact | undefined>,
      artifact_id: string | null,
      name: string | null
    ) => {
      let artifact: Artifact | undefined = undefined;
      if (artifact_id !== null) {
        artifact = artifactsById.get(artifact_id);
        if (artifact === undefined) {
          //setError(Error("Artifact missing"));
          return;
        }
      }
      map.set(
        name ? name : "null",
        artifact_id ? artifactsById.get(artifact_id) : undefined
      );
    };

    edges.forEach((edge) => {
      if (edge.destination_run_id === selectedRun?.id) {
        setArtifact(ioArtifacts.input, edge.artifact_id, edge.destination_name);
      }
      if (edge.source_run_id === selectedRun?.id) {
        setArtifact(ioArtifacts.output, edge.artifact_id, edge.source_name);
      }
    });
    return ioArtifacts;
  }, [edges, artifactsById, selectedRun]);

  const actions = [
    [<FileCopy />, "Clone"],
    [<History />, "Schedule"],
    [<Insights />, "Share"],
  ];

  return (
    <Box sx={{ gridColumn: 2, gridRow: 2, overflowY: "scroll" }}>
      {selectedPanel === "graph" && (
        <>
          <FlowWithProvider
            // Nasty hack to make sure the DAG is remounted each time to trigger a ReactFlow onInit
            // to trigger a new layout
            key={Math.random().toString()}
            runs={Array.from(runsById.values())}
            edges={edges}
            artifactsById={artifactsById}
            onSelectRun={onSelectRun}
            selectedRunId={selectedRun.id}
          />
        </>
      )}
      {selectedPanel === "run" && (
        <Box sx={{ p: 5 }}>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr auto auto" }}>
            <Box sx={{ paddingBottom: 3, gridColumn: 1 }}>
              <Box marginBottom={3}>
                <Typography variant="h6">{selectedRun.name}</Typography>
                <CalculatorPath calculatorPath={"ID: " + selectedRun.id} />
                <br />
                <CalculatorPath calculatorPath={selectedRun.calculator_path} />
              </Box>
              <Tags tags={selectedRun.tags || []} />
            </Box>
            <Box sx={{ gridColumn: 2, pt: 3, pr: 10 }}>
              <RunActionMenu
                run={selectedRun}
                rootRun={rootRun}
                edges={edges}
              />
            </Box>
            <Box sx={{ gridColumn: 3, pt: 3, pr: 5 }}>
              <RunStateChip state={selectedRun.future_state} variant="full" />
              <RunTime run={selectedRun} prefix="in " />
            </Box>
          </Box>
          <Box sx={{ my: 10 }}>
            <Docstring docstring={selectedRun.description} />
          </Box>
          <RunTabs run={selectedRun} artifacts={selectedRunArtifacts} />
        </Box>
      )}
    </Box>
  );
}

function RunActionMenu(props: { run: Run; rootRun: Run; edges: Edge[] }) {
  const { run, rootRun, edges } = props;

  const { user } = useContext(UserContext);
  const { setSnackMessage } = useContext(SnackBarContext);

  const onRerunClick = useCallback(() => {
    fetchJSON({
      url: "/api/v1/resolutions/" + run.root_id + "/rerun",
      method: "POST",
      body: { rerun_from: run.id },
      apiKey: user?.api_key,
      callback: (payload) => {},
      setError: (error) => {},
    });
  }, []);

  const rerunEnabled = useMemo(
    () => edges.every((edge) => !!edge.artifact_id),
    [edges]
  );

  return (
    <ActionMenu title="Actions">
      <ActionMenuItem
        title="Rerun from here"
        onClick={onRerunClick}
        enabled={true || rerunEnabled}
      >
        <Typography>Rerun this pipeline from this run in the graph.</Typography>
        <Typography>All upstream runs will use cached outputs.</Typography>
      </ActionMenuItem>
      {false && (
        <ActionMenuItem title="Copy share link">
          <Typography>Copy link to this exact run.</Typography>
        </ActionMenuItem>
      )}
    </ActionMenu>
  );
}
