import { Box, Typography } from "@mui/material";
import { styled } from "@mui/system";
import { useCallback, useContext, useMemo } from "react";
import { UserContext } from "..";
import { ActionMenu, ActionMenuItem } from "../components/ActionMenu";
import CalculatorPath from "../components/CalculatorPath";
import { CopyButton } from "../components/CopyButton";
import Docstring from "../components/Docstring";
import RunId from "../components/RunId";
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

const StyledText = styled('span')`
  font-size: small;
  margin-left: 1em;
  color: grey;
`;

const EnclosingBoxContainer = styled(Box)`
  box-sizing: border-box;
`

const HeaderBox = styled(Box)`
  position: sticky;
  top: 0;
  background: white;
  z-index: 200;
  padding-top: 10px;
  margin-top: -10px;
`;


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

    return (<EnclosingBoxContainer sx={{ p: 5}}>
          <HeaderBox sx={{ display: "grid", gridTemplateColumns: "1fr auto auto", flexShrink: 1 }}>
            <Box sx={{ paddingBottom: 3, gridColumn: 1 }}>
              <Box marginBottom={3}>
                <Typography variant="h6">{selectedRun.name}</Typography>
                <Typography fontSize="small" color="GrayText" component="span">
                  {'ID: '}
                  <code style={{ fontSize: 12 }}>{selectedRun.id}</code>
                </Typography>
                <CopyButton text={selectedRun.id} message="Copied run ID" color={"grey"} />
                {
                    selectedRun.original_run_id &&
                    <StyledText>
                      cloned from <RunId runId={selectedRun.original_run_id} copy={false} />
                    </StyledText>
                }
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
              <RunStateChip run={selectedRun} variant="full" />
              <RunTime run={selectedRun} prefix="in " />
            </Box>
          </HeaderBox>
          <Box sx={{ mb: 10, mt: 5, flexShrink: 1}}>
            <Docstring docstring={selectedRun.description} />
          </Box>
          <RunTabs artifacts={selectedRunArtifacts!} />
        </EnclosingBoxContainer>);
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

    const onCopyShareClick = useCallback(() => {
      navigator.clipboard.writeText(window.location.href);
      setSnackMessage({ message: "Run link copied" });
    }, [setSnackMessage]);
  
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
        >
          <Typography>All upstream runs will use cached outputs.</Typography>
          <Typography>Only available for cloud resolution.</Typography>
        </ActionMenuItem>

        <ActionMenuItem title="Copy share link" onClick={onCopyShareClick}>
            <Typography>Copy link to this exact run.</Typography>
        </ActionMenuItem>
      </ActionMenu>
    );
  }
  