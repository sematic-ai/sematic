import { ContentCopy } from "@mui/icons-material";
import PostAddIcon from '@mui/icons-material/PostAdd';
import { Box, ButtonBase, Link, Tooltip, Typography, useTheme } from "@mui/material";
import { useCallback, useState } from "react";
import { FaGitSquare } from "react-icons/fa";
import { RiGitBranchLine, RiGitCommitLine } from "react-icons/ri";
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
    .replace(/:/, "/");
  return "https://" + domain + "/" + path;
}

function GitInfo(props: {
  text: string, tooltip: string, remote: string, path: string, children?: any
}) {
  const { text, tooltip, remote, path, children } = props;
  const [content, setContent] = useState(text);

  const copy = useCallback(() => {
    navigator.clipboard.writeText(text);
    // avoid temporary resizing by preserving the initial text length
    // by using non-breaking spaces
    setContent("Copied".padStart(text.length, " "));
    setTimeout(() => setContent(text), 1000);
  }, [text]);

  return (

    <Typography color="GrayText" component="span">
      <Tooltip title={tooltip} arrow={true}>
        <Box component="span">
          {children}&nbsp;
          <Link href={makeGithubLink(remote, path)} target="_blank">
            <code>{content}</code>
          </Link>
          <ButtonBase onClick={copy}>
            <ContentCopy fontSize="inherit" sx={{ ml: 1 }}/>
          </ButtonBase>
        </Box>
      </Tooltip>
    </Typography>

  );
}

function DirtyBit(props: { dirty: boolean }) {
  if (!props.dirty) {
    return <div/>;
  }

  return (
    <Tooltip title="The workspace had uncommitted changes" arrow={true}>
      <Typography color="GrayText" component="span">
        <PostAddIcon fontSize="small" sx={{ ml: 4 }}/>
      </Typography>
    </Tooltip>
  );
}

function GitInfoBox(props: { resolution: Resolution | undefined }) {

  const { resolution } = props;
  const theme = useTheme();

  if (!resolution || !resolution.git_info_json) {
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
        <Tooltip title="Git info not found" arrow={true}>
          <div>
            <FaGitSquare size="40" color={theme.palette.grey[200]}/>
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
          text={resolution.git_info_json.branch}
          tooltip="Git branch"
          remote={resolution.git_info_json.remote}
          path={"tree/" + resolution.git_info_json.branch}
        >
          <RiGitBranchLine/>
        </GitInfo>
      </Box>
      <Box>
        <GitInfo
          text={resolution.git_info_json.commit.substring(0, 7)}
          tooltip="Git commit"
          remote={resolution.git_info_json.remote}
          path={"commit/" + resolution.git_info_json.commit}
        >
          <RiGitCommitLine/>
        </GitInfo>
        <DirtyBit dirty={resolution.git_info_json.dirty}/>
      </Box>
    </Box>
  );
}

export default GitInfoBox;
