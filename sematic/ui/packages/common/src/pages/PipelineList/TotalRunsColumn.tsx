import { TableMeta } from "@tanstack/react-table";
import { useEffect } from "react";
import MuiRouterLink from "src/component/MuiRouterLink";
import useBasicMetrics from "src/hooks/metricsHooks";
import { getRunUrlPattern } from "src/hooks/runHooks";
import { ExtendedRunMetadata } from "src/pages/PipelineList/common";

interface TotalRunsColumnProps {
    extendedRun: ExtendedRunMetadata;
    tableMeta: TableMeta<ExtendedRunMetadata> | undefined;
}

function TotalRunsColumn(props: TotalRunsColumnProps) {
    const { extendedRun, tableMeta } = props;
    const { updateRowMetrics } = tableMeta!;

    const { run } = extendedRun;

    const {totalCount, successRate, avgRuntime } = useBasicMetrics({runId: run.id, rootFunctionPath:run.function_path});

    useEffect(() => {
        updateRowMetrics(run.id, {
            totalCount,
            successRate,
            avgRuntime
        });
    }, [run.id, updateRowMetrics, totalCount, successRate, avgRuntime]);

    return <MuiRouterLink href={getRunUrlPattern(run.id)}>{totalCount}</MuiRouterLink>
}

export default TotalRunsColumn;