import { TypeSerialization } from "./types/Types";

export type TypeGitInfo = {
  remote: string;
  branch: string;
  commit: string;
  dirty: boolean;
}

export type Resolution = {
  root_id: string,
  status: string,
  kind: string,
  docker_image_uri: string | null,
  git_info_json: TypeGitInfo | null,
  settings_env_vars: Map<string, string>;
  external_jobs_json: Map<string, any> | null;
}

export type ExceptionMetadata = {
  repr: string;
  name: string;
  module: string;
};

export type Run = {
  id: string;
  future_state: string;
  name: string;
  calculator_path: string;
  description: string | null;
  source_code: string;
  exception_metadata_json: ExceptionMetadata | null;
  external_exception_metadata_json: ExceptionMetadata | null;
  tags: Array<string>;
  parent_id: string | null;
  root_id: string;
  created_at: Date;
  updated_at: Date;
  started_at: Date | null;
  ended_at: Date | null;
  resolved_at: Date | null;
  failed_at: Date | null;
};

export type Artifact = {
  id: string;
  json_summary: any;
  type_serialization: TypeSerialization;
  created_at: Date;
  updated_at: Date;
};

export type Edge = {
  id: string;
  source_run_id: string | null;
  source_name: string | null;
  destination_run_id: string | null;
  destination_name: string | null;
  artifact_id: string | null;
  parent_id: string | null;
  created_at: Date;
  updated_at: Date;
};

export type Note = {
  id: string;
  author_id: string;
  note: string;
  run_id: string;
  root_id: string;
  created_at: Date;
  updated_at: Date;
};

export type User = {
  email: string;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;
  // only returned if user is self
  api_key: string | null;
};
