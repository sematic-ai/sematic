import { useCallback, useMemo } from "react";
import { Edge, Node, getIncomers, useEdges, useNodeId, useNodes, useReactFlow } from "reactflow";

function isAncestorOfNode(node: Node, ancestorNodeId: string, nodesById: Map<string, Node>) {
    let tempNode: Node | undefined = node;
    while (tempNode) {
        if (tempNode.id === ancestorNodeId) {
            return true;
        }
        tempNode = !!tempNode.parentNode ? nodesById.get(tempNode.parentNode) : undefined;
    }
    return false;
}

function hideAllConnectedEdge(edge: Edge[], newNodes: Node[]) {
    const hiddenNode = new Set(newNodes.filter((node) => node.hidden).map((node) => node.id));

    return edge.map((edge) => {
        const { source, target } = edge;
        return {
            ...edge,
            hidden: hiddenNode.has(source) || hiddenNode.has(target),
        };
    });
}

export function useNodeExpandStateToggle(data: any) {
    const expanded = data.expanded ?? true;

    const nodeId = useNodeId();
    const reactFlow = useReactFlow();

    const toggleExpanded = useCallback(() => {
        reactFlow.setNodes((nodes) => {
            const nodesById = new Map(nodes.map((node) => [node.id, node]));
            const newNodeState = nodes.map((node) => {
                if (node.id === nodeId) {
                    return {
                        ...node,
                        data: {
                            ...node.data,
                            expanded: !expanded,
                            height: !expanded ? node.data.originalHeight : 50,
                        },
                    };
                }
                if (isAncestorOfNode(node, nodeId!, nodesById)) {
                    return {
                        ...node,
                        hidden: expanded,
                        data: {
                            ...node.data,
                            expanded: true,
                            height: node.data.originalHeight
                        }
                    };
                }
                return node;
            });

            reactFlow.setEdges((edges) => {
                return hideAllConnectedEdge(edges, newNodeState);
            });

            return newNodeState;
        });
    }, [expanded, nodeId, reactFlow]);

    return { toggleExpanded, expanded };
}

export function useHasIncoming() {
    const nodeId = useNodeId();
    const nodes = useNodes();
    const edges = useEdges();

    return useMemo(() => {
        const node = nodes.find(n => n.id === nodeId);
        const incomers = getIncomers(node!, nodes, edges);
        if (incomers.length === 0) {
            return false;
        }
        if (incomers.every((node) => node.parentNode === nodeId)) {
            return false;
        }
        return true;
    }, [nodeId, nodes, edges])
} ;
