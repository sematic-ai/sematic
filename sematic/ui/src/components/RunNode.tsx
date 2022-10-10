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
import RunStateChip from "./RunStateChip";

function getColor(futureState: string, theme: Theme): PaletteColor {
  if (futureState === "RESOLVED") {
    return theme.palette.success;
  }
  if (futureState === "RETRYING") {
    return theme.palette.warning;
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
        icon={false}
        id={props.data.run.id}
        style={{
          height: "-webkit-fill-available",
        }}
        sx={{
          paddingX: 3,
          cursor: "pointer",
          borderColor: lighten(color.light, props.selected ? 0.5 : 0.5),
          backgroundColor: lighten(color.light, props.selected ? 0.7 : 0.9),
          //"&:hover": {
          //  backgroundColor: lighten(color.light, props.selected ? 0.7 : 0.87),
          //},
          //display: "-webkit-inline-flex",
        }}
      >
        <AlertTitle>
          <RunStateChip state={run.future_state} />
          {run.name}
        </AlertTitle>
        {/*<CalculatorPath calculatorPath={shortCalculatorPath} />*/}
        <Box marginTop={1}>
          {/*
          <Tags
            tags={run.tags}
            chipProps={{ color: getChipColor(run.future_state) }}
          />*/}
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
