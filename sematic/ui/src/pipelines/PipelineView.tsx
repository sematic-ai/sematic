import { useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import Loading from "../components/Loading";
import { useFetchRuns, usePipelineNavigation } from "../hooks/pipelineHooks";
import { Alert } from "@mui/material";

/**
 * This page doesn't do detailed rendering, its main focus is to 
 * load the latest runs, pick the first run, then redirect to that
 * run's detail view.
 * 
 * @returns JSX.element
 */
export default function PipelineView() {
    const params = useParams();
    const { calculatorPath } = params;

    const runFilters = useMemo(() => ({
        "AND": [
          { parent_id: { eq: null } },
          { calculator_path: { eq: calculatorPath! } },
        ]
      }), [calculatorPath]);

    const otherQueryParams = useMemo(() => ({
        limit: '10'
    }), []);

    const {isLoaded, error, runs: latestRuns} = useFetchRuns(runFilters, otherQueryParams);

    const navigate = usePipelineNavigation(calculatorPath!);

    useEffect(() => {
        if (!isLoaded || !!error) {
            return;
        }

        if (latestRuns.length > 0) {
            navigate(latestRuns[0].root_id, true);
        }

    }, [isLoaded, error, latestRuns, navigate])

    return <>
        { !isLoaded && <Loading isLoaded={false} /> }
        { !!error && <Alert severity="error">{error.message}</Alert> }
    </>;
}
