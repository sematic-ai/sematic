import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PendingIcon from "@mui/icons-material/Pending";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";
import CircleOutlinedIcon from "@mui/icons-material/CircleOutlined";
import ErrorIcon from "@mui/icons-material/Error";
import Tooltip from "@mui/material/Tooltip";
import { ReactElement } from "react";
import {
  CheckCircleOutline,
  ErrorOutlined,
  ErrorOutlineOutlined,
  PendingOutlined,
} from "@mui/icons-material";
import { Box, Typography, useTheme } from "@mui/material";

function Pin(props: { color: any; size?: string }) {
  const { color, size } = props;
  return (
    <span
      style={{
        height: size || "7px",
        width: size || "7px",
        backgroundColor: color,
        borderRadius: "50%",
        display: "inline-block",
        marginRight: "5px",
      }}
    ></span>
  );
}

function RunStateChip(props: { state?: string; variant?: string }) {
  const state = props.state || "undefined";
  const variant = props.variant || "mini";
  let statusChip: ReactElement = <HelpOutlineOutlinedIcon color="disabled" />;
  let toolTipMessage = state ? state : "UNDEFINED";
  const theme = useTheme();
  let color = theme.palette.grey[300];

  if (state === "RESOLVED") {
    toolTipMessage = "Succeeded";
    color = theme.palette.success.light;
    //statusChip = <CheckCircleOutline color="success" fontSize="small" />;
  }

  if (["SCHEDULED", "RAN"].includes(state)) {
    toolTipMessage = "Running";
    color = theme.palette.primary.light;
    //statusChip = <PendingOutlined color="primary" fontSize="small" />;
  }

  if (["FAILED", "NESTED_FAILED"].includes(state)) {
    toolTipMessage = "Failed";
    color = theme.palette.error.light;
    //statusChip = <ErrorOutlineOutlined color="error" fontSize="small" />;
  }

  if (state === "CREATED") {
    toolTipMessage = "Created";
    //statusChip = <CircleOutlinedIcon color="disabled" fontSize="small" />;
  }

  if (variant === "mini") {
    return <Pin color={color} />;
  }

  return (
    <Typography component="span" sx={{ display: "flex", alignItems: "center" }}>
      <Pin color={color} />
      {variant === "full" && <Box>{toolTipMessage}</Box>}
    </Typography>
  );

  return (
    <Tooltip title={toolTipMessage} placement="bottom-start">
      <Pin color={color} />
    </Tooltip>
  );
}

export default RunStateChip;
