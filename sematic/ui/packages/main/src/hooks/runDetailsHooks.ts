import { useContext, useEffect } from "react";
import RunPanelContext from "../pipelines/RunDetailsContext";

export function useRunPanelContext() {
    const contextValue = useContext(RunPanelContext);

    if (!contextValue) {
        throw new Error('useRunPanelContext() should be called under a provider.')
    }

    return contextValue;
}

export function useRunPanelLoadingIndicator(isLoading: boolean) {
    const { setIsLoading } = useRunPanelContext();

    useEffect(() => {
        setIsLoading(isLoading);
        return () => {
            setIsLoading(false);
        }
    }, [setIsLoading, isLoading]);
}
