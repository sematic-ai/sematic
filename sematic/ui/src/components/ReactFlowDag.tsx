import { Run, Edge, Artifact } from "../Models";
import ReactFlow, {
  Node,
  Edge as RFEdge,
  ReactFlowInstance,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  Background,
  BackgroundVariant,
} from "react-flow-renderer";
import { Box } from "@mui/material";
import { useCallback, useEffect, useMemo } from "react";
import buildDagLayout from "./utils/buildDagLayout";
import RunNode from "./RunNode";
import ArtifactNode from "./ArtifactNode";

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

interface ReactFlowDagProps {
  runs: Run[];
  edges: Edge[];
  artifactsById: Map<string, Artifact>;
  onSelectRun: (run: Run) => void;
  selectedRunId: string;
}

const nodeTypes = {
  runNode: RunNode,
  artifactNode: ArtifactNode,
};

function ReactFlowDag(props: ReactFlowDagProps) {
  const { runs, edges, artifactsById, onSelectRun, selectedRunId } = props;

  const runsById = useMemo(
    () => new Map(runs.map((run) => [run.id, run])),
    [runs]
  );
  const edgesById = useMemo(
    () => new Map(edges.map((edge) => [edge.id, edge])),
    [edges]
  );

  const [rfNodes, setRFNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRFEdges, onEdgesChange] = useEdgesState([]);

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

  const getNodesEdges = useCallback(() => {
    let node_data: Node[] = [];
    let edge_data: RFEdge[] = [];
    node_data = runs.map((run) => {
      let runArgNames: string[] = [];
      edges.forEach((edge) => {
        if (edge.destination_run_id === run.id) {
          runArgNames.push(edge.destination_name || "");
        }
      });
      return {
        type: "runNode",
        id: run.id,
        data: { label: run.name, run: run, argNames: runArgNames },
        parentNode: run.parent_id === null ? undefined : run.parent_id,
        selected: run.id === selectedRunId,
        position: { x: 0, y: 0 },
        extent: run.parent_id === null ? undefined : "parent",
        // Always render below edges.
        zIndex: 0,
      };
    });

    let makeArtifactNodeId = (edge: Edge) =>
      (edge.source_run_id || "null") +
      (edge.destination_name || "null") +
      (edge.destination_run_id || "null");

    edges.forEach((edge) => {
      let parentId =
        runsById.get(edge.destination_run_id || edge.source_run_id || "")
          ?.parent_id || undefined;

      let artifactNodeId = makeArtifactNodeId(edge);

      if (edge.parent_id === null) {
        node_data.push({
          type: "artifactNode",
          id: artifactNodeId,
          data: {
            label: edge.destination_name,
            nodeId: artifactNodeId,
            sourceRunId: edge.source_run_id,
            destinationRunId: edge.destination_run_id,
          }, //getEdgeLabel(edge) },
          parentNode: parentId,
          position: { x: 0, y: 0 },
          zIndex: 0,
        });
      } else {
        let parentEdge = edgesById.get(edge.parent_id);
        while (parentEdge !== undefined) {
          artifactNodeId = makeArtifactNodeId(parentEdge);
          if (parentEdge.parent_id !== null) {
            parentEdge = edgesById.get(parentEdge.parent_id);
          } else {
            parentEdge = undefined;
          }
        }
      }

      if (edge.source_run_id !== null) {
        edge_data.push({
          id: edge.source_run_id + edge.id,
          source: edge.source_run_id,
          target: artifactNodeId,
          data: { parentId: parentId },
          zIndex: 1000,
        });
      }

      if (edge.destination_run_id !== null) {
        edge_data.push({
          id: edge.destination_run_id + edge.id + (edge.destination_name || ""),
          source: artifactNodeId,
          target: edge.destination_run_id,
          targetHandle: edge.destination_name,
          data: { parentId: parentId },
          zIndex: 1000,
        });
      }

      /*if (edge.source_run_id && edge.destination_run_id) {
        let parentId = runsById.get(edge.source_run_id)?.parent_id;
        edge_data.push({
          id: edge.id,
          source: edge.source_run_id,
          target: edge.destination_run_id,
          //label: getEdgeLabel(edge),
          data: { parentId: parentId },
          // Always render above nodes.
          zIndex: 1000,
          markerEnd: {
            type: MarkerType.Arrow,
          },
          labelShowBg: false,
          labelStyle: { fontFamily: "monospace" },
        });
      }*/
    });
    return { nodes: node_data, edges: edge_data };
  }, [runs, edges, getEdgeLabel, runsById]);

  useEffect(() => {
    let nodesEdges = getNodesEdges();
    setRFNodes(nodesEdges.nodes);
    setRFEdges(nodesEdges.edges);
  }, [runs]);

  const onInit = useCallback(
    (instance: ReactFlowInstance) => {
      let orderedNodes = buildDagLayout(
        instance.getNodes(),
        instance.getEdges(),
        (node) => document.getElementById(node.id)
      );
      setRFNodes(orderedNodes);
      setRFEdges(instance.getEdges());
    },
    [getNodesEdges, setRFNodes, setRFEdges]
  );

  const onNodeClick = useCallback(
    (event: any, node: Node) => {
      let selectedRun = runsById.get(node.id);
      if (selectedRun) {
        onSelectRun(selectedRun);
      }
    },
    [runsById]
  );

  return (
    <>
      {/*<Box width={0} height={0}>
        {rfNodes.map((node) => (
          <RunNode
            {...node}
            type=""
            selected
            zIndex={0}
            isConnectable
            xPos={0}
            yPos={0}
            dragging
            key={node.id}
          />
        ))}
      </Box>*/}
      <Box sx={{ width: "100%", height: "1500px", paddingX: 0, marginX: 0 }}>
        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          nodeTypes={nodeTypes}
          onInit={onInit}
          zoomOnScroll={false}
          //onConnect={onConnect}
          panOnScroll
          nodesDraggable={false}
          onNodeClick={onNodeClick}
        >
          <Background variant={BackgroundVariant.Dots} />
        </ReactFlow>
      </Box>
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
