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
  let toolTipMessage = state ? state : "UNDEFINED";
  const theme = useTheme();
  let color = theme.palette.grey[300];

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

  if (variant === "mini") {
    return <Pin color={color} />;
  }

  return (
    <Typography component="span" sx={{ display: "flex", alignItems: "center" }}>
      <Pin color={color} />
      {variant === "full" && <Box>{toolTipMessage}</Box>}
    </Typography>
  );
}

export default RunStateChip;
