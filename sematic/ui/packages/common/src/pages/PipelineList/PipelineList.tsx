import { createColumnHelper, getCoreRowModel, useReactTable, RowData } from "@tanstack/react-table";
import concat from "lodash/concat";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { FilterCondition } from "src/ApiContracts";
import { Run } from "src/Models";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { getRunUrlPattern, useFiltersConverter, useRunsPagination } from "src/hooks/runHooks";
import AvgRuntimeColumn from "src/pages/PipelineList/AvgRuntimeColumn";
import LastRunColumn from "src/pages/PipelineList/LastRunColumn";
import LatestRunsColumn from "src/pages/PipelineList/LatestRunsColumn";
import SuccessRateColumn from "src/pages/PipelineList/SuccessRateColumn";
import TotalRunsColumn from "src/pages/PipelineList/TotalRunsColumn";
import { ExtendedRunMetadata, Metrics, RowMetadataType } from "src/pages/PipelineList/common";
import NameColumn from "src/pages/RunTableCommon/NameColumn";
import { RunsTableTemplate } from "src/pages/RunTableCommon/PresentationalComponent";
import TagsColumn from "src/pages/RunTableCommon/TagsColumn";
import { AllFilters } from "src/pages/RunTableCommon/filters";
import MuiRouterLink from "src/component/MuiRouterLink";

declare module "@tanstack/react-table" {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    interface TableMeta<TData extends RowData> {
        updateRowMetrics: (runId: string, metrics: Metrics) => void;
        updateLatestRuns: (runId: string, latestRuns: Run[]) => void;
    }
}

const columnHelper = createColumnHelper<ExtendedRunMetadata>()

const columns = [
    columnHelper.accessor(({ run }) => [run.id, run.name, run.function_path], {
        meta: {
            columnStyles: {
                width: "1px",
                minWidth: "190px",
                maxWidth: "calc(100vw - 1120px)"
            }
        },
        header: "Name",
        cell: info => {
            const [id, name, importPath] = info.getValue();
            return <MuiRouterLink href={getRunUrlPattern(id)}>
                <NameColumn name={name} importPath={importPath} />
            </MuiRouterLink>
        },
    }),
    columnHelper.accessor(({ run }) => run.tags, {
        meta: {
            columnStyles: {
                width: "22.5352%", // this is the minWidth(160px) divided by the sum of the minWidths of all other columns.
                minWidth: "160px"
            }
        },
        header: "Tags",
        cell: info => <TagsColumn tags={info.getValue()} />,
    }),
    columnHelper.accessor(extendedRun => extendedRun, {
        meta: {
            columnStyles: {
                width: "14.0845%", // this is the minWidth(100px) divided by the sum of the minWidths of all other columns.
                minWidth: "100px"
            }
        },
        header: "Runs",
        cell: info => <TotalRunsColumn extendedRun={info.getValue()} tableMeta={info.table.options.meta} />,
    }),
    columnHelper.accessor(({ metadata, run }) => [run.id, metadata], {
        meta: {
            columnStyles: {
                width: "14.0845%", // this is the minWidth(100px) divided by the sum of the minWidths of all other columns.
                minWidth: "100px"
            }
        },
        header: "Avg. runtime",
        cell: info => {
            const [id, metadata] = info.getValue();
            return <MuiRouterLink href={getRunUrlPattern(id as string)}>
                <AvgRuntimeColumn metadata={metadata as RowMetadataType} />
            </MuiRouterLink>
        },
    }),
    columnHelper.accessor(({ metadata, run }) => [run.id, metadata], {
        meta: {
            columnStyles: {
                width: "14.0845%", // this is the minWidth(100px) divided by the sum of the minWidths of all other columns.
                minWidth: "100px"
            }
        },
        header: "Success",
        cell: info => {
            const [id, metadata] = info.getValue();
            return <MuiRouterLink href={getRunUrlPattern(id as string)}>
                <SuccessRateColumn metadata={metadata as RowMetadataType} />
            </MuiRouterLink>;
        },
    }),
    columnHelper.accessor(({ metadata }) => metadata, {
        meta: {
            columnStyles: {
                width: "16.9014%", // this is the minWidth(120px) divided by the sum of the minWidths of all other columns.
                minWidth: "120px"
            }
        },
        header: "Last ran",
        cell: info => <LastRunColumn metadata={info.getValue()} />,
    }),
    columnHelper.accessor(extendedRun => extendedRun, {
        meta: {
            columnStyles: {
                width: "21.1268%", // this is the minWidth(150px) divided by the sum of the minWidths of all other columns.
                minWidth: "150px"
            }
        },
        header: "Last 5 runs",
        cell: info => <LatestRunsColumn extendedRun={info.getValue()} tableMeta={info.table.options.meta} />,
    })
]


interface RunListProps {
    filters: AllFilters | null;
}

function PipelineList(props: RunListProps) {
    const { filters } = props;

    const { setIsLoading } = useContext(LayoutServiceContext);

    const { runFilter, queryParams } = useFiltersConverter(filters);

    const combinedRunFilter = useMemo(() => {
        const rootCondition = { parent_id: { eq: null } } as FilterCondition;
        if (!runFilter) {
            return rootCondition
        }
        if ("AND" in runFilter) {
            return { AND: concat([rootCondition], (runFilter as any)["AND"]) };
        }
        return { AND: concat([rootCondition], runFilter as FilterCondition) };
    }, [runFilter]);

    const combinedQueryParams = useMemo(() => {
        return { ...queryParams, group_by: "function_path" };
    }, [queryParams]);

    const { runs, error, page, isLoaded, isLoading, totalPages, totalRuns, nextPage, previousPage } = useRunsPagination(
        combinedRunFilter, combinedQueryParams
    );

    const [rowMetaData, setRowMetaData] = useState(new Map<string, RowMetadataType>());

    const updateRowMetrics = useCallback((runId: string, metrics: Metrics) => {
        setRowMetaData(prev => new Map(prev).set(runId, { ...prev.get(runId), metrics }));
    }, []);

    const updateLatestRuns = useCallback((runId: string, latestRuns: Run[]) => {
        setRowMetaData(prev => new Map(prev).set(runId, { ...prev.get(runId), latestRuns }));
    }, []);

    const data = useMemo(() => {
        if (!runs) {
            return [];
        }
        return runs.map(run => ({
            run,
            metadata: rowMetaData.get(run.id)
        }));
    }, [runs, rowMetaData]);

    const tableInstance = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        meta: {
            updateRowMetrics,
            updateLatestRuns
        }
    });

    const hasFilters = useMemo(() => !!filters && Object.keys(filters).length > 0, [filters]);

    useEffect(() => {
        setIsLoading(isLoading)
    }, [setIsLoading, isLoading]);

    return <RunsTableTemplate
        isLoading={isLoading}
        isLoaded={isLoaded}
        hasFilters={hasFilters}
        totalRuns={totalRuns}
        singularNoun={"Pipeline"}
        pluralNoun={"Pipelines"}
        error={error}
        currentPage={page}
        totalPages={totalPages}
        tableInstance={tableInstance}
        onPreviousPageClicked={previousPage}
        onNextPageClicked={nextPage} />
}

export default PipelineList;