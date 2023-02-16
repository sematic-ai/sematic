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
import CalculatorPath from "../components/CalculatorPath";
import GitInfoBox from "../components/GitInfo";
import Loading from "../components/Loading";
import RunStateChip from "../components/RunStateChip";
import TimeAgo from "../components/TimeAgo";
import { ActionMenu, ActionMenuItem } from "../components/ActionMenu";
import { SnackBarContext } from "../components/SnackBarProvider";
import { useFetchRuns, useRunNavigation, usePipelineRunContext } from "../hooks/pipelineHooks";
import { ExtractContextType } from "../components/utils/typings";
import PipelineRunViewContext from "./PipelineRunViewContext";

function PipelineActionMenu(props: {
  onCancel: () => void;
}) {
  const { onCancel } = props;
  const { user } = useContext(UserContext);
  const theme = useTheme();
  const { setSnackMessage } = useContext(SnackBarContext);

  const { rootRun, resolution } = usePipelineRunContext() as {rootRun: Run, resolution: Resolution};

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
        if (error) setSnackMessage({ message: "Failed to cancel pipeline run." });
      },
    });
  }, [rootRun.id, setSnackMessage, user?.api_key]);

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
    [rootRun.id, setSnackMessage, user?.api_key]
  );

  const onCopyShareClick = useCallback(() => {
    navigator.clipboard.writeText(window.location.href);
    setSnackMessage({ message: "Resolution link copied" });
  }, [setSnackMessage]);

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

export default function PipelineBar() {
  const { setSnackMessage } = useContext(SnackBarContext);

  const { rootRun, resolution } 
  = usePipelineRunContext() as ExtractContextType<typeof PipelineRunViewContext> & {
    rootRun: Run, resolution: Resolution
  };;

  const pipelinePath = rootRun.calculator_path;

  const theme = useTheme();

  const runFilters = useMemo(() => ({
    AND: [
      { parent_id: { eq: null } },
      { calculator_path: { eq: pipelinePath } },
    ],
  }), [pipelinePath]);

  const otherQueryParams = useMemo(() => ({
      limit: '10'
  }), []);

  const {isLoaded, error, runs: latestRuns, reloadRuns } = useFetchRuns(runFilters, otherQueryParams);

  const navigate = useRunNavigation();

  const changeRootId = useCallback((runId: string) => {
    navigate(runId);
  }, [navigate]);

  useEffect(() => {
    pipelineSocket.removeAllListeners("update");
    pipelineSocket.on("update", async (args: { calculator_path: string }) => {
      if (args.calculator_path === pipelinePath) {
        const runs = await reloadRuns();
        if (runs[0].id !== latestRuns[0].id) {
          setSnackMessage({
            message: "New run available.",
            actionName: "view",
            autoHide: false,
            closable: true,
            onClick: () => changeRootId(runs[0].id),
          });
        }
      }
    });
  }, [latestRuns, pipelinePath, changeRootId, reloadRuns, setSnackMessage]);

  const onSelect = useCallback(
    ({ target: { value } }: SelectChangeEvent) => {
      changeRootId(value);
    },
    [changeRootId]
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
            <PipelineActionMenu onCancel={onCancel} />
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
              {latestRuns.map((run) => {
                const {id, created_at} = run;
                return <MenuItem value={id} key={id}>
                  <Typography
                    component="span"
                    sx={{ display: "flex", alignItems: "center" }}
                  >
                    <RunStateChip run={run} />
                    <Box>
                      <Typography sx={{ fontSize: "small", color: "GrayText" }}>
                        <code>{id.substring(0, 6)}</code>
                      </Typography>
                    </Box>
                    <Box ml={3}>
                      <TimeAgo date={created_at} />
                    </Box>
                  </Typography>
                </MenuItem>
              })}
            </Select>
          </FormControl>
        </Box>
      </Box>
    );
  }

  return <></>;
}
