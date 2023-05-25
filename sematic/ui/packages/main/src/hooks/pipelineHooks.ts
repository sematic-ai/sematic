import { atomWithHashCustomSerialization } from "@sematic/common/src/utils/url";
import { useContext } from "react";
import PipelinePanelsContext from "src/pipelines/PipelinePanelsContext";
import PipelineRunViewContext from "src/pipelines/PipelineRunViewContext";

export type QueryParams = {[key: string]: string};

export const selectedPanelHashAtom = atomWithHashCustomSerialization("panel", "")

export function usePipelineRunContext() {
    const contextValue = useContext(PipelineRunViewContext);

    if (!contextValue) {
        throw new Error("usePipelineRunContext() should be called under a provider.")
    }

    return contextValue;
}

export function usePipelinePanelsContext() {
    const contextValue = useContext(PipelinePanelsContext);

    if (!contextValue) {
        throw new Error("usePipelinePanelsContext() should be called under a provider.")
    }

    return contextValue;
}
