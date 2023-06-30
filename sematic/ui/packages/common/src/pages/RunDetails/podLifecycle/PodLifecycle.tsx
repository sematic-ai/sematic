import styled from "@emotion/styled";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useEffect } from "react";
import CopyButton from "src/component/CopyButton";
import { useRunJobHistory } from "src/hooks/podHistoryHooks";
import { useTextSelection } from "src/hooks/textSelectionHooks";
import PodEventHistory from "src/pages/RunDetails/podLifecycle/PodEventHistory";

const StyledCode = styled.code`
  font-size: 12px;
  cursor: text;
  user-select: text;  
`;

interface PodLifecycleProps {
    runId: string,
    setIsLoading: (isLoading: boolean) => void
    className?: string;
}

// Separate component to assign key to the component, so that it will be re-mounted when runId changes
export default function PodLifecycle(prop: PodLifecycleProps) {
    const { runId, setIsLoading, className } = prop;

    const { value, loading } = useRunJobHistory(runId);


    const elementRef = useTextSelection<HTMLDivElement>();

    useEffect(() => {
        setIsLoading(loading);
    }, [loading, setIsLoading]);

    if (!value) return null;
    if (value?.length === 0) return <Typography variant="body2">No pod history found.</Typography>;

    return <>
        <Typography fontSize="small" color="GrayText" style={{ marginBottom: "1em" }}>
      The information in this tab is provided for debugging purposes.
      The information it displays is periodically polled from Kubernetes,
      and some intermediate states may not be represented in the timelines.
        </Typography>
        {value!.map(
            (job, index) =>
                <Accordion key={index} defaultExpanded={index === value.length - 1} className={className}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />} >
                        <Box ref={elementRef} style={{ width: "100%" }}>
                            <Typography fontSize="small" color="GrayText" component="span">
                                {"Job ID: "}
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
