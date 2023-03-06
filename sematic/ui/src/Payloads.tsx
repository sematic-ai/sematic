import { Artifact, Edge, Note, Resolution, Run, User } from "./Models";

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

export type ResolutionPayload = {
  content: Resolution;
};

export type ArtifactMap = {
  input: Map<string, Artifact>;
  output: Map<string, Artifact>;
};

export type RunArtifactMap = Map<string, ArtifactMap>;

export type ArtifactListPayload = {
  content: Artifact[];
};

export type EdgeListPayload = {
  content: Edge[];
};

export type RunGraphPayload = {
  root_id: string;
  runs: Run[];
  edges: Edge[];
  artifacts: Artifact[];
};

export type LogLineResult = {
  more_before: boolean;
  more_after: boolean;
  lines: string[];
  continuation_cursor: string | null;
  log_info_message: string | null;
};

export type LogLineRequestResponse = {
  content: LogLineResult;
};

export type NoteListPayload = {
  content: Note[];
  authors: User[];
};

export type NoteCreatePayload = {
  content: Note;
};

export type GoogleLoginPayload = {
  user: User;
};

export type AuthenticatePayload = {
  authenticate: boolean;
  providers: {
    GOOGLE_OAUTH_CLIENT_ID?: string;
    GITHUB_OAUTH_CLIENT_ID?: string;
  };
};

export type EnvPayload = {
  env: { [k: string]: string };
};

export type SemanticVersion = [number, number, number];

export interface VersionPayload {
  min_client_supported: SemanticVersion;
  server: SemanticVersion;
} 

type Operator = "eq";

type FilterCondition = {
    [key: string]: {[eq in Operator]? : string | null} | undefined
}

export type Filter = FilterCondition | {
    AND : Array<FilterCondition>
} | {
  OR : Array<FilterCondition>
}

export type CompactMetrics = {
  [name: string]: {[rootId: string]: [number, Date, string | null][]}
}

export type CompactMetricsPayload = {
  content: CompactMetrics
}
