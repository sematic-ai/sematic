import styled from "@emotion/styled"
import theme from "src/theme/new";

export const ArtifactPaneContainer = styled.div`
    min-width: 600px;
    width: calc(100% - 10px);
    position: relative;
    padding: 0 ${theme.spacing(5)};

    &:after {
        content: '';
        position: absolute;
        bottom: 0;
        height: 1px;
        width: calc(100% + ${theme.spacing(10)});
        background: ${theme.palette.p3border.main};
        left: -${theme.spacing(5)};
    }
`;
