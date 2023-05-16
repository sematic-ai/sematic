import styled from "@emotion/styled";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import { Row, createColumnHelper, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { parseJSON } from "date-fns";
import { useCallback, useContext, useEffect, useMemo } from "react";
import { Run } from "src/Models";
import { DateTimeLongConcise } from "src/component/DateTime";
import NameTag from "src/component/NameTag";
import { RunReference } from "src/component/RunReference";
import TableComponent, { TableComponentProps } from "src/component/Table";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { getRunUrlPattern, useRunsPagination } from "src/hooks/runHooks";
import NameColumn from "src/pages/RunSearch/NameColumn";
import RunStatusColumn from "src/pages/RunSearch/RunStatusColumn";
import TagsColumn from "src/pages/RunSearch/TagsColumn";
import { AllFilters, FilterType, StatusFilters, convertMiscellaneousFilterToRunFilters, convertOwnersFilterToRunFilters, convertStatusFilterToRunFilters } from "src/pages/RunSearch/filters/common";
import theme from "src/theme/new";

const Container = styled.div`
    display: flex;
    flex-direction: column;
    height: 100%;
    margin-right: -${theme.spacing(5)};
`;

const Stats = styled.div`
    height: 50px;
    width: 100%;
    display: flex;
    align-items: center;
    flex-grow: 0;
    flex-shrink: 0;
`;

const Pagination = styled.div`
    height: 50px;
    width: 100%;
    display: flex;
    align-items: center;
    flex-grow: 0;
    flex-shrink: 0;
    justify-content: flex-end;
    padding-right: ${theme.spacing(6)};

    svg {
        cursor: pointer;
    }
`;

const StyledRunReferenceLink = styled(RunReference)`
    color: ${theme.palette.mediumGrey.main};
`;

const StyledTableComponent = styled(TableComponent)<TableComponentProps<Run>>`
    min-width: 850px;
` as typeof TableComponent;

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
                maxWidth: "calc(100vw - 1060px)"
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
    columnHelper.accessor(data => `${data.user?.first_name} ${data.user?.last_name}`, {
        meta: {
            columnStyles: {
                width: "8.39092%",
                minWidth: "100px"
            }
        },
        header: "Owner",
        cell: info => <NameTag>{info.getValue()}</NameTag>,
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

    const runFilter = useMemo(() => {
        const conditions = [];

        if (!filters) {
            return undefined;
        }

        if (filters[FilterType.STATUS]) {
            const statusFilters = convertStatusFilterToRunFilters(filters[FilterType.STATUS] as StatusFilters[]);
            if (statusFilters) {
                conditions.push(statusFilters);
            }
        }

        if (filters[FilterType.OWNER]) {
            const ownersFilters = convertOwnersFilterToRunFilters(filters[FilterType.OWNER]!);
            if (ownersFilters) {
                conditions.push(ownersFilters);
            }
        }

        if (filters[FilterType.OTHER]) {
            const miscellaneousFilters = convertMiscellaneousFilterToRunFilters(filters[FilterType.OTHER]!);
            if (miscellaneousFilters) {
                conditions.push(miscellaneousFilters);
            }
        }

        if (conditions.length > 1 ) {
            return {
                "AND": conditions
            }
        }

        if (conditions.length === 0) {
            return undefined;
        }
        return conditions[0];
    }, [filters]);

    const queryParams = useMemo(() => {
        if (!filters) {
            return undefined;
        }

        if (filters[FilterType.SEARCH]) {
            return {
                "search": filters[FilterType.SEARCH]![0]
            };
        }
    }, [filters]);


    const { runs, page, isLoading, totalPages, totalRuns, nextPage, previousPage } = useRunsPagination(
        runFilter as any, queryParams
    );

    const { setIsLoading } = useContext(LayoutServiceContext);

    const tableInstance = useReactTable({
        data: runs,
        columns,
        getCoreRowModel: getCoreRowModel()
    });

    const getRowLink = useCallback((row: Row<Run>): string => {
        return getRunUrlPattern(row.original.id);
    }, [])

    useEffect(() => {
        setIsLoading(isLoading)
    }, [setIsLoading, isLoading]);

    return <Container>
        <Stats>
            <Typography variant={"bold"}>{`${totalRuns || "?"} ${totalRuns === 1 ? "Run" : "Runs"}`}</Typography>
        </Stats>
        <StyledTableComponent table={tableInstance} getRowLink={getRowLink} />
        <Pagination>
            <IconButton aria-label="previous" disabled={page === 0} onClick={previousPage}>
                <ChevronLeft />
            </IconButton>
            {`${page + 1} / ${totalPages}`}
            <IconButton aria-label="next" disabled={page + 1 === totalPages} onClick={nextPage}>
                <ChevronRight />
            </IconButton>
        </Pagination>
    </Container>
}

export default RunList;