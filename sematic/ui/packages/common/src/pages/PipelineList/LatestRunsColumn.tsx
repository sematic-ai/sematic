import styled from "@emotion/styled";
import CircularProgress from "@mui/material/CircularProgress";
import { TableMeta } from "@tanstack/react-table";
import { useEffect, useMemo } from "react";
import { Run } from "src/Models";
import MuiRouterLink from "src/component/MuiRouterLink";
import { getRunStateChipByState } from "src/component/RunStateChips";
import { getRunUrlPattern, useFetchRuns } from "src/hooks/runHooks";
import { ExtendedRunMetadata } from "src/pages/PipelineList/common";

const HOW_MANY_LATEST_RUNS = "5";

const StyledChipContainer = styled.span`
    min-width: 25px;
    display: inline-block;
    &:hover {
        filter: drop-shadow(1px 2px 2px rgb(0 0 0 / 0.4));
        transform: translate(-1px, -1px);
    }
`;

function StatusChips({ runs }: { runs: Run[] }) {
    return <>{runs.map(run => <MuiRouterLink href={getRunUrlPattern(run.id)}>
        <StyledChipContainer key={`${run.id}---${run.future_state}`}>
            {getRunStateChipByState(run.future_state)}
        </StyledChipContainer></MuiRouterLink>)}
    </>;
}

interface LatestRunsColumnProps {
    extendedRun: ExtendedRunMetadata;
    tableMeta: TableMeta<ExtendedRunMetadata> | undefined;
}

function LatestRunsColumn(props: LatestRunsColumnProps) {
    const { extendedRun, tableMeta } = props;
    const { updateLatestRuns } = tableMeta!;

    const { run } = extendedRun;

    const runFilters = useMemo(
        () => ({
            function_path: { eq: run.function_path },
        }),
        [run.function_path]
    );

    const otherQueryParams = useMemo(
        () => ({
            limit: HOW_MANY_LATEST_RUNS,
        }), []);

    const { isLoading, runs } = useFetchRuns(runFilters, otherQueryParams);

    useEffect(() => {
        updateLatestRuns(run.id, runs);
    }, [run.id, runs, updateLatestRuns]);

    return useMemo(() => {
        if (isLoading || !runs) {
            return <CircularProgress size={20} />;
        }

        return <StatusChips runs={runs} />;
    }, [isLoading, runs]);
}

export default LatestRunsColumn;