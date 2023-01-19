import Alert from "@mui/material/Alert";
import Table from "@mui/material/Table";
import TableContainer from "@mui/material/TableContainer";
import TableBody from "@mui/material/TableBody";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import { useState, useEffect, useCallback, useMemo } from "react";
import TablePagination from "@mui/material/TablePagination";
import TableFooter from "@mui/material/TableFooter";
import { Filter, RunListPayload } from "../Payloads";
import Loading from "./Loading";
import { Run } from "../Models";
import { useFetchRunsFn } from "../hooks/pipelineHooks";

const defaultPageSize = 10;

type RunListProps = {
  columns: Array<string>;
  children: Function;
  groupBy?: string;
  search?: string;
  filters?: Filter;
  pageSize?: number;
  size?: "small" | "medium" | undefined;
  emptyAlert?: string;
  onRunsLoaded?: (runs: Run[]) => void;
  triggerRefresh?: (refreshCallback: () => void) => void;
};

export function RunList(props: RunListProps) {
  let { triggerRefresh, filters, groupBy, onRunsLoaded, search } = props;
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
  }, [pageSize, groupBy]);

  const {isLoaded, error, load} = useFetchRunsFn(filters, queryParams);

  useEffect(() => {
    if (currentPage <= pages.length - 1) {
      return;
    }

    (async () => {
      let params: any = undefined;

      if (pages.length > 0) {
        let cursor = pages.at(-1)!.next_cursor || "";
        params = { cursor };
      }

      const payload = await load(params);

      setPages(pages.concat(payload));
      onRunsLoaded?.(payload.content);
    })().catch(console.error);
  }, [currentPage, pages, load, onRunsLoaded]);

  let tableBody;
  let currentPayload = pages[currentPage];

  if (error || !isLoaded) {
    tableBody = (
      <TableBody>
        <TableRow>
          <TableCell colSpan={props.columns.length} align="center">
            <Loading error={error} isLoaded={isLoaded} />
          </TableCell>
        </TableRow>
      </TableBody>
    );
  } else if (currentPayload) {
    tableBody = (
      <TableBody>
        {currentPayload.content.length > 0 &&
          currentPayload.content.map((run) => props.children(run))}
        {currentPayload.content.length === 0 && (
          <TableRow>
            <TableCell colSpan={props.columns.length}>
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
    <>
      <TableContainer>
        <Table size={props.size}>
          <TableHead>
            <TableRow>
              {props.columns.map((column) => (
                <TableCell key={column}>{column}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          {tableBody}
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
      </TableContainer>
    </>
  );
}
