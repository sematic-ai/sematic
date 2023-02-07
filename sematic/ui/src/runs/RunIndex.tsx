import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import { Run } from "../Models";
import { RunList } from "../components/RunList";
import RunStateChip from "../components/RunStateChip";
import React, { ChangeEvent, FormEvent, FormEventHandler, useCallback, useState } from "react";
import Tags from "../components/Tags";
import CalculatorPath from "../components/CalculatorPath";
import Id from "../components/Id";
import TimeAgo from "../components/TimeAgo";
import { Box, Button, Container, TextField } from "@mui/material";
import { RunTime } from "../components/RunTime";
import { SearchOutlined } from "@mui/icons-material";

type RunRowProps = {
  run: Run;
  variant?: string;
  onClick?: React.MouseEventHandler;
  selected?: boolean;
  noRunLink?: boolean;
};

export function RunRow(props: RunRowProps) {
  let run = props.run;

  let calculatorPath: React.ReactElement | undefined = undefined;
  let createdAt: React.ReactElement | undefined;

  if (props.variant !== "skinny") {
    calculatorPath = <Box><CalculatorPath calculatorPath={run.calculator_path}/></Box>;

    createdAt = (
      <Typography fontSize="small" color="GrayText">
        {new Date(run.created_at).toLocaleString()}
      </Typography>
    );
  }

  return (
    <TableRow
      key={run.id}
      hover={props.onClick !== undefined}
      sx={{ cursor: props.onClick ? "pointer" : undefined }}
      selected={props.selected}
    >
      <TableCell onClick={props.onClick} width={1}>
        <Id id={run.id} trimTo={8} />
      </TableCell>
      <TableCell onClick={props.onClick}>
      <Typography variant="h6">
        {props.noRunLink && run.name}
        {!props.noRunLink && (
          <Link href={"/runs/" + run.id} underline="hover">
            {run.name}
          </Link>
        )}
        </Typography>
        {calculatorPath}
      </TableCell>
      <TableCell>
        <Tags tags={run.tags || []} />
      </TableCell>
      <TableCell onClick={props.onClick}>
        <TimeAgo date={run.created_at} /><RunTime run={run} prefix="in" />
      </TableCell>
      <TableCell onClick={props.onClick}>
        <RunStateChip run={run} variant="full"/>
      </TableCell>
    </TableRow>
  );
}

export function RunIndex() {

  const [searchString, setSearchString] = useState<string | undefined>(undefined);
  const [submitedSearchString, setSubmitedSearchString] = useState<string | undefined>(undefined);

  const onChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setSearchString(event.target.value);
  }, []);

  const onSubmit = useCallback((event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    console.log(searchString);
    setSubmitedSearchString(searchString);
  }, [searchString]);

  return (
    <Container sx={{ pt: 10, height: "100vh", overflowY: "scroll", display: "grid", gridTemplateRows: "auto 1fr" }}>

      <Box sx={{gridRow: 1}}>

      <Typography variant="h4" component="h2">
        Runs
      </Typography>
      <form onSubmit={onSubmit}>
      <Box sx={{py: 10, display: "grid", gridTemplateColumns: "1fr auto"}}>
        <Box sx={{gridColumn: 1, pr: 10}}>
        <TextField 
        id="outlined-basic"
        label="Search"
        variant="outlined"
        sx={{width: "100%"}}
        onChange={onChange}
        />
        </Box>
        <Box sx={{gridColumn: 2}}>
          <Button variant="contained" size="large" startIcon={<SearchOutlined/>} sx={{height: "100%"}} type="submit">SEARCH</Button>
        </Box>
      </Box>
      </form>
        </Box>
        <Box sx={{gridRow: 2}}>
      <RunList columns={["ID", "Name", "Tags", "Time", "Status"]} search={submitedSearchString}>
        {(run: Run) => <RunRow run={run} key={run.id} onClick={() => null}/>}
      </RunList>
        </Box>
    </Container>
  );
}
