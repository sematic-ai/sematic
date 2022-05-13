import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CircleOutlinedIcon from "@mui/icons-material/CircleOutlined";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";
import Tooltip from "@mui/material/Tooltip";
import { ReactElement } from "react";

function RunStateChip(props: { state?: string }) {
  const state = props.state || "undefined";
  let statusChip: ReactElement = <HelpOutlineOutlinedIcon color="disabled" />;

  if (state === "RESOLVED") {
    statusChip = <CheckCircleIcon color="success" />;
  }

  if (state === "SCHEDULED") {
    statusChip = <CircleOutlinedIcon color="primary" />;
  }

  return (
    <Tooltip title={state} placement="right">
      {statusChip}
    </Tooltip>
  );
}

export default RunStateChip;
