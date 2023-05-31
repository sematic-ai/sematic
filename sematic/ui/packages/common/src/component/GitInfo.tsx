import styled from "@emotion/styled";
import { Code } from "@mui/icons-material";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Skeleton from "@mui/material/Skeleton";
import Tooltip from "@mui/material/Tooltip";
import Typography, { typographyClasses } from "@mui/material/Typography";
import { useMemo } from "react";
import { RiGitBranchLine, RiGitCommitLine } from "react-icons/ri";
import CopyButton from "src/component/CopyButton";
import { useRootRunContext } from "src/context/RootRunContext";
import theme from "src/theme/new";
import { makeGithubLink } from "src/utils/url";

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
    hasGitInfo?: boolean;
    hasUncommittedChanges?: boolean;
    commit?: string;
    branch?: string;
    commitLink?: string;
    branchLink?: string;
}

export const GitInfoBoxPresentation = (prop: GitInfoBoxProps) => {
    const { hasUncommittedChanges = false, hasGitInfo = true, branch, branchLink,
        commit, commitLink } = prop;

    if (!hasGitInfo) {
        return <StyledBox><Typography color="GrayText" variant={"small"}>
            No Git information.
        </Typography></StyledBox>
    }

    return <>
        <StyledBox>
            <RiGitBranchLine />
            <Link variant={"small"} href={branchLink} target="_blank">{branch}</Link>
            <CopyButton text={branch!} />
        </StyledBox>
        <StyledBox>
            <RiGitCommitLine />
            <Link variant={"small"} href={commitLink} target="_blank" type={"code"}>
                {commit?.substring(0, 7)}
            </Link>
            <CopyButton text={commit!} />
        </StyledBox>
        {!!hasUncommittedChanges && <StyledBox>
            <Code />
            <Tooltip title={"This run used code with uncommitted changed on top of the above commit."} arrow={true} >
                <Typography variant="small">Uncommited changes</Typography>
            </Tooltip>
        </StyledBox>}
    </>
};

const GitInfoBox = () => {
    const { resolution, isResolutionLoading } = useRootRunContext();

    return useMemo(() => {
        if (isResolutionLoading) {
            return <Skeleton />
        }
        if (!resolution!.git_info_json) {
            return <GitInfoBoxPresentation hasGitInfo={false} />
        }
        const branchName = resolution!.git_info_json!.branch;
        const remote = resolution!.git_info_json!.remote;
        const branchLink = makeGithubLink(remote, `tree/${branchName}`);

        const commit = resolution!.git_info_json!.commit;
        const commitLink = makeGithubLink(remote, `commit/${commit}`);

        return <GitInfoBoxPresentation branch={branchName} commit={commit}
            commitLink={commitLink} branchLink={branchLink}
            hasUncommittedChanges={resolution!.git_info_json!.dirty} />;
    }, [isResolutionLoading, resolution]);
}

export default GitInfoBox;