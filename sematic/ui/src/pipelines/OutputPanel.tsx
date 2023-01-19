import { Alert } from "@mui/material";
import { useMemo } from "react";
import { Link } from "react-router-dom";
import { getPipelineUrlPattern, usePipelinePanelsContext } from "../hooks/pipelineHooks";
import { Artifact } from "../Models";
import { ArtifactList } from "./Artifacts";

export default function OutputPanel(props: {
    outputArtifacts: Map<string, Artifact | undefined>
}) {
    const { outputArtifacts } = props;
    const { selectedRun } = usePipelinePanelsContext();
    const { future_state } = selectedRun!;

    const logsLinkPath = useMemo(
        () => {
            const { calculator_path, id} = selectedRun!;
            return {
                pathname: getPipelineUrlPattern(calculator_path, id),
                hash: 'tab=logs'
            }
        }, [selectedRun]);

    return <>
        {["CREATED", "SCHEDULED", "RAN"].includes(future_state) && (
            <Alert severity="info">No output yet. Run has not completed.</Alert>
        )}
        {["FAILED", "NESTED_FAILED"].includes(future_state) && (
            <Alert severity="error">
                Run has failed. See&nbsp;
                <Link to={logsLinkPath} reloadDocument>Logs</Link>
                &nbsp;tab for details.
            </Alert>
        )}
        {future_state === "RESOLVED" && (<ArtifactList artifacts={outputArtifacts} />
        )}
    </>
}