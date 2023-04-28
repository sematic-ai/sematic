import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Typography, { typographyClasses } from "@mui/material/Typography";
import { RiGitBranchLine, RiGitCommitLine } from "react-icons/ri";
import styled from "@emotion/styled";
import theme from "src/theme/new";
import CopyButton from "src/component/CopyButton";
import { Code } from "@mui/icons-material";
import Tooltip from "@mui/material/Tooltip";

const StyledBox = styled(Box)`
    display: flex;
    align-items: center;

    & svg {
        font-size: ${theme.typography.body1.fontSize}px;
        fill: ${theme.palette.lightGrey.main};
    }

    & .${typographyClasses.root} {
        color: ${theme.palette.mediumGrey.main};

        margin-left: ${theme.spacing(1)};
    }
`;

interface GitInfoBoxProps {
    hasUncommittedChanges?: boolean;
}

const GitInfoBox = (prop: GitInfoBoxProps) => {
    const { hasUncommittedChanges = false } = prop;

    return <>
        <StyledBox>
            <RiGitBranchLine />
            <Link variant={"small"}>acme/feature-branch</Link>
            <CopyButton text={"acme/feature-branch"} />
        </StyledBox>
        <StyledBox>
            <RiGitCommitLine />
            <Link variant={"small"} type={"code"}>pf49df3</Link>
            <CopyButton text={"pf49df36ae2e09b5f5780b38140f83cfe9f866b5"} />
        </StyledBox>
        {!!hasUncommittedChanges && <StyledBox>
            <Code />
            <Tooltip title={"This run used code with uncommitted changed on top of the above commit."} arrow={true} >
                <Typography variant="small">Uncommited changes</Typography>
            </Tooltip>            
        </StyledBox>}
    </>
};

export default GitInfoBox;