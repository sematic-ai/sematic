import PostAddIcon from "@mui/icons-material/PostAdd";
import { Box, Link, Tooltip, Typography, useTheme } from "@mui/material";
import { Resolution } from "@sematic/common/src/Models";
import { RiGitBranchLine, RiGitCommitLine } from "react-icons/ri";
import CopyButton from "@sematic/common/src/component/CopyButton";

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
  code?: boolean;
}) {
  const {
    text,
    copyText,
    tooltip,
    remote,
    path,
    children,
    extra,
    code = false,
  } = props;

  const theme = useTheme();

  return (
    <Typography
      color="GrayText"
      component="span"
      sx={{ display: "flex", alignItems: "center" }}
    >
      {children}&nbsp;
      <Tooltip title={tooltip}>
        <Link href={makeGithubLink(remote, path)} target="_blank">
          {!code && text}
          {code && <code>{text}</code>}
        </Link>
      </Tooltip>
      <Typography sx={{ color: theme.palette.grey[400] }}>
        <CopyButton text={copyText || text} />
      </Typography>
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
          paddingTop: 3,
        }}
      >
        No Git information.
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
          code
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
