import React from "react";
import { Run } from "src/Models";

export const RunDetailsSelectionContext = React.createContext<{
    selectedRun: Run | undefined;
    setSelectedRunId: (runId: string) => void;
} | null>(null);

export default RunDetailsSelectionContext;

export function useRunDetailsSelectionContext() {
    const context = React.useContext(RunDetailsSelectionContext);
    if (!context) {
        throw new Error(
            "useRunDetailsSelectionContext must be used within a RunDetailsSelectionContextProvider"
        );
    }
    return context;
}
