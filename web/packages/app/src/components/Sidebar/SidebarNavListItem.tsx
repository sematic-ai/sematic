import React, { forwardRef } from "react";
import styled from "@emotion/styled";
import { rgba, darken } from "polished";

import {
  Chip,
  Collapse,
  ListItemProps,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import { ExpandLess, ExpandMore } from "@mui/icons-material";

type ItemType = {
  activeclassname?: string;
  onClick?: () => void;
  to?: string;
  component?: any;
  depth: number;
};

const Item = styled(ListItemButton)<ItemType>`
  padding-top: ${(props: any) =>
    props.theme.spacing(props.depth && props.depth > 0 ? 2 : 3)};
  padding-bottom: ${(props: any) =>
    props.theme.spacing(props.depth && props.depth > 0 ? 2 : 3)};
  padding-left: ${(props: any) =>
    props.theme.spacing(props.depth && props.depth > 0 ? 14 : 8)};
  padding-right: ${(props: any) =>
    props.theme.spacing(props.depth && props.depth > 0 ? 4 : 7)};
  font-weight: ${(props: any) => props.theme.typography.fontWeightRegular};
  svg {
    color: ${(props: any) => props.theme.sidebar.color};
    font-size: 20px;
    width: 20px;
    height: 20px;
    opacity: 0.5;
  }
  &:hover {
    background: rgba(0, 0, 0, 0.08);
    color: ${(props: any) => props.theme.sidebar.color};
  }
  &.${(props: any) => props.activeclassname} {
    background-color: ${(props: any) =>
      darken(0.03, props.theme.sidebar.background)};
    span {
      color: ${(props: any) => props.theme.sidebar.color};
    }
  }
`;

type TitleType = {
  depth: number;
};

const Title = styled(ListItemText)<TitleType>`
  margin: 0;
  span {
    color: ${(props: any) =>
      rgba(
        props.theme.sidebar.color,
        props.depth && props.depth > 0 ? 0.7 : 1
      )};
    font-size: ${(props: any) => props.theme.typography.body1.fontSize}px;
    padding: 0 ${(props: any) => props.theme.spacing(4)};
  }
`;

const Badge = styled(Chip)`
  font-weight: ${(props: any) => props.theme.typography.fontWeightBold};
  height: 20px;
  position: absolute;
  right: 26px;
  top: 12px;
  background: ${(props: any) => props.theme.sidebar.badge.background};
  z-index: 1;
  span.MuiChip-label,
  span.MuiChip-label:hover {
    font-size: 11px;
    cursor: pointer;
    color: ${(props: any) => props.theme.sidebar.badge.color};
    padding-left: ${(props: any) => props.theme.spacing(2)};
    padding-right: ${(props: any) => props.theme.spacing(2)};
  }
`;

const ExpandLessIcon = styled(ExpandLess)`
  color: ${(props: any) => rgba(props.theme.sidebar.color, 0.5)};
`;

const ExpandMoreIcon = styled(ExpandMore)`
  color: ${(props: any) => rgba(props.theme.sidebar.color, 0.5)};
`;

type SidebarNavListItemProps = ListItemProps & {
  className?: string;
  depth: number;
  href: string;
  icon: React.FC<any>;
  badge?: string;
  open?: boolean;
  title: string;
};

const SidebarNavListItem: React.FC<SidebarNavListItemProps> = (props) => {
  const {
    title,
    href,
    depth = 0,
    children,
    icon: Icon,
    badge,
    open: openProp = false,
  } = props;

  const [open, setOpen] = React.useState(openProp);

  const handleToggle = () => {
    setOpen((state) => !state);
  };

  if (children) {
    return (
      <React.Fragment>
        <Item depth={depth} onClick={handleToggle}>
          {Icon && <Icon />}
          <Title depth={depth}>
            {title}
            {badge && <Badge label={badge} />}
          </Title>
          {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </Item>
        <Collapse in={open}>{children}</Collapse>
      </React.Fragment>
    );
  }

  return (
    <React.Fragment>
      <Item
        depth={depth}
        component={undefined}
        to={href}
        activeclassname="active"
      >
        {Icon && <Icon />}
        <Title depth={depth}>
          {title}
          {badge && <Badge label={badge} />}
        </Title>
      </Item>
    </React.Fragment>
  );
};

export default SidebarNavListItem;
