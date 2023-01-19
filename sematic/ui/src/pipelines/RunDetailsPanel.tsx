import { Box, Typography } from "@mui/material";
import { useCallback, useContext, useMemo } from "react";
import { UserContext } from "..";
import { ActionMenu, ActionMenuItem } from "../components/ActionMenu";
import CalculatorPath from "../components/CalculatorPath";
import Docstring from "../components/Docstring";
import RunStateChip from "../components/RunStateChip";
import { RunTime } from "../components/RunTime";
import { SnackBarContext } from "../components/SnackBarProvider";
import Tags from "../components/Tags";
import { ExtractContextType } from "../components/utils/typings";
import { useGraphContext } from "../hooks/graphHooks";
import { usePipelinePanelsContext, usePipelineRunContext } from "../hooks/pipelineHooks";
import { Artifact, Edge, Resolution, Run } from "../Models";
import { fetchJSON } from "../utils";
import PipelinePanelsContext from "./PipelinePanelsContext";
import PipelineRunViewContext from "./PipelineRunViewContext";
import RunTabs, { IOArtifacts } from "./RunTabs";

export function RunDetailsPanel() {
    const { selectedRun } = usePipelinePanelsContext() as ExtractContextType<typeof PipelinePanelsContext> & {
      selectedRun: Run
    };
    const { graph } = useGraphContext();

    const { edges, artifactsById } = graph!;

    const selectedRunArtifacts = useMemo(() => {
        if (edges === undefined) return;
        if (artifactsById === undefined) return;
    
        let ioArtifacts: IOArtifacts = { input: new Map(), output: new Map() };
    
        const setArtifact = (
          map: Map<string, Artifact | undefined>,
          artifact_id: string | null,
          name: string | null
        ) => {
          let artifact: Artifact | undefined = undefined;
          if (artifact_id !== null) {
            artifact = artifactsById.get(artifact_id);
            if (artifact === undefined) {
              console.error(Error("Artifact missing"));
              return;
            }
          }
          map.set(
            name ? name : "null",
            artifact_id ? artifactsById.get(artifact_id) : undefined
          );
        };
    
        edges.forEach((edge) => {
          if (edge.destination_run_id === selectedRun?.id) {
            setArtifact(ioArtifacts.input, edge.artifact_id, edge.destination_name);
          }
          if (edge.source_run_id === selectedRun?.id) {
            setArtifact(ioArtifacts.output, edge.artifact_id, edge.source_name);
          }
        });
        return ioArtifacts;
      }, [edges, artifactsById, selectedRun]);

    const selectedRunInputEdges = useMemo(
        () => edges.filter((edge) => edge.destination_run_id === selectedRun.id),
        [edges, selectedRun.id]
    );

    return (<Box sx={{ p: 5, height: '100%', 'boxSizing': 'border-box', display: 'flex', 
          flexFlow: 'column'}}>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr auto auto", flexShrink: 1 }}>
            <Box sx={{ paddingBottom: 3, gridColumn: 1 }}>
              <Box marginBottom={3}>
                <Typography variant="h6">{selectedRun.name}</Typography>
                <Typography fontSize="small" color="GrayText" component="span">
                  <code style={{ fontSize: 12 }}>
                  ID: {selectedRun.id}
                  {
                    selectedRun.original_run_id &&
                    /*
                      TODO #278: replace full id with a 6-character trimmed
                      link using "./Notes/RunId"
                    */
                    <> (cloned from {selectedRun.original_run_id})</>
                  }
                  </code>
                </Typography>
                <br />
                <CalculatorPath calculatorPath={selectedRun.calculator_path} />
              </Box>
              <Tags tags={selectedRun.tags || []} />
            </Box>
            <Box sx={{ gridColumn: 2, pt: 3, pr: 10 }}>
              <RunActionMenu
                run={selectedRun}
                inputEdges={selectedRunInputEdges}
              />
            </Box>
            <Box sx={{ gridColumn: 3, pt: 3, pr: 5 }}>
              <RunStateChip state={selectedRun.future_state} variant="full" />
              <RunTime run={selectedRun} prefix="in " />
            </Box>
          </Box>
          <Box sx={{ mb: 10, mt: 5, flexShrink: 1}}>
            <Docstring docstring={selectedRun.description} />
          </Box>
          <RunTabs artifacts={selectedRunArtifacts!} />
        </Box>);
}

function RunActionMenu(props: {
    run: Run;
    inputEdges: Edge[];
  }) {
    const { run, inputEdges } = props;
    const { resolution } 
      = usePipelineRunContext() as ExtractContextType<typeof PipelineRunViewContext> & {
      resolution: Resolution
    };
    const { user } = useContext(UserContext);
  
    const { setSnackMessage } = useContext(SnackBarContext);
  
    const onRerunClick = useCallback(() => {
      fetchJSON({
        url: "/api/v1/resolutions/" + run.root_id + "/rerun",
        method: "POST",
        body: { rerun_from: run.id },
        apiKey: user?.api_key,
        callback: (payload) => {},
        setError: (error) => {
          if (error) setSnackMessage({ message: "Failed to trigger a rerun" });
        },
      });
    }, [run.id, run.root_id, setSnackMessage, user?.api_key]);
  
    const rerunEnabled = useMemo(
      () =>
        inputEdges.every((edge) => !!edge.artifact_id) &&
        resolution.container_image_uri !== null,
      [inputEdges, resolution]
    );
  
    return (
      <ActionMenu title="Actions">
        <ActionMenuItem
          title="Rerun pipeline from this run"
          onClick={onRerunClick}
          enabled={rerunEnabled}
          beta
        >
          <Typography>All upstream runs will use cached outputs.</Typography>
          <Typography>Only available for cloud resolution.</Typography>
        </ActionMenuItem>
  
        {/* 
        TODO: Implement nested run deep linking
        <ActionMenuItem title="Copy share link">
            <Typography>Copy link to this exact run.</Typography>
    </ActionMenuItem>
    */}
      </ActionMenu>
    );
  }
  