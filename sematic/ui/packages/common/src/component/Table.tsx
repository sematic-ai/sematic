import styled from "@emotion/styled";
import TableMui from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { Table, flexRender } from "@tanstack/react-table";
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
    padding-left: ${theme.spacing(5)};
`;

const StyledHeader = styled(TableHead, {
    shouldForwardProp: (prop) => prop !== 'stickyHeader'
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
`;

const TableDataRow = styled(TableRow)`
    height: 50px;

    & td {
        padding-left: 0;
        padding-right: ${theme.spacing(2.5)};
        padding-top: 0;
        padding-bottom: 0;
        border-bottom: none;

        &:last-of-type {
            padding-right: 0
        };
    }
`;

interface TableComponentProps<T> {
    table: Table<T>;
    stickyHeader?: boolean;
}

const TableComponent = <T,>(props: TableComponentProps<T>) => {
    const { table, stickyHeader = true } = props;
    const { getLeafHeaders } = table;

    return <TableScroller>
        <TableMui>
            <StyledHeader stickyHeader={stickyHeader}>
                <TableRow>
                    {getLeafHeaders().map(header =>
                        <th key={header.id} style={(header.column.columnDef.meta! as any).columnStyles}>
                            {flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                            )}
                        </th>)}
                </TableRow>
            </StyledHeader>
            <TableBody>
                {table.getRowModel().rows.map(row => (
                    <TableDataRow key={row.id}>
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
