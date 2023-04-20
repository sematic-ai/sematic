import styled from '@emotion/styled';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CopyButton from '@sematic/common/lib/src/component/CopyButton';
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { useRunJobHistory } from 'src/hooks/podHistoryHooks';
import { useRunPanelLoadingIndicator } from 'src/hooks/runDetailsHooks';
import { useTextSelection } from 'src/hooks/textSelectionHooks';
import PodEventHistory from 'src/pipelines/pod_lifecycle/PodEventHistory';

const StyledCode = styled.code`
  font-size: 12px;
  cursor: text;
  user-select: text;  
`;

// Separate component to assign key to the component, so that it will be re-mounted when runId changes
function PodLifecycleWithRunId(prop: { runId: string }) {
  const { runId } = prop;

  const { value, loading } = useRunJobHistory(runId);

  useRunPanelLoadingIndicator(loading);

  const elementRef = useTextSelection<HTMLDivElement>();

  if (!value) return null;
  if (value?.length === 0) return <Typography variant="body2">No pod history found.</Typography>;

  return <>
    <Typography fontSize="small" color="GrayText" style={{ marginBottom: '1em' }}>
      The information in this tab is provided for debugging purposes.
      The information it displays is periodically polled from Kubernetes,
      and some intermediate states may not be represented in the timelines.
    </Typography>
    {value!.map(
      (job, index) =>
        <Accordion key={index} defaultExpanded={index === value.length - 1}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} >
            <Box ref={elementRef} style={{ width: `100%` }}>
              <Typography fontSize="small" color="GrayText" component="span">
                {`Job ID: `}
                <StyledCode>{job.name}</StyledCode>
                <span>
                  <CopyButton text={job.name} message="Copied Job ID" color={"grey"} />
                </span>
              </Typography>
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
