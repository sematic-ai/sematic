import TimelineConnector from "@mui/lab/TimelineConnector/TimelineConnector";
import TimelineContent from "@mui/lab/TimelineContent/TimelineContent";
import TimelineDot from "@mui/lab/TimelineDot/TimelineDot";
import TimelineItem from "@mui/lab/TimelineItem/TimelineItem";
import TimelineSeparator from "@mui/lab/TimelineSeparator/TimelineSeparator";
import Chip from "@mui/material/Chip/Chip";
import Typography from "@mui/material/Typography/Typography";
import styled from "@emotion/styled";
import { Job } from "@sematic/common/lib/src/Models";
import { format } from 'date-fns';
import { useMemo } from "react";

const TERMINATE_STATE = 'Deleted';
const SpacedText = styled(Typography)`
    margin: 4px 0;
`;

function StyledChip(props: React.ComponentProps<typeof Chip>) {
    return <Chip {...props} sx={{ mr: 1 }} />
};

function StyledChipWithColor(props:
    React.ComponentProps<typeof StyledChip> & { resourceState: string }) {
    const { resourceState, ...restProps } = props;

    const color = useMemo(() => getColorByState(resourceState), [resourceState]);

    return <StyledChip {...restProps} color={color} label={resourceState} />
}

interface PodLifecycleEventProps {
    podStatus: Job['status_history_serialization'][number];
    isLast: boolean;
}

function getColorByState(podEvent: string) {
    if (["Running", "Pending"].includes(podEvent)) {
        return 'primary';
    }
    return undefined;
}

function TimelineDotWithColor({ resourceState }: { resourceState: string }) {
    const color = useMemo(() => getColorByState(resourceState) || 'grey', [resourceState]);
    return <TimelineDot color={color} />;
};

export default function PodLifecycleEvent(props: PodLifecycleEventProps) {
    const { podStatus: { message, last_updated_epoch_seconds, state }, isLast } = props;

    const timeString = useMemo(
        () => format(
            new Date(last_updated_epoch_seconds * 1000),
            'LLL\xa0d,\xa0yyyy\xa0h:mm:ss\xa0a'), [last_updated_epoch_seconds]);

    return <TimelineItem>
        <TimelineSeparator>
            {isLast ?
                <TimelineDotWithColor resourceState={state} />
                : <TimelineDot />}
            {state !== TERMINATE_STATE && <TimelineConnector />}
        </TimelineSeparator>
        <TimelineContent>
            {isLast ?
                <StyledChipWithColor size={"small"} resourceState={state} />
                : <StyledChip size={"small"} label={state} />}
            <SpacedText>{message}</SpacedText>
            <SpacedText>{timeString}</SpacedText>
        </TimelineContent>
    </TimelineItem>
}
