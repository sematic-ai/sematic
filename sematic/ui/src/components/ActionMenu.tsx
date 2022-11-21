import { KeyboardArrowDown } from "@mui/icons-material";
import { Box, Button, Chip, Menu, Typography, useTheme } from "@mui/material";
import React, { MouseEvent, useState } from "react";

export function ActionMenuItem(props: {
  title: string;
  enabled?: boolean;
  onClick?: () => void;
  titleColor?: string;
  children?: any;
  handleClose?: () => void;
  beta?: boolean;
  soon?: boolean;
}) {
  const theme = useTheme();
  const {
    title,
    enabled = true,
    titleColor = theme.palette.primary.main,
    beta = false,
    soon = false,
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
      <Box sx={{ display: "grid", gridTemplateColumns: "1fr auto" }}>
        <Box sx={{ gridColumn: 1 }}>
          <Typography
            sx={{
              color: titleColor,
              display: "block",
              fontWeight: "inherit",
            }}
          >
            {title}
          </Typography>
        </Box>
        <Box sx={{ gridColumn: 2 }}>
          {beta && (
            <Chip
              label="beta"
              size="small"
              color="warning"
              variant="outlined"
            />
          )}
          {soon && (
            <Chip
              label="coming soon"
              size="small"
              color="info"
              variant="outlined"
            />
          )}
        </Box>
      </Box>
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
