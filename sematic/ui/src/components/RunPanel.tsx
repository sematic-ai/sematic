import { Box, Typography } from "@mui/material";
import { useMemo } from "react";
import { Artifact, Edge, Run } from "../Models";
import CalculatorPath from "./CalculatorPath";
import { IOArtifacts, RunTabs } from "./DagTab";
import Docstring from "./Docstring";
import { FlowWithProvider } from "./ReactFlowDag";
import RunStateChip from "./RunStateChip";
import { RunTime } from "./RunTime";
import Tags from "./Tags";

export type Graph = {
  runs: Map<string, Run>;
  edges: Edge[];
  artifacts: Artifact[];
};

export default function RunPanel(props: {
  selectedPanel: string;
  graph: Graph;
  selectedRun: Run;
  onSelectRun: (run: Run) => void;
}) {
  const { selectedPanel, graph, selectedRun, onSelectRun } = props;

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
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 150px" }}>
            <Box sx={{ paddingBottom: 3, gridColumn: 1 }}>
              <Box marginBottom={3}>
                <Typography variant="h6">{selectedRun.name}</Typography>
                <CalculatorPath
                  calculatorPath={"ID:" + selectedRun.id.substring(0, 6)}
                />{" "}
                &middot;{" "}
                <CalculatorPath calculatorPath={selectedRun.calculator_path} />
              </Box>
              <Tags tags={selectedRun.tags || []} />
            </Box>
            <Box sx={{ gridColumn: 2 }}>
              <RunStateChip state={selectedRun.future_state} variant="full" />
              <RunTime run={selectedRun} prefix="in " />
            </Box>
          </Box>
          <Docstring docstring={selectedRun.description} />
          <RunTabs run={selectedRun} artifacts={selectedRunArtifacts} />
        </Box>
      )}
    </Box>
  );
}
