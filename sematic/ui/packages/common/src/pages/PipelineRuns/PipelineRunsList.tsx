import { Row, createColumnHelper, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import concat from "lodash/concat";
import { useCallback, useContext, useEffect, useMemo } from "react";
import { FilterCondition } from "src/ApiContracts";
import { Run } from "src/Models";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { useRootRunContext } from "src/context/RootRunContext";
import { getRunUrlPattern, useFiltersConverter, useRunsPagination } from "src/hooks/runHooks";
import { RunsTableTemplate } from "src/pages/RunTableCommon/PresentationalComponent";
import { IdColumnDef, OwnerColumnDef, StatusColumnDef, SubmissionTimeColumnDef, TagsColumnDef } from "src/pages/RunTableCommon/columnDefinition";
import { AllFilters } from "src/pages/RunTableCommon/filters";

const columnHelper = createColumnHelper<Run>();

const columns =[
    IdColumnDef(columnHelper),
    SubmissionTimeColumnDef(columnHelper),
    TagsColumnDef(columnHelper),
    OwnerColumnDef(columnHelper),
    StatusColumnDef(columnHelper),
];

interface PipelineRunsListProps {
    filters: AllFilters | null;
}

const PipelineRunsList = (props: PipelineRunsListProps) => {
    const { filters } = props;

    const { rootRun } = useRootRunContext();

    const { runFilter, queryParams } = useFiltersConverter(filters);

    const combinedRunFilter = useMemo(() => {
        const rootCondition = [
            { function_path: { eq: rootRun?.function_path } },
            { parent_id: { eq: null } }
        ] as [FilterCondition, FilterCondition];

        if (!runFilter) {
            return { AND: rootCondition };
        }
        if ("AND" in runFilter) {
            return { AND: concat(rootCondition, (runFilter as any)["AND"]) };
        }
        return { AND: concat(rootCondition, runFilter as FilterCondition) };
    }, [runFilter, rootRun]);

    const { runs, error, page, isLoaded, isLoading, totalPages, totalRuns, nextPage, previousPage } = useRunsPagination(
        combinedRunFilter as any, queryParams
    );

    const { setIsLoading } = useContext(LayoutServiceContext);

    const tableInstance = useReactTable({
        data: runs,
        columns,
        getCoreRowModel: getCoreRowModel()
    });

    const hasFilters = useMemo(() => !!filters && Object.keys(filters).length > 0, [filters]);

    const getRowLink = useCallback((row: Row<Run>): string => {
        return getRunUrlPattern(row.original.id);
    }, [])

    useEffect(() => {
        setIsLoading(isLoading)
    }, [setIsLoading, isLoading]);

    return <RunsTableTemplate
        isLoading={isLoading}
        isLoaded={isLoaded}
        hasFilters={hasFilters}
        totalRuns={totalRuns}
        singularNoun={"Resolution"}
        pluralNoun={"Resolutions"}
        error={error}
        currentPage={page}
        totalPages={totalPages}
        tableInstance={tableInstance}
        onPreviousPageClicked={previousPage}
        onNextPageClicked={nextPage}
        getRowLink={getRowLink} />
}

export default PipelineRunsList;

