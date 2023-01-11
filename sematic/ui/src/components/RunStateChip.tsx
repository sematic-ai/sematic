import { Box, Tooltip, Typography, useTheme } from "@mui/material";
import React from "react";

const Pin = React.forwardRef<HTMLDivElement, { color: any; hollow?: boolean }>(
  (props, ref) => {
    const { color, hollow, ...otherProps } = props;
    return (
      <div
        ref={ref}
        {...otherProps}
        style={{
          height: "7px",
          width: "7px",
          backgroundColor: hollow === true ? null : color,
          borderColor: color,
          borderWidth: "1px",
          borderStyle: "solid",
          borderRadius: "50%",
          display: "inline-block",
          marginRight: "5px",
        }}
      ></div>
    );
  }
);

function RunStateChip(props: { state?: string; variant?: string }) {
  const state = props.state || "undefined";
  const variant = props.variant || "mini";
  let toolTipMessage = state ? state : "UNKNOWN";
  const theme = useTheme();
  let color = theme.palette.grey[300];
  let hollow = false;

  if (state === "RESOLVED") {
    toolTipMessage = "Succeeded";
    color = theme.palette.success.light;
  }

  if (["SCHEDULED", "RAN"].includes(state)) {
    toolTipMessage = "Running";
    color = theme.palette.primary.light;
  }

  if (["FAILED", "NESTED_FAILED"].includes(state)) {
    toolTipMessage = "Failed";
    color = theme.palette.error.light;
  }

  if (state === "RETRYING") {
    toolTipMessage = "Retrying";
    color = theme.palette.warning.light;
  }

  if (state === "CREATED") {
    toolTipMessage = "Created";
  }

  if (state === "CANCELED") {
    toolTipMessage = "Canceled";
    color = theme.palette.error.light;
    hollow = true;
  }

  if (variant === "mini") {
    return (
      <Tooltip title={toolTipMessage}>
        <Pin color={color} hollow={hollow} />
      </Tooltip>
    );
  }

  return (
    <Tooltip title={toolTipMessage}>
      <Typography
        component="span"
        sx={{ display: "flex", alignItems: "center" }}
      >
        <Pin color={color} hollow={hollow} />
        {variant === "full" && <Box>{toolTipMessage}</Box>}
      </Typography>
    </Tooltip>
  );
}

export default RunStateChip;
