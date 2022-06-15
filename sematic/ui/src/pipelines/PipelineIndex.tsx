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
import ReactTimeAgo from "react-time-ago";
import { Alert, AlertTitle, Card, Container, useTheme } from "@mui/material";
import { SiDiscord, SiReadthedocs } from "react-icons/si";
import { InfoOutlined } from "@mui/icons-material";

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
          <Box sx={{ mb: 3 }}>
            <Link
              href={"/new/pipelines/" + run.calculator_path}
              underline="hover"
            >
              <Typography variant="h6">{run.name}</Typography>
            </Link>
            <Typography fontSize="small" color="GrayText">
              <code>{run.calculator_path}</code>
            </Typography>
          </Box>
          <Tags tags={run.tags || []} />
        </TableCell>
        <TableCell key="last-run">
          {<ReactTimeAgo date={new Date(run.created_at)} locale="en-US" />}
          <Typography fontSize="small" color="GrayText">
            {Number.parseFloat((durationMS / 1000).toString()).toFixed(1)}{" "}
            seconds
            {/*on&nbsp;
            {new Date(run.created_at).toLocaleString()*/}
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
  const theme = useTheme();
  return (
    <Box sx={{ display: "grid", gridTemplateColumns: "1fr 300px" }}>
      <Box sx={{ gridColumn: 1 }}>
        <Container sx={{ pt: 15 }}>
          <Box sx={{ mx: 5 }}>
            <Box sx={{ mb: 10 }}>
              <Typography variant="h2" component="h2">
                Your pipelines
              </Typography>
            </Box>
            <RunList
              columns={["Name", "Last run", "Status"]}
              groupBy="calculator_path"
              filters={{ AND: [{ parent_id: { eq: null } }] }}
              emptyAlert="No pipelines."
            >
              {(run: Run) => <PipelineRow run={run} key={run.id} />}
            </RunList>
          </Box>
        </Container>
      </Box>
      <Box sx={{ gridColumn: 2, pr: 5, pt: 45 }}>
        <Alert severity="warning" icon={<InfoOutlined />}>
          <AlertTitle>Your latest pipelines are listed here</AlertTitle>
          <p>
            Pipelines are identified by the import path of their entry point,
            which is the function you called <code>.resolve()</code> on.
          </p>
        </Alert>
      </Box>
    </Box>
  );
}

export default PipelineIndex;
