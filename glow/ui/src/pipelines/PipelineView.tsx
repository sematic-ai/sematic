import Container from "@mui/material/Container";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useState, useEffect, useCallback } from "react";
import { Artifact, Run } from "../Models";
import { ArtifactListPayload, RunListPayload } from "../Payloads";
import Loading from "../components/Loading";
import Tags from "../components/Tags";
import { useParams } from "react-router-dom";
import { Card, Grid, Typography } from "@mui/material";
import { RunList, RunFilterType } from "../components/RunList";
import { RunRow } from "../runs/RunIndex";
import CalculatorPath from "../components/CalculatorPath";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import python from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import docco from "react-syntax-highlighter/dist/esm/styles/hljs/docco";
import ReactMarkdown from "react-markdown";
import { ArtifactList } from "../components/Artifacts";

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

  if (error) {
    return <Alert severity="error">API Error: {error.message}</Alert>;
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
                <Card variant="outlined" sx={{ padding: 4, fontSize: "small" }}>
                  {(lastRun.description && (
                    <ReactMarkdown>{lastRun.description}</ReactMarkdown>
                  )) || (
                    <Typography color="GrayText">
                      Your function's docstring will appear here.
                    </Typography>
                  )}
                </Card>
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
            />
          )}
        </RunList>
        <SelectedRun run={selectedRun} />
      </>
    );
  }
  return (
    <Box textAlign="center">
      <Loading />
    </Box>
  );
}

type ArtifactMap = {
  input: Map<string, Artifact>;
  output: Map<string, Artifact>;
};

type RunArtifactMap = Map<string, ArtifactMap>;

function buildArtifactMap(payload: ArtifactListPayload): ArtifactMap {
  let artifactsByID: Map<string, Artifact> = new Map();
  payload.content.forEach((artifact) =>
    artifactsByID.set(artifact.id, artifact)
  );
  let artifactMap: ArtifactMap = { input: new Map(), output: new Map() };
  Object.entries(payload.extra.run_mapping).forEach(([runId, mapping]) => {
    Object.entries(mapping).forEach(([relationship, artifacts]) => {
      Object.entries(artifacts).forEach(([name, artifactId]) => {
        let artifact = artifactsByID.get(artifactId);
        if (artifact) {
          let map =
            relationship === "input" ? artifactMap.input : artifactMap.output;
          map.set(name, artifact);
        } else {
          throw Error("Missing artifact");
        }
      });
    });
  });

  return artifactMap;
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
    fetch("/api/v1/artifacts?run_ids=" + run.id)
      .then((res) => res.json())
      .then(
        (result: ArtifactListPayload) => {
          if (run === undefined) return;
          let newMap = artifacts;
          newMap.set(run.id, buildArtifactMap(result));
          setArtifacts(newMap);
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

  console.log(artifactMap);

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
          <Loading />
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
            <Grid container>
              <Grid item xs={6}>
                <Typography variant="overline" fontSize="small">
                  Input
                </Typography>
                <ArtifactList artifacts={artifactMap.input} />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="overline" fontSize="small">
                  Output
                </Typography>
                <ArtifactList artifacts={artifactMap.output} />
              </Grid>
            </Grid>
          </TabPanel>
          <TabPanel value={selectedTab} index={tabIndex.SOURCE}>
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
          </TabPanel>
          <TabPanel value={selectedTab} index={tabIndex.DAG}>
            Item Two
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
