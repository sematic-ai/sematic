import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useState, useEffect, useCallback } from "react";
import { Run } from "../Models";
import {
  ArtifactListPayload,
  RunListPayload,
  ArtifactMap,
  RunArtifactMap,
} from "../Payloads";
import Loading from "../components/Loading";
import Tags from "../components/Tags";
import { useParams } from "react-router-dom";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import { RunList, RunFilterType } from "../components/RunList";
import { RunRow } from "../runs/RunIndex";
import CalculatorPath from "../components/CalculatorPath";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import python from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import docco from "react-syntax-highlighter/dist/esm/styles/hljs/docco";
import { ArtifactList } from "../components/Artifacts";
import { fetchJSON } from "../utils";
import DagTab from "../components/DagTab";
import Docstring from "../components/Docstring";

SyntaxHighlighter.registerLanguage("python", python);

function PipelineView() {
  let params = useParams();
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [lastRun, setLastRun] = useState<Run | undefined>(undefined);
  const [selectedRun, setSelectedRun] = useState<Run | undefined>(undefined);

  useEffect(() => {
    let filters = JSON.stringify({
      calculator_path: { eq: params.calculatorPath },
    });
    fetchJSON(
      "/api/v1/runs?limit=1&filters=" + filters,
      (result: RunListPayload) => {
        if (result.content.length > 0) {
          setLastRun(result.content[0]);
          setSelectedRun(result.content[0]);
        } else {
          setError(Error("No pipeline named " + params.calculatorPath));
        }
      },
      setError,
      setIsLoaded
    );
  }, [params.calculatorPath]);

  let onRowClick = useCallback(
    (run: Run) => {
      if (selectedRun && selectedRun.id === run.id) {
        setSelectedRun(undefined);
      } else {
        setSelectedRun(run);
      }
    },
    [selectedRun]
  );

  if (error || !isLoaded) {
    return <Loading error={error} isLoaded={isLoaded} />;
  } else if (lastRun) {
    let runFilters: RunFilterType = {
      AND: [
        { parent_id: { eq: null } },
        { calculator_path: { eq: lastRun.calculator_path } },
      ],
    };

    return (
      <>
        <Box marginTop={2} marginBottom={12}>
          <Box marginBottom={3}>
            <Typography variant="h3" component="h2">
              {lastRun.name}
            </Typography>
            <CalculatorPath calculatorPath={lastRun.calculator_path} />
          </Box>
          <Box>
            <Tags tags={lastRun.tags || []} />
          </Box>
          <Grid container>
            <Grid item xs={6}>
              <Box marginY={3}>
                <Docstring run={lastRun} />
              </Box>
            </Grid>
            <Grid item xs={6}></Grid>
          </Grid>
        </Box>
        <Typography variant="h6" component="h3">
          Latest runs
        </Typography>
        <RunList
          columns={["ID", "Name", "Tags", "Time", "Status"]}
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
              noRunLink
            />
          )}
        </RunList>
        <Box paddingY={10}>
          {!selectedRun && <Alert severity="info">Select a run.</Alert>}
          {selectedRun && <DagTab rootRun={selectedRun} />}
        </Box>
        {
          //<SelectedRun run={selectedRun} />
        }
      </>
    );
  }
  return <></>;
}

