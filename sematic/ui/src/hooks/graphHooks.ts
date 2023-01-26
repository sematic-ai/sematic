import { useContext, useEffect, useMemo, useRef } from "react";
import useAsyncRetry from "react-use/lib/useAsyncRetry";
import GraphContext from "../pipelines/graph/graphContext";
import { Graph, RunTreeNode } from "../interfaces/graph";
import { RunGraphPayload } from "../Payloads";
import { graphSocket, testingSocket } from "../utils";
import { useHttpClient } from "./httpHooks";

export function useGraph(runRootId: string): [
    Graph | undefined,
    boolean,
    Error | undefined
] {
    const {fetch} = useHttpClient();

    const loadResultPromise = useRef<Promise<RunGraphPayload> | null>(null);

    const {value: graphPayload, loading, error, retry} = useAsyncRetry(async () => {
        loadResultPromise.current = new Promise(async (resolve) => {
            const response: RunGraphPayload = await fetch({
                url: `/api/v1/runs/${runRootId}/graph?root=1`,
            });
            resolve(response);
        });

        return await loadResultPromise.current;
    }, [runRootId, loadResultPromise]);

    const graph = useMemo<Graph | undefined >(() => {
        if (!graphPayload) {
            return undefined;
        }

        const {runs, edges, artifacts} = graphPayload;

        return {
            runs,
            runsById: new Map(runs.map((run) => [run.id, run])), 
            edges, 
            artifacts,
            artifactsById: new Map((artifacts || []).map((artifact) => [artifact.id, artifact]))
        }

    }, [graphPayload]);

    // Auto manage reloading by hooking up with graphSocket.
    useEffect(() => {
        testingSocket.removeAllListeners();
        var received = [];
        testingSocket.on("update", (args: any) => {
            received.push(1);
            console.log(args);
            console.log("Received " + received.length + " of " + args.n);
        });

        graphSocket.removeAllListeners();
        graphSocket.on("update", (args: { run_id: string }) => {
          if (args.run_id === runRootId) {
            setTimeout(async () => {
                if (loadResultPromise.current) {
                    await loadResultPromise.current;
                }
                retry();
            });
          }
        });
      }, [runRootId, retry, loadResultPromise])

    return [graph, loading, error];
}

export function useRunsTree(graph: Graph | undefined) {
    return useMemo(() => {
        if (!graph) {
            return undefined;
        }

        const rootTreeNode: RunTreeNode = {
            run: null,
            children: []
        };

        const runTreeNodeMappinng = new Map<string, RunTreeNode>(
            graph.runs.map(run => {
                return [run.id, { run, children: []}];
            })
        );

        graph.runs.forEach(run => {
            const {id, parent_id} = run;
            const parentNode = parent_id ? runTreeNodeMappinng.get(parent_id) : rootTreeNode;
            const treeNode = runTreeNodeMappinng.get(id);
            parentNode!.children.push(treeNode!);
        });
        return rootTreeNode;
    }, [graph]);
}

export function useGraphContext() {
    const contextValue = useContext(GraphContext);

    if (!contextValue) {
        throw new Error('useGraphContext() should be called under a provider.')
    }

    return contextValue
}
