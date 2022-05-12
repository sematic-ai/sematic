import Alert from '@mui/material/Alert';
import Table from '@mui/material/Table';
import TableContainer from '@mui/material/TableContainer';
import TableBody from '@mui/material/TableBody';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import Typography from "@mui/material/Typography";
import CircularProgress from '@mui/material/CircularProgress';
import { useState, useEffect, ReactElement } from 'react';
import { Run } from '../Models';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CircleOutlinedIcon from '@mui/icons-material/CircleOutlined';
import HelpOutlineOutlinedIcon from '@mui/icons-material/HelpOutlineOutlined';
import Tooltip from '@mui/material/Tooltip';
import TablePagination from '@mui/material/TablePagination';
import Link from '@mui/material/Link';
import TableFooter from '@mui/material/TableFooter';
import TimeAgo from 'javascript-time-ago';
import ReactTimeAgo from 'react-time-ago';
import en from 'javascript-time-ago/locale/en.json';


TimeAgo.addDefaultLocale(en)


type RunListPayload = {
  current_page_url: string,
  next_page_url: string | undefined,
  limit: number,
  next_cursor: string | undefined,
  after_cursor_count: number,
  content: Array<Run>,
}


function RunStateChip(props: {state: string}) {
  const state = props.state;
  let statusChip: ReactElement = <HelpOutlineOutlinedIcon color="disabled"></HelpOutlineOutlinedIcon>;
  
  if (state === "RESOLVED") {
    statusChip = <CheckCircleIcon color="success"></CheckCircleIcon>;
  }
  
  if (state === "SCHEDULED") {
    statusChip = <CircleOutlinedIcon color="primary"></CircleOutlinedIcon>;
  }
  
  return <Tooltip title={state} placement="right">
    {statusChip}
  </Tooltip>;
}


const pageSize = 10;


function RunList() {
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [pages, setPages] = useState<Array<RunListPayload>>([]);
  const [currentPage, setPage] = useState(0);

  useEffect(() => {
    if (currentPage <= pages.length - 1) {
      return;
    }
    let cursor = "";
    if (pages.length > 0) {
      cursor = pages[pages.length - 1].next_cursor || "";
    }
    fetch("/api/v1/runs?limit=" + pageSize + "&cursor=" + cursor)
      .then(res => res.json())
      .then(
        (result) => {
          setPages(pages.concat(result));
          setIsLoaded(true);
        },
        (error) => {
          setIsLoaded(true);
          setError(error);
        }
      )
  }, [currentPage, pages])

  let tableBody;
  let currentPayload = pages[currentPage];

  if (error) {
    tableBody = <TableBody>
      <TableRow>
      <TableCell colSpan={4}>
        <Alert severity="error">API Error: {error.message}</Alert>
        </TableCell>
      </TableRow>
      </TableBody>
      ;
  } else if (!isLoaded) {
    tableBody = <TableBody>
      <TableRow>
        <TableCell colSpan={4} align="center">
          <CircularProgress sx={{marginY: 5}}></CircularProgress>
        </TableCell>
      </TableRow>
    </TableBody>;
  } else if (currentPayload) {
    tableBody = (
    <TableBody>
        {
          currentPayload.content.map(run => (
            <TableRow key={run.id}>
              <TableCell><code>{ run.id.substring(0,8) }</code></TableCell>
              <TableCell>
                <Link href={"/runs/" + run.id} underline="hover">
                  {run.name}
                </Link>
                <Typography fontSize="small" color="GrayText">
                  <code>
                    {run.calculator_path}
                    </code>
                </Typography>
              </TableCell>
              <TableCell>
                {<ReactTimeAgo date={new Date(run.created_at)} locale="en-US" />}
                <Typography fontSize='small' color='GrayText'>
                  {(new Date(run.created_at)).toLocaleString()}
                  </Typography>
              </TableCell>
              <TableCell><RunStateChip state={run.future_state} /></TableCell>
            </TableRow>
          ))
        }
        </TableBody>
    );
  }

  let totalCount = currentPage * pageSize + (currentPayload?.after_cursor_count || 0);
  let page = currentPage;
  if (!currentPayload?.after_cursor_count) {
    page = 0;
  }

  return (<>
    <Typography variant="h4" component="h2">Run list</Typography>
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>Time</TableCell>
            <TableCell>Status</TableCell>
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
  </>);
}

export default RunList;