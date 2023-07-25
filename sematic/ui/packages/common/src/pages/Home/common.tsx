import { ColumnHelper, Row, Table } from "@tanstack/react-table";
import { Run } from "src/Models";
import TimeAgo from "src/component/TimeAgo";
import { differenceInHours, format } from "date-fns";
import { useCallback, useEffect, useRef, useState } from "react";
import findIndex from "lodash/findIndex";
import useMeasure from "react-use/lib/useMeasure";
import styled from "@emotion/styled";
import TableComponent from "src/component/Table";
import { css } from "@emotion/css";
import { getRunUrlPattern } from "src/hooks/runHooks";

interface LastActiveTimeColumnProps {
    resolvedAt: string | null;
    failedAt: string | null;
    endedAt: string | null;
    createdAt: string | null;
    updatedAt: string | null;
    startedAt: string | null;
}

function LastActiveTimeColumn(props: LastActiveTimeColumnProps) {
    const { resolvedAt, failedAt, endedAt, createdAt, updatedAt, startedAt } = props;

    const time = failedAt || resolvedAt || endedAt || updatedAt || startedAt ||  createdAt;

    if (differenceInHours(new Date(), new Date(time as any)) > 12 ) {
        return <TimeAgo date={time as any}  />
    };
    return <>{format(new Date(time as any), "h:mm aaa")}</>;
}

export const LastActiveTimeColumnDef = (columnHelper: ColumnHelper<Run>) =>
    columnHelper.accessor(data => ({
        resolvedAt: data.resolved_at,
        failedAt: data.failed_at,
        endedAt: data.ended_at,
        createdAt: data.created_at,
        updatedAt: data.updated_at,
        startedAt: data.started_at,
    }), {
        meta: {
            columnStyles: {
                width: "0%",
                minWidth: "100px",
                textAlign: "right"
            }
        },
        header: "Last active",
        cell: info => <LastActiveTimeColumn {...info.getValue() as any} />,
    });


const StyledTable = styled(TableComponent)`
margin: 0;
`;

const StyledTableContainer = styled.div`
    flex-grow: 1;
    flex-shrink: 1;
    overflow-y: hidden;
`;

interface RowAutoAdaptTableProps {
    tableInstance: Table<unknown>;
}

export function RowAutoAdaptTable(props: RowAutoAdaptTableProps) {
    const { tableInstance } = props;

    const [ref, { height }] = useMeasure<HTMLDivElement>();
    const refMeasureDom = useRef<HTMLDivElement>();

    const setRef = useCallback((element: HTMLDivElement) => {
        refMeasureDom.current = element as HTMLDivElement;
        ref(element);
    }, [ref]);

    const [rowsCap, setRowsCap] = useState(10000);

    const getRowLink = useCallback((row: Row<unknown>): string => {
        return getRunUrlPattern((row.original as Run).id);
    }, [])

    useEffect(() => {   
        const exceedItem = findIndex(refMeasureDom.current?.querySelectorAll("tr"), 
            (tr) => {
                return tr.offsetTop + tr.offsetHeight > height;
            });
        setRowsCap(exceedItem > 0 ? exceedItem : 10000);
    }, [height, ref]);


    return <StyledTableContainer ref={setRef} className={css`tr:nth-child(n+${rowsCap+1}) { visibility: hidden; }`}>
        <StyledTable table={tableInstance} headerless={true} getRowLink={getRowLink}  />
    </StyledTableContainer>;
}
