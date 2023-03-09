import { Typography } from "@mui/material";
import { Run } from "../Models";

export function RunTime(props: { run: Run; prefix?: string }) {
  const { run, prefix = "" } = props;
  let startedAt = new Date(run.started_at || run.created_at);
  let endedAt = new Date();
  let endTimeString = run.failed_at || run.resolved_at;
  if (endTimeString) {
    endedAt = new Date(endTimeString);
  }

  let durationS: number = Math.round(
    (endedAt.getTime() - startedAt.getTime()) / 1000
  );
  let displayH: number = Math.floor(durationS / 3600);
  let displayM: number = Math.floor((durationS % 3600) / 60);
  let displayS: number = Math.round(durationS % 60);

  let display = [
    prefix,
    displayH > 0 ? displayH.toString() + "h" : "",
    displayM > 0 ? displayM.toString() + "m " : "",
    displayS > 0 ? displayS.toString() + "s" : "",
    durationS === 0 ? "<1s" : "",
  ]
    .join(" ")
    .trim();

  return (
    <Typography fontSize="small" color="GrayText">
      {display}
    </Typography>
  );
}
