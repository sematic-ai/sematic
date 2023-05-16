import styled from "@emotion/styled";
import { useMemo } from "react";
import ErrorBoundary from "src/component/ErrorBoundary";
import { getRunStateChipByState } from "src/component/RunStateChips";
import getRunStateText from "src/component/RunStateText";
import theme from "src/theme/new";

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
    endedAt?: string;
}

const RunStatusColumn = (props: RunStatusColumnProps) => {
    const { futureState, createdAt, failedAt, resolvedAt, endedAt } = props;

    const runStateChip = useMemo(() => getRunStateChipByState(futureState), [futureState]);

    const runStateText = useMemo(() => getRunStateText(
        futureState,
        {createdAt, failedAt, resolvedAt, endedAt}
    ), [futureState, createdAt, failedAt, resolvedAt, endedAt]);

    return <StyledContainer>{runStateChip} {runStateText}</StyledContainer>;
}

const RunStatusColumnWithErrorBoundary = (props: RunStatusColumnProps) => {
    return <ErrorBoundary fallback={"Invalid state"}>
        <RunStatusColumn {...props} />
    </ErrorBoundary>
}

export default RunStatusColumnWithErrorBoundary;
