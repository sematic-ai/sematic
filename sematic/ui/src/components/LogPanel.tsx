import { Exception, ExternalException } from "./Exception";
import { Box } from "@mui/material";
import { Run } from "../Models";
import { fetchJSON } from "../utils";
import { useCallback, useContext, useState } from "react";
import { UserContext } from "..";
import { LogLineRequestResponse } from "../Payloads";
import ScrollingLogView from "./ScrollingLogView";
import { MoreLinesCallback } from "./ScrollingLogView";
import { Alert } from "@mui/material";

export default function LogPanel(props: { run: Run }) {
  const { run } = props;
  const { user } = useContext(UserContext);
  const [error, setError] = useState<Error | undefined>(undefined);

  const loadLogs = useCallback(
    (
      source: string,
      cursor: string | null,
      filterString: string,
      callback: MoreLinesCallback
    ) => {
      var url = "/api/v1/runs/" + source + "/logs?max_lines=2000";
      if (cursor != null) {
        url += "&continuation_cursor=" + cursor;
      }
      if (filterString.length !== 0) {
        url += "&filter_string=" + filterString;
      }
      fetchJSON({
        url: url,
        apiKey: user?.api_key,
        callback: (payload: LogLineRequestResponse) => {
          callback(
            source,
            filterString,
            payload.content.lines,
            payload.content.continuation_cursor,
            payload.content.log_unavailable_reason
          );
        },
        setError: setError,
      });
    },
    [user?.api_key]
  );

  const standardLogView = (
    <ScrollingLogView getLines={loadLogs} logSource={run.id} />
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
        {run.external_exception_json && <ExternalException exception_metadata={run.external_exception_json} />}
      </Box>
      <Box sx={{ gridRow: 2, paddingBottom: 4, }} >
        {run.exception_json && <Exception exception_metadata={run.exception_json} />}
      </Box>
      <Box sx={{ gridRow: 3, paddingBottom: 4, }} >
        {logView}
      </Box>
    </Box>
  );
}
