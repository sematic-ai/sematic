import { useContext, useState } from "react";
import { UserContext } from "../index";
import { Run } from "../Models";
import { Filter, RunListPayload } from "../Payloads";
import { fetchJSON } from "../utils";

export function useFetchLatestRuns(runFilters: Filter | undefined = undefined, qParams: {
    [queryKey: string]: string
} = {}) {

    const { user } = useContext(UserContext);
    
    const [latestRuns, setLatestRuns] = useState<Run[]>([]);
    const [error, setError] = useState<Error | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);

    fetchJSON({
        url: "/api/v1/runs?limit=10&filters=" + JSON.stringify(runFilters),
        apiKey: user?.api_key,
        callback: (response: RunListPayload) => {
            setLatestRuns(response.content);
        },
        setError: (error => setError(error as (Error | undefined))),
        setIsLoaded,
      });
}