import Box from "@mui/material/Box";
import { useContext, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { UserContext } from "..";
import PipelineBar from "../components/PipelineBar";
import PipelinePanels from "../components/PipelinePanels";
import { Resolution, Run } from "../Models";
import { ResolutionPayload, RunViewPayload } from "../Payloads";
import { fetchJSON } from "../utils";

export default function PipelineView() {
  const [rootRun, setRootRun] = useState<Run | undefined>(undefined);
  const [resolution, setResolution] = useState<Resolution | undefined>(undefined);

  const { user } = useContext(UserContext);

  const params = useParams();

  const { calculatorPath, rootId } = params;

  useEffect(() => {
    if (!rootId) return;
    fetchJSON({
      url: "/api/v1/runs/" + rootId,
      apiKey: user?.api_key,
      callback: (payload: RunViewPayload) => setRootRun(payload.content),
    });
    fetchJSON({
      url: "/api/v1/resolutions/" + rootId,
      apiKey: user?.api_key,
      callback: (payload: ResolutionPayload) => setResolution(payload.content),
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
          initialResolution={resolution}
        />
        {rootRun && <PipelinePanels rootRun={rootRun}/>}
      </Box>
    );
  }
  return <></>;
}
