import { Resolution, Run } from "@sematic/common/src/Models";
import React from "react";

export const PipelineRunViewContext = React.createContext<{
    rootRun: Run | undefined;
    resolution: Resolution | undefined;
    isLoading: boolean;
} | null>(null);

export default PipelineRunViewContext;