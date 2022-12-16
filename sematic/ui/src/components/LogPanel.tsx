import { Alert, Box, TextField } from "@mui/material";
import { useCallback, useState } from "react";
import { Run } from "../Models";
import { Exception, ExternalException } from "./Exception";
import ScrollingLogView from "./ScrollingLogView";

export default function LogPanel(props: { run: Run }) {
  const { run } = props;
  const [error, setError] = useState<Error | undefined>(undefined);
  const [filterString, setFilterString] = useState<string>("");

  const onFilterStringChange = useCallback(
    (evt: any) => {
      setFilterString(evt.target.value);
    },
    [setFilterString]
  );

  const standardLogView = (
    <ScrollingLogView key={`${run.id}---${filterString}`} logSource={run.id} onError={setError} 
      filterString={filterString} />
  );
  const logErrorView = (
    <Alert severity="error" sx={{ my: 5 }}>
      The server returned an error when asked for logs for this run.
    </Alert>
  );
  const logView = error === undefined ? standardLogView : logErrorView;

  return (
    <Box sx={{ display: "grid" }} >
      <Box sx={{ gridRow: 1, paddingBottom: 4, }} >
        {run.external_exception_metadata_json && <ExternalException
            exception_metadata={run.external_exception_metadata_json} />}
      </Box>
      <Box sx={{ gridRow: 2, paddingBottom: 4, }} >
        {run.exception_metadata_json &&
            <Exception exception_metadata={run.exception_metadata_json} />}
      </Box>
      <Box sx={{ gridRow: 3, paddingBottom: 4, }} >
        <TextField
          variant="standard"
          fullWidth={true}
          placeholder={"Filter..."}
          onChange={onFilterStringChange}
        />
        {logView}
      </Box>
    </Box>
  );
}
