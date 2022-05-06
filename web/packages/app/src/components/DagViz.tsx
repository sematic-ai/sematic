import React, { useState } from "react";

import styled from "@emotion/styled";

import {
    Breadcrumbs as MuiBreadcrumbs,
    Button as MuiButton,
    Card as MuiCard,
    CardMedia as MuiCardMedia,
    Divider as MuiDivider,
  } from "@mui/material";

import { spacing } from "@mui/system";

const Card = styled(MuiCard)(spacing);

const Button = styled(MuiButton)(spacing);

const Divider = styled(MuiDivider)(spacing);

const Breadcrumbs = styled(MuiBreadcrumbs)(spacing);

const CardMedia = styled(MuiCardMedia)`
  height: 220px;
`;

const orgChart = {
    name: 'CEO'
};

function DagViz() {
    return (
        <div id="treeWrapper" style={{ width: '50em', height: '20em' }}>
            
        </div>
    );
}

export default DagViz;