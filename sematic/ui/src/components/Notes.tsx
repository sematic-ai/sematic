import { Box, Typography, useTheme } from "@mui/material";
import { Note } from "../Models";
import TimeAgo from "./TimeAgo";
import DeleteIcon from "@mui/icons-material/Delete";

export function NoteView(props: { note: Note }) {
  const { note } = props;
  const theme = useTheme();

  return (
    <Box
      sx={{
        borderTop: 1,
        borderColor: theme.palette.grey[200],
        color: theme.palette.grey[800],
        px: 2,
        py: 1,
      }}
      key={note.id}
    >
      <Typography sx={{ fontSize: "small", color: theme.palette.grey[500] }}>
        {note.author_id}:
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
          <code style={{ fontSize: 12 }}>{note.root_id.substring(0, 6)}</code>
        </Typography>
      </Box>
    </Box>
  );
}
