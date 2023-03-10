import { Run, Edge } from "../../Models";
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
import buildDagLayout from "../../components/utils/buildDagLayout";
import RunNode from "./RunNode";
import ArtifactNode from "./ArtifactNode";
import { usePipelinePanelsContext } from "../../hooks/pipelineHooks";
import { useGraphContext } from "../../hooks/graphHooks";
import { ExtractContextType } from "../../components/utils/typings";
import PipelinePanelsContext from "../PipelinePanelsContext";
import HiddenRunNode from "./HiddenRunNode";
import { HIDDEN_RUN_NAME_LIST } from "../../constants";

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

const nodeTypes = {
  runNode: RunNode,
  hiddenRunNode: HiddenRunNode,
  artifactNode: ArtifactNode,
};

function ReactFlowDag() {
  const { graph } = useGraphContext();

  const { runs, edges } = graph!;

  const { selectedRun, setSelectedPanelItem, setSelectedRunId, setSelectedRunTab, setSelectedArtifactName } 
  = usePipelinePanelsContext() as ExtractContextType<typeof PipelinePanelsContext> & {
    selectedRun: Run
  };

  const onSelectRun = useCallback((runId: string) => {
    setSelectedRunTab("output");
    setSelectedRunId(runId);
    setSelectedPanelItem("run");
  }, [setSelectedRunTab, setSelectedRunId, setSelectedPanelItem]);

  const runsById = useMemo(
    () => new Map(runs.map((run) => [run.id, run])),
    [runs]
  );
  const edgesById = useMemo(
    () => new Map(edges.map((edge) => [edge.id, edge])),
    [edges]
  );

  const onSelectArtifact = useCallback((node: Node) => {
    const runId = node.data.sourceRunId || node.data.destinationRunId;
    const artifactRun = graph?.runsById.get(runId);

    if (artifactRun) {
      setSelectedRunTab(node.data.sourceRunId ? "output" : "input");
      //Labels do not exist for output artifacts and they are labelled as null.
      setSelectedArtifactName(node.data.label || "null");
      setSelectedRunId(artifactRun.id);
      setSelectedPanelItem("run");
    }
  }, [graph, setSelectedRunTab, setSelectedRunId, setSelectedPanelItem, setSelectedArtifactName]);

  const [rfNodes, setRFNodes] = useNodesState([]);
  const [rfEdges, setRFEdges] = useEdgesState([]);

  const getNodesEdges = useCallback(() => {
    let node_data: Node[] = [];
    let edge_data: RFEdge[] = [];
    node_data = runs.map((run) => {
      let runArgNames: string[] = [];
      const isHiddenRun = HIDDEN_RUN_NAME_LIST.indexOf(run.name) !== -1;

      edges.forEach((edge) => {
        if (edge.destination_run_id === run.id) {
          runArgNames.push(edge.destination_name || "");
        }
      });

      return {
        type: isHiddenRun ? "hiddenRunNode" : "runNode",
        id: run.id,
        data: { label: run.name, run: run, argNames: runArgNames },
        parentNode: run.parent_id === null ? undefined : run.parent_id,
        selected: run.id === selectedRun.id,
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
            artifactId: edge.artifact_id,
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
  }, [runs, edges, runsById, edgesById, selectedRun.id]);

  useEffect(() => {
    let nodesEdges = getNodesEdges();
    setRFNodes(nodesEdges.nodes);
    setRFEdges(nodesEdges.edges);
  }, [runs, getNodesEdges, setRFNodes, setRFEdges]);

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
    [setRFNodes, setRFEdges]
  );

  const onNodeClick = useCallback(
    (event: any, node: Node) => {
      if (node.type === "artifactNode") {
        onSelectArtifact(node);
      } else {
        let selectedRun = runsById.get(node.id);
        if (selectedRun) {
          onSelectRun(selectedRun.id);
        }
    }
  },[runsById, onSelectRun, onSelectArtifact]);

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

export function FlowWithProvider(props: any) {
  return (
    <ReactFlowProvider>
      <ReactFlowDag {...props} />
    </ReactFlowProvider>
  );
}

export default ReactFlowDag;
