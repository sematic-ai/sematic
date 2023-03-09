import { Artifact, Edge, Run } from "../Models";
export interface Graph {
    runs: Array<Run>;
    runsById: Map<string, Run>;
    edges: Edge[];
    artifacts: Artifact[];
    artifactsById: Map<string, Artifact>;
}

export interface RunTreeNode {
    run: Run | null;
    children: Array<RunTreeNode>;
}
