import * as React from 'react';
import Table from '@mui/material/Table';
import Title from './Title';
import Chip from '@mui/material/Chip';
import { DataGrid, GridColDef, GridValueGetterParams } from '@mui/x-data-grid';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 90 },
  {
    field: 'createdAt',
    headerName: 'Created at',
    editable: true,
    flex: 1,
  },
  {
    field: 'blockName',
    headerName: '📦 Name',
    editable: true,
    flex: 1,
    renderCell: (props) => {
      return (
        <React.Fragment>
          <a href="localhost:3000/">{props.row.blockName}</a>
        </React.Fragment>
      );
    }
  },
  {
    field: 'tags',
    headerName: 'Tags',
    editable: true,
    flex: 1,
    renderCell: (props) => {
      return (
        <React.Fragment>
          {props.row.tags.map((tagName: string, index: number) =>
            <React.Fragment key={index}>
              <Chip label={tagName}/>
            </React.Fragment>
          )}
        </React.Fragment>
      );
    }
  },
  {
    field: 'status',
    headerName: 'Status',
    description: 'This column has a value getter and is not sortable.',
    flex: 1,
  },
];

function createData(
  id: number,
  createdAt: string,
  blockName: string,
  tags: Array<any>,
) {
  return { id, createdAt, blockName, tags };
}

const rows = [
  createData(
    0,
    '16 Mar, 2019',
    'Auto Featurization',
    ['experiment-blahsd', 'random-tag'],
  ),
  createData(
    1,
    '16 Mar, 2019',
    'Train model',
    ['experiment-bler', 'randfdsf'],
  ),
  createData(
    2,
    '16 Mar, 2019',
    'Train model',
    ['experiment-bler', '2daf-tags', 'dadceef'],
  ),
  createData(
    3,
    '15 Mar, 2019',
    'Evaluate model',
    ['ddasgfa'],
  ),
];

export default function RunsList() {
  return (
    <React.Fragment>
      <Title>Glow Runs</Title>
      <Table size="small">
        <div style={{ height: 400, width: '100%' }}>
          <DataGrid
            rows={rows}
            columns={columns}
            pageSize={5}
            rowsPerPageOptions={[5]}
            checkboxSelection
            disableSelectionOnClick
          />
        </div>
      </Table>
    </React.Fragment>
  );
}
