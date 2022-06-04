import {
  Alert,
  AlertTitle,
  Box,
  lighten,
  PaletteColor,
  Theme,
  useTheme,
} from "@mui/material";
import { Handle, NodeProps, Position } from "react-flow-renderer";
import { Run } from "../Models";
import CalculatorPath from "./CalculatorPath";
import RunStateChip from "./RunStateChip";
import Tags from "./Tags";

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

function getChipColor(
  futureState: string
):
  | "default"
  | "primary"
  | "secondary"
  | "error"
  | "info"
  | "success"
  | "warning"
  | undefined {
  if (futureState === "RESOLVED") {
    return "success";
  }
  if (["SCHEDULED", "RAN"].includes(futureState)) {
    return "info";
  }
  if (["FAILED", "NESTED_FAILED"].includes(futureState)) {
    return "error";
  }
  return "default";
}

export default function RunNode(props: NodeProps) {
  const run: Run = props.data.run;
  // let shortCalculatorPath = getShortCalculatorPath(run.calculator_path);
  const calculatorPathParts = run.calculator_path.split(".");
  let shortCalculatorPath = calculatorPathParts[calculatorPathParts.length - 1];
  const theme = useTheme();
  let color = getColor(run.future_state, theme);

  return (
    <>
      {props.data.argNames.map((argName: string) => (
        <Handle
          key={argName}
          isConnectable={false}
          id={argName}
          position={Position.Top}
          type="target"
          style={{
            backgroundColor: lighten(color.light, props.selected ? 0.5 : 0.5),
            border: 0,
          }}
        />
      ))}
      {/*<Handle
        isConnectable={false}
        type="target"
        position={Position.Top}
        style={{
          backgroundColor: lighten(color.light, props.selected ? 0.5 : 0.5),
          border: 0,
        }}
      />*/}
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
          borderColor: lighten(color.light, props.selected ? 0.5 : 0.5),
          backgroundColor: lighten(color.light, props.selected ? 0.7 : 0.9),
          "&:hover": {
            backgroundColor: lighten(color.light, props.selected ? 0.7 : 0.87),
          },
          //display: "-webkit-inline-flex",
        }}
      >
        <AlertTitle>{run.name}</AlertTitle>
        <CalculatorPath calculatorPath={shortCalculatorPath} />
        <Box marginTop={1}>
          <Tags
            tags={run.tags}
            chipProps={{ color: getChipColor(run.future_state) }}
          />
        </Box>
      </Alert>
      <Handle
        id={run.id}
        isConnectable={false}
        type="source"
        position={Position.Bottom}
        style={{
          backgroundColor: lighten(color.light, props.selected ? 0.5 : 0.5),
          border: 0,
        }}
      />
    </>
  );
}
