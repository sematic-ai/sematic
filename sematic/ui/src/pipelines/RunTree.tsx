import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import { Fragment, useCallback } from "react";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";
import { RunTreeNode } from "../interfaces/graph";
import { Run } from "../Models";
import RunStateChip from "../components/RunStateChip";
import { ExtractContextType } from "../components/utils/typings";
import PipelinePanelsContext from "./PipelinePanelsContext";

export default function RunTree(props: {
  runTreeNodes: Array<RunTreeNode>;
}) {
  let { runTreeNodes } = props;

  const { selectedRun, setSelectedPanelItem, setSelectedRunId } 
  = usePipelinePanelsContext() as ExtractContextType<typeof PipelinePanelsContext> & {
    selectedRun: Run
  };

  const onSelectRun = useCallback((runId: string) => {
    setSelectedRunId(runId);
    setSelectedPanelItem('run');
  }, [setSelectedPanelItem, setSelectedRunId]);

  if (runTreeNodes.length === 0) {
    return <></>;
  }
  return (
    <List
      sx={{
        pt: 0,
      }}
    >
      {runTreeNodes.map(({run, children}) => (
        <Fragment key={run!.id}>
          <ListItemButton
            onClick={() => onSelectRun(run!.id)}
            key={run!.id}
            sx={{ height: "30px" }}
            selected={selectedRun.id === run!.id}
          >
            <ListItemIcon sx={{ minWidth: "20px" }}>
              <RunStateChip state={run!.future_state} />
            </ListItemIcon>
            <ListItemText primary={run!.name} />
          </ListItemButton>
          {children.length > 0 && (
            <Box marginLeft={3}>
              <RunTree runTreeNodes={children}/>
            </Box>
          )}
        </Fragment>
      ))}
    </List>
  );
}
