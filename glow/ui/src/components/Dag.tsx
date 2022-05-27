import { Run } from "../Models";
import ReactFlow from "react-flow-renderer";
import Typography from "@mui/material/Typography";
import { Container } from "@mui/material";

interface DagProps {
  runs?: Array<Run>;
}

function Dag(props: DagProps) {
  const initialNodes = [
    {
      id: "1",
      data: { label: "ABC" },
      position: { x: 250, y: 25 },
    },

    {
      id: "2",
      data: { label: <div>Default Node</div> },
      position: { x: 100, y: 125 },
    },
    {
      id: "3",
      data: { label: "Output Node" },
      position: { x: 250, y: 250 },
    },
  ];

  const initialEdges = [
    { id: "e1-2", source: "1", target: "2" },
    { id: "e2-3", source: "2", target: "3" },
  ];
  return (
    <>
      <Typography variant="h6">Execution graph</Typography>
      <Container sx={{ width: "100%", height: "1000px" }}>
        <ReactFlow nodes={initialNodes} edges={initialEdges} />
      </Container>
    </>
  );
}

export default Dag;
