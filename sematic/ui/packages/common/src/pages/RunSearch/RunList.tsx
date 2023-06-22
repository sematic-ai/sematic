import { Row, createColumnHelper, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { useCallback, useContext, useEffect, useMemo } from "react";
import { Run } from "src/Models";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { getRunUrlPattern, useFiltersConverter, useRunsPagination } from "src/hooks/runHooks";
import { RunsTableTemplate } from "src/pages/RunTableCommon/PresentationalComponent";
import { IdColumnDef, NameColumnDef, OwnerColumnDef, StatusColumnDef, SubmissionTimeColumnDef, TagsColumnDef } from "src/pages/RunTableCommon/columnDefinition";
import { AllFilters } from "src/pages/RunTableCommon/filters";

const columnHelper = createColumnHelper<Run>();

const columns =[
    IdColumnDef(columnHelper),
    SubmissionTimeColumnDef(columnHelper),
    NameColumnDef(columnHelper),
    TagsColumnDef(columnHelper),
    OwnerColumnDef(columnHelper),
    StatusColumnDef(columnHelper),
];

interface RunListProps {
    filters: AllFilters | null;
}

const RunList = (props: RunListProps) => {
    const { filters } = props;

    const { runFilter, queryParams } = useFiltersConverter(filters);

    const { runs, error, page, isLoaded, isLoading, totalPages, totalRuns, nextPage, previousPage } = useRunsPagination(
        runFilter as any, queryParams
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
        singularNoun={"Run"}
        pluralNoun={"Runs"}
        error={error}
        currentPage={page}
        totalPages={totalPages}
        tableInstance={tableInstance}
        onPreviousPageClicked={previousPage}
        onNextPageClicked={nextPage}
        getRowLink={getRowLink} />
}

export default RunList;