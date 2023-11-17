import styled from "@emotion/styled";
import TableMui from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { Table, flexRender, Row } from "@tanstack/react-table";
import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import theme from "src/theme/new";

const TableScroller = styled.div`
    @supports(overflow: overlay) {
        overflow-y: overlay;
    }
    overflow-x: hidden;
    flex-grow: 1;
    flex-shrink: 1;
    position: relative;
    margin-left: -${theme.spacing(5)};
`;

const StyledHeader = styled(TableHead, {
    shouldForwardProp: (prop) => prop !== "stickyHeader"
}) <{
    stickyHeader: boolean;
}>`
    height: 50px;
    position: absolute;
    z-index: 255;

    ${props => props.stickyHeader && ` 
            position: sticky;
            top: 0;

            & th {
                background: ${theme.palette.white.main};
            }
        `
}
    
    &:after {
        content: '';
        position: absolute;
        bottom: 0;
        height: 1px;
        width: calc(100% + ${theme.spacing(10)});
        margin-left: -${theme.spacing(5)};
        background: ${theme.palette.p3border.main};
    }

    & th:first-of-type {
        padding-left: ${theme.spacing(5)};
    }
`;

const TableDataRow = styled(TableRow)`
    height: 50px;
    cursor: pointer;

    &:hover {
        td {
            background: ${theme.palette.p3border.main};
        }
    }

    & td {
        padding-left: 0;
        padding-right: ${theme.spacing(5)};
        padding-top: 0;
        padding-bottom: 0;
        border-bottom: none;

        &:last-of-type {
            padding-right: 0
        };

        &:first-of-type {
            padding-left: ${theme.spacing(5)};
        }
    }
`;

export interface TableComponentProps<T> {
    table: Table<T>;
    stickyHeader?: boolean;
    headerless?: boolean;
    getRowLink?: (row: Row<T>) => string;
    className?: string;
}

const TableComponent = <T,>(props: TableComponentProps<T>) => {
    const { table, headerless = false, stickyHeader = true, getRowLink, className } = props;
    const { getLeafHeaders } = table;

    const navigate = useNavigate();
    const onClick = useCallback((event: React.MouseEvent, row: Row<T>) => {
        if (!getRowLink) {
            return;
        }
        if(event.metaKey || event.ctrlKey) {
            // open in a new tab
            window.open(getRowLink(row), "_blank");
        } else {
            navigate(getRowLink(row));
        }
    }, [getRowLink, navigate]);

    return <TableScroller className={className} data-cy={"RunList"}>
        <TableMui>
            {!headerless && <StyledHeader stickyHeader={stickyHeader}>
                <TableRow>
                    {getLeafHeaders().map(header =>
                        <th key={header.id} style={(header.column.columnDef.meta! as any).columnStyles}>
                            {flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                            )}
                        </th>)}
                </TableRow>
            </StyledHeader>}
            <TableBody>
                {table.getRowModel().rows.map(row => (
                    <TableDataRow key={row.id} onClick={(event) => onClick(event, row)} data-cy={"runlist-row"}>
                        {row.getVisibleCells().map(cell => (
                            <TableCell key={cell.id} style={(cell.column.columnDef.meta as any).columnStyles}>
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </TableCell>
                        ))}
                    </TableDataRow>
                ))}
            </TableBody>
        </TableMui>
    </TableScroller>
}

export default TableComponent;
