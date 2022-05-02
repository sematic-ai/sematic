import React from "react";
import styled from "@emotion/styled";

import { Typography } from "@mui/material";

import { SidebarItemsType } from "../../types/sidebar";
import SidebarNavList from "./SidebarNavList";

const Title = styled(Typography)`
  color: ${(props: any) => props.theme.sidebar.color};
  font-size: ${(props: any) => props.theme.typography.caption.fontSize};
  padding: ${(props: any) => props.theme.spacing(4)}
    ${(props: any) => props.theme.spacing(7)} ${(props: any) => props.theme.spacing(1)};
  opacity: 0.4;
  text-transform: uppercase;
  display: block;
`;

type SidebarNavSectionProps = {
  className?: Element;
  component?: React.ElementType;
  pages: SidebarItemsType[];
  title?: string;
};

const SidebarNavSection: React.FC<SidebarNavSectionProps> = (props: any) => {
  const {
    title,
    pages,
    className,
    component: Component = "nav",
    ...rest
  } = props;

  return (
    <Component {...rest}>
      {title && <Title variant="subtitle2">{title}</Title>}
      <SidebarNavList pages={pages} depth={0} />
    </Component>
  );
};

export default SidebarNavSection;
