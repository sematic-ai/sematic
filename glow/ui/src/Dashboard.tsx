import Typography from "@mui/material/Typography";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import { useEffect, useState } from "react";
import RunList from "./components/RunList";
import { Run } from "./Models";
import Link from '@mui/material/Link';
import { RunListPayload } from "./Payloads";
import RunStateChip from "./components/RunStateChip";
import CircleOutlined from "@mui/icons-material/CircleOutlined";

function RecentStatuses(props: { runs: Array<Run> | undefined }) {
  function statusChip(index: number) {
    if (props.runs === undefined) {
      return <RunStateChip key={index}/>;
    }
    if (props.runs.length > index) {
      return <RunStateChip state={props.runs[index].future_state} key={index}/>
    } else {
      return <CircleOutlined color="disabled" key={index}/>
    }
  }
  return (
    <>
      {[...Array(5)].map((e, i) => statusChip(i))}
    </>
    );
};


function PipelineRow(props: { run: Run }) {
  let run = props.run;

  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [runs, setRuns] = useState<Array<Run> | undefined>(undefined);

  
  useEffect(() => {
    let filters = JSON.stringify({calculator_path: {eq: run.calculator_path}})

    fetch("/api/v1/runs?limit=5&filters=" + filters)
      .then(res => res.json())
      .then(
        (result: RunListPayload) => { 
          setRuns(result.content);
          setIsLoaded(true);
        },
        (error) => { 
          setError(error);
          setIsLoaded(true);
        }
      );
  }, [run.calculator_path]);

  let startedAt = new Date(run.started_at || run.created_at);
  let endedAt = new Date()
  let endTimeString = run.failed_at || run.resolved_at;
  if (endTimeString) {
    endedAt = new Date(endTimeString)
  }

  let durationMS: number = endedAt.getTime() - startedAt.getTime();

  return (
    <TableRow key={run.id}>
      <TableCell key="name">
      <Link href={"/runs/" + run.id} underline="hover">
        <Typography variant="h6">
          {run.name}
            </Typography>
        </Link>
        <Typography fontSize="small" color="GrayText">
          <code>
            {run.calculator_path}
          </code>
          </Typography>
      </TableCell>
      <TableCell key="last-run">
        <Typography fontSize='small' color='GrayText'>
          {durationMS / 1000} seconds on&nbsp;
          {(new Date(run.created_at)).toLocaleString()}
          </Typography>
      </TableCell>
      <TableCell key="status">
        <RecentStatuses runs={runs} />
      </TableCell>
    </TableRow>
  );  
};


function Dashboard() {    
  return (
    <>
      <Typography variant="h4" component="h2">Pipelines</Typography>
      <RunList columns={['Name', 'Last run', 'Status']} groupBy="calculator_path" filters={{ parent_id: { eq: null } }}>
        {(run: Run) => <PipelineRow run={run} key={run.id}/>}
        </RunList>
    </>
  );
}

export default Dashboard;