import React from "react";
import { Resolution, Run } from "src/Models";

export const RootRunContext = React.createContext<{
    rootRun: Run | undefined;
    resolution: Resolution | undefined;
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
