import Box from "@mui/material/Box";
import { useCallback, useContext, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { UserContext } from "..";
import PipelineBar from "../components/PipelineBar";
import PipelinePanels from "../components/PipelinePanels";
import { Resolution, Run } from "../Models";
import { ResolutionPayload, RunViewPayload } from "../Payloads";
import { fetchJSON } from "../utils";

export default function PipelineRunView() {
  const [rootRun, setRootRun] = useState<Run | undefined>(undefined);
  const [resolution, setResolution] = useState<Resolution | undefined>(
    undefined
  );

  const { user } = useContext(UserContext);

  const params = useParams();

  const { calculatorPath, rootId } = params;

  const fetchRootRun = useCallback(
    (rootId: string) => {
      fetchJSON({
        url: "/api/v1/runs/" + rootId,
        apiKey: user?.api_key,
        callback: (payload: RunViewPayload) => setRootRun(payload.content),
      });
    },
    [setRootRun, user?.api_key]
  );

  const fetchResolution = useCallback(
    (rootId: string) => {
      fetchJSON({
        url: "/api/v1/resolutions/" + rootId,
        apiKey: user?.api_key,
        callback: (payload: ResolutionPayload) =>
          setResolution(payload.content),
      });
    },
    [setResolution, user?.api_key]
  );

  useEffect(() => {
    fetchRootRun(rootId!);
    fetchResolution(rootId!);
  }, [rootId, fetchRootRun, fetchResolution]);

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
          rootRun={rootRun}
          resolution={resolution}
        />
        {rootRun && resolution && (
          <PipelinePanels
            rootRun={rootRun}
            resolution={resolution}
            onRootRunUpdate={setRootRun}
          />
        )}
      </Box>
    );
  }
  return <></>;
}
