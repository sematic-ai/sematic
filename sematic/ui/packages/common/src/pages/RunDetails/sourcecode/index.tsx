import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import SourceCode from "src/pages/RunDetails/sourcecode/SourceCode";
import styled from "@emotion/styled";
import theme from "src/theme/new";

const StyledSourceCode = styled(SourceCode)`
    margin: 0;

    & pre {
        margin: 0;
        padding: ${theme.spacing(2)} ${theme.spacing(5)}!important;
    }
`;

export default function SourceCodePanel() {

    const { selectedRun } = useRunDetailsSelectionContext();

    if (!selectedRun) {
        return null;
    }

    return <StyledSourceCode run={selectedRun}  />;
}
