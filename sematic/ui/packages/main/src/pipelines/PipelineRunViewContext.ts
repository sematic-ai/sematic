import React from "react";
import { Resolution, Run } from "../Models";

export const PipelineRunViewContext = React.createContext<{
    rootRun: Run | undefined;
    resolution: Resolution | undefined;
    isLoading: boolean;
} | null>(null);

export default PipelineRunViewContext;