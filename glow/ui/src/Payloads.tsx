import { Run, Artifact } from "./Models";

export type RunListPayload = {
  current_page_url: string;
  next_page_url?: string;
  limit: number;
  next_cursor?: string;
  after_cursor_count: number;
  content: Run[];
};

export type RunViewPayload = {
  content: Run;
};

export type ArtifactMap = {
  input: Map<string, Artifact>;
  output: Map<string, Artifact>;
};

export type RunArtifactMap = Map<string, ArtifactMap>;

export type ArtifactListPayload = {
  content: Artifact[];
  extra: {
    run_mapping: {
      [runId: string]: {
        input: { [name: string]: string };
        output: { [name: string]: string };
      };
    };
  };
};

export function buildArtifactMap(payload: ArtifactListPayload): RunArtifactMap {
  let artifactsByID: Map<string, Artifact> = new Map();
  payload.content.forEach((artifact) =>
    artifactsByID.set(artifact.id, artifact)
  );
  let runArtifactMap: RunArtifactMap = new Map();
  Object.entries(payload.extra.run_mapping).forEach(([runId, mapping]) => {
    let inputArtifacts: Map<string, Artifact> = new Map();
    let outputArtifacts: Map<string, Artifact> = new Map();
    Object.entries(mapping).forEach(([relationship, artifacts]) => {
      Object.entries(artifacts).forEach(([name, artifactId]) => {
        let artifact = artifactsByID.get(artifactId);
        if (artifact) {
          let map = relationship === "input" ? inputArtifacts : outputArtifacts;
          map.set(name, artifact);
        } else {
          throw Error("Missing artifact");
        }
      });
    });
    runArtifactMap.set(runId, {
      input: inputArtifacts,
      output: outputArtifacts,
    });
  });

  return runArtifactMap;
}
