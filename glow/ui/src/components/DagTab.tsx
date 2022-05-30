import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useEffect, useMemo, useState } from "react";
import { Artifact, Edge, Run } from "../Models";
import {
  ArtifactListPayload,
  EdgeListPayload,
  RunListPayload,
} from "../Payloads";
import { fetchJSON } from "../utils";
import { ArtifactList } from "./Artifacts";
import Loading from "./Loading";
import { FlowWithProvider } from "./ReactFlowDag";
import SourceCode from "./SourceCode";
import CalculatorPath from "./CalculatorPath";
import Alert from "@mui/material/Alert";
import Tab from "@mui/material/Tab";
import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import { Tooltip } from "@mui/material";
import Tags from "./Tags";
import Docstring from "./Docstring";

type IOArtifacts = {
  input: Map<string, Artifact | undefined>;
  output: Map<string, Artifact | undefined>;
};

function DagTab(props: { rootRun: Run }) {
  let rootRun = props.rootRun;

  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoadedRuns, setIsLoadedRuns] = useState(false);
  const [isLoadedEdges, setIsLoadedEdges] = useState(false);
  const [isLoadedArtifacts, setIsLoadedArtifacs] = useState(false);

  const [runsByRootId, setRunsByRootId] = useState<
    Map<string, Map<string, Run>>
  >(new Map());
  const [edgesByRootId, setEdgesByRootId] = useState<Map<string, Edge[]>>(
    new Map()
  );
  const [artifactsByRootId, setArtifactsByRootId] = useState<
    Map<string, Artifact[]>
  >(new Map());

  const [selectedRun, setSelectedRun] = useState<Run>(rootRun);

  useEffect(() => {
    setSelectedRun(rootRun);
  }, [rootRun]);

  useEffect(() => {
    if (runsByRootId.has(rootRun.id)) return;
    let filters = JSON.stringify({ root_id: { eq: rootRun.id } });

    fetchJSON(
      "/api/v1/runs?limit=-1&filters=" + filters,
      (payload: RunListPayload) =>
        setRunsByRootId(
          (currentMap) =>
            // Have to make a new map to make sure memoized values get refreshed
            new Map([
              ...Array.from(currentMap),
              [
                rootRun.id,
                new Map<string, Run>(
                  payload.content.map((run) => [run.id, run])
                ),
              ],
            ])
        ),
      setError,
      setIsLoadedRuns
    );
  }, [rootRun, runsByRootId]);

  useEffect(() => {
    if (edgesByRootId.has(rootRun.id)) return;
    let runs = runsByRootId.get(rootRun.id);
    if (runs === undefined) return;

    let runIds = Array.from(runs.keys());

    let filters = JSON.stringify({
      OR: [
        { source_run_id: { in: runIds } },
        { destination_run_id: { in: runIds } },
      ],
    });

    fetchJSON(
      "/api/v1/edges?limit=-1&filters=" + filters,
      (payload: EdgeListPayload) =>
        setEdgesByRootId(
          (currentMap) =>
            // Have to make a new map to make sure memoized values get refreshed
            new Map([...Array.from(currentMap), [rootRun.id, payload.content]])
        ),
      setError,
      setIsLoadedEdges
    );
  }, [rootRun, edgesByRootId, runsByRootId]);

  useEffect(() => {
    if (artifactsByRootId.has(rootRun.id)) return;
    let edges = edgesByRootId.get(rootRun.id);
    if (edges === undefined) return;

    let artifactIds = edges
      .map((edge) => edge.artifact_id)
      .filter((artifactId) => artifactId !== null);

    let filters = JSON.stringify({ id: { in: artifactIds } });

    fetchJSON(
      "/api/v1/artifacts?limit=-1&filters=" + filters,
      (payload: ArtifactListPayload) =>
        setArtifactsByRootId(
          (currentMap) =>
            // Have to make a new map to make sure memoized values get refreshed
            new Map([...Array.from(currentMap), [rootRun.id, payload.content]])
        ),
      setError,
      setIsLoadedArtifacs
    );
  }, [rootRun.id, artifactsByRootId, edgesByRootId]);

  const runs = useMemo(
    () => runsByRootId.get(rootRun.id),
    [runsByRootId, rootRun]
  );

  const artifactsById = useMemo(() => {
    let allArtifactsForRoot = artifactsByRootId.get(rootRun.id);
    return (
      allArtifactsForRoot &&
      new Map(allArtifactsForRoot.map((artifact) => [artifact.id, artifact]))
    );
  }, [artifactsByRootId.size, rootRun]);

  const edges = useMemo(
    () => edgesByRootId.get(rootRun.id),
    [edgesByRootId, rootRun]
  );

  const selectedRunArtifacts = useMemo(() => {
    if (edges === undefined) return;
    if (artifactsById === undefined) return;

    let ioArtifacts: IOArtifacts = { input: new Map(), output: new Map() };

    const setArtifact = (
      map: Map<string, Artifact | undefined>,
      artifact_id: string | null,
      name: string | null
    ) => {
      let artifact: Artifact | undefined = undefined;
      if (artifact_id !== null) {
        artifact = artifactsById.get(artifact_id);
        if (artifact === undefined) {
          setError(Error("Artifact missing"));
          return;
        }
      }
      map.set(
        name ? name : "null",
        artifact_id ? artifactsById.get(artifact_id) : undefined
      );
    };

    edges.forEach((edge) => {
      if (edge.destination_run_id === selectedRun.id) {
        setArtifact(ioArtifacts.input, edge.artifact_id, edge.destination_name);
      }
      if (edge.source_run_id === selectedRun.id) {
        setArtifact(ioArtifacts.output, edge.artifact_id, edge.source_name);
      }
    });
    return ioArtifacts;
  }, [edges, artifactsById, selectedRun]);

  if (error || !(isLoadedRuns && isLoadedEdges && isLoadedArtifacts))
    return (
      <Loading
        error={error}
        isLoaded={isLoadedRuns && isLoadedArtifacts && isLoadedEdges}
      />
    );

  if (runs == undefined || edges === undefined || artifactsById === undefined) {
    setError(
      Error(
        "There was problem loading the graph: no runs or edges or artifacts."
      )
    );
    return <></>; // necessary to ensure runs is defined below.
  }

  return (
    <Grid container>
      <Grid item xs={6}>
        <Typography variant="h6">Execution graph</Typography>
        <Box paddingTop={6} paddingX={0}>
          {
            //<ReaflowDag runs={Array.from(runs.values())} edges={edges} />
          }
          {
            <FlowWithProvider
              runs={Array.from(runs.values())}
              edges={edges}
              artifactsById={artifactsById}
              onSelectRun={(run) => {
                if (run.id != selectedRun.id) {
                  setSelectedRun(run);
                }
              }}
            />
          }
        </Box>
      </Grid>
      <Grid item xs={6}>
        <Box paddingBottom={3}>
          <Box marginBottom={3}>
            <Typography variant="h6">{selectedRun.name}</Typography>
            <CalculatorPath calculatorPath={selectedRun.calculator_path} />
          </Box>
          <Tags tags={selectedRun.tags || []} />
        </Box>
        <RunTabs run={selectedRun} artifacts={selectedRunArtifacts} />
      </Grid>
    </Grid>
  );
}

