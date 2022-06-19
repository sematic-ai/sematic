import { Box, TextField, useTheme } from "@mui/material";
import { useState } from "react";
import Notes from "./Notes";

export default function NotesPanel(props: { calculatorPath: string }) {
  const theme = useTheme();

  const [messages, setMessages] = useState([]);

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
        <Notes calculatorPath={props.calculatorPath} />
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
