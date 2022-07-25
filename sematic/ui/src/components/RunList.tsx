import Alert from "@mui/material/Alert";
import Table from "@mui/material/Table";
import TableContainer from "@mui/material/TableContainer";
import TableBody from "@mui/material/TableBody";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import { useState, useEffect, useCallback, useContext } from "react";
import TablePagination from "@mui/material/TablePagination";
import TableFooter from "@mui/material/TableFooter";
import { RunListPayload } from "../Payloads";
import Loading from "./Loading";
import { Run } from "../Models";
import { fetchJSON } from "../utils";
import { UserContext } from "..";

const defaultPageSize = 10;

export type RunFilterType = {
  [k: string]: Array<{
    [v: string]: { [vv: string]: string | number | null };
  }>;
};

type RunListProps = {
  columns: Array<string>;
  children: Function;
  groupBy?: string;
  filters?: RunFilterType;
  pageSize?: number;
  size?: "small" | "medium" | undefined;
  emptyAlert?: string;
  onRunsLoaded?: (runs: Run[]) => void;
  triggerRefresh?: (refreshCallback: () => void) => void;
};

export function RunList(props: RunListProps) {
  let { triggerRefresh } = props;
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [pages, setPages] = useState<Array<RunListPayload>>([]);
  const [currentPage, setPage] = useState(0);

  const { user } = useContext(UserContext);

  let pageSize = props.pageSize || defaultPageSize;

  const refreshCallback = useCallback(() => {
    setPages([]);
    setPage(0);
  }, [setPages, setPage]);

  useEffect(() => {
    if (triggerRefresh !== undefined) {
      triggerRefresh(refreshCallback);
    }
  }, [triggerRefresh]);

  useEffect(() => {
    if (currentPage <= pages.length - 1) {
      return;
    }

    let url = "/api/v1/runs?limit=" + pageSize;

    if (pages.length > 0) {
      let cursor = pages[pages.length - 1].next_cursor || "";
      url = url + "&cursor=" + cursor;
    }

    if (props.groupBy) {
      url = url + "&group_by=" + props.groupBy;
    }

    if (props.filters) {
      let filters = JSON.stringify(props.filters);
      url += "&filters=" + filters;
    }

    fetchJSON({
      url: url,
      callback: (result: RunListPayload) => {
        setPages(pages.concat(result));
        if (props.onRunsLoaded !== undefined) {
          props.onRunsLoaded(result.content);
        }
      },
      setError: setError,
      setIsLoaded: setIsLoaded,
      apiKey: user?.api_key,
    });
  }, [currentPage, pages, props.filters, props.groupBy, pageSize]);

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
