import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import TimeAgo from "javascript-time-ago";
import ReactTimeAgo from "react-time-ago";
import en from "javascript-time-ago/locale/en.json";
import { Run } from "../Models";
import RunList from "../components/RunList";
import RunStateChip from "../components/RunStateChip";

TimeAgo.addDefaultLocale(en);

function RunRow(props: { run: Run }) {
  let run = props.run;

  return (
    <TableRow key={run.id}>
      <TableCell>
        <code>{run.id.substring(0, 8)}</code>
      </TableCell>
      <TableCell>
        <Link href={"/runs/" + run.id} underline="hover">
          {run.name}
        </Link>
        <Typography fontSize="small" color="GrayText">
          <code>{run.calculator_path}</code>
        </Typography>
      </TableCell>
      <TableCell>
        {<ReactTimeAgo date={new Date(run.created_at)} locale="en-US" />}
        <Typography fontSize="small" color="GrayText">
          {new Date(run.created_at).toLocaleString()}
        </Typography>
      </TableCell>
      <TableCell>
        <RunStateChip state={run.future_state} />
      </TableCell>
    </TableRow>
  );
}

function RunIndex() {
  return (
    <>
      <Typography variant="h4" component="h2">
        Run list
      </Typography>
      <RunList columns={["ID", "Name", "Time", "Status"]}>
        {(run: Run) => <RunRow run={run} key={run.id} />}
      </RunList>
    </>
  );
}

export default RunIndex;
