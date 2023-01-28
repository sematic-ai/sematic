import TimelineConnector from "@mui/lab/TimelineConnector/TimelineConnector";
import TimelineContent from "@mui/lab/TimelineContent/TimelineContent";
import TimelineDot from "@mui/lab/TimelineDot/TimelineDot";
import TimelineItem from "@mui/lab/TimelineItem/TimelineItem";
import TimelineSeparator from "@mui/lab/TimelineSeparator/TimelineSeparator";
import { TERMINATE_STATE } from "../../hooks/externalResourceHooks";
import { format } from 'date-fns'
import { useMemo } from "react";
import Typography from "@mui/material/Typography/Typography";
import { ExternalResourceHistorySerialization, ExternalResourceState as ExternalResourceStateType } from "../../Models";
import { styled } from "@mui/system";
import Chip from "@mui/material/Chip/Chip";

const HighLightenedText = styled(Typography)`
    font-weight: bold;
    display: inline;
`;

const SpacedText = styled(Typography)`
    margin: 4px 0;
`;

function StyledChip(props: React.ComponentProps<typeof Chip>) {
    return <Chip {...props} sx={{mr: 1}}/>
};

function StyledChipWithColor(props:
    React.ComponentProps<typeof StyledChip> & {
        resourceState: ExternalResourceStateType
    }) {
    const {resourceState, ...restProps } = props;

    const color = useMemo(() => getColorByState(resourceState), [resourceState]);

    return <StyledChip {...restProps} color={color} label={resourceState} />
}

interface ExternalResourceStateProps {
    historyRecord: ExternalResourceHistorySerialization;
    isLast: boolean;
}

function getColorByState(resourceState: ExternalResourceStateType) {
    if (["ACTIVATING", "DEACTIVATING"].includes(resourceState)) {
        return 'primary';
    }
    if ('ACTIVE' === resourceState) {
        return 'success';
    }
    if (["CREATED", "DEACTIVATED"].includes(resourceState)) {
        return undefined;
    }
    return undefined;
}

function TimelineDotWithColor({ resourceState }: { resourceState: ExternalResourceStateType }) {
    const color = useMemo(() => getColorByState(resourceState) || 'grey', [resourceState]);
    return <TimelineDot color={color} />;
};

export default function ExternalResourceState({ historyRecord, isLast }: ExternalResourceStateProps) {
    const { root_type, values: { id, status: { values: { state, last_update_epoch_time, message } } } } = historyRecord;
    const timeString = useMemo(
        () => format(
            new Date(last_update_epoch_time * 1000),
            'LLL\xa0d,\xa0yyyy\xa0h:mm:ss\xa0a'), [last_update_epoch_time]);

    const resourceName = root_type.type[1];

    return <TimelineItem key={id}>
        <TimelineSeparator>
            {isLast ?
                <TimelineDotWithColor resourceState={state} />
                : <TimelineDot />}
            {state !== TERMINATE_STATE && <TimelineConnector />}
        </TimelineSeparator>
        <TimelineContent>
            {isLast ?
                <StyledChipWithColor size={"small"} resourceState={state}/>
                : <StyledChip size={"small"} label={state} />}
            <HighLightenedText>{resourceName}</HighLightenedText>
            <SpacedText>{message}</SpacedText>
            <SpacedText>{timeString}</SpacedText>
        </TimelineContent>
    </TimelineItem>
}
