import { ChevronLeft } from "@mui/icons-material";
import {
  Box,
  FormControl,
  InputLabel,
  Link,
  MenuItem,
  Select,
  SelectChangeEvent,
  Typography,
  useTheme,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import TimeAgo from "javascript-time-ago";
import en from "javascript-time-ago/locale/en.json";

import ReactTimeAgo from "react-time-ago";
import { Run } from "../Models";
import { RunListPayload } from "../Payloads";
import { fetchJSON, pipelineSocket } from "../utils";
import CalculatorPath from "./CalculatorPath";
import Loading from "./Loading";
import { RunFilterType } from "./RunList";
import RunStateChip from "./RunStateChip";

TimeAgo.addDefaultLocale(en);

export default function PipelineBar(props: {
  calculatorPath: string;
  onRootRunChange: (run: Run) => void;
}) {
  const { onRootRunChange, calculatorPath } = props;
  const [rootRun, setRootRun] = useState<Run | undefined>(undefined);
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [latestRuns, setLatestRuns] = useState<Run[]>([]);
  const [hasNewRun, setHasNewRun] = useState(false);

  const theme = useTheme();

  const fetchLatestRuns = useCallback(
    (calcPath: string, onResults: (runs: Run[]) => void) => {
      const runFilters: RunFilterType = {
        AND: [
          { parent_id: { eq: null } },
          { calculator_path: { eq: calcPath } },
        ],
      };

      fetchJSON(
        "/api/v1/runs?limit=5&filters=" + JSON.stringify(runFilters),
        (response: RunListPayload) => {
          onResults(response.content);
        },
        setError,
        setIsLoaded
      );
    },
    []
  );

  useEffect(() => {
    if (calculatorPath === undefined) return;
    fetchLatestRuns(calculatorPath, (runs) => {
      setLatestRuns(runs);
      setRootRun(runs[0]);
      onRootRunChange(runs[0]);
    });
  }, [calculatorPath]);

  useEffect(() => {
    pipelineSocket.removeAllListeners();
    pipelineSocket.on("update", (args: { calculator_path: string }) => {
      if (args.calculator_path === calculatorPath) {
        fetchLatestRuns(calculatorPath, (runs) => {
          setLatestRuns(runs);
          setHasNewRun(true);
        });
      }
    });
  }, []);

  const onSelect = useCallback(
    (event: SelectChangeEvent) => {
      const newRootRunId = event.target.value;
      latestRuns.forEach((run) => {
        if (run.id === newRootRunId) {
          setRootRun(run);
          onRootRunChange(run);
          setHasNewRun(false);
        }
      });
    },
    [latestRuns]
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
          gridTemplateColumns: "70px 1fr auto",
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
        <Box
          sx={{
            gridColumn: 3,
            borderLeft: 1,
            borderColor: theme.palette.grey[200],
            paddingX: 10,
            paddingTop: 1,
            display: "flex",
          }}
        >
          <Box sx={{ width: "100px" }}>
            {hasNewRun && (
              <Typography color={theme.palette.warning.light}>
                New run available.
              </Typography>
            )}
          </Box>
          <FormControl fullWidth size="small">
            <InputLabel id="demo-simple-select-label">Latest runs</InputLabel>
            <Select
              labelId="demo-simple-select-label"
              id="demo-simple-select"
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
    );
  }

  return <></>;
}
