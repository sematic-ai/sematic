import { ContentCopy } from "@mui/icons-material";
import { Box, ButtonBase, Tooltip, Typography, useTheme } from "@mui/material";
import { useCallback, useContext } from "react";
import { redirect, useNavigate } from "react-router-dom";
import { Note, Run, User } from "../Models";
import { CopyButton } from "./CopyButton";
import { SnackBarContext } from "./SnackBarProvider";
import TimeAgo from "./TimeAgo";
import UserAvatar from "./UserAvatar";

export function NoteView(props: { note: Note; author: User; rootRun: Run }) {
  const { note, author, rootRun } = props;
  const theme = useTheme();

  return (
    <Box
      sx={{
        borderTop: 1,
        borderColor: theme.palette.grey[200],
        color: theme.palette.grey[800],
        px: 2,
        py: 2,
      }}
      key={note.id}
    >
      <Typography
        component="span"
        sx={{ display: "flex", alignItems: "center" }}
      >
        <UserAvatar user={author} sx={{ width: 24, height: 24 }} />
        <Typography
          sx={{
            fontSize: "small",
            ml: 1,
            color: theme.palette.grey[500],
            fontWeight: 500,
          }}
        >
          {author.first_name}:
        </Typography>
      </Typography>
      <Box sx={{ my: 4 }}>
        <Typography fontSize="small">{note.note}</Typography>
      </Box>
      <Box sx={{ display: "grid", gridTemplateColumns: "auto 1fr auto" }}>
        <Box sx={{ gridColumn: 1, color: theme.palette.grey[300] }}>
          {/*<DeleteIcon style={{ fontSize: 16 }} />*/}
        </Box>
        <Typography
          sx={{
            gridColumn: 3,
            fontSize: "small",
            color: theme.palette.grey[500],
            textAlign: "right",
          }}
        >
          <TimeAgo date={note.created_at} /> on run{" "}
          <RunId
            runId={note.root_id}
            // Doesn't work yet
            //link={"/pipelines/" + rootRun.calculator_path + "/" + note.root_id}
            trim
          />
        </Typography>
      </Box>
    </Box>
  );
}

function RunId(props: { runId: string; link?: string; trim?: boolean }) {
  const { runId, trim = true, link } = props;
  const navigate = useNavigate();

  return (
    <>
      <ButtonBase onClick={() => link && navigate(link)} disabled={!link}>
        <code
          style={{
            fontSize: 12,
          }}
        >
          {trim ? runId.substring(0, 6) : runId}
        </code>
      </ButtonBase>
      <CopyButton text={runId} message="Copied run ID." />
    </>
  );
}
