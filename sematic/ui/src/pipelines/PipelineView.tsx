import Box from "@mui/material/Box";
import { useEffect, useMemo, useState } from "react";
import { Run } from "../Models";
import { useParams } from "react-router-dom";
import PipelineBar from "../components/PipelineBar";
import PipelinePanels from "../components/PipelinePanels";
import { fetchJSON } from "../utils";
import { RunViewPayload } from "../Payloads";

export default function PipelineView() {
  const [rootRun, setRootRun] = useState<Run | undefined>(undefined);

  const params = useParams();

  const { calculatorPath, rootId } = params;

  useEffect(() => {
    if (!rootId) return;
    fetchJSON({
      url: "/api/v1/runs/" + rootId,
      callback: (payload: RunViewPayload) => setRootRun(payload.content),
    });
  }, [rootId]);

  useMemo(() => {
    if (rootRun === undefined) return;
    var runURL =
      window.location.protocol +
      "//" +
      window.location.host +
      "/pipelines/" +
      rootRun.calculator_path +
      "/" +
      rootRun.id;
    window.history.pushState({ path: runURL }, "", runURL);
  }, [rootRun]);

  if (calculatorPath) {
    return (
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "250px 1fr 350px",
          gridTemplateRows: "70px 1fr",
          height: "100vh",
        }}
      >
        <PipelineBar
          calculatorPath={calculatorPath}
          onRootRunChange={setRootRun}
          setInitialRootRun={rootId === undefined}
          initialRootRun={rootRun}
        />
        {rootRun && <PipelinePanels rootRun={rootRun} />}
      </Box>
    );
  }
  return <></>;
}
