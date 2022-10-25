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
import { ActionMenu, ActionMenuItem } from "./ActionMenu";
import { SnackBarContext } from "./SnackBarProvider";

function PipelineActionMenu(props: {
  rootRun: Run;
  resolution: Resolution;
  onCancel: () => void;
}) {
  const { rootRun, resolution, onCancel } = props;
  const { user } = useContext(UserContext);
  const theme = useTheme();
  const { setSnackMessage } = useContext(SnackBarContext);

  useEffect(() => {
    pipelineSocket.removeAllListeners("cancel");
    pipelineSocket.on("cancel", (args: { calculator_path: string }) => {
      if (args.calculator_path === rootRun.calculator_path) {
        setSnackMessage({ message: "Pipeline run was canceled." });
        onCancel();
      }
    });
  });

  const onCancelClick = useCallback(() => {
    if (!window.confirm("Are you sure you want to cancel this pipeline?"))
      return;
    fetchJSON({
      url: "/api/v1/resolutions/" + rootRun.id + "/cancel",
      method: "PUT",
      apiKey: user?.api_key,
      callback: (payload) => {},
      setError: (error) => {
        setSnackMessage({ message: "Failed to cancel pipeline run." });
      },
    });
  }, [rootRun, setSnackMessage]);

  const onRerunClick = useCallback(
    (rerunFrom?: string) => {
      fetchJSON({
        url: "/api/v1/resolutions/" + rootRun.id + "/rerun",
        method: "POST",
        body: { rerun_from: rerunFrom },
        apiKey: user?.api_key,
        callback: (payload) => {},
        setError: (error) => {
          setSnackMessage({ message: "Failed to trigger rerun." });
        },
      });
    },
    [rootRun]
  );

  const onCopyShareClick = useCallback(() => {
    navigator.clipboard.writeText(window.location.href);
    setSnackMessage({ message: "Pipeline link copied." });
  }, []);

  const cancelEnabled = ![
    "FAILED",
    "NESTED_FAIL",
    "RESOLVED",
    "CANCELED",
  ].includes(rootRun.future_state);

  const rerunEnable = !!resolution.container_image_uri;

  return (
    <>
      <ActionMenu title="Actions">
        <ActionMenuItem
          title="Rerun"
          enabled={rerunEnable}
          onClick={() => onRerunClick(rootRun.id)}
        >
          <Typography>Rerun pipeline from scratch.</Typography>
          <Typography>Only available for remote resolutions.</Typography>
        </ActionMenuItem>
        <ActionMenuItem title="Retry from failure" enabled={false}>
          <Typography>Rerun pipeline from where it failed.</Typography>
          <Typography>Coming soon.</Typography>
        </ActionMenuItem>
        <ActionMenuItem title="Copy share link" onClick={onCopyShareClick}>
          <Typography>Copy link to this exact pipeline execution.</Typography>
        </ActionMenuItem>
        <ActionMenuItem
          title="Cancel Execution"
          titleColor={theme.palette.error.dark}
          enabled={cancelEnabled}
          onClick={onCancelClick}
        >
          <Typography>Cancel all ongoing and upcoming runs.</Typography>
        </ActionMenuItem>
      </ActionMenu>
    </>
  );
}

export default function PipelineBar(props: {
  calculatorPath: string;
  onRootRunChange: (run: Run, resolution: Resolution) => void;
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
  const [latestRuns, setLatestRuns] = useState<Run[]>([]);
  const { user } = useContext(UserContext);
  const { setSnackMessage } = useContext(SnackBarContext);

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
            onRootRunChange(run, response.content);
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

  const updateRootRun = useCallback(
    (runs: Run[]) => {
      if (!rootRun) return;
      for (let i = 0; i < runs.length; i++) {
        if (runs[i].id === rootRun.id) {
          setRootRun(runs[i]);
          break;
        }
      }
    },
    [rootRun, setRootRun]
  );

  useEffect(() => {
    pipelineSocket.removeAllListeners("update");
    pipelineSocket.on("update", (args: { calculator_path: string }) => {
      if (args.calculator_path === calculatorPath) {
        fetchLatestRuns(calculatorPath, (runs) => {
          setLatestRuns(runs);
          if (runs[0].id !== latestRuns[0].id) {
            setSnackMessage({
              message: "New run available.",
              actionName: "view",
              autoHide: false,
              closable: true,
              onClick: () => selectLatestRun(),
            });
          }
          updateRootRun(runs);
        });
      }
    });
  }, [latestRuns, calculatorPath, fetchLatestRuns, updateRootRun]);

  const onSelect = useCallback(
    (event: SelectChangeEvent) => {
      const newRootRunId = event.target.value;
      latestRuns.forEach((run) => {
        if (run.id === newRootRunId) {
          setRootRun(run);
          fetchResolution(run);
          setSnackMessage(undefined);
        }
      });
    },
    [latestRuns, onRootRunChange, setResolution, fetchResolution]
  );

  const onCancel = useCallback(() => {
    fetchLatestRuns(calculatorPath, (runs) => {
      setLatestRuns(runs);
      updateRootRun(runs);
    });
  }, [setLatestRuns, fetchLatestRuns, updateRootRun]);

  const selectLatestRun = useCallback(() => {
    setRootRun(latestRuns[0]);
    fetchResolution(latestRuns[0]);
  }, [latestRuns, setRootRun, onRootRunChange, fetchResolution]);

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
          {resolution && (
            <PipelineActionMenu
              rootRun={rootRun}
              onCancel={onCancel}
              resolution={resolution}
            />
          )}
        </Box>
        <Box
          sx={{
            gridColumn: 4,
            textAlign: "left",
            paddingX: 10,
            borderLeft: 1,
            borderColor: theme.palette.grey[200],
            pt: 1,
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
