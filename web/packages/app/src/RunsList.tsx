import * as React from 'react';
import styled from "@emotion/styled";
import {
  Link,
  Breadcrumbs as MuiBreadcrumbs,
  Card as MuiCard,
  CardContent as MuiCardContent,
  Divider as MuiDivider,
  Paper as MuiPaper,
  Typography,
  Stack,
  Alert,
} from "@mui/material";
import Chip from '@mui/material/Chip';
import { DataGrid, GridColDef, GridToolbar } from '@mui/x-data-grid';
import { spacing } from "@mui/system";

const Card = styled(MuiCard)(spacing);

const CardContent = styled(MuiCardContent)(spacing);

const Divider = styled(MuiDivider)(spacing);

const Breadcrumbs = styled(MuiBreadcrumbs)(spacing);

const Paper = styled(MuiPaper)(spacing);

const columns: GridColDef[] = [
  { field: 'id', headerName: 'Run ID', width: 90 },
  {
    field: 'createdAt',
    headerName: 'Created at',
    editable: false,
    flex: 1,
  },
  {
    field: 'blockName',
    headerName: 'Name',
    editable: false,
    flex: 1,
    renderCell: (props) => {
      return (
        <React.Fragment>
          <Link href="localhost:3000/">{props.row.blockName}</Link>
        </React.Fragment>
      );
    }
  },
  {
    field: 'tags',
    headerName: 'Tags',
    editable: false,
    flex: 1,
    renderCell: (props) => {
      return (
        <React.Fragment>
          <Stack direction="row">
            {props.row.tags.map((tagName: string, index: number) =>
              <React.Fragment key={index}>
                <Chip label={tagName} color="secondary" variant="outlined"/>
              </React.Fragment>
            )}
          </Stack>
        </React.Fragment>
      );
    }
  },
  {
    field: 'status',
    headerName: 'Status',
    description: 'This column has a value getter and is not sortable.',
    flex: 1,
    renderCell: (props: any) => {
      if (props.row.status === 'success') {
        return (
          <React.Fragment>
            <Alert variant="outlined" severity="success">
              Completed
            </Alert>
          </React.Fragment>
        );
      } else {
        return (
          <React.Fragment>
            <Alert variant="outlined" severity="error">
              Failed
            </Alert>
          </React.Fragment>
        );
      }
    }
  },
];

function createData(
  id: number,
  createdAt: string,
  blockName: string,
  tags: Array<any>,
  status: string
) {
  return { id, createdAt, blockName, tags, status };
}

const rows = [
  createData(
    0,
    '16 Mar, 2019',
    'Auto Featurization',
    ['experiment-blahsd', 'random-tag'],
    'success'
  ),
  createData(
    1,
    '16 Mar, 2019',
    'Train model',
    ['experiment-bler', 'randfdsf'],
    'success'
  ),
  createData(
    2,
    '16 Mar, 2019',
    'Train model',
    ['experiment-bler', '2daf-tags', 'dadceef'],
    'failed'
  ),
  createData(
    3,
    '15 Mar, 2019',
    'Evaluate model',
    ['ddasgfa'],
    'success'
  ),
];

export default function RunsList() {
  return (
    <Card mb={6}>
      <CardContent pb={1}>
        <Typography variant="h6" gutterBottom>
          Runs
        </Typography>
      </CardContent>
      <Paper>
        <div style={{ height: 400, width: "100%" }}>
          <DataGrid
            rowsPerPageOptions={[5, 10, 25]}
            rows={rows}
            columns={columns}
            pageSize={5}
            checkboxSelection
            components={{ Toolbar: GridToolbar }}
          />
        </div>
      </Paper>
    </Card>
  );
}
