import styled from "@emotion/styled";
import { useMemo } from "react";
import ErrorBoundary from "src/component/ErrorBoundary";
import RunStateChip from "src/component/RunStateChips";
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
    originalRunId: string | null;
    createdAt: string;
    failedAt?: string;
    resolvedAt?: string;
    endedAt?: string;
}

const RunStatusColumn = (props: RunStatusColumnProps) => {
    const { futureState, originalRunId, createdAt, failedAt, resolvedAt, endedAt } = props;

    const runStateText = useMemo(() => getRunStateText(
        futureState, originalRunId,
        {createdAt, failedAt, resolvedAt, endedAt},
        { short: true }
    ), [futureState, createdAt, failedAt, resolvedAt, endedAt, originalRunId]);

    return <StyledContainer>
        <RunStateChip futureState={futureState} originalRunId={originalRunId} /> {runStateText}
    </StyledContainer>;
}

const RunStatusColumnWithErrorBoundary = (props: RunStatusColumnProps) => {
    return <ErrorBoundary fallback={"Invalid state"}>
        <RunStatusColumn {...props} />
    </ErrorBoundary>
}

export default RunStatusColumnWithErrorBoundary;
