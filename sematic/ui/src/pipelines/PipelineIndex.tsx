import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import { useEffect, useState } from "react";
import { RunList } from "../components/RunList";
import Tags from "../components/Tags";
import { Run } from "../Models";
import Link from "@mui/material/Link";
import { RunListPayload } from "../Payloads";
import RunStateChip from "../components/RunStateChip";
import CircleOutlined from "@mui/icons-material/CircleOutlined";
import Tooltip from "@mui/material/Tooltip";
import ReactTimeAgo from "react-time-ago";

function RecentStatuses(props: { runs: Array<Run> | undefined }) {
  function statusChip(index: number) {
    if (props.runs === undefined) {
      return <RunStateChip key={index} />;
    }
    if (props.runs.length > index) {
      return (
        <RunStateChip state={props.runs[index].future_state} key={index} />
      );
    } else {
      return <CircleOutlined color="disabled" key={index} />;
    }
  }
  return <>{[...Array(5)].map((e, i) => statusChip(i))}</>;
}

function PipelineRow(props: { run: Run }) {
  let run = props.run;

  const [runs, setRuns] = useState<Array<Run> | undefined>(undefined);

  useEffect(() => {
    let filters = JSON.stringify({
      calculator_path: { eq: run.calculator_path },
    });

    fetch("/api/v1/runs?limit=5&filters=" + filters)
      .then((res) => res.json())
      .then((result: RunListPayload) => {
        setRuns(result.content);
      });
  }, [run.calculator_path]);

  let startedAt = new Date(run.started_at || run.created_at);
  let endedAt = new Date();
  let endTimeString = run.failed_at || run.resolved_at;
  if (endTimeString) {
    endedAt = new Date(endTimeString);
  }

  let durationMS: number = endedAt.getTime() - startedAt.getTime();

  return (
    <>
      <TableRow key={run.id}>
        <TableCell key="name">
          <Link href={"/pipelines/" + run.calculator_path} underline="hover">
            <Typography variant="h6">{run.name}</Typography>
          </Link>
          <Typography fontSize="small" color="GrayText">
            <code>{run.calculator_path}</code>
          </Typography>
        </TableCell>
        <TableCell key="description">
          <Box
            maxWidth={400}
            sx={{
              textOverflow: "ellipsis",
              overflow: "hidden",
              whiteSpace: "nowrap",
            }}
            component="div"
          >
            <Tooltip title={run.description || ""} placement="bottom-start">
              <Typography variant="caption" color="GrayText">
                {run.description}
              </Typography>
            </Tooltip>
          </Box>
          <Tags tags={run.tags || []} />
        </TableCell>
        <TableCell key="last-run">
          {<ReactTimeAgo date={new Date(run.created_at)} locale="en-US" />}
          <Typography fontSize="small" color="GrayText">
            {Number.parseFloat((durationMS / 1000).toString()).toFixed(1)}{" "}
            seconds on&nbsp;
            {new Date(run.created_at).toLocaleString()}
          </Typography>
        </TableCell>
        <TableCell key="status" width={120}>
          <RecentStatuses runs={runs} />
        </TableCell>
      </TableRow>
    </>
  );
}

function PipelineIndex() {
  return (
    <>
      <Typography variant="h4" component="h2">
        Pipelines
      </Typography>
      <RunList
        columns={["Name", "Description", "Last run", "Status"]}
        groupBy="calculator_path"
        filters={{ AND: [{ parent_id: { eq: null } }] }}
        emptyAlert="No pipelines."
      >
        {(run: Run) => <PipelineRow run={run} key={run.id} />}
      </RunList>
    </>
  );
}

export default PipelineIndex;
