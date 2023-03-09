import { Box, Chip } from "@mui/material";
import { Handle, NodeProps, Position } from "react-flow-renderer";

export default function ArtifactNode(props: NodeProps) {
  let handleStyle = { border: 0, backgroundColor: "rgba(0, 0, 0, 0.1)" };
  return (
    <>
      {props.data.sourceRunId !== null && (
        <Handle
          isConnectable={false}
          position={Position.Top}
          type="target"
          style={handleStyle}
        />
      )}
      <Box id={props.data.nodeId}>
        <Chip
          label={props.data.label || "<output>"}
          sx={{
            border: 1,
            backgroundColor: "rgba(255, 255, 255, 0.3)",
            borderColor: "rgba(0, 0, 0, 0.1)",
          }}
          size="small"
        />
      </Box>
      {props.data.destinationRunId && (
        <Handle
          isConnectable={false}
          position={Position.Bottom}
          type="source"
          style={handleStyle}
        />
      )}
    </>
  );
}
