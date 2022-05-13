import { Typography } from "@mui/material";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import RunList from "./components/RunList";
import { Run } from "./Models";


function PipelineRow(props: { run: Run }) {
  let run = props.run;
  return (
    <TableRow key={run.id}>
      <TableCell key="name">
        <Typography variant="h6">
          {run.name}
        </Typography>
      </TableCell>
    </TableRow>
  );  
};


function Dashboard() {    
  return (
    <RunList columns={['Name']} groupBy="calculator_path" filters={{ parent_id: { eq: null } }}>
      {(run: Run) => <PipelineRow run={run} key={run.id}/>}
    </RunList>
  );
}

export default Dashboard;