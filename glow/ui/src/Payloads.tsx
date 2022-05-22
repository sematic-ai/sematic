import { Run, Artifact } from "./Models";

export type RunListPayload = {
  current_page_url: string;
  next_page_url?: string;
  limit: number;
  next_cursor?: string;
  after_cursor_count: number;
  content: Array<Run>;
};

export type RunViewPayload = {
  content: Run;
};

export type ArtifactListPayload = {
  content: Array<Artifact>;
  extra: {
    run_mapping: {
      [runId: string]: {
        input: { [name: string]: string };
        output: { [name: string]: string };
      };
    };
  };
};
