import Box from "@mui/material/Box";
import { useState, useCallback, useEffect, useMemo } from "react";
import { Artifact, Edge, Run } from "../Models";
import Loading from "../components/Loading";
import Tags from "../components/Tags";
import { useParams } from "react-router-dom";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import { RunList, RunFilterType } from "../components/RunList";
import { RunRow } from "../runs/RunIndex";
import CalculatorPath from "../components/CalculatorPath";
import { fetchJSON, pipelineSocket } from "../utils";
import DagTab from "../components/DagTab";
import Docstring from "../components/Docstring";
import {
  BubbleChart,
  ChevronLeft,
  FormatListBulleted,
  Timeline,
} from "@mui/icons-material";
import {
  FormControl,
  InputLabel,
  Link,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  TextField,
  useTheme,
} from "@mui/material";
import { RunGraphPayload, RunListPayload } from "../Payloads";
import RunStateChip from "../components/RunStateChip";
import Id from "../components/Id";
import ReactTimeAgo from "react-time-ago";
import { FlowWithProvider } from "../components/ReactFlowDag";

type Graph = {
  runs: Map<string, Run>;
  edges: Edge[];
  artifacts: Artifact[];
};

const borderColor = "#f0f0f0";
const backgroundColor = "#f8f9fb";

function ThreePanels(props: { rootRun: Run }) {
  const { rootRun } = props;
  const theme = useTheme();
  const [selectedPanelItem, setSelectedPanelItem] = useState("graph");
  const [graphsByRootId, setGraphsByRootId] = useState<Map<string, Graph>>(
    new Map()
  );
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);

  const loadGraph = useCallback(() => {
    fetchJSON(
      "/api/v1/runs/" + rootRun.id + "/graph",
      (payload: RunGraphPayload) => {
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
      setError
    );
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

  if (error || !isLoaded) {
    return (
      <Box sx={{ p: 5, gridColumn: "1 / 4" }}>
        <Loading error={error} isLoaded={isLoaded} />
      </Box>
    );
  } else {
    return (
      <>
        <Box
          sx={{
            gridColumn: 1,
            gridRow: 2,
            backgroundColor: backgroundColor,
            borderRight: 1,
            borderColor: borderColor,
            overflowY: "scroll",
          }}
        >
          <List sx={{ py: 0 }}>
            <ListItem disablePadding>
              <ListItemButton
                sx={{ height: "4em" }}
                selected={selectedPanelItem == "graph"}
              >
                <ListItemIcon sx={{ minWidth: "40px" }}>
                  <BubbleChart />
                </ListItemIcon>
                <ListItemText primary="Execution graph" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                sx={{ height: "4em" }}
                selected={selectedPanelItem == "topline"}
              >
                <ListItemIcon sx={{ minWidth: "40px" }}>
                  <Timeline />
                </ListItemIcon>
                <ListItemText primary="Topline metrics" />
              </ListItemButton>
            </ListItem>
            <ListItem sx={{ height: "4em" }}>
              <ListItemIcon sx={{ minWidth: "40px" }}>
                <FormatListBulleted />
              </ListItemIcon>
              <ListItemText primary="Nested runs" />
            </ListItem>
          </List>
          <List
            sx={{
              pt: 0,
              borderLeft: 3,
              borderColor: theme.palette.primary.dark,
            }}
          >
            <ListItem disablePadding sx={{}}>
              <ListItemButton>
                <ListItemIcon sx={{ minWidth: "30px" }}>
                  <RunStateChip state={rootRun.future_state} />
                </ListItemIcon>
                <ListItemText primary={rootRun.name} />
              </ListItemButton>
            </ListItem>
          </List>
        </Box>
        <Box sx={{ gridColumn: 2, gridRow: 2, overflowY: "scroll" }}>
          {selectedPanelItem == "graph" && runs && edges && artifactsById && (
            <>
              <FlowWithProvider
                // Nasty hack to make sure the DAG is remounted each time to trigger a ReactFlow onInit
                // to trigger a new layout
                key={Math.random().toString()}
                runs={Array.from(runs.values())}
                edges={edges}
                artifactsById={artifactsById}
                onSelectRun={(run) => {
                  //if (run.id !== selectedRun.id) {
                  //setSelectedRunId(run.id);
                  //}
                }}
                selectedRunId={rootRun.id}
              />
            </>
          )}
        </Box>
        <Box
          sx={{
            gridColumn: 3,
            gridRow: 2,
            borderLeft: 1,
            borderColor: borderColor,
            display: "grid",
            gridTemplateRows: "1fr auto",
          }}
        >
          <Box sx={{ gridRow: 1 }}></Box>
          <Box sx={{ gridRow: 2 }}>
            <TextField
              sx={{ width: "100%", backgroundColor: "#ffffff" }}
              id="filled-textarea"
              label="Add a note"
              placeholder="Your note..."
              multiline
              variant="filled"
            />
          </Box>
        </Box>
      </>
    );
  }
}

export function NewPipelineView() {
  const [error, setError] = useState<Error | undefined>(undefined);
  const [rootRun, setRootRun] = useState<Run | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [latestRuns, setLatestRuns] = useState<Run[]>([]);

  const params = useParams();

  const { calculatorPath } = params;

  useEffect(() => {
    if (calculatorPath === undefined) return;
    const runFilters: RunFilterType = {
      AND: [
        { parent_id: { eq: null } },
        { calculator_path: { eq: calculatorPath } },
      ],
    };

    fetchJSON(
      "/api/v1/runs?limit=5&filters=" + JSON.stringify(runFilters),
      (response: RunListPayload) => {
        setLatestRuns(response.content);
        setRootRun(response.content[0]);
      },
      setError,
      setIsLoaded
    );
  }, [calculatorPath]);

  if (error || !isLoaded) {
    return (
      <Box sx={{ p: 5 }}>
        <Loading error={error} isLoaded={isLoaded} />
      </Box>
    );
  } else if (rootRun) {
    return (
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "250px 1fr 250px",
          gridTemplateRows: "70px 1fr",
          height: "100vh",
        }}
      >
        <Box
          sx={{
            gridRow: 1,
            gridColumn: "1 / 4",
            borderBottom: 1,
            borderColor: borderColor,
            paddingY: 3,
            display: "grid",
            gridTemplateColumns: "70px 1fr auto",
          }}
        >
          <Box
            sx={{
              gridColumn: 1,
              textAlign: "center",
              paddingTop: 2,
              borderRight: 1,
              borderColor: borderColor,
            }}
          >
            <Link href="/new/pipelines">
              <ChevronLeft fontSize="large" />
            </Link>
          </Box>
          <Box sx={{ gridColumn: 2, pl: 7 }}>
            <Typography variant="h4">{rootRun.name}</Typography>
            <CalculatorPath calculatorPath={rootRun.calculator_path} />
          </Box>
          <Box
            sx={{
              gridColumn: 3,
              borderLeft: 1,
              borderColor: borderColor,
              paddingX: 10,
              paddingTop: 1,
            }}
          >
            <FormControl fullWidth size="small">
              <InputLabel id="demo-simple-select-label">Latest runs</InputLabel>
              <Select
                labelId="demo-simple-select-label"
                id="demo-simple-select"
                value={rootRun.id}
                label="Latest runs"
                //onChange={handleChange}
              >
                {latestRuns.map((run) => (
                  <MenuItem value={run.id}>
                    <Typography
                      component="span"
                      sx={{ display: "flex", alignItems: "center" }}
                    >
                      <RunStateChip state={run.future_state} />
                      <Box ml={3}>
                        <Typography
                          sx={{ fontSize: "small", color: "GrayText" }}
                        >
                          <code>{run.id.substring(0, 6)}</code>
                        </Typography>
                      </Box>
                      <Box ml={3}>
                        {
                          <ReactTimeAgo
                            date={new Date(run.created_at)}
                            locale="en-US"
                          />
                        }
                      </Box>
                    </Typography>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>
        {rootRun && <ThreePanels rootRun={rootRun} />}
      </Box>
    );
  }
  return <></>;
}

export default function PipelineView() {
  const [error, setError] = useState<Error | undefined>(undefined);
  const [selectedRun, setSelectedRun] = useState<Run | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);

  let params = useParams();

  let { calculatorPath } = params;

  const triggerRefresh = useCallback(
    (refreshCallback: () => void) => {
      pipelineSocket.removeAllListeners();
      pipelineSocket.on("update", (args: { calculator_path: string }) => {
        if (args.calculator_path === calculatorPath) {
          refreshCallback();
        }
      });
    },
    [calculatorPath]
  );

  const onRowClick = useCallback(
    (run: Run) => {
      if (selectedRun?.id !== run.id) {
        setSelectedRun(run);
      }
    },
    [selectedRun]
  );

  const onRunsLoaded = useCallback(
    (runs: Run[]) => {
      if (runs.length > 0) {
        if (selectedRun === undefined) {
          setSelectedRun(runs[0]);
          setIsLoaded(true);
        }
      } else {
        setError(Error("No such pipeline."));
      }
    },
    [selectedRun]
  );

  if (calculatorPath === undefined) {
    setError(Error("undefined function path"));
  } else if (error === undefined) {
    let runFilters: RunFilterType = {
      AND: [
        { parent_id: { eq: null } },
        { calculator_path: { eq: calculatorPath } },
      ],
    };
    return (
      <>
        {selectedRun && (
          <Box marginTop={2} marginBottom={12}>
            <Box marginBottom={3}>
              <Typography variant="h3" component="h2">
                {selectedRun.name}
              </Typography>
              <CalculatorPath calculatorPath={selectedRun.calculator_path} />
            </Box>
            <Box>
              <Tags tags={selectedRun.tags || []} />
            </Box>
            <Grid container>
              <Grid item xs={6}>
                <Box marginY={3}>
                  <Docstring docstring={selectedRun.description} />
                </Box>
              </Grid>
              <Grid item xs={6}></Grid>
            </Grid>
          </Box>
        )}
        <Typography variant="h6" component="h3">
          Latest runs
        </Typography>
        <RunList
          columns={["ID", "Name", "Tags", "Time", "Status"]}
          filters={runFilters}
          pageSize={5}
          size="small"
          onRunsLoaded={(runs: Run[]) => onRunsLoaded(runs)}
          triggerRefresh={triggerRefresh}
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
        {selectedRun && (
          <Box paddingY={10}>
            <DagTab rootRun={selectedRun} />
          </Box>
        )}
      </>
    );
  }
  return <Loading error={error} isLoaded={isLoaded} />;
}
