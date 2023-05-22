import React from "react";
import { Resolution, Run } from "src/Models";
import { Graph } from "src/interfaces/graph";

export const RootRunContext = React.createContext<{
    rootRun: Run | undefined;
    resolution: Resolution | undefined;
    graph: Graph | undefined;
    isResolutionLoading: boolean;
    isGraphLoading: boolean;
} | null>(null);

export default RootRunContext;

export function useRootRunContext() {
    const context = React.useContext(RootRunContext);
    if (!context) {
        throw new Error(
            "useRootRunContext must be used within a RootRunContextProvider"
        );
    }
    return context;
}
