import { Run } from "src/Models";

export type RunListPayload = {
    current_page_url: string;
    next_page_url?: string;
    limit: number;
    next_cursor?: string;
    after_cursor_count: number;
    content: Run[];
};

type Operator = "eq";

type FilterCondition = {
    [key: string]: { [eq in Operator]?: string | null } | undefined
}

export type Filter = FilterCondition | {
    AND: Array<FilterCondition>
} | {
    OR: Array<FilterCondition>
}

