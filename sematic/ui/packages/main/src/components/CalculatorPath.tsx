import Typography from "@mui/material/Typography";

function CalculatorPath(props: { functionPath: string; component?: string }) {
  return (
    <Typography fontSize="small" color="GrayText" component="span">
      <code style={{ fontSize: 12, wordWrap: "break-word" }}>
        {props.functionPath}
      </code>
    </Typography>
  );
}

export default CalculatorPath;
