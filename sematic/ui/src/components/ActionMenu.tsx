import { KeyboardArrowDown } from "@mui/icons-material";
import { Box, Button, Menu, Typography, useTheme } from "@mui/material";
import React, { MouseEvent, useState } from "react";

export function ActionMenuItem(props: {
  title: string;
  enabled?: boolean;
  onClick?: () => void;
  titleColor?: string;
  children?: any;
  handleClose?: () => void;
}) {
  const theme = useTheme();
  const {
    title,
    enabled = true,
    titleColor = theme.palette.primary.main,
    children,
    onClick,
    handleClose,
  } = props;

  return (
    <Button
      sx={{
        display: "block",
        textAlign: "left",
        px: 5,
        py: 2,
        width: "100%",
        opacity: enabled ? 1 : 0.5,
      }}
      disabled={!enabled}
      onClick={() => {
        handleClose && handleClose();
        onClick && onClick();
      }}
    >
      <Typography
        sx={{
          color: titleColor,
          display: "block",
          fontWeight: "inherit",
        }}
      >
        {title}
      </Typography>
      <Box sx={{ color: "GrayText" }}>{children}</Box>
    </Button>
  );
}

export function ActionMenu(props: { title: string; children?: any }) {
  const [anchorElement, setAnchorElement] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorElement);
  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    setAnchorElement(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorElement(null);
  };

  const { children, title } = props;

  const makeClosable = (element: React.ReactElement<any>) =>
    React.isValidElement(element)
      ? React.cloneElement(element as React.ReactElement<any>, {
          handleClose: handleClose,
          key: Math.random().toString(),
        })
      : element;

  let closableChildren = children;
  if (Array.isArray(children)) {
    closableChildren = children.map(makeClosable);
  } else {
    closableChildren = makeClosable(children);
  }

  return (
    <>
      <Button endIcon={<KeyboardArrowDown />} onClick={handleClick}>
        {title}
      </Button>
      <Menu
        id="basic-menu"
        anchorEl={anchorElement}
        open={open}
        onClose={handleClose}
      >
        {closableChildren}
      </Menu>
    </>
  );
}
