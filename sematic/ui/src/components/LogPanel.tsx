import GrafanaPanel from "../addons/grafana/GrafanaPanel";
import Exception from "./Exception";
import { Box, Button } from "@mui/material";
import { Run } from "../Models";
import { fetchJSON } from "../utils";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { UserContext } from "..";
import { LogLineRequestResponse } from "../Payloads";
import ScrollingLogView from "./ScrollingLogView";
import { GetLines, MoreLinesCallback } from "./ScrollingLogView";


export default function LogPanel(props: { run: Run }) {
  const { run } = props;
  const { user } = useContext(UserContext);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<Error | undefined>(undefined);

  const loadLogs = useCallback((cursor: string | null, callback: MoreLinesCallback) => {
    var url = "/api/v1/runs/" + run.id + "/logs?maxLines=100";
    if (cursor != null){
        url += "&continuation_cursor=" + cursor;
    }
    fetchJSON({
      url: url,
      apiKey: user?.api_key,
      callback: (payload: LogLineRequestResponse) => {
        setIsLoaded(true);
        callback(payload.content.lines, payload.content.continuation_cursor, payload.content.log_unavailable_reason);
      },
      setError: setError,
    });
  }, [run]);

  return (
    <Box>
        {run.exception && <Exception exception={run.exception} />}
        <GrafanaPanel run={run} />
        
        <ScrollingLogView getLines={loadLogs} initialLines={[]} initialCursor={null}/>
    </Box>
  );
}
