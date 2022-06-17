import { Typography } from "@mui/material";
import { Run } from "../Models";

export function RunTime(props: { run: Run; prefix?: string }) {
  const { run, prefix } = props;
  let startedAt = new Date(run.started_at || run.created_at);
  let endedAt = new Date();
  let endTimeString = run.failed_at || run.resolved_at;
  if (endTimeString) {
    endedAt = new Date(endTimeString);
  }

  let durationMS: number = endedAt.getTime() - startedAt.getTime();

  return (
    <Typography fontSize="small" color="GrayText">
      {prefix}
      {Number.parseFloat((durationMS / 1000).toString()).toFixed(0)} seconds
      {/*on&nbsp;
              {new Date(run.created_at).toLocaleString()*/}
    </Typography>
  );
}