function SelectedRun(props: { run: Run | undefined }) {
  const tabIndex = { ARTIFACTS: 0, SOURCE: 1, DAG: 2 };

  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<Error | undefined>(undefined);
  const [selectedTab, setSelectedTab] = useState(tabIndex.ARTIFACTS);
  const [artifacts, setArtifacts] = useState<RunArtifactMap>(new Map());
  const [runsByRootId, setRunsByRootId] = useState<Map<string, Array<Run>>>(
    new Map()
  );

  let run = props.run;
  useEffect(() => {
    setError(undefined);
    if (run === undefined) return;

    if (artifacts.has(run.id)) return;

    setIsLoaded(false);
    fetch("/api/v1/artifacts?run_ids=" + JSON.stringify([run.id]))
      .then((res) => res.json())
      .then(
        (result: ArtifactListPayload) => {
          /*if (run === undefined) return;
          let newMap = artifacts;
          let artifactMap = buildArtifactMap(result).get(run.id);
          if (artifactMap) {
            newMap.set(run.id, artifactMap);
          } else {
            setError(Error("Incorrect artifact response"));
          }
          setArtifacts(newMap);*/
          setIsLoaded(true);
        },
        (error) => {
          setError(error);
          setIsLoaded(true);
        }
      );
  }, [run, selectedTab, artifacts]);

  useEffect(() => {
    if (run === undefined) return;

    if (runsByRootId.has(run.id)) return;

    setIsLoaded(false);

    let filters = JSON.stringify({ root_id: { eq: run.id } });
    fetch("/api/v1/runs?limit=-1&filters=" + filters)
      .then((res) => res.json())
      .then(
        (result: RunListPayload) => {
          if (!run) return;
          let newMap = runsByRootId;
          newMap.set(run.id, result.content);
          setRunsByRootId(newMap);
          setIsLoaded(true);
        },
        (error) => {
          setError(error);
          setIsLoaded(true);
        }
      );
  }, [run, runsByRootId]);

  let tabsDisabled = run === undefined || !isLoaded;

  let artifactMap: ArtifactMap = { input: new Map(), output: new Map() };
  let runs: Array<Run> = [];
  let uniqueRunsByCalculator: Map<string, Run> = new Map();

  if (run) {
    artifactMap = artifacts.get(run.id) || artifactMap;
    runs = runsByRootId.get(run.id) || runs;
    runs.forEach((run_) =>
      uniqueRunsByCalculator.set(run_.calculator_path, run_)
    );
  }

  return (
    <>
      <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs
          value={selectedTab}
          onChange={(e, n) => setSelectedTab(n)}
          aria-label="run-tabs"
        >
          <Tab label="Artifacts" disabled={tabsDisabled} {...a11yProps(0)} />
          <Tab label="Soure code" disabled={tabsDisabled} {...a11yProps(1)} />
          <Tab label="Graph" disabled={tabsDisabled} {...a11yProps(2)} />
        </Tabs>
      </Box>

      {run && !isLoaded && (
        <Box textAlign="center">
          <Loading isLoaded={isLoaded} />
        </Box>
      )}

      {!run && (
        <Box padding={3}>
          <Alert severity="info">Select a run.</Alert>
        </Box>
      )}

      {error && (
        <Box padding={3}>
          <Alert severity="error">API Error: {error.message}</Alert>
        </Box>
      )}

      {run && isLoaded && !error && (
        <>
          <TabPanel value={selectedTab} index={tabIndex.ARTIFACTS}>
            <Grid container paddingTop={5}>
              <Grid item xs={6}>
                <Typography variant="h6">Input values</Typography>
                <ArtifactList artifacts={artifactMap.input} />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="h6">Output value</Typography>
                <ArtifactList artifacts={artifactMap.output} />
              </Grid>
            </Grid>
          </TabPanel>
          <TabPanel value={selectedTab} index={tabIndex.SOURCE}>
            <Box paddingTop={5}>
              <Typography variant="h6">Calculator source code</Typography>
              {Array.from(uniqueRunsByCalculator).map(
                ([calculatorPath, run_]) => (
                  <Box key={calculatorPath} sx={{ marginTop: 2 }}>
                    <Box sx={{ marginTop: 7 }}>
                      <CalculatorPath calculatorPath={calculatorPath} />
                    </Box>
                    <SyntaxHighlighter
                      language="python"
                      style={docco}
                      showLineNumbers
                      customStyle={{ fontSize: 14 }}
                    >
                      {run_.source_code}
                    </SyntaxHighlighter>
                  </Box>
                )
              )}
            </Box>
          </TabPanel>
          <TabPanel value={selectedTab} index={tabIndex.DAG}>
            <Box paddingTop={5}>
              <Typography variant="h6">Execution graph</Typography>
            </Box>
          </TabPanel>
        </>
      )}
    </>
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
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
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
