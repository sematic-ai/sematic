import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PendingIcon from "@mui/icons-material/Pending";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";
import ErrorIcon from "@mui/icons-material/Error";
import Tooltip from "@mui/material/Tooltip";
import { ReactElement } from "react";

function RunStateChip(props: { state?: string }) {
  const state = props.state || "undefined";
  let statusChip: ReactElement = <HelpOutlineOutlinedIcon color="disabled" />;
  let toolTipMessage = state ? state : "UNDEFINED";

  if (state === "RESOLVED") {
    toolTipMessage = "Succeeded";
    statusChip = <CheckCircleIcon color="success" />;
  }

  if (["SCHEDULED", "RAN"].includes(state)) {
    toolTipMessage = "Running";
    statusChip = <PendingIcon color="primary" />;
  }

  if (["FAILED", "NESTED_FAILED"].includes(state)) {
    toolTipMessage = "Failed";
    statusChip = <ErrorIcon color="error" />;
  }

  return (
    <Tooltip title={toolTipMessage} placement="right">
      {statusChip}
    </Tooltip>
  );
}

export default RunStateChip;
