import { useRootRunContext } from "src/context/RootRunContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import ArtifactComponent from "src/pages/RunDetails/artifacts/artifact";
import { useMemo } from "react";
import { Artifact } from "src/Models";
import { ArtifactPaneContainer } from "src/pages/RunDetails/artifacts/common";
import { Exception, ExternalException } from "src/component/Exception";
import { Box } from "@mui/material";
import Alert from "@mui/material/Alert";

function OutputPane() {
    const { selectedRun } = useRunDetailsSelectionContext();
    const { graph, isGraphLoading } = useRootRunContext();

    const outputArtifact = useMemo(() => {
        if (!graph) {
            return null;
        }

        const { edges, artifactsById } = graph;

        const outputArtifacts: Array<{ name: string, artifact: Artifact }> = []

        edges.forEach((edge) => {
            if (edge.source_run_id === selectedRun?.id) {
                if (!edge.artifact_id || !artifactsById.has(edge.artifact_id!)) {
                    console.warn(Error("Artifact missing"));
                    return;
                }
                outputArtifacts.push({
                    name: edge.source_name!,
                    artifact: artifactsById.get(edge.artifact_id!)!
                });
            }
        });

        return outputArtifacts;

    }, [graph, selectedRun?.id]);

    const exceptions = useMemo(() => {
        if (isGraphLoading) {
            return null;
        }
        const { future_state, external_exception_metadata_json, exception_metadata_json } = selectedRun!;

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
    }, [isGraphLoading, selectedRun]);

    if (isGraphLoading) {
        return null;
    }

    const { future_state } = selectedRun! || {};

    if (["CREATED", "SCHEDULED", "RAN"].includes(future_state)) {
        return <Alert severity="info">No output yet. Run has not completed.</Alert>;
    }
    if (["FAILED", "NESTED_FAILED"].includes(future_state)) {
        return <>
            <Alert severity="error">
                Run has failed.
            </Alert>
            {exceptions}
        </>;
    }

    return <OutputPanePresentation outputArtifacts={outputArtifact || []} />;
}

interface OutputPanePresentationProps {
    outputArtifacts: Array<{ name: string, artifact: Artifact }>;
}

function OutputPanePresentation(props: OutputPanePresentationProps) {
    const { outputArtifacts } = props;
    if (!outputArtifacts[0]) {
        return null;
    }
    const theArtifact = outputArtifacts[0];
    return <ArtifactPaneContainer>
        <ArtifactComponent key={theArtifact.artifact.id} name={theArtifact.name || "output"}
            artifact={theArtifact.artifact} expanded={true} />
    </ArtifactPaneContainer>;
}

export default OutputPane;