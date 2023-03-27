import { Box, styled } from "@mui/material";
import { FlowWithProvider } from "src/pipelines/graph/ReactFlowDag";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { useGraphContext } from "src/hooks/graphHooks";
import { RunDetailsPanel } from "src/pipelines/RunDetailsPanel";
import BasicMetricsPanel from "src/pipelines/BasicMetricsPanel";
import RunPanelContext from "src/pipelines//RunDetailsContext";
import { useMemo, useRef, useState } from "react";
import { ExtractContextType } from "src/components/utils/typings";
import Loading from "src/components/Loading";

const FloatingFooter = styled('div')`
  width: 100%;
  position: sticky;
  bottom: 0;
  height: 0;
`;

const FloatingFooterAnchor = styled('div')`
  width: 100%;
  position: absolute;
  bottom: 0;
`;

const LoadingOverlay = styled(Box)`
  width: 100%;
  position: absolute;
  z-index: 251;
  height: 100%;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
`

export default function RunPanel() {
  const { graph } = useGraphContext();
  const { selectedPanelItem } = usePipelinePanelsContext();

  const scrollerId = 'run-panel-scrolling-area';
  const scrollContainerRef = useRef<HTMLElement>();

  const [footerRenderProp, setFooterRenderPropState] = useState<(() => JSX.Element) | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const runDetailsContextValue = useMemo<
        ExtractContextType<typeof RunPanelContext>
    >(() => ({
      setFooterRenderProp: (renderProp) => {
        setFooterRenderPropState(() => renderProp);
      },
      scrollerId,
      scrollContainerRef,
      setIsLoading
    }), [setFooterRenderPropState]);

  if (!graph) {
    return <></>;
  }
  return (
    <Box sx={{ gridColumn: 2, gridRow: 2, height: '100%', overflow: 'hidden', 
    position: 'relative'}}>
        {isLoading && <LoadingOverlay>
          <Loading isLoaded={false} />
        </LoadingOverlay>}
      <Box id={scrollerId} ref={scrollContainerRef}
      sx={{ overflowY: "auto", position: 'relative', height: '100%' }}>
        <RunPanelContext.Provider value={runDetailsContextValue}>
          {
            selectedPanelItem === "metrics" && <BasicMetricsPanel />
          }
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
        </RunPanelContext.Provider>

        <FloatingFooter >
          <FloatingFooterAnchor>
          {!!footerRenderProp && footerRenderProp()}
          </FloatingFooterAnchor>
        </FloatingFooter>
      </Box>
    </Box>
  );
}
