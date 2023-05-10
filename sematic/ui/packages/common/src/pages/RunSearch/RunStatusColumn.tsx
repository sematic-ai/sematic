import styled from '@emotion/styled';
import { useMemo } from 'react';
import { getRunStateChipByState } from 'src/component/RunStateChips';
import getRunStateText from 'src/component/RunStateText';
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

    const runStateChip = useMemo(() => getRunStateChipByState(futureState), [futureState]);

    const runStateText = useMemo(() => getRunStateText(
        futureState,
        {createdAt, failedAt, resolvedAt, canceledAt}
    ), [futureState, createdAt, failedAt, resolvedAt, canceledAt]);

    return <StyledContainer>{runStateChip} {runStateText}</StyledContainer>;
}

export default RunStatusColumn;