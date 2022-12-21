import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import { Fragment, useCallback, useMemo } from "react";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";
import { Run } from "../Models";
import RunStateChip from "./RunStateChip";

function getTime(run: Run) {
  let date = run.started_at || run.created_at;
  return new Date(date).getTime();
}

export default function RunTree(props: {
  runsByParentId: Map<string | null, Run[]>;
  parentId: string | null;
}) {
  let { runsByParentId, parentId } = props;

  const { selectedRun, setSelectedPanelItem, setSelectedRun } = usePipelinePanelsContext();

  const onSelectRun = useCallback((run: Run) => {
    setSelectedRun(run);
    setSelectedPanelItem('run');
  }, [setSelectedPanelItem, setSelectedRun]);

  const directChildren = useMemo(() => {
    let runs = runsByParentId.get(parentId);
    if (runs !== undefined) {
      return runs.sort((a, b) => {
        if (a.started_at && !b.started_at) {
          return -1;
        }
        if (b.started_at && !a.started_at) {
          return 1;
        }
        return getTime(a) - getTime(b);
      });
    }
  }, [runsByParentId, parentId]);

  if (directChildren === undefined) {
    return <></>;
  }
  return (
    <List
      sx={{
        pt: 0,
      }}
    >
      {directChildren.map((run) => (
        <Fragment key={run.id}>
          <ListItemButton
            onClick={() => onSelectRun(run)}
            key={run.id}
            sx={{ height: "30px" }}
            selected={selectedRun.id === run.id}
          >
            <ListItemIcon sx={{ minWidth: "20px" }}>
              <RunStateChip state={run.future_state} />
            </ListItemIcon>
            <ListItemText primary={run.name} />
          </ListItemButton>
          {runsByParentId.get(run.id) !== undefined && (
            <Box marginLeft={3}>
              <RunTree
                runsByParentId={runsByParentId}
                parentId={run.id}
              />
            </Box>
          )}
        </Fragment>
      ))}
    </List>
  );
}
