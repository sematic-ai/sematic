import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Artifact, Edge, Run } from "../Models";
import { RunGraphPayload } from "../Payloads";
import { fetchJSON, graphSocket } from "../utils";
import { ArtifactList } from "./Artifacts";
import Loading from "./Loading";
import { FlowWithProvider } from "./ReactFlowDag";
import SourceCode from "./SourceCode";
import CalculatorPath from "./CalculatorPath";
import Tab from "@mui/material/Tab";
import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import Tags from "./Tags";
import Docstring from "./Docstring";
import { Alert } from "@mui/material";
import { UserContext } from "..";

export type IOArtifacts = {
  input: Map<string, Artifact | undefined>;
  output: Map<string, Artifact | undefined>;
};

type Graph = {
  runs: Map<string, Run>;
  edges: Edge[];
  artifacts: Artifact[];
};

function DagTab(props: { rootRun: Run }) {
  let rootRun = props.rootRun;

  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [graphsByRootId, setGraphsByRootId] = useState<Map<string, Graph>>(
    new Map()
  );
  const { user } = useContext(UserContext);

  const [selectedRunId, setSelectedRunId] = useState<string>(rootRun.id);

  useEffect(() => {
    graphSocket.removeAllListeners();
    graphSocket.on("update", (args: { run_id: string }) => {
      if (args.run_id === rootRun.id) {
        loadGraph();
      }
    });
  }, [rootRun]);

  useEffect(() => {
    setSelectedRunId(rootRun.id);
  }, [rootRun.id]);

  const loadGraph = useCallback(() => {
    fetchJSON({
      url: "/api/v1/runs/" + rootRun.id + "/graph?root=1",
      apiKey: user?.api_key,
      callback: (payload: RunGraphPayload) => {
        let graph = {
          runs: new Map(payload.runs.map((run) => [run.id, run])),
          edges: payload.edges,
          artifacts: payload.artifacts,
        };
        setGraphsByRootId((currentMap) => {
          currentMap.set(rootRun.id, graph);
          return new Map(currentMap);
        });
        setIsLoaded(true);
      },
      setError: setError,
    });
  }, [rootRun]);

  useEffect(() => {
    if (!graphsByRootId.has(rootRun.id)) {
      setIsLoaded(false);
      loadGraph();
    }
  }, [rootRun]);

  const runs = useMemo(
    () => graphsByRootId.get(rootRun.id)?.runs,
    [graphsByRootId, rootRun]
  );

  const artifactsById = useMemo(() => {
    let allArtifactsForRoot = graphsByRootId.get(rootRun.id)?.artifacts;
    return (
      allArtifactsForRoot &&
      new Map(allArtifactsForRoot.map((artifact) => [artifact.id, artifact]))
    );
  }, [graphsByRootId, rootRun]);

  const edges = useMemo(
    () => graphsByRootId.get(rootRun.id)?.edges,
    [graphsByRootId, rootRun]
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
          //setError(Error("Artifact missing"));
          return;
        }
      }
      map.set(
        name ? name : "null",
        artifact_id ? artifactsById.get(artifact_id) : undefined
      );
    };

    edges.forEach((edge) => {
      if (edge.destination_run_id === selectedRunId) {
        setArtifact(ioArtifacts.input, edge.artifact_id, edge.destination_name);
      }
      if (edge.source_run_id === selectedRunId) {
        setArtifact(ioArtifacts.output, edge.artifact_id, edge.source_name);
      }
    });
    return ioArtifacts;
  }, [edges, artifactsById, selectedRunId]);

  let selectedRun = useMemo(
    () => runs?.get(selectedRunId),
    [runs, selectedRunId]
  );

  if (error || !isLoaded) return <Loading error={error} isLoaded={isLoaded} />;

  if (
    runs === undefined ||
    edges === undefined ||
    artifactsById === undefined ||
    selectedRun === undefined
  ) {
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
          <FlowWithProvider
            // Nasty hack to make sure the DAG is remounted each time to trigger a ReactFlow onInit
            // to trigger a new layout
            key={Math.random().toString()}
            runs={Array.from(runs.values())}
            edges={edges}
            artifactsById={artifactsById}
            onSelectRun={(run) => {
              //if (run.id !== selectedRun.id) {
              setSelectedRunId(run.id);
              //}
            }}
            selectedRunId={selectedRunId}
          />
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

export function RunTabs(props: {
  run: Run;
  artifacts: IOArtifacts | undefined;
}) {
  const { run, artifacts } = props;

  const [selectedTab, setSelectedTab] = useState("output");

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
            <Tab label="Source" value="source" />
            <Tab label="Logs" value="logs" disabled />
          </TabList>
        </Box>
        <TabPanel value="input">
          {artifacts && <ArtifactList artifacts={artifacts.input} />}
        </TabPanel>
        <TabPanel value="output" sx={{ pt: 5 }}>
          {["CREATED", "SCHEDULED", "RAN"].includes(run.future_state) && (
            <Alert severity="info">No output yet. Run has not completed</Alert>
          )}
          {["FAILED", "NESTED_FAILED"].includes(run.future_state) && (
            <Alert severity="error">Run has failed. No output.</Alert>
          )}
          {artifacts && run.future_state === "RESOLVED" && (
            <ArtifactList artifacts={artifacts.output} />
          )}
        </TabPanel>
        <TabPanel value="documentation">
          <Docstring docstring={run.description} />
        </TabPanel>
        <TabPanel value="source">
          <SourceCode run={run} />
        </TabPanel>
      </TabContext>
    </>
  );
}

export default DagTab;