const defaultSelectedTab: { [k: string]: string } = {
  RESOLVED: "output",
  CREATED: "input",
  SCHEDULED: "input",
  RAN: "input",
  FAILED: "logs",
  NESTED_FAILED: "logs",
};

function getDefaultTab(future_state: string): string {
  if (future_state in defaultSelectedTab) {
    return defaultSelectedTab[future_state];
  }
  return "input";
}

function RunTabs(props: { run: Run; artifacts: IOArtifacts | undefined }) {
  const { run, artifacts } = props;

  const [selectedTab, setSelectedTab] = useState(
    getDefaultTab(run.future_state)
  );

  const handleChange = (event: React.SyntheticEvent, newValue: string) => {
    setSelectedTab(newValue);
  };

  return (
    <>
      <TabContext value={selectedTab}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList onChange={handleChange} aria-label="Selected run tabs">
            <Tab label="Input" value="input" />
            <Tab label="Output" value="output" />
            <Tab label="Documentation" value="documentation" />
            <Tab label="Source" value="source" />
            <Tab label="Comments" value="comments" disabled />
            <Tab label="Logs" value="logs" disabled />
          </TabList>
        </Box>
        <TabPanel value="input">
          {artifacts && <ArtifactList artifacts={artifacts.input} />}
        </TabPanel>
        <TabPanel value="output">
          {artifacts && <ArtifactList artifacts={artifacts.output} />}
        </TabPanel>
        <TabPanel value="documentation">
          <Docstring run={run} />
        </TabPanel>
        <TabPanel value="source">
          <SourceCode run={run} />
        </TabPanel>
      </TabContext>
    </>
  );
}

export default DagTab;
