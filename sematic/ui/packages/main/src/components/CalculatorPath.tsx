import Typography from "@mui/material/Typography";

function CalculatorPath(props: { calculatorPath: string; component?: string }) {
  return (
    <Typography fontSize="small" color="GrayText" component="span">
      <code style={{ fontSize: 12, wordWrap: 'break-word' }}>{props.calculatorPath}</code>
    </Typography>
  );
}

export default CalculatorPath;
