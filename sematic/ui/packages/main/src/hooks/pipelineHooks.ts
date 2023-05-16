import { Resolution, Run } from "@sematic/common/src/Models";
import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import { RESET } from "jotai/utils";
import { useCallback, useContext } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import useAsync from "react-use/lib/useAsync";
import { ResolutionPayload, RunViewPayload } from "src/Payloads";
import PipelinePanelsContext from "src/pipelines/PipelinePanelsContext";
import PipelineRunViewContext from "src/pipelines/PipelineRunViewContext";
import { atomWithHashCustomSerialization } from "src/utils";
import { getRunUrlPattern } from "@sematic/common/src/hooks/runHooks";

export type QueryParams = {[key: string]: string};

export const selectedRunHashAtom = atomWithHashCustomSerialization("run", "")
export const selectedTabHashAtom = atomWithHashCustomSerialization("tab", "")
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

export function useFetchRun(runID: string): [
    Run | undefined, boolean, Error | undefined
] {
    const {fetch} = useHttpClient();

    const {value, loading, error} = useAsync(async () => {
        const response = await fetch({
            url: `/api/v1/runs/${runID}`
        });
        return (await response.json() as RunViewPayload).content
    }, [runID]);
    
    return [value, loading, error];
}

export function useFetchResolution(resolutionId: string): [
    Resolution | undefined, boolean, Error | undefined
] {
    const {fetch} = useHttpClient();

    const {value, loading, error} = useAsync(async () => {
        const response  = await fetch({
            url: `/api/v1/resolutions/${resolutionId}`
        });
        return ((await response.json()) as ResolutionPayload).content;
    }, [resolutionId]);
    
    return [value, loading, error];
}

export function useRunNavigation() {
    const navigate = useNavigate();
    const { hash } = useLocation();

    return useCallback((requestedRootId: string, replace: boolean = false,
        hashOverrideValues: Record<string, string | Symbol> | undefined = undefined) => {

        let newHashValue = hash.replace(/^#/, "");

        if (hashOverrideValues) {
            newHashValue = updateHash(hash, hashOverrideValues);
        }

        navigate({
            pathname: getRunUrlPattern(requestedRootId),
            hash: newHashValue
        }, {
            replace
        });
    }, [hash, navigate]);
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

function updateHash(currentHash: string, hashOverrideValues: Record<string, string | Symbol>) {
    let newHashValue = currentHash.replace(/^#/, "");

    const searchParams = new URLSearchParams(newHashValue);
    for (const key of Object.keys(hashOverrideValues)) {
        const value = hashOverrideValues[key]; 
        if (value === RESET) {
            searchParams.delete(key);
        } else {
            searchParams.set(key, value as string);
        }
    }
    return searchParams.toString();
}
