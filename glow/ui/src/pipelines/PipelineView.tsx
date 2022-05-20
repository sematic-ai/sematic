import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useState, useEffect, useMemo, useCallback } from "react";
import { Run } from "../Models";
import { RunListPayload } from "../Payloads";
import Loading from "../components/Loading";
import { useParams } from "react-router-dom";
import { TableCell, TableRow, Typography } from "@mui/material";
import Chip from "@mui/material/Chip";
import { RunList, RunFilterType } from "../components/RunList";
import { RunRow } from "../runs/RunIndex";

function PipelineView() {
  let params = useParams();
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [lastRun, setLastRun] = useState<Run | undefined>(undefined);
  const [selectedRun, setSelectedRun] = useState<Run | undefined>(undefined);
  const [runIsLoading, setRunIsLoading] = useState(false);

  useEffect(() => {
    let filters = JSON.stringify({
      calculator_path: { eq: params.calculatorPath },
    });
    fetch("/api/v1/runs?limit=1&filters=" + filters)
      .then((res) => res.json())
      .then(
        (result: RunListPayload) => {
          if (result.content.length > 0) {
            setLastRun(result.content[0]);
          } else {
            setError(Error("No pipeline named " + params.calculatorPath));
          }
          setIsLoaded(true);
        },
        (error) => {
          setError(error);
          setIsLoaded(true);
        }
      );
  }, [params.calculatorPath]);

  useEffect(() => {
    setRunIsLoading(selectedRun !== undefined);
  }, [selectedRun]);

  if (error) {
    return <Alert severity="error">API Error: {error.message}</Alert>;
  } else if (lastRun) {
    let runFilters: RunFilterType = {
      AND: [
        { parent_id: { eq: null } },
        { calculator_path: { eq: lastRun.calculator_path } },
      ],
    };

    let onRowClick = (run: Run) => {
      if (selectedRun && selectedRun.id === run.id) {
        setSelectedRun(undefined);
      } else {
        setSelectedRun(run);
      }
    };

    let tabsDisabled = !selectedRun || runIsLoading;

    let selectedTab: number = 0;

    return (
      <>
        <Box marginBottom={5}>
          <Box marginBottom={3}>
            <Typography variant="h5" component="h2">
              {lastRun.name}
            </Typography>
            <Typography fontSize="small" color="GrayText">
              <code>{lastRun.calculator_path}</code>
            </Typography>
          </Box>
          <Box marginBottom={1}>
            <Typography variant="overline" component="h3">
              Description
            </Typography>
            <Typography>{lastRun.description}</Typography>
          </Box>
          <Box>
            {(lastRun.tags || []).map((tag) => (
              <Chip
                label={tag}
                color="primary"
                size="small"
                variant="outlined"
                key={tag}
                sx={{ marginRight: 1 }}
              />
            ))}
          </Box>
        </Box>
        <Typography variant="h6" component="h3">
          Latest runs
        </Typography>
        <RunList
          columns={["ID", "Name", "Time", "Status"]}
          filters={runFilters}
          pageSize={5}
          size="small"
        >
          {(run: Run) => (
            <RunRow
              run={run}
              key={run.id}
              variant="skinny"
              onClick={(e) => onRowClick(run)}
              selected={selectedRun?.id === run.id}
            />
          )}
        </RunList>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <Tabs value={0} onChange={undefined} aria-label="input artifacts">
            <Tab label="Inputs" disabled={tabsDisabled} />
            <Tab label="Output" disabled={tabsDisabled} />
            <Tab label="Graph" disabled={tabsDisabled} />
          </Tabs>
        </Box>
        {runIsLoading && (
          <Box textAlign="center">
            <Loading />
          </Box>
        )}
        {!runIsLoading && !selectedRun && (
          <Box padding={3}>
            <Alert severity="info">Select a run.</Alert>
          </Box>
        )}
        {!runIsLoading && selectedRun && (
          <>
            <TabPanel value={selectedTab} index={0}>
              Item One
            </TabPanel>
            <TabPanel value={selectedTab} index={1}>
              Item Two
            </TabPanel>
            <TabPanel value={selectedTab} index={2}>
              Item Three
            </TabPanel>
          </>
        )}
      </>
    );
  }
  return (
    <Box textAlign="center">
      <Loading />
    </Box>
  );
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    "aria-controls": `simple-tabpanel-${index}`,
  };
}

export default PipelineView;
