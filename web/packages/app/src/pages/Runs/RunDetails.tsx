import React from "react";

import {
    Card as MuiCard,
    CardContent as MuiCardContent,
    Paper as MuiPaper,
    Typography,
  } from "@mui/material";

import styled from "@emotion/styled";

import { spacing } from "@mui/system";

import RunViz from "../../components/Run/RunViz";
import DagViz from "../../components/DagViz";

const Card = styled(MuiCard)(spacing);

const CardContent = styled(MuiCardContent)(spacing);

const Paper = styled(MuiPaper)(spacing);

function RunDetails() {
    return (
      <div>
        <Card mb={6}>
          <CardContent pb={1}>
            <Typography variant="h6" gutterBottom>
              Run Details
            </Typography>
          </CardContent>
          <Paper>
            <div style={{ width: "100%" }}>
              <RunViz />
            </div>
          </Paper>
        </Card>
        <Card mb={6} style={{ height: "400px" }}>
          <DagViz />
        </Card>
      </div>
    );
}

export default RunDetails;