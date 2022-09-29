import GrafanaPanel from "../addons/grafana/GrafanaPanel";
import Exception from "./Exception";
import { Box } from "@mui/material";
import { Run } from "../Models";
import { fetchJSON } from "../utils";
import { useCallback, useContext, useState } from "react";
import { UserContext } from "..";
import { LogLineRequestResponse } from "../Payloads";
import ScrollingLogView from "./ScrollingLogView";
import { MoreLinesCallback } from "./ScrollingLogView";

export default function LogPanel(props: { run: Run }) {
  const { run } = props;
  const { user } = useContext(UserContext);
  const [error, setError] = useState<Error | undefined>(undefined);

  const loadLogs = useCallback(
    (source: string, cursor: string | null, callback: MoreLinesCallback) => {
      var url = "/api/v1/runs/" + source + "/logs?max_lines=2000";
      if (cursor != null) {
        url += "&continuation_cursor=" + cursor;
      }
      fetchJSON({
        url: url,
        apiKey: user?.api_key,
        callback: (payload: LogLineRequestResponse) => {
          callback(
            source,
            payload.content.lines,
            payload.content.continuation_cursor,
            payload.content.log_unavailable_reason
          );
        },
        setError: setError,
      });
    },
    [run, user?.api_key]
  );

  const standardLogView = (
    <ScrollingLogView getLines={loadLogs} logSource={run.id} />
  );
  const logErrorView = (
    <div>The server returned an error when asked for logs for this run.</div>
  );
  const logView = error === undefined ? standardLogView : logErrorView;

  return (
    <Box>
      {run.exception && <Exception exception={run.exception} />}
      <GrafanaPanel run={run} />
      {logView}
    </Box>
  );
}
