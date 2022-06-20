import { Box, Stack, TextField, useTheme } from "@mui/material";
import {
  KeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Note, Run } from "../Models";
import { NoteCreatePayload, NoteListPayload } from "../Payloads";
import { fetchJSON } from "../utils";
import { NoteView } from "./Notes";

export default function NotesPanel(props: { rootRun: Run; selectedRun: Run }) {
  const theme = useTheme();

  const { rootRun, selectedRun } = props;

  const calculatorPath = useMemo(() => rootRun.calculator_path, [rootRun]);

  const [notes, setNotes] = useState<Note[]>([]);
  const [inputDisabled, setInputDisabled] = useState(false);
  const [composedNote, setComposedNote] = useState("");

  useEffect(() => {
    fetchJSON(
      "/api/v1/notes?calculator_path=" + calculatorPath,
      (payload: NoteListPayload) => {
        setNotes(payload.content);
      }
    );
  }, [calculatorPath]);

  const submitNote = useCallback(
    (event: KeyboardEvent) => {
      if (event.key !== "Enter" || event.shiftKey) return;
      if (composedNote.length === 0) return;

      setInputDisabled(true);

      const requestOptions = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          note: {
            author_id: "anonymous@acme.com",
            note: composedNote,
            root_id: rootRun.id,
            run_id: selectedRun.id,
          },
        }),
      };
      fetch("/api/v1/notes", requestOptions)
        .then((response) => response.json())
        .then((payload: NoteCreatePayload) => {
          setNotes([...notes, payload.content]);
          setComposedNote("");
          setInputDisabled(false);
        });
    },
    [composedNote, rootRun, selectedRun, notes]
  );

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
      <Box
        sx={{
          gridRow: 1,
          display: "grid",
          gridTemplateRows: "1fr auto",
          borderBottom: 1,
          borderColor: theme.palette.grey[200],
        }}
      >
        <Box sx={{ gridRow: 1 }}></Box>
        <Box sx={{ gridRow: 2, display: "flex", flexDirection: "column" }}>
          <Box sx={{ display: "grid", gridTemplateRows: "1fr auto" }}>
            <Box sx={{ gridRow: 1 }}></Box>

            <Stack sx={{ gridRow: 2 }}>
              {notes.map((note) => (
                <NoteView note={note} />
              ))}
            </Stack>
          </Box>
        </Box>
      </Box>
      <Box
        sx={{
          gridRow: 2,
          padding: 1,
          paddingBottom: 3,
        }}
      >
        <TextField
          sx={{ width: "100%", backgroundColor: "#ffffff" }}
          id="filled-textarea"
          label="Add a note"
          placeholder="Your note..."
          multiline
          variant="standard"
          onKeyUp={submitNote}
          onChange={(e) => setComposedNote(e.target.value)}
          disabled={inputDisabled}
          value={composedNote}
        />
      </Box>
    </Box>
  );
}
