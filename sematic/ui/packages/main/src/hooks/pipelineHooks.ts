import { atomWithHashCustomSerialization, updateHash } from "@sematic/common/src/utils/url";
import { useCallback, useContext } from "react";
import { useLocation, useNavigate } from "react-router-dom";
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

export function useHashUpdater() {
    const { hash } = useLocation();
    const navigate = useNavigate();

    return useCallback((
        hashOverrideValues: Record<string, string | Symbol>, replace: boolean = false) => {
        let newHashValue = hash.replace(/^#/, "");

        newHashValue = updateHash(newHashValue, hashOverrideValues);

        navigate({
            hash: newHashValue
        }, {
            replace
        });
    }, [hash, navigate]);
}
