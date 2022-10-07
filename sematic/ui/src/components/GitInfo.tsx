import { useCallback, useState } from "react";
import { Box, ButtonBase, Link, Tooltip, Typography, useTheme } from "@mui/material";
import { ContentCopy, OpenInNew } from "@mui/icons-material";
import PostAddIcon from '@mui/icons-material/PostAdd';
import { RiGitBranchLine, RiGitCommitLine, RiGitRepositoryCommitsLine } from "react-icons/ri";
import { FaGitSquare } from "react-icons/fa";
import { Resolution } from "../Models";

/**
 * Turns the following remote formats:
 * - git@gihub.com:sematic-ai/sematic.git
 * - https://github.com/sematic-ai/sematic.git
 * into clickable links:
 * - https://github.com/sematic-ai/sematic/tree/<branch>
 * - https://github.com/sematic-ai/sematic/commit/<SHA>
 */
function makeGithubLink(remote: string, path: string) {
  let domain = remote
    .replace(/^(git@)|(https:\/\/)/, "")
    .replace(/(\.git)$/, "")
    .replace(/:/, "/")
  return "https://" + domain + "/" + path
}

function GitInfo(props: {
    text: string, tooltip: string, remote: string, path: string, children?: any
}) {

  const [content, setContent] = useState(props.text);

  const copy = useCallback(() => {
    navigator.clipboard.writeText(props.text);
    // avoid temporary resizing by preserving the initial text length
    // by using non-breaking spaces
    setContent("Copied".padStart(props.text.length, " "));
    setTimeout(() => setContent(props.text), 1000);
  }, [props.text]);

  return (

    <Typography color="GrayText" component="span">
      <Tooltip title={props.tooltip}>
        <ButtonBase onClick={copy}>
          {props.children}: <code>{content}</code>
          <ContentCopy fontSize="inherit" sx={{ ml: 1 }} />
        </ButtonBase>
      </Tooltip>
      <Link href={makeGithubLink(props.remote, props.path)} target="_blank">
      <OpenInNew fontSize="inherit" sx={{ ml: 1 }} /></Link>
    </Typography>

  );
}

function DirtyBit(props: { dirty: boolean }) {
  if (!props.dirty) {
    return <div />
  }

  return (
    <Tooltip title="The workspace had uncommitted changes">
      <Typography color="GrayText" component="span">
        <PostAddIcon fontSize="small" sx={{ ml: 4 }} />
      </Typography>
    </Tooltip>
  )
}

function GitInfoBox(props: { resolution: Resolution | undefined }) {

  const theme = useTheme();

  if (!props.resolution || !props.resolution.git_info) {
    return (
      <Box
        sx={{
          gridColumn: 3,
          paddingX: 10,
          paddingTop: 1,
          borderLeft: 1,
          borderColor: theme.palette.grey[200],
        }}
      >
        <Tooltip title="Git info not found">
          <div>
            <FaGitSquare size="40" color={theme.palette.grey[200]} />
          </div>
        </Tooltip>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        gridColumn: 3,
        textAlign: "left",
        paddingX: 10,
        borderLeft: 1,
        borderColor: theme.palette.grey[200],
      }}
    >
      <Box>
        <GitInfo
          text={props.resolution.git_info.branch}
          tooltip="Git branch"
          remote={props.resolution.git_info.remote}
          path={"tree/" + props.resolution.git_info.branch}
        >
          <RiGitBranchLine />
        </GitInfo>
      </Box>
      <Box>
        <GitInfo
          text={props.resolution.git_info.commit.substring(0, 7)}
          tooltip="Git commit"
          remote={props.resolution.git_info.remote}
          path={"commit/" + props.resolution.git_info.commit}
        >
          <RiGitCommitLine />
        </GitInfo>
        <DirtyBit dirty={props.resolution.git_info.dirty} />
      </Box>
    </Box>
  );
}

export default GitInfoBox;
