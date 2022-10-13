import { Add, ContentCopy } from "@mui/icons-material";
import PostAddIcon from "@mui/icons-material/PostAdd";
import {
  Box,
  ButtonBase,
  Link,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useCallback, useState } from "react";
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
  text: string;
  copyText?: string;
  tooltip: string;
  remote: string;
  path: string;
  extra?: JSX.Element;
  children?: any;
}) {
  const { text, copyText, tooltip, remote, path, children, extra } = props;
  const [content, setContent] = useState(text);
  const theme = useTheme();
  const copy = useCallback(() => {
    navigator.clipboard.writeText(copyText || text);
    // avoid temporary resizing by preserving the initial text length
    // by using non-breaking spaces
    setContent("Copied".padStart(text.length, " "));
    setTimeout(() => setContent(text), 1000);
  }, [text]);

  return (
    <Typography
      color="GrayText"
      component="span"
      sx={{ display: "flex", alignItems: "center" }}
    >
      {children}&nbsp;
      <Tooltip title={tooltip}>
        <Link href={makeGithubLink(remote, path)} target="_blank">
          <code>{content}</code>
        </Link>
      </Tooltip>
      <ButtonBase onClick={copy}>
        <ContentCopy fontSize="inherit" sx={{ ml: 1 }} />
      </ButtonBase>
      {extra}
    </Typography>
  );
}

function GitInfoBox(props: { resolution: Resolution | undefined }) {
  const { resolution } = props;
  const theme = useTheme();

  if (!resolution || !resolution.git_info_json) {
    return (
      <Typography
        color="GrayText"
        sx={{
          gridColumn: 3,
          paddingX: 10,
          paddingTop: 3,
          borderColor: theme.palette.grey[200],
        }}
      >
        Git info not found
      </Typography>
    );
  }

  return (
    <>
      <Box>
        <GitInfo
          text={resolution.git_info_json.branch}
          tooltip="Git branch"
          remote={resolution.git_info_json.remote}
          path={"tree/" + resolution.git_info_json.branch}
        >
          <RiGitBranchLine />
        </GitInfo>
      </Box>
      <Box>
        <GitInfo
          text={resolution.git_info_json.commit.substring(0, 7)}
          copyText={resolution.git_info_json.commit}
          tooltip="Git commit"
          remote={resolution.git_info_json.remote}
          path={"commit/" + resolution.git_info_json.commit}
          extra={
            resolution.git_info_json.dirty ? (
              <Tooltip title="Uncommitted changes">
                <PostAddIcon
                  fontSize="inherit"
                  sx={{ color: theme.palette.warning.light, ml: 2 }}
                />
              </Tooltip>
            ) : undefined
          }
        >
          <RiGitCommitLine />
        </GitInfo>
      </Box>
    </>
  );
}

export default GitInfoBox;
