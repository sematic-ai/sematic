import { Box, TextField, useTheme } from "@mui/material";
import Messages from "./Messages";

export default function MessagePanel() {
  const theme = useTheme();

  return (
    <Box
      sx={{
        gridColumn: 3,
        gridRow: 2,
        borderLeft: 1,
        borderColor: theme.palette.grey[200],
        display: "grid",
        gridTemplateRows: "1fr auto",
      }}
    >
      <Box sx={{ gridRow: 1, display: "flex" }}>
        <Messages />
      </Box>
      <Box sx={{ gridRow: 2 }}>
        <TextField
          sx={{ width: "100%", backgroundColor: "#ffffff" }}
          id="filled-textarea"
          label="Add a note"
          placeholder="Your note..."
          multiline
          variant="filled"
        />
      </Box>
    </Box>
  );
}
