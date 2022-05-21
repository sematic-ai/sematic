import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import TimeAgo from "javascript-time-ago";
import ReactTimeAgo from "react-time-ago";
import en from "javascript-time-ago/locale/en.json";
import { Run } from "../Models";
import { RunList } from "../components/RunList";
import RunStateChip from "../components/RunStateChip";
import React, { useState } from "react";
import Tags from "../components/Tags";
import CalculatorPath from "../components/CalculatorPath";

TimeAgo.addDefaultLocale(en);

type RunRowProps = {
  run: Run;
  variant?: string;
  onClick?: React.MouseEventHandler;
  selected?: boolean;
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
        <Typography fontSize="small" color="GrayText">
          <code>{run.id.substring(0, 8)}</code>
        </Typography>
      </TableCell>
      <TableCell onClick={props.onClick}>
        <Link href={"/runs/" + run.id} underline="hover">
          {run.name}
        </Link>
        {calculatorPath}
      </TableCell>
      <TableCell>
        <Tags tags={run.tags || []} />
      </TableCell>
      <TableCell onClick={props.onClick}>
        {<ReactTimeAgo date={new Date(run.created_at)} locale="en-US" />}
        {createdAt}
      </TableCell>
      <TableCell onClick={props.onClick}>
        <RunStateChip state={run.future_state} />
      </TableCell>
    </TableRow>
  );
}

export function RunIndex() {
  return (
    <>
      <Typography variant="h4" component="h2">
        Run list
      </Typography>
      <RunList columns={["ID", "Name", "Tags", "Time", "Status"]}>
        {(run: Run) => <RunRow run={run} key={run.id} />}
      </RunList>
    </>
  );
}
