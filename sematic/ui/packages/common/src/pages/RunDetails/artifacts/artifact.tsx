import Headline from "src/component/Headline";
import Section from "src/component/Section";
import styled from "@emotion/styled";
import MoreVertButton from "src/component/MoreVertButton";
import { Artifact as ArtifactType } from "src/Models";
import { renderArtifactRow } from "src/typeViz/common";
import theme from "src/theme/new";

const StyledSection = styled(Section)`
    height: 50px;
    display: flex;
    align-items: center;
    position: relative;
`;

const StyledVertButton = styled(MoreVertButton)`
    position: absolute;
    right: 0;
    top: 12px;
    transform: translate(50%,0);
`;

const ArtifactRepresentation = styled.div`
    margin-left: -${theme.spacing(5)};
`;

interface ArtifactProps {
    name: string;
    artifact: ArtifactType;
    expanded?: boolean;
}

function Artifact(props: ArtifactProps) {
    const { name, artifact, expanded } = props;

    const { type_serialization, json_summary } = artifact;

    return <>
        <StyledSection>
            <Headline>Artifact</Headline>
            <StyledVertButton />
        </StyledSection>
        <ArtifactRepresentation>
            {renderArtifactRow(name, type_serialization, json_summary, { expanded })}
        </ArtifactRepresentation>
    </>;
}

export default Artifact;
