import {
  lighten,
  Paper,
  useTheme,
} from "@mui/material";
import SettingsIcon from '@mui/icons-material/Settings';
import { Handle, NodeProps, Position } from "react-flow-renderer";
import { Run } from "../../Models";
import { getColor } from "../../components/utils/graphUtils";

export default function HiddenRunNode(props: NodeProps) {
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
            backgroundColor: lighten(color.light, 0.5),
            border: 0,
          }}
        />
      ))}
      
      <Paper
        variant="outlined"
        id={props.data.run.id}
        style={{
          height: "-webkit-fill-available",
        }}
        sx={{
          paddingX: 2,
          marginX: 0.5,
          paddingY: 1,
          cursor: "pointer",
          borderColor: lighten(color.light, 0.5),
          backgroundColor: lighten(color.light, props.selected ? 0.7 : 0.9),
          color: color.dark
        }}
      >
        <SettingsIcon />
      </Paper>
      <Handle
        id={run.id}
        isConnectable={false}
        type="source"
        position={Position.Bottom}
        style={{
          backgroundColor: lighten(color.light, 0.5),
          border: 0,
        }}
      />
    </>
  );
}
