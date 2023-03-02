import Alert from "@mui/material/Alert";
import Table from "@mui/material/Table";
import TableContainer from "@mui/material/TableContainer";
import TableBody from "@mui/material/TableBody";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import { useState, useEffect, useCallback, useMemo, ReactNode } from "react";
import TablePagination from "@mui/material/TablePagination";
import TableFooter from "@mui/material/TableFooter";
import { Filter, RunListPayload } from "../Payloads";
import Loading from "./Loading";
import { useFetchRunsFn } from "../hooks/pipelineHooks";
import useLatest from "react-use/lib/useLatest";
import usePreviousDistinct from "react-use/lib/usePreviousDistinct";
import { styled } from "@mui/system";
import { Run } from "src/Models";

const defaultPageSize = 10;

export interface RunListColumn {
  name: string;
  width: string;
  render: (run: Run) => ReactNode;
}

type RunListProps = {
  columns: Array<RunListColumn>;
  groupBy?: string;
  search?: string;
  filters?: Filter;
  pageSize?: number;
  size?: "small" | "medium" | undefined;
  emptyAlert?: string;
  triggerRefresh?: (refreshCallback: () => void) => void;
};



const StyledTableContainer = styled(TableContainer)`
  display: flex;
  flex-direction: column;
  height: 100%;

  & table {
    flex-shrink: 1;
  }
`;

const TBodyScroller = styled('div')`
  flex-grow: 1;
  overflow-y: auto;
`;

function TBodyRow(props: {
  run: Run;
  columns: Array<RunListColumn>;
}) {
  const { run, columns } = props;
  return <TableRow data-cy={"runlist-row"}>
    {columns.map((column, i) => <TableCell key={i} style={{width: column.width}}>
      {column.render(run)}
    </TableCell>)}
 </TableRow>;
}

export function RunList(props: RunListProps) {
  let { triggerRefresh, filters, groupBy, search, columns } = props;
  const [pages, setPages] = useState<Array<RunListPayload>>([]);
  const [currentPage, setPage] = useState(0);

  let pageSize = props.pageSize || defaultPageSize;

  const refreshCallback = useCallback(() => {
    setPages([]);
    setPage(0);
  }, [setPages, setPage]);

  useEffect(() => {
    if (triggerRefresh !== undefined) {
      triggerRefresh(refreshCallback);
    }
  }, [triggerRefresh, refreshCallback]);

  const queryParams = useMemo(() => {
    let queryParams: any = {
      limit: pageSize.toString(),
    }
    if (!!groupBy) {
      queryParams['group_by'] = groupBy;
    }
    if (!!search && search.length > 0) {
      queryParams['search'] = search;
    }
    return queryParams;
  }, [pageSize, groupBy, search]);

  const { isLoaded, error, load } = useFetchRunsFn(filters, queryParams);

  const loadCurrent = useLatest(load);

  useEffect(() => {
    // logic for turning to the next page which has not been seen
    if (currentPage <= pages.length - 1) {
      return;
    }

    (async () => {
      let params: any = undefined;

      if (pages.length > 0) {
        let cursor = pages.at(-1)!.next_cursor || "";
        params = { cursor };
      }

      const payload = await loadCurrent.current(params);

      setPages(pages.concat(payload));
    })().catch(console.error);
  }, [currentPage, pages, loadCurrent]);

  const prevSearch = usePreviousDistinct(search);

  useEffect(() => {
    // logic for updating search terms
    if (search === prevSearch) {
      return;
    }

    (async () => {
      const payload = await loadCurrent.current();

      setPages([payload]);
      setPage(0);
    })().catch(console.error);
  }, [search, prevSearch, loadCurrent]);

  let tableBody;
  let currentPayload = pages[currentPage];
  
  if (error || !isLoaded) {
    tableBody = (
      <TableBody>
        <TableRow>
          <TableCell colSpan={columns.length} align="center">
            <Loading error={error} isLoaded={isLoaded} />
          </TableCell>
        </TableRow>
      </TableBody>
    );
  } else if (currentPayload) {
    tableBody = (
      <TableBody>
        {currentPayload.content.length > 0 &&
          currentPayload.content.map(
            (run) => <TBodyRow run={run} columns={columns} key={run.id} />)}
        {currentPayload.content.length === 0 && (
          <TableRow>
            <TableCell colSpan={columns.length}>
              <Alert severity="info">{props.emptyAlert || "No runs."}</Alert>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    );
  }

  let totalCount =
    currentPage * pageSize + (currentPayload?.after_cursor_count || 0);
  let page = currentPage;
  if (!currentPayload?.after_cursor_count) {
    page = 0;
  }

  return (
    <StyledTableContainer data-cy={"RunList"}>
      <Table size={props.size} >
        <TableHead>
          <TableRow>
            {columns.map(({name, width}) => (
              <TableCell key={name} style={{width}}>{name}</TableCell>
            ))}
          </TableRow>
        </TableHead>
      </Table>
      <TBodyScroller>
        <Table>
          {tableBody}
        </Table>
      </TBodyScroller>
      <Table>
        <TableFooter>
          <TableRow>
            <TablePagination
              count={totalCount}
              page={page}
              onPageChange={(event, page) => setPage(page)}
              rowsPerPage={pageSize}
              rowsPerPageOptions={[pageSize]}
            />
          </TableRow>
        </TableFooter>
      </Table>
    </StyledTableContainer>
  );
}
