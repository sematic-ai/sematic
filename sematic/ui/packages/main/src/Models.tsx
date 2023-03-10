import { AnyTypeSerialization } from "./types/Types";

export type TypeGitInfo = {
  remote: string;
  branch: string;
  commit: string;
  dirty: boolean;
};

export type Resolution = {
  root_id: string;
  status: string;
  kind: string;
  container_image_uri: string | null;
  git_info_json: TypeGitInfo | null;
  settings_env_vars: Map<string, string>;
  external_jobs_json: Map<string, any> | null;
};

export type ExceptionMetadata = {
  repr: string;
  name: string;
  module: string;
};

export type User = {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;
  // only returned if user is self
  api_key: string | null;
};

export interface HasUserMixin {
  user_id: string | null;
  user: User | null;
}

export interface Run extends HasUserMixin {
  id: string;
  original_run_id: string | null;
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
  type_serialization: AnyTypeSerialization;
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

export interface Note extends HasUserMixin {
  id: string;
  note: string;
  run_id: string;
  root_id: string;
  created_at: Date;
  updated_at: Date;
};

export type ExternalResourceState = 
"CREATED" |
"ACTIVATING" |
"ACTIVE" |
"DEACTIVATING" |
"DEACTIVATED";

export type ExternalResource = {
  id: string,
  resource_state: ExternalResourceState,
  managed_by: string,
  status_message: string,
  last_updated_epoch_seconds: Date,
  type_serialization: AnyTypeSerialization,
  value_serialization: any,
  history_serializations: any,
  created_at: Date
  updated_at: Date
};

export type ExternalResourceHistorySerialization = {
  root_type: AnyTypeSerialization,
  types: unknown,
  values: {
    allocation_seconds: number,
    deallocation_seconds: number,
    epoch_time_activation_began: any,
    epoch_time_deactivation_began: any,
    id: string,
    max_active_seconds: number,
    message: string,
    status: {
      root_type: AnyTypeSerialization,
      values: {
        last_update_epoch_time: number,
        managed_by: string,
        message: string,
        state: ExternalResourceState
      }
    }
  }
};


