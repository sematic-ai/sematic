import Timeline from '@mui/lab/Timeline';
import timelineItemClasses from '@mui/lab/TimelineItem/timelineItemClasses';
import { styled } from '@mui/system';
import PodLifecycleEvent from 'src/pipelines/pod_lifecycle/PodLifecycleEvent';
import { Job } from '@sematic/common/lib/src/Models';

const ThinTimetime = styled(Timeline)`
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

  return <ThinTimetime>
      {historyRecords.map(
        (state, index) =>
          <PodLifecycleEvent key={index} podStatus={state}
            isLast={historyRecords.length - 1 === index} isFirst={index === 0} />
      )}
    </ThinTimetime>
}
