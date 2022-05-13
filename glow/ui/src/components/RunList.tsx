import Alert from "@mui/material/Alert";
import Table from "@mui/material/Table";
import TableContainer from "@mui/material/TableContainer";
import TableBody from "@mui/material/TableBody";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import CircularProgress from "@mui/material/CircularProgress";
import { useState, useEffect } from "react";
import TablePagination from "@mui/material/TablePagination";
import TableFooter from "@mui/material/TableFooter";
import { RunListPayload } from "../Payloads";

const pageSize = 10;

type RunListProps = {
  columns: Array<string>;
  children: Function;
  groupBy?: string;
  filters?: { [k: string]: { [v: string]: string | number | null } };
};

function RunList(props: RunListProps) {
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [pages, setPages] = useState<Array<RunListPayload>>([]);
  const [currentPage, setPage] = useState(0);

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

    fetch(url)
      .then((res) => res.json())
      .then(
        (result) => {
          setPages(pages.concat(result));
          setIsLoaded(true);
        },
        (error) => {
          setIsLoaded(true);
          setError(error);
        }
      );
  }, [currentPage, pages, props.filters, props.groupBy]);

  let tableBody;
  let currentPayload = pages[currentPage];

  if (error) {
    tableBody = (
      <TableBody>
        <TableRow>
          <TableCell colSpan={4}>
            <Alert severity="error">API Error: {error.message}</Alert>
          </TableCell>
        </TableRow>
      </TableBody>
    );
  } else if (!isLoaded) {
    tableBody = (
      <TableBody>
        <TableRow>
          <TableCell colSpan={4} align="center">
            <CircularProgress sx={{ marginY: 5 }}></CircularProgress>
          </TableCell>
        </TableRow>
      </TableBody>
    );
  } else if (currentPayload) {
    tableBody = (
      <TableBody>
        {currentPayload.content.map((run) => props.children(run))}
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
        <Table>
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

export default RunList;
