import React from "react";
import styled from "@emotion/styled";

import {
  Grid,
  List,
  ListItemText as MuiListItemText,
  ListItemButtonProps as MuiListItemButtonProps,
  ListItemButton as MuiListItemButton,
} from "@mui/material";

interface ListItemButtonProps extends MuiListItemButtonProps {
  component?: string;
  href?: string;
}

const Wrapper = styled.div`
  padding: ${(props: any) => props.theme.spacing(0.25)}
    ${(props: any) => props.theme.spacing(4)};
  background: ${(props: any) => props.theme.footer.background};
  position: relative;
`;

const ListItemButton = styled(MuiListItemButton)<ListItemButtonProps>`
  display: inline-block;
  width: auto;
  padding-left: ${(props: any) => props.theme.spacing(2)};
  padding-right: ${(props: any) => props.theme.spacing(2)};

  &,
  &:hover,
  &:active {
    color: #ff0000;
  }
`;

const ListItemText = styled(MuiListItemText)`
  span {
    color: ${(props: any) => props.theme.footer.color};
  }
`;

function Footer() {
  return (
    <Wrapper>
      <Grid container spacing={0}>
        <Grid
          sx={{ display: { xs: "none", md: "block" } }}
          container
          item
          xs={12}
          md={6}
        >
          <List>
            <ListItemButton component="a" href="#">
              <ListItemText primary="Documentation" />
            </ListItemButton>
            <ListItemButton component="a" href="#">
              <ListItemText primary="Github" />
            </ListItemButton>
            <ListItemButton component="a" href="#">
              <ListItemText primary="Discord" />
            </ListItemButton>
          </List>
        </Grid>
      </Grid>
    </Wrapper>
  );
}

export default Footer;