import styled from "@emotion/styled";
import { ColumnHelper } from "@tanstack/react-table";
import { Run } from "src/Models";
import ErrorBoundary from "src/component/ErrorBoundary";
import RunStateChip from "src/component/RunStateChips";
import theme from "src/theme/new";

const StyledContainer = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;
`;

interface RunStatusColumnProps {
    futureState: string;
    originalRunId: string | null;
    createdAt: string;
    failedAt?: string;
    resolvedAt?: string;
    endedAt?: string;
}

const RunStateColumn = (props: RunStatusColumnProps) => {
    const { futureState, originalRunId } = props;

    return <StyledContainer>
        <RunStateChip futureState={futureState} orignalRunId={originalRunId} />
    </StyledContainer>;
}

const RunStateColumnWithErrorBoundary = (props: RunStatusColumnProps) => {
    return <ErrorBoundary fallback={"Invalid state"}>
        <RunStateColumn {...props} />
    </ErrorBoundary>
}

const StateChipColumnDef = (columnHelper: ColumnHelper<Run>) =>
    columnHelper.accessor(data => ({
        futureState: data.future_state,
        originalRunId: data.original_run_id,
    }), {
        meta: {
            columnStyles: {
                width: "0%",
                minWidth: "30px",
                boxSizing: "border-box",
                padding: `0 ${theme.spacing(2)} 0 0`,
            }
        },
        header: "Status",
        cell: info => <RunStateColumnWithErrorBoundary {...info.getValue() as any} />,
    });

export default StateChipColumnDef;
