import { Alert, Box } from "@mui/material";
import { Artifact } from "@sematic/common/src/Models";
import { useMemo } from "react";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { ArtifactList } from "src/pipelines/Artifacts";
import { Exception, ExternalException } from "src/components/Exception";

export default function OutputPanel(props: {
    outputArtifacts: Map<string, Artifact | undefined>
}) {
    const { outputArtifacts } = props;
    const { selectedRun } = usePipelinePanelsContext();
    const { future_state, external_exception_metadata_json, exception_metadata_json } = selectedRun!;

    const exceptions = useMemo(() => {
        if (["FAILED", "NESTED_FAILED"].includes(future_state)) {
            return <>
                {external_exception_metadata_json && <Box sx={{ paddingBottom: 4, }} >
                    <ExternalException
                        exception_metadata={external_exception_metadata_json} />
                </Box>}

                {exception_metadata_json && <Box sx={{ paddingBottom: 4, }} >
                    <Exception exception_metadata={exception_metadata_json} /></Box>}
            </>
        }

        return null;
    }, [external_exception_metadata_json, exception_metadata_json, future_state]);

    return <>
        {["CREATED", "SCHEDULED", "RAN"].includes(future_state) && (
            <Alert severity="info">No output yet. Run has not completed.</Alert>
        )}
        {["FAILED", "NESTED_FAILED"].includes(future_state) && (
            <>
                <Alert severity="error">
                    Run has failed.
                </Alert>
                {exceptions}
            </>
        )}
        {future_state === "RESOLVED" && (<ArtifactList artifacts={outputArtifacts} />
        )}
    </>
}