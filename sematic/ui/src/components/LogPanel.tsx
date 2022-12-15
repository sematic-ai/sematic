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
    <Box sx={{ display: "flex", flexGrow: 1 }} >
      {run.external_exception_metadata_json && <Box sx={{ paddingBottom: 4, }} >
        <ExternalException
          exception_metadata={run.external_exception_metadata_json} />
      </Box>}

      {run.exception_metadata_json && <Box sx={{ paddingBottom: 4, }} >
        <Exception exception_metadata={run.exception_metadata_json} /></Box>}

      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column'}} >
        <TextField
          variant="standard"
          fullWidth={true}
          placeholder={"Filter..."}
          onChange={onFilterStringChange}
          style={{ flexShrink: 1 }}
        />
        {logView}
      </Box>
    </Box>
  );
}
