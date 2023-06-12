import styled from "@emotion/styled";
import Typography from "@mui/material/Typography";
import { useMemo } from "react";
import { Artifact } from "src/Models";
import { useRootRunContext } from "src/context/RootRunContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import ArtifactComponent from "src/pages/RunDetails/artifacts/artifact";
import { ArtifactPaneContainer } from "src/pages/RunDetails/artifacts/common";
import theme from "src/theme/new";

const StyledTypography = styled(Typography)`
    margin-top: ${theme.spacing(5)};
`;


function InputPane() {
    const { selectedRun } = useRunDetailsSelectionContext();
    const { graph, isGraphLoading } = useRootRunContext();

    const inputArtifacts = useMemo(() => {
        if (!graph) {
            return null;
        }

        const { edges, artifactsById } = graph;

        const inputArtifacts: Array<{name: string, artifact: Artifact}> = []

        edges.forEach((edge) => {
            if (edge.destination_run_id === selectedRun?.id) {
                if (!edge.artifact_id || !artifactsById.has(edge.artifact_id!)) {
                    console.error(Error("Artifact missing"));
                    return;
                }
                inputArtifacts.push({
                    name: edge.destination_name!,
                    artifact: artifactsById.get(edge.artifact_id!)!
                });
            }
        });

        return inputArtifacts;

    }, [graph, selectedRun?.id]);

    if (isGraphLoading) {
        return null;
    }

    return <InputPanePresentation inputArtifacts={inputArtifacts || []} />;
}

interface InputPanePresentationProps {
    inputArtifacts: Array<{name: string, artifact: Artifact}>;
}

function InputPanePresentation(props: InputPanePresentationProps) {
    const { inputArtifacts } = props;
    if (!inputArtifacts || inputArtifacts.length === 0) { 
        return <ArtifactPaneContainer>
            <StyledTypography variant={"big"}>There are no inputs for this run.</StyledTypography>
        </ArtifactPaneContainer>
    }
    return <ArtifactPaneContainer>{
        inputArtifacts.map(
            ({name, artifact}, index) => <ArtifactComponent key={index} name={name} artifact={artifact} />)
    }</ArtifactPaneContainer>;
}

export default InputPane;