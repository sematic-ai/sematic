import { Run, Edge, Artifact } from "../Models";
import ReactFlow, {
  Node,
  Edge as RFEdge,
  Handle,
  Position,
  ReactFlowInstance,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  ReactFlowProvider,
  MarkerType,
  Background,
  BackgroundVariant,
  applyNodeChanges,
  NodeProps,
} from "react-flow-renderer";
import {
  Alert,
  AlertTitle,
  Collapse,
  Container,
  lighten,
  useTheme,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { useCallback, useEffect, useState } from "react";
import CalculatorPath from "./CalculatorPath";
import buildDagLayout from "./utils/buildDagLayout";

var util = require("dagre/lib/util");
var graphlib = require("graphlib");

/*
 * Monkey patching dagre to add a default node label to the simplified
 * graph. Crashes otherwise.
 */
util.asNonCompoundGraph = function asNonCompoundGraph(g: any) {
  var simplified = new graphlib.Graph({
    multigraph: g.isMultigraph(),
  }).setGraph(g.graph());
  simplified.setDefaultNodeLabel(() => ({}));
  g.nodes().forEach((v: string) => {
    if (!g.children(v).length) {
      simplified.setNode(v, g.node(v));
    }
  });
  g.edges().forEach((e: string) => {
    simplified.setEdge(e, g.edge(e));
  });
  return simplified;
};

function RunNode(props: NodeProps) {
  const theme = useTheme();

  const run: Run = props.data.run;
  const calculatorPathParts = run.calculator_path.split(".");
  let shortCalculatorPath = calculatorPathParts[calculatorPathParts.length - 1];
  if (calculatorPathParts.length > 1) {
    shortCalculatorPath =
      calculatorPathParts[calculatorPathParts.length - 2] +
      "." +
      shortCalculatorPath;
    if (calculatorPathParts.length > 2) {
      shortCalculatorPath = "..." + shortCalculatorPath;
    }
  }

  return (
    <>
      <Handle
        isConnectable={props.isConnectable}
        type="target"
        position={Position.Top}
      />
      <Alert
        severity="success"
        variant="outlined"
        icon={<CheckCircleIcon />}
        id={props.data.run.id}
        style={{
          height: "-webkit-fill-available",
        }}
        sx={{
          paddingX: 3,
          cursor: "pointer",
          borderColor: lighten(
            theme.palette.success.light,
            props.selected ? 0 : 0.3
          ),
          backgroundColor: lighten(
            theme.palette.success.light,
            props.selected ? 0.7 : 0.9
          ),
          "&:hover": {
            backgroundColor: lighten(
              theme.palette.success.light,
              props.selected ? 0.7 : 0.87
            ),
          },
        }}
      >
        <AlertTitle>{props.data.label}</AlertTitle>
        <CalculatorPath calculatorPath={shortCalculatorPath} />
      </Alert>
      <Handle
        isConnectable={props.isConnectable}
        type="source"
        position={Position.Bottom}
      />
    </>
  );
}

interface ReactFlowDagProps {
  runs: Run[];
  edges: Edge[];
  artifactsById: Map<string, Artifact>;
  onSelectRun: (run: Run) => void;
}

const nodeTypes = {
  runNode: RunNode,
};

function ReactFlowDag(props: ReactFlowDagProps) {
  const { runs, edges, artifactsById, onSelectRun } = props;

  const runsById: Map<string, Run> = new Map(runs.map((run) => [run.id, run]));

  const [rfNodes, setRFNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRFEdges, onEdgesChange] = useEdgesState([]);

  const [showTip, setShowTip] = useState(false);

  const reactFlowInstance = useReactFlow();
  const theme = useTheme();

  const getEdgeLabel = useCallback(
    (edge: Edge) => {
      if (edge.artifact_id !== null) {
        let artifact = artifactsById.get(edge.artifact_id);
        if (artifact !== undefined) {
          let typeKey = artifact.type_serialization.type[1];
          return edge.destination_name + ": " + typeKey;
        }
      }
      return edge.destination_name;
    },
    [artifactsById]
  );

  useEffect(() => {
    let node_data: Node[] = [];
    let edge_data: RFEdge[] = [];
    node_data = runs.map((run) => {
      return {
        type: "runNode",
        id: run.id,
        data: { label: run.name, run: run },
        parentNode: run.parent_id === null ? undefined : run.parent_id,
        selected: run.parent_id === null,
        position: { x: 0, y: 0 },
        style: {
          backgroundColor: lighten(theme.palette.success.light, 0.9),
        },
        extent: run.parent_id === null ? undefined : "parent",
        // Always render below edges.
        zIndex: 0,
      };
    });

    edges.forEach((edge) => {
      if (edge.source_run_id && edge.destination_run_id) {
        let parentId = runsById.get(edge.source_run_id)?.parent_id;
        edge_data.push({
          id: edge.id,
          source: edge.source_run_id,
          target: edge.destination_run_id,
          label: getEdgeLabel(edge),
          data: { parentId: parentId },
          // Always render above nodes.
          zIndex: 1000,
          markerEnd: {
            type: MarkerType.Arrow,
          },
          labelShowBg: false,
          labelStyle: { fontFamily: "monospace" },
        });
      }
    });

    setRFNodes(node_data);
    setRFEdges(edge_data);
  }, [runs, edges]);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    let orderedNodes = buildDagLayout(instance, (node) =>
      document.getElementById(node.id)
    );
    setRFNodes(orderedNodes);
    setRFEdges(instance.getEdges());
  }, []);

  useEffect(() => {
    if (reactFlowInstance && reactFlowInstance.getNodes().length > 0) {
      onInit(reactFlowInstance);
    }
  }, [runs]);

  const onConnect = useCallback(
    (connection: any) => setRFEdges((eds) => addEdge(connection, eds)),
    [setRFEdges]
  );

  const onNodeClick = useCallback(
    (event: any, node: Node) => {
      setShowTip(false);
      let selectedRun = runsById.get(node.id);
      if (selectedRun) {
        onSelectRun(selectedRun);
      }
    },
    [runsById]
  );

  return (
    <>
      <Container
        sx={{ width: "100%", height: "1000px", paddingX: 0, marginX: 0 }}
      >
        <Collapse in={showTip}>
          <Alert severity="info" sx={{ marginBottom: 4 }}>
            Select a run to view in the right-hand-side panel.
          </Alert>
        </Collapse>
        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          nodeTypes={nodeTypes}
          onInit={onInit}
          zoomOnScroll={false}
          onConnect={onConnect}
          panOnScroll
          nodesDraggable={false}
          onNodeClick={onNodeClick}
        >
          <Background variant={BackgroundVariant.Dots} />
        </ReactFlow>
      </Container>
    </>
  );
}

export function FlowWithProvider(props: ReactFlowDagProps) {
  return (
    <ReactFlowProvider>
      <ReactFlowDag {...props} />
    </ReactFlowProvider>
  );
}

export default ReactFlowDag;
