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
  const { onRootRunChange, calculatorPath, setInitialRootRun, initialRootRun, initialResolution } =
    props;
  const [rootRun, setRootRun] = useState<Run | undefined>(initialRootRun);
  const [resolution, setResolution] = useState<Resolution | undefined>(initialResolution);
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
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
  }, [calculatorPath, fetchLatestRuns, onRootRunChange, setInitialRootRun, setResolution, fetchResolution]);

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
  }, [latestRuns, calculatorPath, fetchLatestRuns]);

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
        <CloseIcon fontSize="small"/>
      </IconButton>
    </>
  );

  if (error || !isLoaded) {
    return (
      <Box sx={{ p: 5 }}>
        <Loading error={error} isLoaded={isLoaded}/>
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
          gridTemplateColumns: "70px 1fr auto",
        }}
      >
        <Snackbar
          open={hasNewRun}
          anchorOrigin={{ vertical: "top", horizontal: "right" }}
          message="New run available"
          sx={{ marginTop: "50px" }}
          action={snackBarAction}
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
            <ChevronLeft fontSize="large"/>
          </Link>
        </Box>
        <Box sx={{ gridColumn: 2, pl: 7 }}>
          <Typography variant="h4">{rootRun.name}</Typography>
          <CalculatorPath calculatorPath={rootRun.calculator_path}/>
        </Box>
        <GitInfoBox resolution={resolution}/>
        <Box
          sx={{
            gridColumn: 4,
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
                    <RunStateChip state={run.future_state}/>
                    <Box>
                      <Typography sx={{ fontSize: "small", color: "GrayText" }}>
                        <code>{run.id.substring(0, 6)}</code>
                      </Typography>
                    </Box>
                    <Box ml={3}>
                      <TimeAgo date={run.created_at}/>
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
