import { useRootRunContext } from "src/context/RootRunContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import ArtifactComponent from "src/pages/RunDetails/artifacts/artifact";
import { useMemo } from "react";
import { Artifact } from "src/Models";
import { ArtifactPaneContainer } from "src/pages/RunDetails/artifacts/common";

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
                    console.error(Error("Artifact missing"));
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

    if (isGraphLoading) {
        return null;
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