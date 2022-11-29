import React, { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { UserContext } from "../index";
import { Run } from "../Models";
import { Filter, RunListPayload } from "../Payloads";
import { fetchJSON } from "../utils";

export function useFetchLatestRuns(runFilters: Filter | undefined = undefined) {
    const { user } = useContext(UserContext);
    
    const [latestRuns, setLatestRuns] = useState<Run[]>([]);
    const [error, setError] = useState<Error | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        fetchJSON({
            url: "/api/v1/runs?limit=10&filters=" + JSON.stringify(runFilters),
            apiKey: user?.api_key,
            callback: (response: RunListPayload) => {
                setLatestRuns(response.content);
            },
            setError: (error => setError(error as React.SetStateAction<Error | null>)),
            setIsLoaded,
          });
    }, [setLatestRuns, setError, setIsLoaded, user, runFilters])

    return {isLoaded, error, latestRuns};
}

export function usePipelineNavigation(pipelinePath: string) {
    const navigate = useNavigate();
    const { rootId } = useParams();

    return useCallback((requestedRootId: string, replace: boolean) => {
        if ( rootId === requestedRootId ) {
            return
        }

        navigate(`/pipelines/${pipelinePath}/${requestedRootId}`, {
            replace
        });
    }, [pipelinePath, rootId, navigate]);
}