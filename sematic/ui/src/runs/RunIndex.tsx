import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import { Run } from "../Models";
import { RunList } from "../components/RunList";
import RunStateChip from "../components/RunStateChip";
import React, { useCallback, useState } from "react";
import Tags from "../components/Tags";
import CalculatorPath from "../components/CalculatorPath";
import Id from "../components/Id";
import TimeAgo from "../components/TimeAgo";
import { Box, Container, TextField } from "@mui/material";

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
    calculatorPath = <CalculatorPath calculatorPath={run.calculator_path} />;

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
        {props.noRunLink && run.name}
        {!props.noRunLink && (
          <Link href={"/runs/" + run.id} underline="hover">
            {run.name}
          </Link>
        )}
        {calculatorPath}
      </TableCell>
      <TableCell>
        <Tags tags={run.tags || []} />
      </TableCell>
      <TableCell onClick={props.onClick}>
        <TimeAgo date={run.created_at} />
        {createdAt}
      </TableCell>
      <TableCell onClick={props.onClick}>
        <RunStateChip state={run.future_state} />
      </TableCell>
    </TableRow>
  );
}

export function RunIndex() {

  const [searchString, setSearchString] = useState<string | undefined>(undefined);
  
  const onChange = useCallback((value: string) => {
    console.log(value);
    setSearchString(value);
  }, []);

  return (
    <Container sx={{ pt: 10, height: "100vh", overflowY: "scroll" }}>
      <Typography variant="h4" component="h2">
        Run list
      </Typography>
      <Box sx={{py: 10}}>
      <TextField 
        id="outlined-basic"
        label="Search"
        variant="outlined"
        sx={{width: "100%"}}
        onChange={(event) => onChange(event.target.value)}
      />
      </Box>
      <RunList columns={["ID", "Name", "Tags", "Time", "Status"]} search={searchString}>
        {(run: Run) => <RunRow run={run} key={run.id} />}
      </RunList>
    </Container>
  );
}
