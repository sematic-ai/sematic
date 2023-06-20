import styled from "@emotion/styled";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import Alert from "@mui/material/Alert";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import { Row, Table } from "@tanstack/react-table";
import { useMemo } from "react";
import TableComponent from "src/component/Table";
import { NoRunNoFilters, NoRunWithFilters } from "src/pages/RunTableCommon/RunListEmptyState";
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

const EmptyStateContainer = styled.div`
    position: absolute;
    right: 0;
    left: 0;
    top: 100px;
    bottom: 50px;
    display: flex;
    justify-content: center;
    align-items: center;
`;


interface RunsTableTemplateProps<T> {
    isLoading: boolean;
    isLoaded: boolean;
    hasFilters: boolean;
    totalRuns: number | undefined;
    singularNoun: string;
    pluralNoun: string;
    error: Error | undefined;
    currentPage: number;
    totalPages: number;
    tableInstance: Table<T>;
    onPreviousPageClicked: () => void;
    onNextPageClicked: () => void;
    getRowLink?: (row: Row<T>) => string;
}

export function RunsTableTemplate<T>(props: RunsTableTemplateProps<T>) {
    const { isLoading, isLoaded, totalRuns, singularNoun, pluralNoun, error, hasFilters,
        tableInstance, currentPage, totalPages, getRowLink, onNextPageClicked, onPreviousPageClicked } = props;


    const totalRunsText = useMemo(() => {
        if (!isLoading && totalRuns === 0) {
            return `No ${pluralNoun}`;
        }
        const noun = totalRuns === 1 ? singularNoun : pluralNoun;

        return `${totalRuns || "?"} ${noun}`;
    }, [isLoading, totalRuns, singularNoun, pluralNoun]);

    const emtpyStateComponent = useMemo(() => {
        if (!isLoaded || (!!totalRuns && totalRuns > 0) ) {
            return null;
        }
        return <EmptyStateContainer >
            {hasFilters ? <NoRunWithFilters /> : <NoRunNoFilters />}
        </EmptyStateContainer>;
    }, [isLoaded, hasFilters, totalRuns]);

    if (error) {
        return <Alert severity="error">{error.message}</Alert>
    }

    return <Container>
        <Stats>
            <Typography variant={"bold"}>{totalRunsText}</Typography>
        </Stats>
        <TableComponent table={tableInstance} getRowLink={getRowLink} className={"runs-table"} />
        {emtpyStateComponent}
        <Pagination>
            <IconButton aria-label="previous" disabled={currentPage === 0} onClick={onPreviousPageClicked}>
                <ChevronLeft />
            </IconButton>
            {`${currentPage + 1} / ${totalPages}`}
            <IconButton aria-label="next" disabled={currentPage + 1 === totalPages} onClick={onNextPageClicked}>
                <ChevronRight />
            </IconButton>
        </Pagination>
    </Container>
}