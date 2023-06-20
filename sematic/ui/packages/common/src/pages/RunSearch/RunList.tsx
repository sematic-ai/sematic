import styled from "@emotion/styled";
import { Row, createColumnHelper, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { parseJSON } from "date-fns";
import { useCallback, useContext, useEffect, useMemo } from "react";
import { Run } from "src/Models";
import { DateTimeLongConcise } from "src/component/DateTime";
import NameTag from "src/component/NameTag";
import { RunReference } from "src/component/RunReference";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { getRunUrlPattern, useFiltersConverter, useRunsPagination } from "src/hooks/runHooks";
import NameColumn from "src/pages/RunTableCommon/NameColumn";
import RunStatusColumn from "src/pages/RunSearch/RunStatusColumn";
import TagsColumn from "src/pages/RunTableCommon/TagsColumn";
import { AllFilters } from "src/pages/RunTableCommon/filters";
import { RunsTableTemplate } from "src/pages/RunTableCommon/PresentationalComponent";
import theme from "src/theme/new";


const StyledRunReferenceLink = styled(RunReference)`
    color: ${theme.palette.mediumGrey.main};
`;

const columnHelper = createColumnHelper<Run>()

const columns = [
    columnHelper.accessor("id", {
        meta: {
            columnStyles: {
                width: "5.923%",
            }
        },
        header: "ID",
        cell: info => <StyledRunReferenceLink runId={info.getValue()} />,
    }),
    columnHelper.accessor("created_at", {
        meta: {
            columnStyles: {
                width: "12.3396%",
                minWidth: "150px"
            }
        },
        header: "Submitted at",
        cell: info => DateTimeLongConcise(parseJSON(info.getValue())),
    }),
    columnHelper.accessor(run => [run.name, run.function_path], {
        meta: {
            columnStyles: {
                width: "1px",
                maxWidth: "calc(100vw - 1100px)"
            }
        },
        header: "Name",
        cell: info => {
            const [name, importPath] = info.getValue();
            return <NameColumn name={name} importPath={importPath} />
        },
    }),
    columnHelper.accessor("tags", {
        meta: {
            columnStyles: {
                width: "14.5114%",
                minWidth: "160px"
            }
        },
        header: "Tags",
        cell: info => <TagsColumn tags={info.getValue()} />,
    }),
    columnHelper.accessor(data => ({
        firstName: data.user?.first_name,
        lastName: data.user?.last_name
    }), {
        meta: {
            columnStyles: {
                width: "8.39092%",
                maxWidth: "max(100px, 8.39092%)",
            }
        },
        header: "Owner",
        cell: info => <NameTag {...info.getValue()} />,
    }),
    columnHelper.accessor(data => ({
        futureState: data.future_state,
        createdAt: data.created_at,
        failedAt: data.failed_at,
        resolvedAt: data.resolved_at
    }), {
        meta: {
            columnStyles: {
                width: "15.7947%",
                minWidth: "200px"
            }
        },
        header: "Status",
        cell: info => <RunStatusColumn {...info.getValue() as any} />,
    })
]

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