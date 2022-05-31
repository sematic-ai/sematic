import {
  Alert,
  AlertTitle,
  lighten,
  PaletteColor,
  Theme,
  useTheme,
} from "@mui/material";
import { Handle, NodeProps, Position } from "react-flow-renderer";
import { Run } from "../Models";
import CalculatorPath from "./CalculatorPath";
import RunStateChip from "./RunStateChip";

function getShortCalculatorPath(calculatorPath: string): string {
  const calculatorPathParts = calculatorPath.split(".");
  let shortCalculatorPath = calculatorPathParts[calculatorPathParts.length - 1];
  if (calculatorPathParts.length > 1) {
    shortCalculatorPath =
      calculatorPathParts[calculatorPathParts.length - 2] +
      "." +
      shortCalculatorPath;
    if (calculatorPathParts.length > 2) {
      shortCalculatorPath = "..." + shortCalculatorPath;
    }
  }
  return shortCalculatorPath;
}

function getColor(futureState: string, theme: Theme): PaletteColor {
  if (futureState === "RESOLVED") {
    return theme.palette.success;
  }
  if (["SCHEDULED", "RAN"].includes(futureState)) {
    return theme.palette.info;
  }
  if (["FAILED", "NESTED_FAILED"].includes(futureState)) {
    return theme.palette.error;
  }
  return {
    light: theme.palette.grey[400],
    dark: theme.palette.grey[600],
    main: theme.palette.grey[400],
    contrastText: "",
  };
}

export default function RunNode(props: NodeProps) {
  const run: Run = props.data.run;
  let shortCalculatorPath = getShortCalculatorPath(run.calculator_path);
  const theme = useTheme();
  let color = getColor(run.future_state, theme);

  return (
    <>
      <Handle
        isConnectable={props.isConnectable}
        type="target"
        position={Position.Top}
      />
      <Alert
        //severity="success"
        variant="outlined"
        icon={<RunStateChip state={run.future_state} />}
        id={props.data.run.id}
        style={{
          height: "-webkit-fill-available",
        }}
        sx={{
          paddingX: 3,
          cursor: "pointer",
          borderColor: lighten(color.light, props.selected ? 0 : 0.3),
          backgroundColor: lighten(color.light, props.selected ? 0.7 : 0.9),
          "&:hover": {
            backgroundColor: lighten(color.light, props.selected ? 0.7 : 0.87),
          },
          //display: "-webkit-inline-flex",
        }}
      >
        <AlertTitle>{props.data.label}</AlertTitle>
        <CalculatorPath calculatorPath={shortCalculatorPath} />
      </Alert>
      <Handle
        isConnectable={props.isConnectable}
        type="source"
        position={Position.Bottom}
      />
    </>
  );
}
