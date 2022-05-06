import React from "react";
import styled from "@emotion/styled";

import {
  Avatar,
  Breadcrumbs as MuiBreadcrumbs,
  Button,
  Card as MuiCard,
  CardActions,
  CardContent as MuiCardContent,
  CardMedia as MuiCardMedia,
  Chip as MuiChip,
  Divider as MuiDivider,
  Grid,
  Link,
  Typography as MuiTypography,
} from "@mui/material";
import { AvatarGroup as MuiAvatarGroup } from "@mui/material";
import { spacing, SpacingProps } from "@mui/system";

const Breadcrumbs = styled(MuiBreadcrumbs)(spacing);

const Card = styled(MuiCard)(spacing);

const CardContent = styled(MuiCardContent)`
  border-bottom: 1px solid ${(props:any) => props.theme.palette.grey[300]};
`;

const CardMedia = styled(MuiCardMedia)`
  height: 220px;
`;

const Divider = styled(MuiDivider)(spacing);

interface TypographyProps extends SpacingProps {
  component?: string;
}
const Typography = styled(MuiTypography)<TypographyProps>(spacing);

const Chip = styled(MuiChip)<{ color?: string }>`
  height: 20px;
  padding: 4px 0;
  font-size: 85%;
  background-color: ${(props:any) =>
    props.theme.palette[props.color ? props.color : "primary"].light};
  color: ${(props:any) => props.theme.palette.common.white};
  margin-bottom: ${(props:any) => props.theme.spacing(4)};
`;

const AvatarGroup = styled(MuiAvatarGroup)`
  margin-left: ${(props:any) => props.theme.spacing(2)};
`;

type ProjectProps = {
  image?: string;
  title: string;
  description: string;
  chip: JSX.Element;
};
const Project: React.FC<ProjectProps> = ({
  image,
  title,
  description,
  chip,
}) => {
  return (
    <Card>
      <CardContent>
        <Typography gutterBottom variant="h5" component="h2">
          {title}
        </Typography>

        {chip}

        <Typography mb={4} color="textSecondary" component="p">
          {description}
        </Typography>

      </CardContent>
      <CardActions>
        <Button size="small" color="primary">
          Run
        </Button>
      </CardActions>
    </Card>
  );
};

function Discover() {
  return (
    <React.Fragment>

      <Typography variant="h3" gutterBottom display="inline">
        Discover
      </Typography>

      <Divider my={6} />

      <Grid container spacing={6}>
        <Grid item xs={12} lg={6} xl={3}>
          <Project
            title="Featurizer"
            description="Processes DataFrames and outputs a set of features"
            chip={<Chip label="Structured Tabular Data" color="success" />}
          />
        </Grid>
        <Grid item xs={12} lg={6} xl={3}>
          <Project
            title="Image Augmentation"
            description="Takes in an Image and will augment the image with a number of key knobs that you want to tweak"
            chip={<Chip label="Images" color="warning" />}
          />
        </Grid>
        <Grid item xs={12} lg={6} xl={3}>
          <Project
            title="Geometric Transformations"
            description="Randomly flip, crop, rotate or translate images"
            chip={<Chip label="Images" color="success" />}
          />
        </Grid>
        <Grid item xs={12} lg={6} xl={3}>
          <Project
            title="Color Space Transformations"
            description="Change RBG color channels, intensify any color"
            chip={<Chip label="Images" color="warning" />}
          />
        </Grid>
        <Grid item xs={12} lg={6} xl={3}>
          <Project
            title="Kernel filters"
            description="Sharpen or blur an image"
            chip={<Chip label="Images" color="warning" />}
          />
        </Grid>
        <Grid item xs={12} lg={6} xl={3}>
          <Project
            title="Noise injection"
            description="Inject random noise"
            chip={<Chip label="Audio" color="error" />}
          />
        </Grid>
      </Grid>
    </React.Fragment>
  );
}

export default Discover;
