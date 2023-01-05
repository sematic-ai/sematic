import React from "react";
import { Run } from "../Models";

export const PipelinePanelsContext = React.createContext<{
    selectedPanelItem: string;
    setSelectedPanelItem: (panelItem: string) => void;
    selectedRun: Run;
    setSelectedRun: (run: Run) => void;
} | null>(null);

export default PipelinePanelsContext;