import { Artifact, Edge, Resolution, Run, User } from "@sematic/common/src/Models";

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
    can_continue_backward: boolean;
    can_continue_forward: boolean;
    lines: string[];
    line_ids: number[];
    forward_cursor_token: string | null;
    reverse_cursor_token: string | null;
    log_info_message: string | null;
};

export type LogLineRequestResponse = {
    content: LogLineResult;
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
