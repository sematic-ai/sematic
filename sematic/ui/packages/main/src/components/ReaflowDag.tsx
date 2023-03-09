/*
import {
  Canvas,
  CanvasPosition,
  EdgeData,
  NodeData,
  Node,
  Label,
  Edge as EdgeRF,
} from "reaflow";
import { Artifact, Run, Edge } from "../Models";
import { Alert, lighten, Typography, useTheme } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import Box from "@mui/material/Box";
import { FC } from "react";

interface ReaflowDagProps {
  runs: Run[];
  edges: Edge[];
}

function ReaflowDag(props: ReaflowDagProps) {
  let runs = props.runs;
  let edges = props.edges;

  let runsById = new Map(runs.map((run) => [run.id, run]));

  let node_data: NodeData[] = [];
  let edge_data: EdgeData[] = [];

  node_data = runs.map((run) => {
    var calculator_module = run.calculator_path.split(".");
    return {
      id: run.id,
      text: calculator_module[calculator_module.length - 1],
      parent: run.parent_id === null ? undefined : run.parent_id,
      data: { run: run },
    };
  });

  edges.forEach((edge) => {
    if (edge.source_run_id && edge.destination_run_id) {
      let parent_id = runsById.get(
        edge.source_run_id || edge.destination_run_id
      )?.parent_id;
      let parent = parent_id === null ? undefined : parent_id;
      edge_data.push({
        id: edge.id,
        from: edge.source_run_id,
        to: edge.destination_run_id,
        text: edge.destination_name,
        parent: parent,
      });
    }
  });

  const theme = useTheme();

  return (
    <>
      <Canvas
        nodes={node_data}
        edges={edge_data}
        defaultPosition={CanvasPosition.TOP}
        layoutOptions={{
          "org.eclipse.elk.nodeLabels.placement": "INSIDE V_CENTER H_CENTER",
          "org.eclipse.elk.edgeLabels.placement": "INSIDE V_BOTTOM H_CENTER",
        }}
        readonly
        fit
        onLayoutChange={(layout) => console.log(layout)}
        node={
          <Node
            style={{
              stroke: theme.palette.success.dark,
              fill: theme.palette.success.light,
              strokeWidth: 1,
              opacity: 0.5,
            }}
            label={<Label style={{ fill: theme.palette.text.primary }} />}
            icon={<CheckCircleIcon />}
          />
        }
        edge={<EdgeRF style={{ color: theme.palette.text.primary }} />}
      />
    </>
  );
}

export default ReaflowDag;
*/
export {};
