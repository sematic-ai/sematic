import { Node, Edge } from "react-flow-renderer";
import dagre from "dagre";

/*
Builds the nested dag layout
*/
export default function buildDagLayout(
  iNodes: Node[],
  iEdges: Edge[],
  getNodeElement: (node: Node) => HTMLElement | null
): Node[] {
  let iNodesById: Map<string, Node> = new Map(
    iNodes.map((node) => [node.id, node])
  );
  let nodeDimensions = new Map(
    iNodes.map((node) => {
      let element = getNodeElement(node);
      return [
        node.id,
        {
          height: element?.clientHeight || 0,
          width: (element?.clientWidth || 0) + 5,
        },
      ];
    })
  );

  let iNodesByParentId: Map<string | null, Node[]> = new Map();
  iNodes.forEach((node) => {
    let parentNodeId = node.parentNode === undefined ? null : node.parentNode;
    iNodesByParentId.set(parentNodeId, [
      ...(iNodesByParentId.get(parentNodeId) || []),
      node,
    ]);
  });

  const rootNodes = iNodesByParentId.get(null);
  if (rootNodes === undefined || rootNodes.length === 0)
    throw Error("No root node");

  /*
    Algorithm for leaf-first BFS
    We want to create layout for the innermost graphs first
    then work our way up to the root.
    
    Stack my_stask
    Queue my_queue
    
    insert tree.root into my_queue
    
    while my_queue != empty
    pop Node node from my_queue
    push node.children into my_queue
    push node into my_stask
    
    while my_stask != empty
    pop Node node from my_stask
    print node
    */

  let queue: Array<string | null> = [null]; //rootNodes[0].id];
  let stack: Array<string | null> = [];

  // order of parent node Ids in which we should compute layout
  // Innermost sugraphs first, then moving out
  let subGraphOrder: Array<string | null> = [];

  // order in which we should render subgraphs
  // outermost first (root), then moving in
  let renderOrder: string[] = [];

  while (queue.length > 0) {
    let nodeId = queue.shift();
    if (nodeId === undefined) throw Error();

    if (nodeId !== null) {
      renderOrder.push(nodeId);
    }

    (iNodesByParentId.get(nodeId) || []).forEach((node) => {
      queue.push(node.id);
    });

    stack.push(nodeId);
  }

  while (stack.length > 0) {
    let nodeId = stack.pop();
    if (nodeId === undefined) throw Error();
    subGraphOrder.push(nodeId);
  }

  // End of graph algo, now we have subGraphOrder and renderOrder

  let iEdgesByParentId: Map<string | null, Edge[]> = new Map();
  iEdges.forEach((edge) => {
    let parentId: string | null = edge.data.parentId
      ? edge.data.parentId
      : null;
    iEdgesByParentId.set(parentId, [
      ...(iEdgesByParentId.get(parentId) || []),
      edge,
    ]);
  });

  let finalNodes: Map<string, Node> = new Map();

  subGraphOrder.forEach((parentNodeId) => {
    let childrenNodes = iNodesByParentId.get(parentNodeId);
    if (childrenNodes === undefined) return;

    // In case they were already updated
    childrenNodes = childrenNodes.map(
      (node) => finalNodes.get(node.id) || node
    );

    let dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setGraph({ rankdir: "TB" });
    dagreGraph.setDefaultNodeLabel(() => ({}));
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    childrenNodes.forEach((node) => {
      dagreGraph.setNode(node.id, {
        width: nodeDimensions.get(node.id)?.width,
        height: nodeDimensions.get(node.id)?.height,
      });
    });

    (iEdgesByParentId.get(parentNodeId) || []).forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target);
    });
    dagre.layout(dagreGraph);

    let parentNode =
      finalNodes.get(parentNodeId || "") || iNodesById.get(parentNodeId || "");

    childrenNodes.forEach((node) => {
      const dagreNode = dagreGraph.node(node.id);
      let nodeWidth = nodeDimensions.get(node.id)?.width || 0;
      let nodeHeight = nodeDimensions.get(node.id)?.height || 0;

      node.position = {
        x: dagreNode.x - (nodeWidth || 0) / 2 + 20,
        y: dagreNode.y - (nodeHeight || 0) / 2 + (parentNodeId ? 100 : 5),
      };

      node.style = {
        ...node.style,
        width: nodeWidth,
        height: nodeHeight,
      };
      node.width = nodeWidth;
      node.height = nodeHeight;

      if (parentNode) {
        let parentNodeWidth = nodeDimensions.get(parentNode.id)?.width || 0;
        parentNodeWidth = Math.max(
          parentNodeWidth,
          node.position.x + (nodeWidth || 0) + 20
        );

        let parentNodeHeight = nodeDimensions.get(parentNode.id)?.height || 0;
        parentNodeHeight = Math.max(
          parentNodeHeight || 0,
          node.position.y + (nodeHeight || 0) + 40
        );
        let parentDimensions = {
          width: parentNodeWidth,
          height: parentNodeHeight,
        };
        parentNode.style = {
          ...parentNode.style,
          ...parentDimensions,
        };
        parentNode.width = parentDimensions.width;
        parentNode.height = parentDimensions.height;
        nodeDimensions.set(parentNode.id, parentDimensions);
        finalNodes.set(parentNode.id, parentNode);
      }
      finalNodes.set(node.id, node);
    });
  });

  let orderedNodes: Node[] = [];

  renderOrder.forEach((nodeId) => {
    let node = finalNodes.get(nodeId);
    if (node !== undefined) {
      orderedNodes.push(node);
    }
  });

  return orderedNodes;
}
