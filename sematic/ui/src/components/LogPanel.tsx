import { Alert, Box } from "@mui/material";
import { useState } from "react";
import { Run } from "../Models";
import { Exception, ExternalException } from "./Exception";
import ScrollingLogView from "./ScrollingLogView";

export default function LogPanel(props: { run: Run }) {
  const { run } = props;
  const [error, setError] = useState<Error | undefined>(undefined);

  const standardLogView = (
    <ScrollingLogView key={run.id} logSource={run.id} onError={setError} />
  );
  const logErrorView = (
    <Alert severity="error">
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
        {logView}
      </Box>
    </Box>
  );
}
