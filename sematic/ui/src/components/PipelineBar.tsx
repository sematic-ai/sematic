import { ChevronLeft } from "@mui/icons-material";
import CloseIcon from "@mui/icons-material/Close";
import {
  Box,
  Button,
  FormControl,
  IconButton,
  InputLabel,
  Link,
  MenuItem,
  Select,
  SelectChangeEvent,
  Snackbar,
  Typography,
  useTheme,
} from "@mui/material";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { UserContext } from "..";
import { Resolution, Run } from "../Models";
import { ResolutionPayload, RunListPayload } from "../Payloads";
import { fetchJSON, pipelineSocket } from "../utils";
import CalculatorPath from "./CalculatorPath";
import GitInfoBox from "./GitInfo";
import Loading from "./Loading";
import { RunFilterType } from "./RunList";
import RunStateChip from "./RunStateChip";
import TimeAgo from "./TimeAgo";

export default function PipelineBar(props: {
  calculatorPath: string;
  onRootRunChange: (run: Run) => void;
  setInitialRootRun: boolean;
  initialRootRun?: Run;
  initialResolution?: Resolution;
}) {
  const {
    onRootRunChange,
    calculatorPath,
    setInitialRootRun,
    initialRootRun,
    initialResolution,
  } = props;
  const [rootRun, setRootRun] = useState<Run | undefined>(initialRootRun);
  const [resolution, setResolution] = useState<Resolution | undefined>(
    initialResolution
  );
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isCanceling, setIsCanceling] = useState(false);
  const [cancelSnackMessage, setCancelSnackMessage] = useState<
    string | undefined
  >(undefined);
  const [latestRuns, setLatestRuns] = useState<Run[]>([]);
  const [hasNewRun, setHasNewRun] = useState(false);
  const { user } = useContext(UserContext);

  const theme = useTheme();

  useMemo(() => {
    if (initialRootRun) setRootRun(initialRootRun);
  }, [initialRootRun]);

  useMemo(() => {
    if (initialResolution) setResolution(initialResolution);
  }, [initialResolution]);

  const fetchLatestRuns = useCallback(
    (calcPath: string, onResults: (runs: Run[]) => void) => {
      const runFilters: RunFilterType = {
        AND: [
          { parent_id: { eq: null } },
          { calculator_path: { eq: calcPath } },
        ],
      };

      fetchJSON({
        url: "/api/v1/runs?limit=10&filters=" + JSON.stringify(runFilters),
        apiKey: user?.api_key,
        callback: (response: RunListPayload) => {
          onResults(response.content);
        },
        setError: setError,
        setIsLoaded: setIsLoaded,
      });
    },
    []
  );

  const fetchResolution = useCallback(
    (run: Run | undefined) => {
      if (run) {
        fetchJSON({
          url: "/api/v1/resolutions/" + run.id,
          apiKey: user?.api_key,
          callback: (response: ResolutionPayload) => {
            setResolution(response.content);
          },
          setError: (_: Error | undefined) => {
            // this means the pipeline resolution failed
            setResolution(undefined);
          },
        });
      }
    },
    [setResolution]
  );

  useEffect(() => {
    if (calculatorPath === undefined) return;
    fetchLatestRuns(calculatorPath, (runs) => {
      setLatestRuns(runs);
      if (setInitialRootRun) {
        setRootRun(runs[0]);
        onRootRunChange(runs[0]);
        fetchResolution(runs[0]);
      }
    });
  }, [
    calculatorPath,
    fetchLatestRuns,
    onRootRunChange,
    setInitialRootRun,
    setResolution,
    fetchResolution,
  ]);

  useEffect(() => {
    pipelineSocket.removeAllListeners();
    pipelineSocket.on("update", (args: { calculator_path: string }) => {
      if (args.calculator_path === calculatorPath) {
        fetchLatestRuns(calculatorPath, (runs) => {
          setLatestRuns(runs);
          if (runs[0].id !== latestRuns[0].id) {
            setHasNewRun(true);
          }
        });
      }
    });
    pipelineSocket.on("cancel", (args: { calculator_path: string }) => {
      if (args.calculator_path === calculatorPath) {
        fetchLatestRuns(calculatorPath, (runs) => {
          setLatestRuns(runs);
          if (!rootRun) return;
          // Re-rendering
          runs.forEach((run) => {
            if (run.id === rootRun.id) {
              setRootRun(run);
            }
          });
        });
        setCancelSnackMessage("Pipeline run was canceled.");
      }
    });
  }, [latestRuns, calculatorPath, fetchLatestRuns, rootRun]);

  const onSelect = useCallback(
    (event: SelectChangeEvent) => {
      const newRootRunId = event.target.value;
      latestRuns.forEach((run) => {
        if (run.id === newRootRunId) {
          setRootRun(run);
          onRootRunChange(run);
          fetchResolution(run);
          setHasNewRun(false);
        }
      });
    },
    [latestRuns, onRootRunChange, setResolution, fetchResolution]
  );

  const onCancel = useCallback(() => {
    if (!rootRun) return;
    if (!confirm("Are you sure you want to cancel this pipeline?")) return;
    setIsCanceling(true);
    fetchJSON({
      url: "/api/v1/resolutions/" + rootRun.id + "/cancel",
      method: "PUT",
      apiKey: user?.api_key,
      callback: (payload) => {
        setIsCanceling(false);
      },
      setError: (error) => {
        setIsCanceling(false);
        setCancelSnackMessage("Failed to cancel pipeline run.");
      },
    });
  }, [rootRun, setIsCanceling]);

  const selectLatestRun = useCallback(() => {
    setRootRun(latestRuns[0]);
    onRootRunChange(latestRuns[0]);
    fetchResolution(latestRuns[0]);
  }, [latestRuns, setRootRun, onRootRunChange, fetchResolution]);

  const snackBarAction = (
    <>
      <Button
        color="secondary"
        size="small"
        onClick={() => {
          selectLatestRun();
          setHasNewRun(false);
        }}
      >
        View
      </Button>
      <IconButton
        size="small"
        aria-label="close"
        color="inherit"
        onClick={() => setHasNewRun(false)}
      >
        <CloseIcon fontSize="small" />
      </IconButton>
    </>
  );

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
          gridRow: 1,
          gridColumn: "1 / 4",
          borderBottom: 1,
          borderColor: theme.palette.grey[200],
          paddingY: 3,
          display: "grid",
          gridTemplateColumns: "70px 1fr auto auto auto",
        }}
      >
        <Snackbar
          open={hasNewRun}
          anchorOrigin={{ vertical: "top", horizontal: "right" }}
          message="New run available"
          sx={{ marginTop: "50px" }}
          action={snackBarAction}
        />
        <Snackbar
          open={cancelSnackMessage !== undefined}
          anchorOrigin={{ vertical: "top", horizontal: "right" }}
          message="Run was canceled"
          sx={{ marginTop: "50px" }}
          autoHideDuration={5000}
          onClose={() => {
            setCancelSnackMessage(undefined);
          }}
        />
        <Box
          sx={{
            gridColumn: 1,
            textAlign: "center",
            paddingTop: 2,
            borderRight: 1,
            borderColor: theme.palette.grey[200],
          }}
        >
          <Link href="/pipelines">
            <ChevronLeft fontSize="large" />
          </Link>
        </Box>
        <Box sx={{ gridColumn: 2, pl: 7 }}>
          <Typography variant="h4">{rootRun.name}</Typography>
          <CalculatorPath calculatorPath={rootRun.calculator_path} />
        </Box>
        <Box sx={{ gridColumn: 3, pt: 2, px: 7 }}>
          {!["FAILED", "NESTED_FAIL", "RESOLVED", "CANCELED"].includes(
            rootRun.future_state
          ) && (
            <Button
              color="error"
              size="small"
              disabled={isCanceling}
              onClick={onCancel}
            >
              {isCanceling ? "Canceling..." : "Cancel"}
            </Button>
          )}
        </Box>
        <Box
          sx={{
            gridColumn: 4,
            textAlign: "left",
            paddingX: 10,
            borderLeft: 1,
            borderColor: theme.palette.grey[200],
          }}
        >
          <GitInfoBox resolution={resolution} />
        </Box>

        <Box
          sx={{
            gridColumn: 5,
            borderLeft: 1,
            borderColor: theme.palette.grey[200],
            paddingX: 10,
            paddingTop: 1,
            display: "flex",
          }}
        >
          <FormControl fullWidth size="small">
            <InputLabel id="root-run-select-label">Latest runs</InputLabel>
            <Select
              labelId="root-run-select-label"
              id="root-run-select"
              value={rootRun.id}
              label="Latest runs"
              onChange={onSelect}
            >
              {latestRuns.map((run) => (
                <MenuItem value={run.id} key={run.id}>
                  <Typography
                    component="span"
                    sx={{ display: "flex", alignItems: "center" }}
                  >
                    <RunStateChip state={run.future_state} />
                    <Box>
                      <Typography sx={{ fontSize: "small", color: "GrayText" }}>
                        <code>{run.id.substring(0, 6)}</code>
                      </Typography>
                    </Box>
                    <Box ml={3}>
                      <TimeAgo date={run.created_at} />
                    </Box>
                  </Typography>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Box>
    );
  }

  return <></>;
}
