import * as React from "react";
import styled from "@emotion/styled";
import {
  Link,
  Card as MuiCard,
  CardContent as MuiCardContent,
  Paper as MuiPaper,
  Typography,
  Stack,
  Alert as MuiAlert,
  Chip as MuiChip,
} from "@mui/material";
import { DataGrid, GridColDef, GridToolbar } from "@mui/x-data-grid";
import { spacing, sizing } from "@mui/system";

const Card = styled(MuiCard)(spacing);

const CardContent = styled(MuiCardContent)(spacing);

const Paper = styled(MuiPaper)(spacing);

const Chip = styled(MuiChip)(spacing);

const Alert = styled(MuiAlert)(sizing);

const columns: GridColDef[] = [
  { field: "id", headerName: "Run ID", width: 90 },
  {
    field: "createdAt",
    headerName: "Created at",
    editable: false,
    flex: 1,
  },
  {
    field: "blockName",
    headerName: "Name",
    editable: false,
    flex: 1,
    renderCell: (props) => {
      return (
        <React.Fragment>
          <Link href="/">{props.row.blockName}</Link>
        </React.Fragment>
      );
    }
  },
  {
    field: "tags",
    headerName: "Tags",
    editable: false,
    flex: 1,
    renderCell: (props) => {
      return (
        <React.Fragment>
          <Stack direction="row">
            {props.row.tags.map((tagName: string, index: number) =>
              <React.Fragment key={index}>
                <Chip label={tagName} marginRight={"5px"}/>
              </React.Fragment>
            )}
          </Stack>
        </React.Fragment>
      );
    }
  },
  {
    field: "status",
    headerName: "Status",
    description: "This column has a value getter and is not sortable.",
    flex: 1,
    renderCell: (props: any) => {
      if (props.row.status === "success") {
        return (
          <React.Fragment>
            <Alert severity="success" width={"100%"}>
              Completed
            </Alert>
          </React.Fragment>
        );
      } else {
        return (
          <React.Fragment>
            <Alert severity="error" width={"100%"}>
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
    "16 Mar, 2019",
    "Auto Featurization",
    ["experiment-blahsd", "random-tag"],
    "success"
  ),
  createData(
    1,
    "16 Mar, 2019",
    "Train model",
    ["experiment-bler", "randfdsf"],
    "success"
  ),
  createData(
    2,
    "16 Mar, 2019",
    "Train model",
    ["experiment-bler", "2daf-tags", "dadceef"],
    "failed"
  ),
  createData(
    3,
    "15 Mar, 2019",
    "Evaluate model",
    ["ddasgfa"],
    "success"
  ),
];

export default function RunList() {
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
