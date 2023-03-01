import Typography from "@mui/material/Typography";
import { Run } from "../Models";
import { RunList, RunListColumn } from "../components/RunList";
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

function RowNameColumn({run}: {run: Run}) {
  let calculatorPath: React.ReactElement = <Box><CalculatorPath calculatorPath={run.calculator_path} /></Box>;
  return <>
    <Typography variant="h6">
      <MuiRouterLink href={getRunUrlPattern(run.id)} underline="hover">
          {run.name}
      </MuiRouterLink>
    </Typography>
      {calculatorPath}
  </>;
}

const TableColumns: Array<RunListColumn> = [
  {name: "ID", width: "7.5%", render: (run: Run) => <Id id={run.id} trimTo={8} />},
  {name: "Name", width: "47.5%", render: (run: Run) => <RowNameColumn run={run} />},
  {name: "Tags", width: "21%", render: (run: Run) => <Tags tags={run.tags || []} />},
  {name: "Time", width: "12%", 
    render: (run: Run) => <><TimeAgo date={run.created_at} />
    <RunTime run={run} prefix="in" /></>},
  {name: "Status", width: "12%", 
  render: (run: Run) => <RunStateChip run={run} variant="full" />}
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
          <RunList columns={TableColumns} search={submitedSearchString} />
        </Box>
      </StyledScroller>
  );
}
