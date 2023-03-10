import { Run } from "@sematic/common/src/Models";
import React from "react";

export const PipelinePanelsContext = React.createContext<{
    selectedPanelItem: string;
    setSelectedPanelItem: (panelItem: string) => void;
    selectedRun: Run | undefined;
    setSelectedRunId: (runId: string) => void;
    selectedRunTab: string;
    setSelectedRunTab: (runTab: string) => void;
    selectedArtifactName: string;
    setSelectedArtifactName: (artifactName: string) => void;
} | null>(null);

export default PipelinePanelsContext;