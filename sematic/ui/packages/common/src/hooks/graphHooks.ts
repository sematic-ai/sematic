import { useHttpClient } from "src/hooks/httpHooks";
import { useLogger } from "src/utils/logging";
import { useCallback, useContext, useEffect, useMemo, useRef } from "react";
import useAsyncRetry from "react-use/lib/useAsyncRetry";
import usePrevious from "react-use/lib/usePrevious";
import { RunGraphPayload } from "src/ApiContracts";
import { Graph, RunTreeNode } from "src/interfaces/graph";
import GraphContext from "src/context/graphContext";
import { graphSocket } from "../sockets";
import includes from "lodash/includes";
import { HIDDEN_RUN_NAME_LIST } from "src/constants";

export function useGraph(runRootId: string): [
    Graph | undefined,
    boolean,
    Error | undefined
] {
    const {fetch} = useHttpClient();
    const { devLogger } = useLogger();

    const {value: graphPayload, loading, error, retry} = useAsyncRetry(async () => {
        const response = await fetch({
            url: `/api/v1/runs/${runRootId}/graph?root=1`,
        });

        return (await response.json()) as RunGraphPayload;
    }, [runRootId]);

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

    const retryPending = useRef(false);

    const prevLoading = usePrevious(loading);

    useEffect(() => {
        if (prevLoading&& !loading && retryPending.current) {
            retryPending.current = false;
            devLogger("Loading state has switched from true to false," 
                + " and reloading was requested. reloading now...");
            retry();
        }
    }, [loading, prevLoading, retry, devLogger]);

    const graphSocketUpdateHandler = useCallback(async (args: { run_id: string }) => {
        devLogger("Handler triggered with:", args);
        if (args.run_id === runRootId) {
            if (loading) {
                devLogger("Reloading is requested but an ongoing loading process is present." +
                " Mark the state for retrying later.");
                retryPending.current = true;
            } else {
                devLogger("There was no ongoing loading process. Directly reload.")
                retry();
            }
        }
    }, [runRootId, loading, retry, devLogger]); 

    const graphSocketCallbackRef = useRef<(args: { run_id: string })=> Promise<void>>(
        async() => {}
    );

    const onGraphUpdate = useCallback((args: { run_id: string }) => {
        graphSocketCallbackRef.current(args);
    }, [graphSocketCallbackRef]);

    useEffect(() => {
        graphSocketCallbackRef.current = graphSocketUpdateHandler;
    }, [graphSocketUpdateHandler])

    // Auto manage reloading by hooking up with graphSocket.
    useEffect(() => {
        graphSocket.removeAllListeners();
        graphSocket.on("update", onGraphUpdate);
    }, [onGraphUpdate]);

    return [graph, loading, error];
}

/**
 * Sort the run tree by start time.
 * @param rootTreeNode 
 */
function sortRunTree(rootTreeNode: RunTreeNode) {
    const queue = [rootTreeNode];
    while (queue.length > 0) {
        const treeNode = queue.shift()!;
        treeNode.children.sort((a, b) => {
            const aRun = a.run!;
            const bRun = b.run!;

            const aCreatedTime = new Date(aRun.created_at);
            const bCreatedTime = new Date(bRun.created_at);

            if (aCreatedTime < bCreatedTime) {
                return 1;
            } else if (aCreatedTime > bCreatedTime) {
                return -1;
            } else {
                return 0;
            }
        });
        queue.push(...treeNode.children);
    }
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

        // We need to filter out runs whose functions are present in the hidden run name list.
        const filteredRuns = graph.runs.filter(run => !includes(HIDDEN_RUN_NAME_LIST, run.name));

        const runTreeNodeMappinng = new Map<string, RunTreeNode>(
            filteredRuns.map(run => {
                return [run.id, { run, children: []}];
            })
        );

        filteredRuns.forEach(run => {
            const {id, parent_id} = run;
            const parentNode = parent_id ? runTreeNodeMappinng.get(parent_id) : rootTreeNode;
            const treeNode = runTreeNodeMappinng.get(id);
            parentNode!.children.push(treeNode!);
        });
        sortRunTree(rootTreeNode);
        return rootTreeNode;
    }, [graph]);
}

export function useGraphContext() {
    const contextValue = useContext(GraphContext);

    if (!contextValue) {
        throw new Error("useGraphContext() should be called under a provider.")
    }

    return contextValue
}
