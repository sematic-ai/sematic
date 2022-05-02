import React from "react";
import styled from "@emotion/styled";
import { css } from "@emotion/react";
import ReactPerfectScrollbar from "react-perfect-scrollbar";
import { List } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";

import { SidebarItemsType } from "../../types/sidebar";
import SidebarNavSection from "./SidebarNavSection";

import "../../vendor/perfect-scrollbar.css";

const baseScrollbar = (props: any) => css`
  background-color: ${props.theme.sidebar.background};
  border-right: 1px solid rgba(0, 0, 0, 0.12);
  flex-grow: 1;
`;

const Scrollbar = styled.div`
  ${baseScrollbar}
`;

const PerfectScrollbar = styled(ReactPerfectScrollbar)`
  ${baseScrollbar}
`;

const Items = styled.div`
  padding-top: ${(props: any) => props.theme.spacing(2.5)};
  padding-bottom: ${(props: any) => props.theme.spacing(2.5)};
`;

type SidebarNavProps = {
  items: {
    title: string;
    pages: SidebarItemsType[];
  }[];
};

const SidebarNavigation: React.FC<SidebarNavProps> = ({ items }) => {
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.up("md"));
  const ScrollbarComponent = (
    matches ? PerfectScrollbar : Scrollbar
  ) as React.ElementType;

  return (
    <ScrollbarComponent>
      <List disablePadding>
        <Items>
          {items &&
            items.map((item) => (
              <SidebarNavSection
                component="div"
                key={item.title}
                pages={item.pages}
                title={item.title}
              />
            ))}
        </Items>
      </List>
    </ScrollbarComponent>
  );
};

export default SidebarNavigation;