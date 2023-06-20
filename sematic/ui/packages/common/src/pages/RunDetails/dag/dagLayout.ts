import dagre from "dagre";
import includes from "lodash/includes";
import { Node, Position, Edge as RFEdge } from "reactflow";
import { Edge, Run } from "src/Models";
import { HIDDEN_RUN_NAME_LIST } from "src/constants";
import { Graph } from "src/interfaces/graph";
import { LEFT_NODE_MAX_WIDTH, NodeTypes } from "src/pages/RunDetails/dag/common";
import theme from "src/theme/new";

export const SPACING = parseFloat(theme.spacing(4).replace("px", ""));
export const SVG_ICON_WIDTH = 20;
/**
 * dedupEdges() removes duplicate edges which come from the same source and go to the same target.
 * 
 * @param edges 
 * @returns 
 */
function dedupEdges(edges: Edge[]) {
    const seen = new Map<string, Set<string>>();

    const filteredEdges: Edge[] = [];

    for (const edge of edges) {
        const source = edge.source_run_id || "null";
        const target = edge.destination_run_id || "null";
        if (!seen.has(source)) {
            seen.set(source, new Set());
        }

        const entry = seen.get(source)!;

        if (entry.has(target)) {
            continue;
        }
        seen.get(source)!.add(target);
        filteredEdges.push(edge);
    }
    return filteredEdges;
}

function removeHiddenNodes(nodes: Node[], edges: Edge[], runsById: Map<string, Run>) {
    const toHiddenNode = new Map<string, Set<Edge>>();
    const fromHiddenNode = new Map<string, Set<Edge>>();

    const edgesByIds = new Map<string, Edge>(edges.map((edge) => [edge.id, edge]));

    // initialize maps
    for (const node of nodes) {
        if (includes(HIDDEN_RUN_NAME_LIST, runsById.get(node.id)?.name)) {
            toHiddenNode.set(node.id, new Set());
            fromHiddenNode.set(node.id, new Set());
        }
    }

    // Avoid O(N) look up by using maps
    function addEdgeToMetaData(edge: Edge) {
        if (edge.source_run_id) {
            const sourceNode = runsById.get(edge.source_run_id);
            if (sourceNode && includes(HIDDEN_RUN_NAME_LIST, sourceNode.name)) {
                fromHiddenNode.get(edge.source_run_id)!.add(edge);
            }
        }
        if (edge.destination_run_id) {
            const targetNode = runsById.get(edge.destination_run_id);
            if (targetNode && includes(HIDDEN_RUN_NAME_LIST, targetNode.name)) {
                toHiddenNode.get(edge.destination_run_id)!.add(edge);
            }
        }
    }

    function removeMetadataForNode(nodeId: string, sourceEdge: Edge, targetEdge: Edge) {
        fromHiddenNode.get(nodeId)?.delete(sourceEdge);
        toHiddenNode.get(nodeId)?.delete(targetEdge);
    }

    for (const edge of edges) {
        addEdgeToMetaData(edge);
    }

    for (const node of nodes) {
        if (!includes(HIDDEN_RUN_NAME_LIST, runsById.get(node.id)?.name)) {
            continue;
        }
        const nodeId = node.id;
        // remove node and reconnet incomming and outgoing edges
        toHiddenNode.get(nodeId)?.forEach(sourceEdge => {
            fromHiddenNode.get(nodeId)?.forEach(targetEdge => {
                if (!sourceEdge.source_run_id) {
                    return;
                }
                const newEdge: Edge = ({
                    id: sourceEdge.source_run_id + targetEdge.id,
                    source_run_id: sourceEdge.source_run_id!,
                    destination_run_id: targetEdge.destination_run_id!
                }) as unknown as Edge;

                edgesByIds.set(newEdge.id, newEdge);
                addEdgeToMetaData(newEdge);

                edgesByIds.delete(sourceEdge.id);
                edgesByIds.delete(targetEdge.id);
                removeMetadataForNode(nodeId, sourceEdge, targetEdge);
            })
        });
    }

    // remove hidden nodes
    const filteredNodes = nodes.filter((node) => !includes(HIDDEN_RUN_NAME_LIST, runsById.get(node.id)?.name));

    return { nodes: filteredNodes, edges: Array.from(edgesByIds.values()) };
}

