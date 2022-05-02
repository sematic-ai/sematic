import React from "react";
import styled from "@emotion/styled";

import { spacing } from "@mui/system";

import {
  Box as MuiBox,
  Chip,
  Drawer as MuiDrawer,
  ListItemButton,
} from "@mui/material";

// import { ReactComponent as Logo } from "../../vendor/logo.svg";
import { SidebarItemsType } from "../../types/sidebar";
// import Footer from "./SidebarFooter";
import SidebarNavigation from "./SidebarNavigation";

const Box = styled(MuiBox)(spacing);

const Drawer = styled(MuiDrawer)`
  border-right: 0;

  > div {
    border-right: 0;
  }
`;

const Brand = styled(ListItemButton)<{
  component?: React.ReactNode;
  to?: string;
}>`
  font-size: ${(props: any) => props.theme.typography.h5.fontSize};
  font-weight: ${(props: any) => props.theme.typography.fontWeightMedium};
  color: ${(props: any) => props.theme.sidebar.header.color};
  background-color: ${(props: any) => props.theme.sidebar.header.background};
  font-family: ${(props: any) => props.theme.typography.fontFamily};
  min-height: 56px;
  padding-left: ${(props: any) => props.theme.spacing(6)};
  padding-right: ${(props: any) => props.theme.spacing(6)};
  justify-content: center;
  cursor: pointer;
  flex-grow: 0;

  ${(props: any) => props.theme.breakpoints.up("sm")} {
    min-height: 64px;
  }

  &:hover {
    background-color: ${(props: any) => props.theme.sidebar.header.background};
  }
`;

export type SidebarProps = {
  PaperProps: {
    style: {
      width: number;
    };
  };
  variant?: "permanent" | "persistent" | "temporary";
  open?: boolean;
  onClose?: () => void;
  items: {
    title: string;
    pages: SidebarItemsType[];
  }[];
  showFooter?: boolean;
};

const Sidebar: React.FC<SidebarProps> = ({
  items,
  showFooter = true,
  ...rest
}) => {
  return (
    <Drawer variant="permanent" {...rest}>
        <SidebarNavigation items={items} />
    </Drawer>
  );
};

export default Sidebar;
