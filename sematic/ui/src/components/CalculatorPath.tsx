import Typography from "@mui/material/Typography";

function CalculatorPath(props: { calculatorPath: string }) {
  return (
    <Typography fontSize="small" color="GrayText">
      <code style={{ fontSize: 11 }}>{props.calculatorPath}</code>
    </Typography>
  );
}

export default CalculatorPath;
