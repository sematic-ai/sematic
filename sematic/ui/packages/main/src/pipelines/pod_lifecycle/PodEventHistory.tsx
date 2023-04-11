import Timeline from '@mui/lab/Timeline';
import timelineItemClasses from '@mui/lab/TimelineItem/timelineItemClasses';
import { styled } from '@mui/system';
import PodLifecycleEvent from 'src/pipelines/pod_lifecycle/PodLifecycleEvent';
import { Job } from '@sematic/common/lib/src/Models';
import { useMemo } from 'react';

const ThinTimeline = styled(Timeline)`
    margin: 0;
    flex: 0;
    & .${timelineItemClasses.root}:before {
        flex: 0;
        padding: 0;
    }
`;

interface PodEventHistoryProps {
  historyRecords: Job['status_history_serialization'];
}

export default function PodEventHistory(props: PodEventHistoryProps) {
  const { historyRecords } = props;

  const reversedHistoryRecords = useMemo(
    () => historyRecords.slice().reverse(), [historyRecords]);

  return <ThinTimeline>
      {reversedHistoryRecords.map(
        (state, index) =>
          <PodLifecycleEvent key={index} podStatus={state}
            isLast={historyRecords.length - 1 === index} />
      )}
    </ThinTimeline>
}
