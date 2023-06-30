import { Artifact, Edge, Job, Note, Resolution, Run, User } from "src/Models";

export type RunViewPayload = {
    content: Run;
};

export type RunListPayload = {
    current_page_url: string;
    next_page_url?: string;
    limit: number;
    next_cursor?: string;
    after_cursor_count: number;
    content: Run[];
};

export type ResolutionPayload = {
    content: Resolution;
};

export type RunGraphPayload = {
    root_id: string;
    runs: Run[];
    edges: Edge[];
    artifacts: Artifact[];
};

export type RunJobPayload = {
    content: Array<Job>;
};

export type NoteListPayload = {
    content: Note[];
    authors: User[];
};

export type NoteCreateRequestPayload = {
    note: {
        author_id: string,
        note: string,
        root_id: string,
        run_id: string,
    }
};

export type NoteCreateResponsePayload = {
    content: Note;
};


export type UserListPayload = {
    content: User[];
};

export type BasicMetricsPayload = {
    content: {
        avg_runtime_children: {[k: string]: number},
        count_by_state: {[k: string]: number},
        total_count: number
    }
}

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


type Operator = "eq" | "contains" | "in";

export type FilterCondition = {
    [key: string]: { [eq in Operator]?: string | null | Array<string> } | undefined
}

export type Filter = FilterCondition | {
    AND: Array<FilterCondition>
} | {
    OR: Array<FilterCondition>
}

export type MetricsPayload = {
    content: {
        metric_name: string;
        metric_type: string;
        columns: string[];
        series: [number, any[]][];
    };
};
