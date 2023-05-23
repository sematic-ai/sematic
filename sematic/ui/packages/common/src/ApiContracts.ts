import { Resolution, Run, User } from "src/Models";

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

type Operator = "eq";

export type FilterCondition = {
    [key: string]: { [eq in Operator]?: string | null } | undefined
}

export type Filter = FilterCondition | {
    AND: Array<FilterCondition>
} | {
    OR: Array<FilterCondition>
}

