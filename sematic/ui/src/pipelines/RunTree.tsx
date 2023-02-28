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
import { HIDDEN_RUN_NAME_LIST } from "../constants";

export default function RunTree(props: {
  runTreeNodes: Array<RunTreeNode>;
}) {
  let { runTreeNodes } = props;

  // We need to filter out runs whose functions are present in the hidden run name list.
  // The default "" value is required since indexOf does not accept an undefined value.
  runTreeNodes = runTreeNodes.filter(({run}) => HIDDEN_RUN_NAME_LIST.indexOf(run?.name ?? "")===-1);

  const { selectedRun, setSelectedPanelItem, setSelectedRunId, setSelectedArtifactName  } 
  = usePipelinePanelsContext() as ExtractContextType<typeof PipelinePanelsContext> & {
    selectedRun: Run
  };

  const onSelectRun = useCallback((runId: string) => {
    setSelectedArtifactName("");
    setSelectedRunId(runId);
    setSelectedPanelItem('run');
  }, [setSelectedArtifactName, setSelectedPanelItem, setSelectedRunId]);

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
        <Fragment key={`${run!.id}---${run!.future_state}`}>
          <ListItemButton
            onClick={() => onSelectRun(run!.id)}
            key={run!.id}
            sx={{ height: "30px" }}
            selected={selectedRun.id === run!.id}
          >
            <ListItemIcon sx={{ minWidth: "20px" }}>
              <RunStateChip run={run!} />
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
