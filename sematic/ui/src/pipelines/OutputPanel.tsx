import { Alert } from "@mui/material";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";
import { Artifact } from "../Models";
import { ArtifactList } from "./Artifacts";

export default function OutputPanel(props: {
    outputArtifacts: Map<string, Artifact | undefined>
}) {
    const { outputArtifacts } = props;
    const { selectedRun } = usePipelinePanelsContext();
    const { future_state } = selectedRun!;

    return <>
        {["CREATED", "SCHEDULED", "RAN"].includes(future_state) && (
            <Alert severity="info">No output yet. Run has not completed.</Alert>
        )}
        {["FAILED", "NESTED_FAILED"].includes(future_state) && (
            <Alert severity="error">Run has failed. See Logs tab for details.</Alert>
        )}
        {future_state === "RESOLVED" && (<ArtifactList artifacts={outputArtifacts} />
        )}
    </>
}