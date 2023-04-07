import { Typography } from "@mui/material";
import { Run } from "@sematic/common/src/Models";
import {durationSecondsToString} from "src/utils";

function InstantRunTime({ prefix }: { prefix?: string}) {
  return (
    <Typography fontSize="small" color="GrayText">
      {`${prefix} <1s`}
    </Typography>
  );
}

function UnkownRunTime() {
  return (
    <Typography fontSize="small" color="GrayText">
      {"Unknown duration"}
    </Typography>
  );
}

export function RunTime(props: { run: Run; prefix?: string }) {
  const { run, prefix = "" } = props;
  let startedAt = new Date(run.started_at || run.created_at);
  let endedAt = new Date();
  if (run.original_run_id !== null) {
    return <InstantRunTime prefix={prefix} />;
  }
  let endTimeString = run.failed_at || run.resolved_at;
  if (endTimeString) {
    endedAt = new Date(endTimeString);
  } else if (!["CREATED", "SCHEDULED", "RAN", "RETRYING"].includes(run.future_state) ){
    return <UnkownRunTime />;
  }

  let durationS: number = Math.round(
    (endedAt.getTime() - startedAt.getTime()) / 1000
  );

  return (
    <Typography fontSize="small" color="GrayText">
      {prefix} {durationSecondsToString(durationS)}
    </Typography>
  );
}
