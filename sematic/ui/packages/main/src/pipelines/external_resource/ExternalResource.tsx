import Timeline from '@mui/lab/Timeline';
import timelineItemClasses from '@mui/lab/TimelineItem/timelineItemClasses';
import Alert from "@mui/material/Alert";
import { styled } from '@mui/system';
import { ExternalResourceHistorySerialization } from '@sematic/common/src/Models';
import { useMemo } from "react";
import { useExternalResource } from "src/hooks/externalResourceHooks";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { useRunPanelLoadingIndicator } from 'src/hooks/runDetailsHooks';
import ExternalResourceState from 'src/pipelines/external_resource/ExternalResourceState';

const ThinTimeline = styled(Timeline)`
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
    
    const extraResourcesInfoSection = useMemo(() => {
        if ((externalResources?.length || 0) > 1) {
            return <Alert severity="info">
                The run uses more than 1 external resources. Here is only the first one.
            </Alert>
        }
        return <></>;

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

    return <>
        {extraResourcesInfoSection}
        <ThinTimeline key={selectedRun?.id}>
            {historyRecords?.map(
                (state, index) => 
                <ExternalResourceState 
                    historyRecord={state} key={index} isLast={historyRecords.length - 1 === index}/>
            )}
        </ThinTimeline>
    </>
}
