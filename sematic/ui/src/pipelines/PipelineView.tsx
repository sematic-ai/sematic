import Box from "@mui/material/Box";
import { useState } from "react";
import { Run } from "../Models";
import { useParams } from "react-router-dom";
import PipelineBar from "../components/PipelineBar";
import PipelinePanels from "../components/PipelinePanels";

export default function PipelineView() {
  const [rootRun, setRootRun] = useState<Run | undefined>(undefined);

  const params = useParams();

  const { calculatorPath } = params;

  if (calculatorPath) {
    return (
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "250px 1fr 250px",
          gridTemplateRows: "70px 1fr",
          height: "100vh",
        }}
      >
        <PipelineBar
          calculatorPath={calculatorPath}
          onRootRunChange={setRootRun}
        />
        {rootRun && <PipelinePanels rootRun={rootRun} />}
      </Box>
    );
  }
  return <></>;
}
