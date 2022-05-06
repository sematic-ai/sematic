import React, { useState } from "react";

import styled from "@emotion/styled";

import {
    CardActions,
    CardContent,
    Breadcrumbs as MuiBreadcrumbs,
    Button as MuiButton,
    Card as MuiCard,
    CardMedia as MuiCardMedia,
    Divider as MuiDivider,
    Typography,
  } from "@mui/material";

import { spacing } from "@mui/system";

const Card = styled(MuiCard)(spacing);

const Button = styled(MuiButton)(spacing);

const Divider = styled(MuiDivider)(spacing);

const Breadcrumbs = styled(MuiBreadcrumbs)(spacing);

const CardMedia = styled(MuiCardMedia)`
  height: 220px;
`;

const artifactFixture = [{ name: 'Plotly Chart', type: 'Plotly' }, { name: 'Tensorboard', type: 'Url' }, { name: 'Table Data', type: 'Table Data' }];

function RunViz(props: any) {
    const [indexSelected, setIndexSelected] = useState(0);

    // For each artifact that's output, we'll create a button
    const artifactButtons = artifactFixture.map((artifact: any, index) => {
        const outlined = index === indexSelected ? "outlined" : "text"
        return (
            <Button size="small" color="secondary" variant={outlined} onClick={() => {setIndexSelected(index)}}>{artifact.name}</Button>
        );
    });

    // We set the appropriate visualization depending on what type of artifact is selected
    const artifactSelected = artifactFixture[indexSelected];

    let viz = "";
    
    if (artifactSelected.type === 'Url') {
        viz = "its a url..";
    } else if (artifactSelected.type === 'Plotly') {
        viz = "its a plotly visualization";
    } else if (artifactSelected.type === 'Table Data') {
        viz = "its a table view" 
    }

    return (
        <Card mb={6}>
            <CardContent>
                {viz}
                <Typography gutterBottom variant="h5" component="h2">
                    {artifactSelected.name}
                </Typography>
                <Typography component="p">
                    {artifactSelected.name}
                </Typography>
            </CardContent>
            <CardActions>
                {artifactButtons}
            </CardActions>
      </Card>
    );
}

export default RunViz;