export function getReactFlowDag(graph: Graph | undefined, selectedRun: Run | undefined) {
    if (!graph) {
        return { nodes: undefined, edges: undefined };
    }

    const { runs, edges, runsById } = graph;

    let nodeData: Node[] = runs.map((run) => {
        let runArgNames: string[] = [];

        edges.forEach((edge) => {
            if (edge.destination_run_id === run.id) {
                runArgNames.push(edge.destination_name || "");
            }
        });

        return {
            type: NodeTypes.LEAF,
            id: run.id,
            data: {
                label: run.name, run, argNames: runArgNames,
                selected: run.id === selectedRun?.id,
            },
            parentNode: run.parent_id === null ? undefined : run.parent_id,
            position: { x: 0, y: 0 },
            extent: run.parent_id === null ? undefined : "parent",
            zIndex: 0,
            selectable: false
        };
    });
    
    let filteredEdges: Edge[];
    ({nodes: nodeData, edges: filteredEdges} = removeHiddenNodes(nodeData, edges, runsById));

    const edgeData: RFEdge[] = [];
    (dedupEdges(filteredEdges)).forEach((edge) => {
        let parentId = runsById.get(edge.destination_run_id || edge.source_run_id || "")
            ?.parent_id || undefined;

        const newEdge: RFEdge = {
            id: edge.source_run_id + edge.id,
            source: edge.source_run_id!,
            target: edge.destination_run_id!,
            data: { parentId: parentId },
            focusable: false,
            deletable: false,
            updatable: false,
            zIndex: 1000,
        }

        if (!newEdge.target) {
            newEdge.target = runsById.get(newEdge.source)?.parent_id!;
            newEdge.targetHandle = "tb";
            newEdge.sourceHandle = "sb";
            newEdge.type = "straight";
        }
        if (!newEdge.source) {
            // skip edges that don't have a source. This means the source is the parent node of the target.
            // or the source represents the inputs of the pipeline.
            return;
        }
        edgeData.push(newEdge);
    });

    return { nodes: nodeData, edges: edgeData };
}

type SubGraph = {
    root: Node;
    children: SubGraph[];
}

export function buildTree(nodes: Node[]) {
    const nodeMap = new Map<string, SubGraph>();
    nodes.forEach((node) => {
        // default to leaf node, will be overwritten if it's a compound node.
        node.type = NodeTypes.LEAF;
        nodeMap.set(node.id, {
            root: node,
            children: []
        });
    });

    const rootNodes: SubGraph[] = [];
    nodes.forEach((node) => {
        const parentNode = nodeMap.get(node.parentNode || "");
        if (parentNode) {
            parentNode.root.type = NodeTypes.COMPOUND;
            parentNode.children.push(nodeMap.get(node.id || "")!);
        } else {
            rootNodes.push(nodeMap.get(node.id)!);
        }
    });

    return rootNodes;
}

export function layout(nodes: Node[], edges: RFEdge[]) {
    const roots = buildTree(nodes);

    const stack: Array<SubGraph> = [...roots];
    let i = 0;

    // DFS to expand all the subgraphs which will require layout.
    while (i !== stack.length) {
        const root = stack[i];
        const children = root.children;
        for (const child of children) {
            if (child.root.type === NodeTypes.COMPOUND) {
                stack.push(child);
            }
        }
        i++;
    }
    let nodeInRenderingOrder: Node[]  = [];
    // reverse depleting the stack so we can layout the leaves first.
    while (stack.length) {
        const lastRoot = stack.pop()!;
        dagreLayout(lastRoot, edges);

        // Add the root node to the front of the list so the leaves 
        // are rendered later in the DOM tree. This is to ensure the
        // leaves are rendered on top of the compound nodes.
        nodeInRenderingOrder = nodeInRenderingOrder.concat(
            lastRoot.children.map(subGraph => subGraph.root),
            nodeInRenderingOrder);
        nodeInRenderingOrder.unshift(lastRoot.root);
    }

    return nodeInRenderingOrder;
}

function dagreLayout(subgraph: SubGraph, edges: RFEdge[]) {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));
    dagreGraph.setGraph({ rankdir: "TB" });

    subgraph.children.forEach(({ root: node }) => {
        if (node.type === NodeTypes.LEAF) {
            node.width = Math.min(node.width! + SPACING * 2 + SVG_ICON_WIDTH, LEFT_NODE_MAX_WIDTH);
        }
        dagreGraph.setNode(node.id, { width: node.width, height: node.height });
    });

    const nodeIds = new Set(subgraph.children.map(({ root: node }) => node.id));

    // only consider relevant edges.
    edges.forEach((edge) => {
        if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) {
            return;
        }
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    subgraph.children.forEach(({ root: node }) => {
        const nodeWithPosition = dagreGraph.node(node.id);
        node.targetPosition = Position.Top;
        node.sourcePosition = Position.Bottom;

        // We are shifting the dagre node position (anchor=center center) to the top left
        // so it matches the React Flow node anchor point (top left).
        node.position = {
            x: nodeWithPosition.x - node.width! / 2,
            y: nodeWithPosition.y - node.height! / 2,
        };

        return node;
    });

    const dagereGraph = dagreGraph.graph();

    adjustSubgraphWithSpacing(subgraph, dagereGraph);
}

function adjustSubgraphWithSpacing(subgraph: SubGraph, dagreGraph: dagre.GraphLabel) {
    const graphWidth = Math.max(dagreGraph.width! + SPACING * 2, 200);
    const horizontalShift = (graphWidth - dagreGraph.width!) / 2;
    const graphHeight = dagreGraph.height! + SPACING * 2 + 50;

    subgraph.root.width = graphWidth;
    subgraph.root.height = graphHeight;
    subgraph.root.data.width = graphWidth;
    subgraph.root.data.originalWidth = graphWidth;
    subgraph.root.data.height = graphHeight;
    subgraph.root.data.originalHeight = graphHeight;

    const { children } = subgraph;

    children.forEach(({ root: node }) => {
        node.position.x += horizontalShift;
        node.position.y += SPACING + 50;
    });
}

