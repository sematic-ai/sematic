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
import { useCallback, useContext, useEffect, useMemo } from "react";
import { UserContext } from "..";
import { Resolution, Run } from "../Models";
import { fetchJSON, pipelineSocket } from "../utils";
import CalculatorPath from "./CalculatorPath";
import GitInfoBox from "./GitInfo";
import Loading from "./Loading";
import RunStateChip from "./RunStateChip";
import TimeAgo from "./TimeAgo";
import { ActionMenu, ActionMenuItem } from "./ActionMenu";
import { SnackBarContext } from "./SnackBarProvider";
import { useFetchRuns } from "../hooks/pipelineHooks";

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
  }, [rootRun.id, setSnackMessage]);

  const onRerunClick = useCallback(
    (rerunFrom?: string) => {
      fetchJSON({
        url: "/api/v1/resolutions/" + rootRun.id + "/rerun",
        method: "POST",
        body: { rerun_from: rerunFrom },
        apiKey: user?.api_key,
        callback: (payload) => {},
        setError: (error) => {
          if (!error) return;
          setSnackMessage({ message: "Failed to trigger rerun." });
        },
      });
    },
    [rootRun.id]
  );

  const onCopyShareClick = useCallback(() => {
    navigator.clipboard.writeText(window.location.href);
    setSnackMessage({ message: "Pipeline link copied" });
  }, []);

  const cancelEnabled = useMemo(
    () =>
      !["FAILED", "NESTED_FAILED", "RESOLVED", "CANCELED"].includes(
        rootRun.future_state
      ),
    [rootRun.future_state]
  );

  const rerunEnable = useMemo(
    () => !!resolution.container_image_uri,
    [resolution.container_image_uri]
  );

  return (
    <>
      <ActionMenu title="Actions">
        <ActionMenuItem
          title="Rerun"
          enabled={rerunEnable}
          onClick={() => onRerunClick(rootRun.id)}
          beta
        >
          <Typography>Rerun pipeline from scratch.</Typography>
          <Typography>Only available for remote resolutions.</Typography>
        </ActionMenuItem>
        <ActionMenuItem title="Retry from failure" enabled={false} soon>
          <Typography>Rerun pipeline from where it failed.</Typography>
          <Typography>Coming soon.</Typography>
        </ActionMenuItem>
        <ActionMenuItem title="Copy share link" onClick={onCopyShareClick}>
          <Typography>Copy link to this exact resolution.</Typography>
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
  onRootIdChange: (rootId: string) => void;
  rootRun?: Run;
  resolution?: Resolution;
}) {
  const { calculatorPath, onRootIdChange, rootRun, resolution } =
    props;
  const { setSnackMessage } = useContext(SnackBarContext);

  const theme = useTheme();

  const runFilters = useMemo(() => ({
    AND: [
      { parent_id: { eq: null } },
      { calculator_path: { eq: calculatorPath } },
    ],
  }), [calculatorPath]);

  const otherQueryParams = useMemo(() => ({
      limit: '10'
  }), []);

  const {isLoaded, error, runs: latestRuns, reloadRuns } = useFetchRuns(runFilters, otherQueryParams);

  useEffect(() => {
    pipelineSocket.removeAllListeners("update");
    pipelineSocket.on("update", async (args: { calculator_path: string }) => {
      if (args.calculator_path === calculatorPath) {
        const runs = await reloadRuns();
        if (runs[0].id !== latestRuns[0].id) {
          setSnackMessage({
            message: "New run available.",
            actionName: "view",
            autoHide: false,
            closable: true,
            onClick: () => onRootIdChange(runs[0].id),
          });
        }
      }
    });
  }, [latestRuns, calculatorPath, onRootIdChange, reloadRuns, setSnackMessage]);

  const onSelect = useCallback(
    (event: SelectChangeEvent) => {
      onRootIdChange(event.target.value);
    },
    [onRootIdChange]
  );

  const onCancel = reloadRuns;

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
