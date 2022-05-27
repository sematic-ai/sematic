import { Canvas, CanvasPosition, EdgeData, NodeData } from "reaflow";
import { useEffect, useMemo, useState } from "react";
import { Artifact, Run } from "../Models";
import Loading from "./Loading";
import Box from "@mui/material/Box";
import {
  ArtifactListPayload,
  buildArtifactMap,
  RunArtifactMap,
  RunListPayload,
} from "../Payloads";

interface ReaflowDagProps {
  rootId: string;
}

function fetchJSON(
  url: string,
  callback: (payload: any) => void,
  setError?: (error: Error) => void,
  setIsLoaded?: (isLoaded: boolean) => void
) {
  fetch(url)
    .then((res) => res.json())
    .then(
      (payload) => callback(payload),
      (error) => {
        setError && setError(error);
        setIsLoaded && setIsLoaded(true);
      }
    );
}

function ReaflowDag(props: ReaflowDagProps) {
  let rootId = props.rootId;
  const [runs, setRuns] = useState<Map<string, Run[]>>(new Map());
  const [error, setError] = useState<Error | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);
  const [runArtifactMap, setRunArtifactMap] = useState<RunArtifactMap>(
    new Map()
  );

  useEffect(() => {
    let filters = JSON.stringify({ root_id: { eq: rootId } });
    fetchJSON(
      "/api/v1/runs?limit=-1&filters=" + filters,
      (payload: RunListPayload) => {
        setRuns(new Map(runs.set(rootId, payload.content)));
        let runIds = JSON.stringify(payload.content.map((run) => run.id));
        fetchJSON(
          "/api/v1/artifacts?run_ids=" + runIds,
          (payload: ArtifactListPayload) => {
            let fetchedRunArtifactMap = buildArtifactMap(payload);
            let newRunArtifactMap = new Map(runArtifactMap);
            fetchedRunArtifactMap.forEach((artifactMap, runId) => {
              newRunArtifactMap.set(runId, artifactMap);
            });
            setRunArtifactMap(newRunArtifactMap);
            setIsLoaded(true);
          },
          setError,
          setIsLoaded
        );
      },
      setError,
      setIsLoaded
    );
  }, [rootId]);

  let nodes: NodeData[] = [];
  let edges: EdgeData[] = [];

  let dagRuns = runs.get(rootId);

  if (dagRuns) {
    nodes = dagRuns.map((run) => {
      return {
        id: run.id,
        text: run.name,
        parent: run.parent_id === null ? undefined : run.parent_id,
      };
    });
    let dagRunIds = dagRuns.map((run) => run.id);
    let artifacts: Map<
      string,
      { inputTo: [string, string][]; outputOf: string | undefined }
    > = new Map();
    runArtifactMap.forEach((artifactMap, runId) => {
      // Not in current DAG
      if (!dagRunIds.find((dagRunId) => dagRunId === runId)) return;

      artifactMap.input.forEach((artifact, name) => {
        let inputTo = artifacts.get(artifact.id)?.inputTo || [];
        inputTo.push([name, runId]);
        artifacts.set(artifact.id, {
          inputTo: inputTo,
          outputOf: artifacts.get(artifact.id)?.outputOf,
        });
      });
      artifactMap.output.forEach((artifact, name) => {
        artifacts.set(artifact.id, {
          inputTo: artifacts.get(artifact.id)?.inputTo || [],
          outputOf: runId,
        });
      });
    });
    artifacts.forEach((io, artifactId) => {
      if (!io.outputOf) return;
      io.inputTo.forEach(([name, inputToRunId]) => {
        edges.push({
          id: name,
          from: io.outputOf,
          to: inputToRunId,
        });
      });
    });
  }
  /*[
    {
      id: "1-2",
      from: "1",
      to: "2",
    },
  ];*/
  console.log(nodes);
  console.log(edges);
  if (error || !isLoaded) {
    return (
      <Box textAlign="center">
        <Loading error={error} isLoaded={isLoaded} />
      </Box>
    );
  }
  return (
    <>
      <Canvas
        nodes={nodes}
        edges={edges}
        defaultPosition={CanvasPosition.TOP}
        readonly
      />
    </>
  );
}

export default ReaflowDag;
