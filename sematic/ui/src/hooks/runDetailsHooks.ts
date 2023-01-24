import { useContext } from "react";
import RunPanelContext from "../pipelines/RunDetailsContext";

export function useRunPanelContext() {
    const contextValue = useContext(RunPanelContext);

    if (!contextValue) {
        throw new Error('useRunPanelContext() should be called under a provider.')
    }

    return contextValue;
}
