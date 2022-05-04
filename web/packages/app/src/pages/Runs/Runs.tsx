import * as React from "react";
import styled from "@emotion/styled";
import {
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

import { Link } from "react-router-dom";

import UniqueColorAssigner from "../../helpers/UniqueColorAssigner";

import runData from "../../fixtures/runData";

// Styling wrappers, to help us style components declaratively using props.
const Card = styled(MuiCard)(spacing);

const CardContent = styled(MuiCardContent)(spacing);

const Paper = styled(MuiPaper)(spacing);

const Chip = styled(MuiChip)(spacing);

const Alert = styled(MuiAlert)(sizing);

// Define each grid column. @TODO: move this into it's own file, it's getting messy here.
const columns: GridColDef[] = [
  { field: "id", headerName: "Run ID", width: 90 },
  {
    field: "createdAt",
    headerName: "Created at",
    description: "When the run was created.",
    editable: false,
    width: 150,
    resizable: true,
  },
  {
    field: "name",
    headerName: "Name",
    description: "The name of the @glow.func decorator.",
    editable: false,
    width: 200,
    resizable: true,
    renderCell: (props) => {
      return (
        <React.Fragment>
          <Link to={`/runs/${props.row.id}`}>{props.row.name}</Link>
        </React.Fragment>
      );
    }
  },
  {
    field: "tags",
    headerName: "Tags",
    description: "Tags are user defined when triggering a run.",
    editable: false,
    flex: 1,
    resizable: true,
    renderCell: (props) => {
      return (
        <React.Fragment>
          <Stack direction="row">
            {props.row.tags.map((tagObject: any, index: number) =>
              <React.Fragment key={index}>
                <Chip size="small" label={tagObject.value} marginRight={"5px"} sx={{bgcolor: tagObject.color}} />
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
    description: "The status of the run.",
    width: 300,
    resizable: true,
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

export default function RunList() {
  // Sets the inital state of the data grid.
  // We want to only show runs that have succeeded by default.
  const initialState = {
    filter: {
      filterModel: {
        items: [{ columnField: "status", operatorValue: "equals", value: "success" }],
      }
    }
  };

  // We want to assign unique colors to each unique tag.
  // Note that we grab the fixture data here which provides us mocks, we will eventually move
  // this to a service call to grab data from the DB.
  const tagsWithUniqueColors = UniqueColorAssigner(runData.map((row) => row.tags));
  const rowsWithTagUniqueColors = runData.map((row) => {
    // We don't want to mutate the original data we assign an new object.
    const newRow = { ...row };
    newRow.tags = row.tags.map((tag) => {
      return {
        ...tagsWithUniqueColors[tag],
      }
    });
    return newRow;
  });

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
            initialState={initialState}
            rowsPerPageOptions={[5, 10, 25]}
            rows={rowsWithTagUniqueColors}
            columns={columns}
            pageSize={5}
            checkboxSelection
            components={{ Toolbar: GridToolbar }}
            sx={{border: "0px"}}
          />
        </div>
      </Paper>
    </Card>
  );
}
