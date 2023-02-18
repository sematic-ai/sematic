import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Typography from "@mui/material/Typography";
import { Run } from "../Models";
import { RunList } from "../components/RunList";
import RunStateChip from "../components/RunStateChip";
import React, { ChangeEvent, FormEvent, useCallback, useState } from "react";
import Tags from "../components/Tags";
import CalculatorPath from "../components/CalculatorPath";
import Id from "../components/Id";
import TimeAgo from "../components/TimeAgo";
import { Box, Button, Container, TextField, textFieldClasses, buttonClasses } from "@mui/material";
import { RunTime } from "../components/RunTime";
import { SearchOutlined } from "@mui/icons-material";
import { styled } from "@mui/system";
import { spacing } from "../utils";
import { getRunUrlPattern } from "../hooks/pipelineHooks";
import MuiRouterLink from "../components/MuiRouterLink";

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

  if (props.variant !== "skinny") {
    calculatorPath = <Box><CalculatorPath calculatorPath={run.calculator_path} /></Box>;
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
            <MuiRouterLink href={getRunUrlPattern(run.id)} underline="hover">
              {run.name}
            </MuiRouterLink>
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
        <RunStateChip run={run} variant="full" />
      </TableCell>
    </TableRow>
  );
}

const StyledScroller = styled(Container)`
  padding-top: ${spacing(10)};
  height: 100%;
  overflow-y: hidden;
  display: flex;
  flex-direction: column;

  @media (min-width: 1280px) {
    min-width: 1020px;
  }

  & > * {
    flex-shrink: 1;
  }

  & > *.RunListBox {
    flex-grow: 1;
    flex-shrink: unset;
    height: 0;
  }

  & .search-bar {
    padding-top: ${spacing(10)};
    padding-bottom: ${spacing(10)};
    display: flex;
    flex-direction: row;

    & > *:first-of-type {
      padding-right: ${spacing(10)};
      flex-grow: 1
    }

    & .${buttonClasses.root} {
      height: 100%;
    }
  
    & .${textFieldClasses.root} {
      width: 100%;
    }
  }
`;

const TableColumns = [
  {name: "ID", width: "7.5%"},
  {name: "Name", width: "47.5%"},
  {name: "Tags", width: "21%"},
  {name: "Time", width: "12%"},
  {name: "Status", width: "12%"}
]

export function RunIndex() {

  const [searchString, setSearchString] = useState<string | undefined>(undefined);
  const [submitedSearchString, setSubmitedSearchString] = useState<string | undefined>(undefined);

  const onChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setSearchString(event.target.value);
  }, []);

  const onSubmit = useCallback((event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitedSearchString(searchString);
  }, [searchString]);

  return (<StyledScroller>
          <Typography variant="h4" component="h2">
            Runs
          </Typography>
          <form onSubmit={onSubmit}>
            <Box className={'search-bar'}>
              <Box sx={{ gridColumn: 1 }}>
                <TextField
                  id="outlined-basic"
                  label="Search"
                  variant="outlined"
                  onChange={onChange}
                />
              </Box>
              <Box sx={{ gridColumn: 2 }}>
                <Button variant="contained" size="large" startIcon={<SearchOutlined />} 
                type="submit">
                  SEARCH
                </Button>
              </Box>
            </Box>
          </form>
        <Box className="RunListBox">
          <RunList columns={TableColumns} 
            search={submitedSearchString}>
            {(run: Run) => <RunRow run={run} key={run.id} onClick={() => null} />}
          </RunList>
        </Box>
      </StyledScroller>
  );
}
