import styled from "@emotion/styled";
import { RESET } from "jotai/utils";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useCounter from "react-use/lib/useCounter";
import ReactFlow, { Edge, Node, ReactFlowInstance, useEdgesState, useNodesState } from "reactflow";
import { useRootRunContext } from "src/context/RootRunContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import CompoundNode from "src/pages/RunDetails/dag/CompoundNode";
import LeafNode from "src/pages/RunDetails/dag/LeafNode";
import { DagViewServiceContext, NodeTypes } from "src/pages/RunDetails/dag/common";
import { getReactFlowDag, layout } from "src/pages/RunDetails/dag/dagLayout";

const NodeContainer = styled.div`
    width: max-content;
`;

interface ReactFlowDagScratchPadProps {
    nodes: Node[] | undefined;
    onNodesMeasured: (node: Node[]) => void;
}

function ReactFlowDagScratchPad(props: ReactFlowDagScratchPadProps) {
    const { nodes, onNodesMeasured } = props;

    const scratchPad = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!nodes) {
            return;
        }

        const domNodes = scratchPad.current!.querySelectorAll(".node-container");

        // assign initial width to nodes
        domNodes.forEach((domNode, index) => {
            const graphNode = nodes[index];
            graphNode.width = domNode.clientWidth;
            graphNode.height = 50;
        });

        onNodesMeasured(nodes);
    }, [nodes, onNodesMeasured]);

    if (!nodes) {
        return null;
    }

    return <div ref={scratchPad} style={{ visibility: "hidden", position: "absolute" }}>
        {nodes.map((node, index) => {
            return <NodeContainer className="node-container" key={index}>
                {node.data.label}
            </NodeContainer>
        })}
    </div>
}

function ReactFlowDagStaging() {
    const { graph, isGraphLoading } = useRootRunContext();
    const { selectedRun, setSelectedRunId, setSelectedPanel } = useRunDetailsSelectionContext();

    const [nodes, setNodes] = useState<Node[] | undefined>(undefined);
    const [edges, setEdges] = useState<Edge[] | undefined>(undefined);
    const [version, { inc: incVersion }] = useCounter(0);

    const [layoutDone, setLayoutDone] = useState(false);

    const onNodesMeasured = useCallback((nodes: Node[]) => {
        const updatedNodesOrder = layout(nodes, edges!);

        setNodes(updatedNodesOrder);
        setEdges(edges);
        setLayoutDone(true);
        incVersion();
    }, [setLayoutDone, edges, incVersion]);

    const onNodeSelectionChange = useCallback((nodeId: string) => {
        setSelectedPanel(RESET);
        if (nodeId === selectedRun?.id) {
            return;
        }
        setSelectedRunId(nodeId);
    }, [selectedRun, setSelectedRunId, setSelectedPanel]);

    useEffect(() => {
        if (isGraphLoading) {
            return;
        }
        // isGraphLoading === false
        setLayoutDone(false);
        const { nodes, edges } = getReactFlowDag(graph, selectedRun);

        setNodes(nodes);
        setEdges(edges);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isGraphLoading]);

    const dagView = useMemo(() => {
        if (version === 0) {
            return null;
        }
        return <DagViewServiceContext.Provider value={{
            onNodeClick: onNodeSelectionChange
        }} >
            <ReactFlowDag nodes={nodes!} edges={edges!} />
        </DagViewServiceContext.Provider >
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [version]);

    return <>
        {!layoutDone && <div>
            <ReactFlowDagScratchPad nodes={nodes} onNodesMeasured={onNodesMeasured} />
        </div>}
        {dagView}
    </>
}

interface ReactFlowDagProps {
    nodes: Node[];
    edges: Edge[];
}

const nodeTypes = {
    [NodeTypes.COMPOUND]: CompoundNode,
    [NodeTypes.LEAF]: LeafNode
};

function ReactFlowDag(props: ReactFlowDagProps) {
    const { nodes: _nodes, edges: _edges } = props;

    const [nodes, setNodes, onNodesChange] = useNodesState(_nodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(_edges);
    const reactFlowRef = useRef<ReactFlowInstance>()

    useEffect(() => {
        setNodes([..._nodes]);
        setEdges([..._edges]);
        reactFlowRef.current?.fitView({
            maxZoom: 1,
        });
    }, [_nodes, _edges, setNodes, setEdges]);

    return <div style={{ width: "100%", height: "100%" }}>
        <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onInit={reactFlow => reactFlowRef.current = reactFlow}
            fitView
            fitViewOptions={{maxZoom: 1}}
        />
    </div>;
}

export default ReactFlowDagStaging;
