import Box from "@mui/material/Box";
import Typography, {typographyClasses} from "@mui/material/Typography";
import { RiGitBranchLine, RiGitCommitLine } from "react-icons/ri";
import styled from "@emotion/styled";
import theme from "src/theme/new";

const StyledBox = styled(Box)`
    display: flex;
    align-items: center;

    & svg {
        fill: ${theme.palette.lightGrey.main};
    }

    & .${typographyClasses.root} {
        color: ${theme.palette.black.main};
        opacity: 0.5;
        margin-left: ${theme.spacing(1)};
    }
`;

interface GitInfoBoxProps {

}

const GitInfoBox = (props: GitInfoBoxProps) => {
    return <>
        <StyledBox>
            <RiGitBranchLine />
            <Typography>acme/feature-branch</Typography>
        </StyledBox>
        <StyledBox>
            <RiGitCommitLine />
            <Typography>pf49df3</Typography>
        </StyledBox>
    </>
};

export default GitInfoBox;