import { Box } from "@mui/material";
import { FlowWithProvider } from "./ReactFlowDag";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";
import { useGraphContext } from "../hooks/graphHooks";
import { RunDetailsPanel } from "../pipelines/RunDetailsPanel";

export default function RunPanel() {
  const { graph } = useGraphContext();
  const { selectedPanelItem } = usePipelinePanelsContext();

  if (!graph) {
    return <></>;
  }
  return (
    <Box sx={{ gridColumn: 2, gridRow: 2, overflowY: "scroll" }}>
      {selectedPanelItem === "graph" && (
        <>
          <FlowWithProvider
            // Nasty hack to make sure the DAG is remounted each time to trigger a ReactFlow onInit
            // to trigger a new layout
            key={Math.random().toString()}
          />
        </>
      )}
      {selectedPanelItem === "run" && (
          <RunDetailsPanel />
      )}
    </Box>
  );
}
