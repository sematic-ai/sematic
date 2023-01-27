import Timeline from '@mui/lab/Timeline';
import Alert from "@mui/material/Alert";
import { useMemo } from "react";
import { useExternalResource } from "../../hooks/externalResourceHooks";
import { usePipelinePanelsContext } from "../../hooks/pipelineHooks";
import { styled } from '@mui/system';
import ExternalResourceState from './ExternalResourceState';
import timelineItemClasses from '@mui/lab/TimelineItem/timelineItemClasses';
import { ExternalResourceHistorySerialization } from '../../Models';
import { useRunPanelLoadingIndicator } from '../../hooks/runDetailsHooks';

const ThinTimetime = styled(Timeline)`
    margin: 0;
    flex: 0;
    & .${timelineItemClasses.root}:before {
        flex: 0;
        padding: 0;
    }
`;

export default function ExternalResourcePanel() {

    const { selectedRun } = usePipelinePanelsContext();

    const { value: externalResources, loading, error } = useExternalResource(selectedRun!);

    const historyRecords = useMemo<Array<ExternalResourceHistorySerialization> | null>(
        () => {
            if (!externalResources) {
                return null;
            }
            if (externalResources.length === 0) {
                return [];
            }
            const externalResource = externalResources[0];
            const history 
                = externalResource.history_serializations as 
                Array<ExternalResourceHistorySerialization> || [];
            return history.reverse();
        }, [externalResources]);

    useRunPanelLoadingIndicator(loading);

    if (!externalResources || externalResources.length === 0) {
        return <Alert severity="info" sx={{ mt: 3 }}>
            The run does not use any external resource or the external resource state has not been reported yet.
        </Alert>
    }

    if (!!error) {
        return <Alert severity="error" sx={{ mt: 3 }}> {error.message} </Alert>
    }

    return <ThinTimetime key={selectedRun?.id}>
            {historyRecords?.map(
                (state, index) => 
                <ExternalResourceState 
                    historyRecord={state} key={index} isLast={historyRecords.length - 1 === index}/>
            )}
        </ThinTimetime>
}
