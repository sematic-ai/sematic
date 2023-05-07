import { useMemo } from 'react';
import { DurationShort } from 'src/component/DateTime';
import { CanceledStateChip, FailedStateChip, RunningStateChip, SuccessStateChip, SubmittedStateChip } from 'src/component/RunStateChips';
import styled from '@emotion/styled';
import theme from 'src/theme/new';

const StyledContainer = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;

    & svg {
        margin-right: ${theme.spacing(1)};
    }
`;

interface RunStatusColumnProps {
    futureState: string;
    createdAt: string;
    failedAt?: string;
    resolvedAt?: string;
    canceledAt?: string;
}

const RunStatusColumn = (props: RunStatusColumnProps) => {
    const { futureState, createdAt, failedAt, resolvedAt, canceledAt } = props;

    const runStateChip = useMemo(() => {
        if (futureState === 'SUCCESS') {
            return <SuccessStateChip size={'large'} />;
        }
        if (futureState === 'FAILED') {
            return <FailedStateChip size={'large'} />;
        }
        if (futureState === 'RUNNING') {
            return <RunningStateChip size={'large'} />;
        }
        if (futureState === 'CANCELLED') {
            return <CanceledStateChip size={'large'} />;
        }
        if (futureState === 'SCHEDULED') {
            return <SubmittedStateChip size={'large'} />;
        }
    }, [futureState])

    const runStateText = useMemo(() => {
        if (futureState === 'SUCCESS') {
            return `Completed in ${DurationShort(resolvedAt!, createdAt)}`;
        }
        if (futureState === 'FAILED') {
            return `Failed after ${DurationShort(failedAt!, createdAt)}`;
        }
        if (futureState === 'RUNNING') {
            return `Running for ${DurationShort(new Date(), createdAt)}`;
        }
        if (futureState === 'CANCELLED') {
            return `Canceled after ${DurationShort(canceledAt!, createdAt)}`;
        }
        if (futureState === 'SCHEDULED') {
            return 'Submitted';
        }
        return null;
    }, [futureState, createdAt, failedAt, resolvedAt, canceledAt]);

    return <StyledContainer>{runStateChip} {runStateText}</StyledContainer>;
}

export default RunStatusColumn;