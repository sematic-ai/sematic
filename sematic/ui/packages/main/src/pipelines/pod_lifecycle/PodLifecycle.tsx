import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { useRunJobHistory } from 'src/hooks/podHistoryHooks';
import { useRunPanelLoadingIndicator } from 'src/hooks/runDetailsHooks';
import PodEventHistory from 'src/pipelines/pod_lifecycle/PodEventHistory';
import styled from '@emotion/styled';
import { theme } from '@sematic/common/lib/src/theme/mira';
import CopyButton from '@sematic/common/lib/src/component/CopyButton';
import { useCallback } from 'react';

const StyledCode = styled.code`
  font-size: 12px;
  color: ${theme.palette.grey[500]};
  cursor: text;
  user-select: text;  
`;

// Separate component to assign key to the component, so that it will be re-mounted when runId changes
function PodLifecycleWithRunId(prop: {runId: string}) {
  const { runId } = prop;

  const { value, loading } = useRunJobHistory(runId);

  useRunPanelLoadingIndicator(loading);

  const preventPropagation = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
  }, []);

  if (!value) return null;
  if (value?.length === 0) return <Typography variant="body2">No job history found</Typography>;

  return <>
    {value!.map(
      (job, index) =>
        <Accordion key={index} defaultExpanded={index === value.length - 1}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} >
            <Box>
              <Chip label={job.kind} size="small" />
              {' Kubernetes Job ID: '}

              <StyledCode>{job.name}</StyledCode>
              <span onClick={preventPropagation}>
                <CopyButton text={job.name} message="Copied Job ID" color={"grey"} />
              </span>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <PodEventHistory historyRecords={job.status_history_serialization} key={index} />
          </AccordionDetails>
        </Accordion>
    )}
  </>
}

export default function PodLifecycle() {

  const { selectedRun } = usePipelinePanelsContext();

  return <PodLifecycleWithRunId key={selectedRun!.id} runId={selectedRun!.id} />
}
